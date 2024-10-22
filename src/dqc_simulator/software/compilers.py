# -*- coding: utf-8 -*-
"""
Distributed quantum computing compilers.

These compilers take a list of gate tuples, and output a time-sliced dictionary
of what happens on each individual QPU. 

Notes
-----
Some compilation is also done in dqc_control.py. There common 
subroutines used by Cat-comm and TP-comm are broken down into individual gates
and run on individual nodes. The role of these compilers is to break a 
monolithic quantum circuit into the lower level commands used in
:mod: `~dqc_simulator.software.dqc_control`.
That said, very general compilers can be defined here. The main limitations are
that they use only intraprocessor quantum gates and the interprocessor 
subroutines involved in Cat and TP-comm (at least for now) and that the backend
defined in :mod: `~dqc_simulator.software.dqc_control` may not be able to cope
with carrying out multiple inter-QPU gates on a given node within the same
time-slice. Each time slice is intended to be 
greedily compiled and executed by functions in 
:mod: `~dqc_simulator.software.dqc_control` but near-arbitrary compilation can
be done by careful choice of the time slices. 
"""

#Note: some compilation is also done in dqc_control.py. There common 
#subroutines used by Cat-comm and TP-comm are broken down into individual gates
#and run on individual nodes. The role of these compilers is to break a 
#monolithic quantum circuit into the lower level commands used in dqc_control.py.
#That said, very general compilers can be defined here. The only limitation is
#that they use only intraprocessor quantum gates and the interprocessor 
#subroutines involved in Cat and TP-comm

from collections import Counter
from functools import partial

import netsquid as ns
from netsquid.components import instructions as instr




class QpuOps():
    """
    Data structure for tracking the operations of all QPUs within a DQC.
    
    Attributes
    ----------
    ops : dict
        The operations to carry out on each QPU in a DQC.
        
    """
    
    def __init__(self):
        self.ops = {}
# =============================================================================
#         self.comm_schemes = {
#             'cat' : self.cat_comm, 
#             'tp_risky' : self.tp_risky,
#             'tp_safe' : self.tp_safe}
# =============================================================================

    def add_empty_node_entry(self, node_name):
        self.ops[node_name] = [[]]

    def append_op2current_time_slice(self, node_name, op):
        self.ops[node_name][-1].append(op)
    
    def append_multiple_ops2current_time_slice(self, node_name, ops):
        self.ops[node_name][-1] = self.ops[node_name][-1] + ops

    def add_op(self, node_name, op):
        if node_name in self.ops:
            self.append_op2current_time_slice(node_name, op)
        else:
            self.add_empty_node_entry(node_name)
            self.append_op2current_time_slice(node_name, op)
            
    def add_time_slice(self, node_name):
        self.ops[node_name].append([])
            
    def pad_num_time_slices_until_matching(self, 
                                           node_with_fewer_time_slices,
                                           node_with_more_time_slices):
        length_diff = (len(self.ops[node_with_more_time_slices]) - 
                       len(self.ops[node_with_fewer_time_slices]))
        #adding empty time slices to make lengths match (enforcing
        #scheduling)
        start = len(self.ops[node_with_fewer_time_slices])
        end = start + length_diff
        for ii in range(start, end):
            self.add_time_slice(node_with_fewer_time_slices)

    def make_num_time_slices_match(self, node0_name, node1_name):
        if (len(self.ops[node0_name])
            > len(self.ops[node1_name])):
            self.pad_num_time_slices_until_matching(node1_name, node0_name)
        elif (len(self.ops[node0_name])
              < len(self.ops[node1_name])): 
            self.pad_num_time_slices_until_matching(node0_name, node1_name)
            
    def check_if_all_nodes_have_empty_trailing_time_slice(self):
        """
        

        Returns
        -------
        all_nodes_have_empty_trailing_time_slice : bool
            True if all nodes have an empty trailing time slice and false 
            otherwise.
        """
        all_nodes_have_empty_trailing_time_slice = True
        for node_key in self.ops:
            if self.ops[node_key][-1]:
            #if the last time slice is non-empty:
                all_nodes_have_empty_trailing_time_slice = False
        return all_nodes_have_empty_trailing_time_slice
                
    def remove_empty_trailing_time_slices(self):
        """
        Remove empty trailing time slices if they appear for all QPUs.
        
        The constant number of time slices for all nodes is retained.
        """
        need2remove_trailing_time_slices = ( 
            self.check_if_all_nodes_have_empty_trailing_time_slice())
        if need2remove_trailing_time_slices:
            #removing last time slice from each node
            for node_key in self.ops:
                del self.ops[node_key][-1]
        
