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