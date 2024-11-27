# -*- coding: utf-8 -*-
# =============================================================================
# Created on Wed Mar 20 09:52:29 2024
# 
# @author: kenny
# =============================================================================
"""Macros for useful quantum circuits.
"""

from netsquid.components import instructions as instr

from dqc_simulator.qlib.gates import INSTR_T_DAGGER

def get_ghz_gate_tuples(num_qubits):
    """
    Return the gate tuples for a generalised GHZ gate implemented on a
    monolithic quantum processor.

    Parameters
    ----------
    num_qubits : int
        The number of qubits to include in the generalised GHZ state.

    Returns
    -------
    gate_tuples : list of tuple
        The gate_tuples needed to simulate a quantum circuit on a monolithic 
        quantum processor.
    """
    gate_tuples = [(instr.INSTR_INIT, [ii for ii in range(num_qubits)], 
                    'mono_qc'),
                   (instr.INSTR_H, 0, 'mono_qc'),
                   *[(instr.INSTR_CNOT, ii, 'mono_qc', ii+1, 'mono_qc') for 
                     ii in range(num_qubits-1)]]
    return  gate_tuples

def get_gate_tuples_to_create_cluster_state(topology):
    """
    Creates list of cluster state gates for implementation on a single-QPU 
    quantum computer.

    Parameters
    ----------
    topology : list of tuples of ints
        Each tuple should contain the two indices, one for each qubit connected
        by an edge (CZ gate)

    Returns
    -------
    list of tuples
        The gate tuples needed to generate a cluster state with the specified 
        topology.
    """
    qubits_to_initialise = []
    cz_gates = []
    for edge in topology:
        qubit_index0 = edge[0]
        qubit_index1 = edge[1]
        gate_tuple = (instr.INSTR_CZ, qubit_index0, 'mono_qc', qubit_index1,
                      'mono_qc')
        cz_gates.append(gate_tuple)
        if qubit_index0 not in qubits_to_initialise:
            qubits_to_initialise.append(qubit_index0)
        if qubit_index1 not in qubits_to_initialise:
            qubits_to_initialise.append(qubit_index1)
    qubits_to_initialise.sort()
    init_cmd = [(instr.INSTR_INIT, qubits_to_initialise, 'mono_qc')]
    hadamards = [(instr.INSTR_H, qubit_index, 'mono_qc') for qubit_index in 
                 qubits_to_initialise]
    return init_cmd + hadamards + cz_gates


def produce_partitioned_circuit_from_fig4_in_autocomm_paper():
    """
    Macro for a specific circuit (see references)

    Returns
    -------
    partitioned_gates : list of tuples
        The gates needed to describe the monolithic quantum circuit.
        
    Notes
    -----
    This circuit can be used to test implementations of AutoComm [1]_ and
    other compilers (which can be compared to AutoComm)
        
    References
    ----------
    See figure 4 of [1]_ for an diagram of the circuit in question.
    
    .. [1] A. Wu, H. Zhang, G. Li, A. Shabani, Y. Xie, and Y. Ding, Autocomm: 
           A framework for enabling efficient communication in
           distributed quantum programs, in 2022 55th IEEE/ACM International 
           Symposium on Microarchitecture (MICRO) (2022) pp. 1027–1041.
    """
    partitioned_gates = [(instr.INSTR_T, 2, 'node_1'), 
                        (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'),
                        (INSTR_T_DAGGER, 2, 'node_1'),
                        (instr.INSTR_T, 3, 'node_1'),
                        (instr.INSTR_T, 3, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'),
                        (instr.INSTR_CNOT, 3, 'node_0', 3, 'node_1'),
                        (instr.INSTR_CNOT, 2, 'node_0', 3, 'node_2'),
                        (INSTR_T_DAGGER, 3, 'node_0'),
                        (INSTR_T_DAGGER, 3, 'node_1'),
                        (INSTR_T_DAGGER, 3, 'node_2'),
                        (instr.INSTR_CNOT, 3, 'node_0', 3, 'node_1'),
                        (instr.INSTR_CNOT, 2, 'node_0', 3, 'node_2'),
                        (instr.INSTR_H, 2, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_2', 3, 'node_1'),
                        (INSTR_T_DAGGER, 3, 'node_1'),
                        (instr.INSTR_H, 2, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_2', 3, 'node_1'),
                        (instr.INSTR_CNOT, 2, 'node_2', 2, 'node_1'),
                        (instr.INSTR_T, 2, 'node_2'),
                        (instr.INSTR_CNOT, 3, 'node_0', 2, 'node_2'),
                        (INSTR_T_DAGGER, 3, 'node_0'),
                        (instr.INSTR_T, 2, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_2', 3, 'node_0'),
                        (instr.INSTR_CNOT, 2, 'node_2', 2, 'node_0'),
                        (INSTR_T_DAGGER, 3, 'node_0'),
                        (instr.INSTR_T, 3, 'node_1'),
                        (instr.INSTR_CNOT, 3, 'node_0', 2, 'node_1'),
                        (instr.INSTR_CNOT, 2, 'node_2', 3, 'node_1'),
                        (INSTR_T_DAGGER, 3, 'node_0'),
                        (instr.INSTR_T, 2, 'node_1'),
                        (INSTR_T_DAGGER, 3, 'node_1'),
                        (instr.INSTR_T, 2, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_1', 3, 'node_0'),
                        (instr.INSTR_CNOT, 3, 'node_1', 2, 'node_2'),
                        (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1')]
    return partitioned_gates