# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 15:01:31 2023

@author: kenny
"""

#Note: some compilation is also done in dqc_control.py. There common 
#subroutines used by Cat-comm and TP-comm are broken down into individual gates
#and run on individual nodes. The role of these compilers is to break a 
#monolithic quantum circuit into the lower level commands used in dqc_control.py.
#That said, very general compilers can be defined here. The only limitation is
#that they use only intraprocessor quantum gates and the interprocessor 
#subroutines involved in Cat and TP-comm

from functools import partial

import netsquid as ns
from netsquid.components import instructions as instr


class NodeOps():
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
            
    def remove_empty_trailing_time_slices(self):
        for node_key in self.ops:
            if not self.ops[node_key][-1]:
            #if last time slice is empty:
                del self.ops[node_key][-1]
            
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
        #TO DO: have the SWAP gate happen first if possible. The main issue may
        #be that -1 will not be defined without the correct
        node0_ops = [(qubit_index0, node1_name, "tp", "bsm")]
        node1_ops = [(node0_name, "tp", "correct4tele_only"),
                       (instr.INSTR_SWAP, -1, qubit_index1)] 
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
        #For teleportation back:
        self.free_comm_qubit_with_tele(-1, qubit_index0, node1_name,
                                       node0_name)
        self.add_time_slice(node0_name)
        self.add_time_slice(node1_name)
        
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
        


def sort_greedily_by_node_and_time(gate_tuples):
    """
    Distributes the circuit between nodes and splits into explicit time-slices
    (rows in output array). Initialisation of qubits must be specified as 
    an instruction in the gate_tuples input.
    
    INPUT: 
        gate_tuples:  list of tuples
        The gates in the entire circuit. The tuples should be of the form:
        1) single-qubit gate: (gate_instr, qubit, node_name)
        2) two-qubit gate: (list of instructions or gate_instruction or
                            instruction_tuple if local,
                            qubit0, node0_name, qubit1, node1_name, scheme)
                            #can later extend this to multi-qubit gates
                            #keeping scheme as last element
                            list of instructions: list
                                list of same form as gate_tuples containing
                                the local gates to be conducted as part of the
                                remote gate. Ie, for remote-cnot this would
                                contain the cnot (but not the gates used for
                                 bsm or correction).Note if this is given as
                                empty list and scheme = "tp" then it will
                                just do a teleportation
                            gate_instruction : instance ofnetsquid.components.instructions.Instruction
                                The gate instruction for the target gate
                            instruction_tuple : tuple 
                                Tuple of form (gate_instruction, op), where
                                op is the operatution used to perform the 
                                gate. This form is useful if you want to give
                                several gates the same
                                netsquid.components.qprocessor.PhysicalInstruction
                            qubit{ii}: int
                                The qubit index
                            node_name: str
                            The name of the relevant node
                            scheme: str, optional 
                                Only needed for remote gates

                            

    OUTPUT: 
        node_op_dict: dict 
            Dictionary with term for each node which is an list of different 
            time slices (each time slice is a list within the list)
    """
    node_ops = NodeOps()

    for gate_tuple in gate_tuples:
        if len(gate_tuple) == 3: #if single-qubit gate:
            gate_instr = gate_tuple[0]
            qubit_index = gate_tuple[1]
            node_name = gate_tuple[2]
            op = (gate_instr, qubit_index)
            node_ops.add_op(node_name, op)
        elif len(gate_tuple) > 3: #if multi-qubit gate:
            qubit_index0 = gate_tuple[1]
            node0_name = gate_tuple[2]
            qubit_index1 = gate_tuple[3]
            node1_name = gate_tuple[4]
            if node0_name == node1_name: #if local:
                gate_instr = gate_tuple[0]
                node_name = node0_name
                op = (gate_instr, qubit_index0, qubit_index1)
                node_ops.add_op(node_name, op)
            else: #if remote gate:
                scheme = gate_tuple[-1]
                gate_instructions = gate_tuple[0]
                if (isinstance(gate_instructions,ns.components.instructions.IGate)
                    or isinstance(gate_instructions, tuple)):
                    #putting into correct form to use the comm-qubit index
                    #as the control (defers exact index choice to 
                    #HandleOneNodeProtocol in
                    #dqc_simulator.softwaredqc_control.py):
                    gate_instructions = [(gate_instructions, -1, qubit_index1)]
                if node0_name not in node_ops.ops: 
                    node_ops.add_empty_node_entry(node0_name)
                if node1_name not in node_ops.ops: 
                    node_ops.add_empty_node_entry(node1_name)
                    
                node_ops.make_num_time_slices_match(node0_name, node1_name)
                node_ops.apply_remote_gate(scheme, gate_instructions, 
                                           qubit_index0, qubit_index1, 
                                           node0_name, node1_name)
    node_ops.remove_empty_trailing_time_slices()
    return node_ops.ops


#I think rather than compiling dqc_circuit you need to pre-process once more 
#and add initialisation in that stage if you want to use existing machinery
#if not it needs updated to use instance of DqcCircuit

#For communication fusion blocks then you should be inputting a block of 
#different gates sandwhiched by remote gate primitives into 
#HandleCommBlockForOneNodeProtocol