# =============================================================================
#         for node_key in self.ops:
#             if not self.ops[node_key][-1]:
#             #if last time slice is empty:
#                 del self.ops[node_key][-1]
# =============================================================================
            
    def cat_comm(self, gate_instructions, qubit_index0, qubit_index1,
                       node0_name, node1_name):
        node0_ops = (
            [(qubit_index0, node1_name, "cat", "entangle")] + 
            [(qubit_index0, node1_name, "cat", "disentangle_end")])
        node1_ops = (
            [(node0_name, "cat", "correct")]
            + gate_instructions + 
            [(qubit_index1, node0_name,
              "cat", "disentangle_start")])
        self.append_multiple_ops2current_time_slice(node0_name, node0_ops)
        self.append_multiple_ops2current_time_slice(node1_name, node1_ops)

    def tp_risky(self, gate_instructions, qubit_index0, node0_name, 
                 node1_name):
        #does not teleport back to original node to free up 
        #comm-qubit
        node0_ops = [(qubit_index0, node1_name, "tp", "bsm")] 
        node1_ops = [(node0_name, "tp", "correct")] + gate_instructions
        self.append_multiple_ops2current_time_slice(node0_name, node0_ops)
        self.append_multiple_ops2current_time_slice(node1_name, node1_ops)
        
    def free_comm_qubit_with_tele(self, qubit_index0,
                                  qubit_index1, node0_name, node1_name):
        #TO DO: potentially deprecate in favour of tele2data_qubit, however
        #this will require changes to dqc_simulator.software.dqc_control
        node0_ops = [(qubit_index0, node1_name, "tp", "bsm")]
        node1_ops = [(node0_name, "tp", "correct4tele_only"),
                       (instr.INSTR_SWAP, -1, qubit_index1)] 
        self.append_multiple_ops2current_time_slice(node0_name, node0_ops)
        self.append_multiple_ops2current_time_slice(node1_name, node1_ops)
        
    def tele2data_qubit(self, qubit_index0, qubit_index1, node0_name,
                       node1_name):
        node0_ops = [(qubit_index0, node1_name, "tp", "bsm")]
        node1_ops = [(qubit_index1, node0_name, "tp", "swap_then_correct")] 
        self.append_multiple_ops2current_time_slice(node0_name, node0_ops)
        self.append_multiple_ops2current_time_slice(node1_name, node1_ops)

    def tp_safe(self, gate_instructions, qubit_index0, qubit_index1,
                node0_name, node1_name):
        #implements tp remote gate then teleports back to original node 
        #to free up comm-qubit.
        #For remote gate:
        self.tp_risky(gate_instructions, qubit_index0, node0_name, 
                      node1_name)
        self.add_time_slice(node0_name)
        self.add_time_slice(node1_name)
        #for teleportation back:
        self.tele2data_qubit(-1, qubit_index0, node1_name, node0_name)
        self.add_time_slice(node0_name)
        self.add_time_slice(node1_name)
        #implements tp remote gate then teleports back to original node 
        #to free up comm-qubit.
# =============================================================================
#         #For remote gate:
#         self.tp_risky(gate_instructions, qubit_index0, node0_name, 
#                       node1_name)
#         self.add_time_slice(node0_name)
#         self.add_time_slice(node1_name)
#         #For teleportation back:
#         self.free_comm_qubit_with_tele(-1, qubit_index0, node1_name,
#                                        node0_name)
#         self.add_time_slice(node0_name)
#         self.add_time_slice(node1_name)
# =============================================================================
        
