# -*- coding: utf-8 -*-
"""
Tools for partitioning a monolithic quantum circuit between QPUs.
"""


import itertools
import math

from netsquid.components import instructions as instr

from dqc_simulator.hardware.quantum_processors import QPU

def bisect_circuit(dqc_circuit, comm_qubits_per_node=2):
    """
    Bisects a circuit into two QPUs, node_0 and node_1.
    
    For circuits with odd
    numbers of qubits, node_0 will be given the extra qubit. It also adds,
    communication qubits to each node. It is assumed that all indices of the 
    qubits in the input dqc_circuit are intended to be data qubits (so if the
    input circuit is already partitioned in some way, then this function is
    not appropriate to provide an additional bisection.)
    
    Parameters
    ----------
    dqc_circuit : :class: `~dqc_simulator.software.dqc_circuit.DqcCircuit`
        A monolithic quantum circuit.
    comm_qubits_per_node : int
        The number of qubits each QPU node has
    """
    #helper functions:
    def _assign_qubit_to_node(qubit_index, qreg_name,
                              node1starting_index):
            starting_index = (dqc_circuit.qregs[qreg_name]['starting_index'] +
                              comm_qubits_per_node)
            updated_qubit_index = qubit_index + starting_index
            node_name = 'node_0'
            if updated_qubit_index >= node1starting_index:
                updated_qubit_index = (updated_qubit_index - 
                                       node1starting_index + 
                                       comm_qubits_per_node)
                node_name = 'node_1'
            return updated_qubit_index, node_name
            
    #main body:
    total_num_qubits = 2 * comm_qubits_per_node
    for qreg_name in dqc_circuit.qregs:
        qreg = dqc_circuit.qregs[qreg_name]
        total_num_qubits = qreg['size'] + total_num_qubits
    node_0_size = math.ceil(total_num_qubits/2) #ceiling division
    node_1_size = total_num_qubits - node_0_size
    node1starting_index = node_0_size #as indexing starts from zero
    for gate_spec in dqc_circuit.ops:
        qubit_index1 = gate_spec[1]
        qreg_name1 = gate_spec[2]
        updated_qubit_index, node_name = _assign_qubit_to_node(
                                                    qubit_index1,
                                                    qreg_name1,
                                                    node1starting_index)
        gate_spec[1] = updated_qubit_index
        gate_spec[2] = node_name
        if len(gate_spec) >= 5:
            qubit_index2 = gate_spec[3]
            qreg_name2 = gate_spec[4]
            updated_qubit_index, node_name = _assign_qubit_to_node(
                                                    qubit_index2, 
                                                    qreg_name2,
                                                    node1starting_index)
            gate_spec[3] = updated_qubit_index
            gate_spec[4] = node_name
    
    dqc_circuit.node_sizes = {'node_0' : node_0_size, 'node_1' : node_1_size}
    dqc_circuit.circuit_type = 'partitioned'


def first_come_first_served_qubits_to_qpus(gate_tuples, qpu_nodes):
    """
    Allocates qubits from a monolithic circuit to different QPUs as evenly as 
    possible. 
    
    The extra remainder qubits are 
    allocated one by one to each QPU node until all are allocated (meaning some 
    QPU nodes won't get an extra qubit.)

    Parameters
    ----------
    gate_tuples : list of tuples
        The gates describing a monolithic quantum circuit
    qpu_nodes : list of `~netsquid.node.nodes.Node`s
        The QPU nodes.

    Raises
    ------
    ValueError
        If first instruction in gate tuples is not an 
        `~netsquid.components.instructions.Instruction`

    Returns
    -------
    qpu_old_to_new_index_lookup : dict
        Lookup table from the old qubit indices in the orignal monolithic 
        circuit to the index and QPU name that qubit is assigned to.
    """
    num_qpu_nodes = len(qpu_nodes)
    #assuming that first thing that is done is to initialise all data qubits
    init_gate_tuple = gate_tuples[0]
    if init_gate_tuple[0] is not instr.INSTR_INIT:
        raise ValueError('first instruction in gate_tuples must initialise '
                         'the processing qubits. The first instruction, '
                         f'{init_gate_tuple}, does not do this')
    original_qubit_indices = init_gate_tuple[1] #num qubits in original circuit
    #defining total number of processing qubits
    total_num_proc_qubits = len(original_qubit_indices)
    proc_qubits_per_qpu = total_num_proc_qubits//num_qpu_nodes
    remainder = len(original_qubit_indices) % num_qpu_nodes
    #initialising values to be filled in by loop
    qpu_old_to_new_index_lookup = {}
    starting_index = 0
    for qpu_node in qpu_nodes:
        end_index = starting_index + proc_qubits_per_qpu
        if remainder > 0: #if num_qubits/num_qpu has remainder not yet allocated:
            #allocate one qubit from the remainder to this qpu
            end_index = end_index + 1
            remainder = remainder - 1
        #assigning qubits to the qpu
        old_indices_assigned_to_qpu = [ii for ii in range(starting_index, 
                                                          end_index)]
        #creating lookup table to navigate from the qubit indices assigned to 
        #each QPU the new indices wrt the QPU those qubits are assigned to
        old2new = {old_indices_assigned_to_qpu[ii] : 
                   (qpu_node.qmemory.processing_qubit_positions[0] + ii, 
                    qpu_node.name)
                    for ii in range(end_index - starting_index)}
        starting_index = end_index
        qpu_old_to_new_index_lookup.update(old2new)
    return qpu_old_to_new_index_lookup
                

