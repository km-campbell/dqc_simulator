# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu Aug 17 12:28:32 2023
# 
# @author: kenny
# =============================================================================
"""
Extendable library of useful quantum states.
"""

import netsquid as ns
from netsquid.qubits import ketstates as ks

def werner_state(F):
    """
    Defines the density matrix for the Werner state.

    Parameters
    ----------
    F : float
        The Werner state fidelity (fidelity of |Phi^+>) within the Werner
        state.

    Returns
    -------
    werner_state : array or array-like
        The density matrix for the Werner state.
    """
    werner_state = (F * ns.qubits.ketutil.ket2dm(ks.b00) + 
                    (1-F)/3 * ns.qubits.ketutil.ket2dm(ks.b01) + 
                    (1-F)/3 * ns.qubits.ketutil.ket2dm(ks.b10) + 
                    (1-F)/3 * ns.qubits.ketutil.ket2dm(ks.b11))
    return werner_state