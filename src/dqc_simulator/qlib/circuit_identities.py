# -*- coding: utf-8 -*-

# =============================================================================
# Created on Tue May  9 15:16:05 2023
# 
# @author: kenny
# =============================================================================
"""Useful circuit identity macros.
"""

from netsquid.components import instructions as instr

from dqc_simulator.qlib.gates import INSTR_T_DAGGER


def two_control_ibm_toffoli_decomp(ctrl_qubit1_index, ctrl_node_name1, 
                                   ctrl_qubit2_index,
                                   ctrl_node_name2, target_qubit_index, 
                                   target_node_name, scheme="cat"):
    """
    A macro for the decomposition of a toffoli, or CCX, gate in terms U, CX, H 
    and T gates.
    
    For direct use by protocols in 
    :mod: `~dqc_simulator.software.dqc_control`.

    Parameters
    ----------
    ctrl_qubit1_index, ctrl_qubit_2_index : int
        The index of the first and second control qubits of the toffoli gate
    ctrl_node_name1, ctrl_node_name2 : str
        The names of the QPU nodes upon which the first and second control 
        qubits of the toffoli gate reside.
    target_qubit_index : int
        The index of the target qubit for the toffoli gate
    target_node_name : str
        DESCRIPTION.
    scheme : str, optional
        The remote gate scheme to use. The default is "cat" (referring to 
        cat-comm (AKA telegate).

    Returns
    -------
    sub_ops : list of tuples
        The gates constituting the decomposed toffoli gate.
        
    Notes
    -----
    This decomposition of the toffoli gate is as specified in the IBM 
    Quantum Experience standard header for openQASM 2.0 [1]_.
    
    References
    ----------
    ..[1] A. W. Cross, L. S. Bishop, J. A. Smolin, and J. M. Gambetta, Open 
        Quantum Assembly Language, arXiv:1707.03429 [quant-ph].

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

#stabiliser circuits
#-------------------

def stabiliser_measurement(qubits2check, ancilla_to_use, stabiliser_type):
    """
    Specifies circuit for single stabiliser measurement using one ancilla 
    qubit.

    Parameters
    ----------
    qubits2check : list or tuple of int
        The qubits (specified by their indices_ to apply the (non-destructive) 
        stabiliser measurement to. 
    ancilla_to_use : int
        The qubit (index) to use as an ancilla.
    stabiliser_type : str
        Whether to apply an 'x' or a 'z' stabiliser measurement. Allowed values
        are 'x' or 'X' and 'z' or 'Z'

    Returns
    -------
    gate_tuples : list of tuples
        The circuit specification for the stabiliser measurement.
    """
    #in next line 'mono_qc' is placeholder for a node name and can be replaced
    #later
    cnots = [(instr.INSTR_CNOT, qubit_index, 'mono_qc', ancilla_to_use, 
              'mono_qc') for qubit_index in qubits2check]
    if (stabiliser_type == 'x') or (stabiliser_type == 'X'):
        #TO DO: decide whether to use hadamard then z measurement or 
        #INSTR_MEASURE_X in the following. Both are equivalent but when declaring
        #physical errors in the quantum processor you need to ensure that the 
        #instruction is defined. You also don't want to have the duration of a 
        #physical hadamard gate if such a gate is not done.
# =============================================================================
#         measurement = [(instr.INSTR_MEASURE_X, ancilla_to_use, 'mono_qc')]
# =============================================================================
        measurement = [(instr.INSTR_H, ancilla_to_use, 'mono_qc'),
                       (instr.INSTR_MEASURE, ancilla_to_use, 'mono_qc')]
    elif (stabiliser_type == 'z') or (stabiliser_type == 'Z'):
        measurement = [(instr.INSTR_MEASURE, ancilla_to_use, 'mono_qc')]
    else:
        raise ValueError(f'{stabiliser_type} is not an allowed value of '
                         'stabiliser_type. Allowed values are: "x", "X", "z", '
                         'or "Z". ')
    return cnots + measurement 