# =============================================================================
#     def tp_block(self, gate_instructions, qubit_index0, qubit_index1, 
#                  node0_name, node1_name):
#         #Very similar to TP-safe except that the SWAP happens before the 
#         #correction and the measurement dependent gates act on the data qubit
#         #(see figure 2b of published version of AutoComm paper)
#         #For remote gate:
#         self.tp_risky(gate_instructions, qubit_index0, node0_name, 
#                       node1_name)
#         self.add_time_slice(node0_name)
#         self.add_time_slice(node1_name)
#         #for teleportation back:
#         self.tele2data_qubit(-1, qubit_index0, node1_name, node0_name)
#         self.add_time_slice(node0_name)
#         self.add_time_slice(node1_name)
# =============================================================================
            
    def apply_remote_gate(self, scheme, gate_instructions, qubit_index0,
                          qubit_index1, node0_name, node1_name):
        #the use of functools.partial in the following just bakes in the 
        #arguments and allows a single call of the dict to be used despite
        #the arguments being different
        comm_schemes = {
            'cat' : partial(self.cat_comm, gate_instructions, qubit_index0, 
                            qubit_index1, node0_name, node1_name), 
            'tp_risky' : partial(self.tp_risky, gate_instructions,
                                 qubit_index0, node0_name, node1_name),
            'free_comm_qubit_with_tele' : partial(self.free_comm_qubit_with_tele,
                                                  qubit_index0, qubit_index1,
                                                  node0_name, node1_name),
            'tp_safe' : partial(self.tp_safe, gate_instructions, qubit_index0,
                                qubit_index1, node0_name, node1_name)}
                            
        comm_schemes[scheme]()
        


#helper functions:
    
    
def find_qubit_node_pairs(partitioned_gates):
    """
    Parameters
    ----------
    partitioned_gates : list of tuples
        List of tuples with gate information including type of gate, qubit
        indices acted on, node names acted on, and (for remote gates) a string 
        indicating the scheme (here this should be some placeholder string
        as the scheme is not yet decided).
        
    Returns
    -------
    qubit_node_pairs : dict
        All of the gates associated with a qubit-node pair. Qubit-node pairs
        are referred to by a key of the form (qubit0_index, node0_name,
                                              node1_name), where the first two
        entries define the qubit and the latter the node. The remote gates for
        each qubit-node pair are lists of the form [gate, ID] where gate is 
        the gate tuple form partitioned gates and ID

    """
    def _add_entry(a_dict, key, value):
        if key in a_dict:
            a_dict[key].append(value)
        else:
            a_dict[key] = [value]
            
    qubit_node_pairs = {}
    for ii, gate in enumerate(partitioned_gates): #you will also iterate over gates of different
                                   #type in linear merge but I'm not sure this can be
                                   #avoided
        if len(gate) > 3 and gate[2] != gate[4]:
        #if two-qubit remote gate (node names not the same):
            ctrl_qubit = gate[1]
            ctrl_node = gate[2]
            target_qubit = gate[3]
            target_node = gate[4]
            key = (ctrl_qubit, ctrl_node, target_node)
            #first two entries of key needed to fully specify ctrl qubit
            _add_entry(qubit_node_pairs, key, (gate, ii))
            #index ii needed so that duplicate gates can be identified later 
            #and their position in partitioned_gates can be ascertained
            key = (target_qubit, target_node, ctrl_node)
            _add_entry(qubit_node_pairs, key, (gate, ii))
    return qubit_node_pairs

