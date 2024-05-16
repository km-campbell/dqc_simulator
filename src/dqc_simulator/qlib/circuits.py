# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 09:52:29 2024

@author: kenny
"""

from netsquid.components import instructions as instr

from dqc_simulator.qlib.gates import INSTR_T_DAGGER

def produce_partitioned_circuit_from_fig4_in_autocomm_paper():
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