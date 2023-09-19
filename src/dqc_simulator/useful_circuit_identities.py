# -*- coding: utf-8 -*-
"""
Created on Tue May  9 15:16:05 2023

@author: kenny
"""

from netsquid.components import instructions as instr
from custom_quantum_processors import INSTR_T_DAGGER


def two_control_ibm_toffoli_decomp(ctrl_qubit1_index, ctrl_node_name1, ctrl_qubit2_index,
                                   ctrl_node_name2, target_qubit_index, target_node_name, scheme="cat"):
    """
    The decomposition of the toffoli gate that appears in 
    https://quantumcomputing.stackexchange.com/questions/10315/decompose-toffoli-gate-with-minimum-cost-for-ibm-quantum-compute
    and is used by ibm composer.
    Lower circuit depths can be obtained with the use of ancillae qubits or 
    approximation
     
    OUTPUT: list of one and two-qubit gate-tuples needed to implement the toffoli 
    gate 
    """
    #INSTR_T_dagger defined in my network.py module
    sub_ops = [(instr.INSTR_H, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit2_index, ctrl_node_name2, target_qubit_index, target_node_name),
               (INSTR_T_DAGGER, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, target_qubit_index, target_node_name),
               (instr.INSTR_T, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit2_index, ctrl_node_name2, target_qubit_index, target_node_name),
               (INSTR_T_DAGGER, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, target_qubit_index, target_node_name),
               (instr.INSTR_T, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_T, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_H, target_qubit_index, target_node_name),
               (instr.INSTR_T, ctrl_qubit1_index, ctrl_node_name1),
               (INSTR_T_DAGGER, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, ctrl_qubit2_index, ctrl_node_name2)]
    if ctrl_node_name1 == ctrl_node_name2 == target_node_name:
        return sub_ops
    else:
        for ii, element in enumerate(sub_ops):
            if len(element) > 3 and element[2] != element[-1]:
                sub_ops[ii] = (*element, scheme)
    return sub_ops