def find_node_node_pairs(partitioned_gates):
    node_node_pairs = {}
    for ii, gate in enumerate(partitioned_gates):
        if len(gate) > 3 and gate[2] != gate[4]:
        #if two-qubit remote gate (node names not the same):
            ctrl_node = gate[2]
            target_node = gate[4]
            key = (ctrl_node, target_node)
            key = tuple(sorted(key)) #puts key in intuitive ordering 
                                     #(eg, node_0, node_1, ... rather than
                                     #node_1, node_0, ...)
            if key in node_node_pairs:
                node_node_pairs[key].append((gate, ii))
                #index ii needed so that the position in partitioned_gates can 
                #be ascertained later, during scheduling, to avoid illegal 
                #commutation
            elif (key[1], key[0]) in node_node_pairs:
                node_node_pairs[(key[1], key[0])].append((gate, ii))
            else:
                node_node_pairs[key] = [(gate, ii)]
    return node_node_pairs


def find_pairs(partitioned_gates, pair_type):
    """
    Parameters
    ----------
    partitioned_gates : list of tuples
        List of tuples with gate information including type of gate, qubit
        indices acted on, node names acted on, and (for remote gates) a string 
        indicating the scheme (here this should be some placeholder string
        as the scheme is not yet decided).
    pair_type : str
        Whether to return 'qubit_node' or 'node_node' pairs.

    Returns
    -------
    pairs : dict
        The remote gates for each qubit-node or node-node pair

    """
    if pair_type == "qubit_node":
        pairs = find_qubit_node_pairs(partitioned_gates)
    elif pair_type == "node_node":
        pairs = find_node_node_pairs(partitioned_gates)
    return pairs

            
def order_pairs(pairs):
    """
    Sorts dict of the remote gates associated with different qubit-node or
    node-node pairs in descending order

    Parameters
    ----------
    pairs : dict
        Sorts dict of the remote gates associated with different qubit-node or
        node-node pairs 

    Returns
    -------
    dict
        The pairs ordered from those with the most remote gates to those with
        the least.

    """
    return dict(sorted(pairs.items(), key=lambda items : len(items[1]),
                       reverse=True))

# =============================================================================
# def something_btwn_gates(all_gates, gate1_info, gate2_info):
#     if element1 
# =============================================================================
    
def get_qubit_id(gate):
    """
    Collecting info needed to uniquely ID the qubits of a gate within a
    partitioned circuit

    Parameters
    ----------
    gate : TYPE
        DESCRIPTION.

    Returns
    -------
    qubit0 : TYPE
        DESCRIPTION.
    qubit1 : TYPE
        DESCRIPTION.

    """
    #TO DO: convert this function to handle multi-qubit gate using the pattern
    #of indices (would need to return a single tuple which can be unpacked)
    if len(gate) == 3:
        qubit_index0 = gate[1]
        qubit_index1 = None
        node_index0 = gate[2]
        node_index1 = None
        qubit1 = (None, None)
    elif len(gate) > 3:
        qubit_index0 = gate[1]
        qubit_index1 = gate[3]
        node_index0 = gate[2]
        node_index1 = gate[4]
        qubit1 = (qubit_index1, node_index1) # fully defining 2nd qubit
    qubit0 = (qubit_index0, node_index0)
    return qubit0, qubit1

def shared_qubit(gate0, gate1):
    gate0qubit0, gate0qubit1 = get_qubit_id(gate0)
    gate1qubit0, gate1qubit1 = get_qubit_id(gate1)
    gate0shares_gate1qubit0 = (
        (gate0qubit0 == gate1qubit0 or gate0qubit0 == gate1qubit1)
        and None not in gate0qubit0)
    gate0shares_gate1qubit1 = (
        (gate0qubit1 == gate1qubit0 or gate0qubit1 == gate1qubit1)
        and None not in gate0qubit1)
    return (gate0shares_gate1qubit0 or 
            gate0shares_gate1qubit1)

