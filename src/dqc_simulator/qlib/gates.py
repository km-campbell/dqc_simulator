# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 12:13:12 2023

@author: kenny
"""

#This script defines additional quantum gates to those included natively in 
#NetSquid (as of version 1.1.6). 


import numpy as np

from netsquid.qubits.operators import (Operator, H, T, I, S, Y,
                                       create_rotation_op)
from netsquid.components import instructions as instr



def INSTR_ARB_GEN(alpha, beta):
    total_probability_q1 = abs(alpha)**2 + abs(beta)**2
    if round(total_probability_q1, 3) !=1.000:
        raise ValueError('alpha and beta do not give normalised input to circuit')
    
    state_gen_op = Operator("state_generating_op", 
                            np.array([[alpha, 0], [0, beta]]) @ 
                            np.array([[1, 1], [1, -1]]))
    instruction = instr.IGate("state_gen_gate", state_gen_op)
    return instruction

INSTR_CH = instr.IGate("CH", H.ctrl) #creates CH gate as instruction

INSTR_CT = instr.IGate("CT", T.ctrl) 

INSTR_IDENTITY = instr.IGate("I", operator=I)

INSTR_T_DAGGER = instr.IGate("T_dagger", operator=T.conj)

INSTR_S_DAGGER = instr.IGate("S_dagger", operator=S.conj)



INSTR_SINGLE_QUBIT_UNITARY = instr.IGate('single_qubit_unitary',
                                         num_positions=1)
INSTR_TWO_QUBIT_UNITARY = instr.IGate('two_qubit_unitary', num_positions=2)

def INSTR_U(theta, phi, lambda_var, controlled=False):
    """
    (controlled) single qubit unitary

    Parameters
    ----------
    theta : float
        An angle in radians.
    phi : float
        An angle in radians.
    lambda_var : float
        An angle in radians.

    Returns
    -------
    instructionNop : tuple
        The NetSquid instruction and operation needed to carry out this gate.
        Here the instruction essentially indicates all relevant metadata and 
        can be used to dictate which noise should be applied to the gate, 
        while the operation is the matrix used to apply the actual quantum 
        operation defining the gate.

    """
    a11 = np.exp(-1j * (phi + lambda_var)/2) * np.cos(theta/2)
    a12 = -np.exp(-1j * (phi - lambda_var)/2) * np.sin(theta/2)
    a21 = np.exp(1j * (phi - lambda_var)/2) * np.sin(theta/2)
    a22 = np.exp(1j * (phi + lambda_var)/2) * np.cos(theta/2)
    op = Operator("single_qubit_unitary_op",
                  np.array([[a11, a12], [a21, a22]]))
    instruction = INSTR_SINGLE_QUBIT_UNITARY
    if controlled==True:
        op = op.ctrl
        instruction = INSTR_TWO_QUBIT_UNITARY
    elif type(controlled) != bool:
        raise TypeError(f"{controlled} is not of type `bool' ")
    instructionNop = (instruction, op)
    return instructionNop



INSTR_CY = instr.IGate("CY", operator=Y.ctrl)


def _add_options2single_qubit_gate(op, controlled, conjugate):
    instruction = INSTR_SINGLE_QUBIT_UNITARY
    if controlled == True:
        op = op.ctrl
        instruction = INSTR_TWO_QUBIT_UNITARY
    elif type(controlled) != bool:
        raise TypeError("{controlled} is not of type `bool' ")
        
    if conjugate == True:
        op = op.conj
    elif type(conjugate) != False:
        raise TypeError("{conjugate} is not of type `bool' ")
    
    return (instruction, op)
        


def instrNop_RZ(angle, controlled=False, conjugate=False):
    """
    

    Parameters
    ----------
    angle : float
        Angle of rotation in radians.
    controlled : bool, optional
        Whether this is implemented as a control gate (CRz) or not. The default
        is False.
    conjugate : bool, optional
        Whether to implement the complex conjugate of Rz or not. The default 
        is False.

    Returns
    -------
    instructionNop : tuple
        The NetSquid instruction and operation needed to carry out this gate.
        Here the instruction essentially indicates all relevant metadata and 
        can be used to dictate which noise should be applied to the gate, 
        while the operation is the matrix used to apply the actual quantum 
        operation defining the gate.

    """
    op = create_rotation_op(angle, axis=(0, 0, 1))
    instructionNop = _add_options2single_qubit_gate(op, controlled, conjugate)
    return instructionNop



instrNop_SX = (INSTR_SINGLE_QUBIT_UNITARY, 
            Operator('SX', S.conj.arr @ H.arr @ S.conj.arr))

instrNop_SXDG = (INSTR_SINGLE_QUBIT_UNITARY,
                 Operator('SXDG', S.arr @ H.arr @ S.arr))

instrNop_CSX = (INSTR_TWO_QUBIT_UNITARY, instrNop_SX[1].ctrl)



        
    
        
    

    
