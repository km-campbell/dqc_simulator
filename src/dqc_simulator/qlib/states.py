# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu Aug 17 12:28:32 2023
#
# @author: kenny
# =============================================================================
"""
Extendable library of useful quantum states and helper functions for creating
states.
"""

import functools as ft

import netsquid as ns
from netsquid.qubits import ketstates as ks
import numpy as np


def get_zket(*args):
    """
    Define arbitrary tensor product of kets in the computational basis.

    Parameters
    ----------
    *args : int
        The bits defining the basis. Eg, for args 1, 0, 1, basis return |101>

    Returns
    -------
    np.array
        Ket of form |ijkl....> for args i, j, k, l....

    """
    ket_lookup = {0: ks.s0, 1: ks.s1}
    return ft.reduce(np.kron, [ket_lookup[arg] for arg in args])


def get_ghz_state_ket(num_qubits):
    """
    Return a ket vector for the n-qubit generalised GHZ state

    Parameters
    ----------
    num_qubits : int
        The number of qubits, n, in the n-qubit generalised GHZ state.

    Returns
    -------
    :class:`~numpy.ndarray`
        The ket vector for an n-qubit genralised GHZ state.

    """
    return (
        1
        / np.sqrt(2)
        * (
            ft.reduce(np.kron, [ks.s0] * num_qubits)
            + ft.reduce(np.kron, [ks.s0] * num_qubits)
        )
    )


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
    werner_state = (
        F * ns.qubits.ketutil.ket2dm(ks.b00)
        + (1 - F) / 3 * ns.qubits.ketutil.ket2dm(ks.b01)
        + (1 - F) / 3 * ns.qubits.ketutil.ket2dm(ks.b10)
        + (1 - F) / 3 * ns.qubits.ketutil.ket2dm(ks.b11)
    )
    return werner_state