def find_consecutive_gate(partitioned_gates, gate, gate_position):
    """
    
    Finds the next gate to the gate from gateNindex which has shared qubits.
    Otherwise, the next gate in partitioned gates may be completely unrelated
    to the gate of interest with no need to maintain their ordering. They 
    may even occur on completely different nodes or pairs of nodes.

    Parameters
    ----------
    partitioned_gates : list of tuples
        DESCRIPTION.
    gate: tuple
        A gate.
    gate_position : int
        The positional index of the gate in partitioned gates.

    Returns
    -------
    nxt_gate : tuple
        The gate consecutive to the gate of interest (inputted as part of
        gateNindex)

    """
    #TO DO: replace following with generator for memory efficiency to avoid
    #storing whole sublist
    unvisited_partitioned_gates = partitioned_gates[gate_position+1:]
    nxt_gate = None
    for gate2check in unvisited_partitioned_gates:
# =============================================================================
#         print(f'gate of interest is {gate}')
#         print(f'gate to check is {gate2check}')
#         print(f'they are consecutive: {shared_qubit(gate, gate2check)}')
# =============================================================================
        if shared_qubit(gate, gate2check):
            nxt_gate = gate2check
# =============================================================================
#             print(f'consecutive gate is {gate2check}')
# =============================================================================
            break
    return nxt_gate


#TO DO: think about whether the following function should be internal to 
#aggregate_comms (in which case filtered_remote_gates would be qubit_node_pairs)
def find_consecutive_remote_gates(partitioned_gates, filtered_remote_gates):
    """
    Finds the consecutive gates in a filtered set of remote gates (eg, those
    in the same qubit-node or node-node pair)

    Parameters
    ----------
    partitioned_gates : list of tuples
        All gates in quantum circuit (partitioned into different nodes)
    filtered_remote_gates : list of tuples of form 
                            (gate, postional index of gate within partitioned gates)
        The filtered list of remote gates and their positional indices wrt
        the overall list of partitioned gates.
        

    Returns
    -------
    burst_comm_blocks : list of lists
        The identified burst communication blocks as found in the first step of 
        the autocomm communication aggregation process (identifying blocks)
        without circuit restructuring.

    """
    current_filtered_gateNindex = filtered_remote_gates[0]
    current_filtered_gate = current_filtered_gateNindex[0]
    current_filtered_gate_position = current_filtered_gateNindex[1]
    burst_comm_blocks = [[current_filtered_gateNindex]]
    unvisited_gates = filtered_remote_gates[1:]
    for ii, nxt_remote_gateNindex in enumerate(unvisited_gates, start=1):
        nxt_filtered_gate = nxt_remote_gateNindex[0]
        nxt_filtered_gate_position = nxt_remote_gateNindex[1]
        nxt_partitioned_gate = find_consecutive_gate(partitioned_gates,
                                                     current_filtered_gate,
                                                     current_filtered_gate_position)
        if nxt_partitioned_gate == nxt_filtered_gate:
        #if the remote gates from the filtered set ARE consecutive:
            burst_comm_blocks[-1].append(nxt_remote_gateNindex)
        else:
        #if the remote gates from the filtered set are NOT consecutive:
            burst_comm_blocks.append([nxt_remote_gateNindex])
        current_filtered_gate = nxt_filtered_gate
        current_filtered_gate_position = nxt_filtered_gate_position
    #removing trailing empty sublist
    if not burst_comm_blocks[-1]:
    #if final element empty:
        del burst_comm_blocks[-1]
    return burst_comm_blocks
    #TO DO: figure out why this is not giving desired output
            
        
    

# =============================================================================
# def aggregate_comms(partitioned_gates):
#     qubit_node_pairs = find_pairs(partitioned_gates, 'qubit_node')
#     #ordering pairs by number of associated remote gates (largest first):
#     qubit_node_pairs = order_pairs(qubit_node_pairs)
#     for qubit_node_pair in qubit_node_pairs:
#         burst_comm_blocks = find_consecutive_remote_gates(partitioned_gates,
#                                                           qubit_node_pairs)
#         #linear fusion here on burst_comm_blocks
# # =============================================================================
# #         for remote_gateNindex in qubit_node_pair:
# #             pos_in_partitioned_gates = remote_gateNindex[1]
# # =============================================================================
# #TO DO (longer term): generalise aggregate_comms to work with node-node pairs as well
# =============================================================================

#compilers