def network2qpu_nodes(network):
    """
    Get list of QPU nodes from a network.

    Parameters
    ----------
    network : :class: `~netsquid.nodes.network.Network`
        The quantum network for a quantum data centre.

    Returns
    -------
    qpu_nodes : list of :class: `~netsquid.nodes.node.Node`
        The nodes with a QPU. These are intended to contribute directly to a 
        computation rather than performing an administrative function.
    """
    qpu_nodes = []
    for node in network.nodes.values():
        if isinstance(node.qmemory, QPU):
            qpu_nodes.append(node)
    return qpu_nodes


#Can potentially convert the following to a function called partition gate 
#tuples which accepts a function to create the old_to_new_index_lookup as an
#input
def partition_gate_tuples(gate_tuples, network, scheme, 
                          qubit2qpu_allocator):
    """
    

    Parameters
    ----------
    gate_tuples : list of tuples
        The gate_tuples for a monolithic circuit. These can have the form 
        (instruction, qubit_index_ii, qubit_index_jj, ...) and/or 
        (instruction, qubit_index_ii, node_name, qubit_index_jj, node_name, ...)
        where in the latter case node_name will be a constant (the name of the 
        monolithic quantum processor the circuit was originally designed for)
    network : :class: `~netsquid.nodes.network.Network`
        The quantum network for a quantum data centre.
    scheme : str
        The scheme to use for remote gates. Allowed values are 'cat', '1tp',
        '2tp', and 'tp_safe'
    qubit2qpu_allocator : func
        A function that returns a lookup table (dict) with the keys being the 
        old indices from a monolithic quantum circuit and the values being 
        tuples containing the new index and QPU node name that the 
        corresponding old index is assigned to. An example of such a function 
        would be `first_come_first_served_qubits_to_qpus`

    Returns
    -------
    partitioned_gate_tuples : list of tuples
        The gate tuples for a distributed quantum circuit in the at the 
        gate-level. This means the circuit is ready to be compiled by a 
        compiler that further decomposes remote gates into communication 
        primitives: 
            1) single-qubit gate: (gate_instr, qubit, node_name)
            2) two-qubit gate: (list of instructions or gate_instruction or
                                instruction_tuple if local,
                                qubit0, node0_name, qubit1, node1_name, scheme if remote)
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
    """
    
    def _split_up_initial_init_instruction(gate_tuples, old_to_new_lookup):
        """
        Distributes an intialisation instruction at the start of a monolithic quantum
        circuit between differnet QPUs.

        Parameters
        ----------
        gate_tuples : list of tuples
            The gates for a monolithic quantum circuit
        old_to_new_lookup : dict
            Keys should be indices of qubits in monolithic circuit and values should
            be tuples containing the new index for each qubit and the QPU node that
            that qubit now belongs to.

        Returns
        -------
        gate_tuples : list of tuples
            The gate_tuples with the initialisation instruction distributed

        """
        if gate_tuples[0][0] is instr.INSTR_INIT and isinstance(gate_tuples[0][1],
                                                                list):
            old_indices = gate_tuples[0][1]
            old_indices.sort()
            qubits4qpu = {}
            #get new indices for all processing qubits that need initialisation 
            #on each QPU
            for ii in old_indices:
                new_info = old_to_new_lookup[ii]
                qubit_index = new_info[0]
                node_name = new_info[1]
                if node_name not in qubits4qpu:
                    qubits4qpu[node_name] = [qubit_index]
                else:
                    qubits4qpu[node_name].append(qubit_index)
            #split up the intialisation instruction into an instruction initialisng
            #the relevant qubits on each QPU.
            init_instructions = []
            for node_name in qubits4qpu:
                init_instructions.append((instr.INSTR_INIT, qubits4qpu[node_name],
                                          node_name))
        return init_instructions
    
    qpu_nodes = network2qpu_nodes(network)
    old_to_new_lookup = qubit2qpu_allocator(gate_tuples, qpu_nodes)
    partitioned_init_instructions = _split_up_initial_init_instruction(
                                                           gate_tuples,
                                                           old_to_new_lookup)
    partitioned_gate_tuples = []
    #assuming that the first gate_tuples is an initialisation instruction which
    #was dealt with above
    for gate_tuple in gate_tuples[1:]:
        if all(isinstance(entry, int) for entry in gate_tuple[:1]):
        #if all entries after the first are qubit indices:
            step = 1
        else:
            step = 2
        repeating_pattern = list(itertools.chain.from_iterable(
                                (old_to_new_lookup[gate_tuple[ii]][0],
                                 old_to_new_lookup[gate_tuple[ii]][1])
                                 for ii in range(1, len(gate_tuple), step)))
        new_gate = [gate_tuple[0]] + repeating_pattern
        if len(new_gate) > 3 and any(new_gate[ii] != new_gate[ii+2]
                                     for ii in range(2, len(new_gate)-2, 2)):
        #if this is at least a 2 qubit gate and any of the nodes acted on are 
        #not the same (ie, if remote gate):
            new_gate = new_gate + [scheme]
        partitioned_gate_tuples.append(tuple(new_gate))
    partitioned_gate_tuples = (partitioned_init_instructions 
                               + partitioned_gate_tuples)
    return partitioned_gate_tuples