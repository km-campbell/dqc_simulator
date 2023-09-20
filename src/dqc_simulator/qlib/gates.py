# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 12:13:12 2023

@author: kenny
"""

#This script defines additional quantum gates to those included natively in 
#NetSquid (as of version 1.1.6). 


import numpy as np

from netsquid.qubits.operators import Operator, H, T, I
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