def sort_greedily_by_node_and_time(partitioned_gates):
    """
    Distributes the circuit between nodes and splits into explicit time-slices
    (rows in output array). Initialisation of qubits must be specified as 
    an instruction in the partitioned_gates input.
    
    Parameters
    ----------
    partitioned_gates:  list of tuples
        The gates in the entire circuit. The tuples should be of the form:
        1) single-qubit gate: (gate_instr, qubit, node_name)
        2) two-qubit gate: (list of instructions or gate_instruction or
                            instruction_tuple if local,
                            qubit0, node0_name, qubit1, node1_name, scheme)
                            #can later extend this to multi-qubit gates
                            #keeping scheme as last element
                            list of instructions: list
                                list of same form as partitioned_gates containing
                                the local gates to be conducted as part of the
                                remote gate. Ie, for remote-cnot this would
                                contain the cnot (but not the gates used for
                                 bsm or correction).Note if this is given as
                                empty list and scheme = "tp" then it will
                                just do a teleportation
                            gate_instruction : :class: `~netsquid.components.instructions.Instruction`
                                The gate instruction for the target gate
                            instruction_tuple : tuple 
                                Tuple of form (gate_instruction, op), where
                                op is the operatution used to perform the 
                                gate. This form is useful if you want to give
                                several gates the same
                                `netsquid.components.qprocessor.PhysicalInstruction`
                            qubit{ii}: int
                                The qubit index
                            node_name: str
                            The name of the relevant node
                            scheme: str, optional 
                                Only needed for remote gates

    Returns
    -------
    dict 
        Dictionary with term for each node which is an list of different 
        time slices (each time slice is a list within the list)
    """
    qpu_ops = QpuOps()

    for gate_tuple in partitioned_gates:
        if len(gate_tuple) == 3: #if single-qubit gate:
            gate_instr = gate_tuple[0]
            qubit_index = gate_tuple[1]
            node_name = gate_tuple[2]
            op = (gate_instr, qubit_index)
            qpu_ops.add_op(node_name, op)
        elif len(gate_tuple) > 3: #if multi-qubit gate:
            qubit_index0 = gate_tuple[1]
            node0_name = gate_tuple[2]
            qubit_index1 = gate_tuple[3]
            node1_name = gate_tuple[4]
            if node0_name == node1_name: #if local:
                gate_instr = gate_tuple[0]
                node_name = node0_name
                op = (gate_instr, qubit_index0, qubit_index1)
                qpu_ops.add_op(node_name, op)
            else: #if remote gate:
                scheme = gate_tuple[-1]
                gate_instructions = gate_tuple[0]
                if (isinstance(gate_instructions, 
                               ns.components.instructions.IGate)
                    or isinstance(gate_instructions, tuple)):
                    #putting into correct form to use the comm-qubit index
                    #as the control (defers exact index choice to 
                    #QpuOSProtocol in
                    #dqc_simulator.software.dqc_control.py):
                    gate_instructions = [(gate_instructions, -1, qubit_index1)]
                if node0_name not in qpu_ops.ops: 
                    qpu_ops.add_empty_node_entry(node0_name)
                if node1_name not in qpu_ops.ops: 
                    qpu_ops.add_empty_node_entry(node1_name)
                    
                qpu_ops.make_num_time_slices_match(node0_name, node1_name)
                qpu_ops.apply_remote_gate(scheme, gate_instructions, 
                                           qubit_index0, qubit_index1, 
                                           node0_name, node1_name)
                #Time slices are added in the above line as part of the QpuOps
                #methods corresponding to specific remote gate schemes
    qpu_ops.remove_empty_trailing_time_slices()
    return qpu_ops.ops




#I think rather than compiling dqc_circuit you need to pre-process once more 
#and add initialisation in that stage if you want to use existing machinery
#if not it needs updated to use instance of DqcCircuit

#For communication fusion blocks then you should be inputting a block of 
#different gates sandwhiched by remote gate primitives into 
#HandleCommBlockForOneNodeProtocol

