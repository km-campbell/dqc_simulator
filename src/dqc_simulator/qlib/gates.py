# -*- coding: utf-8 -*-
# =============================================================================
# Created on Wed Sep 20 12:13:12 2023
#
# @author: kenny
# =============================================================================
"""
Additional quantum gates to those included natively in NetSquid.

The gates defined in this module are
:class:`~netsquid.components.instructions.Instruction` objects or tuples
containing :class:`~netsquid.components.instructions.Instruction` objects or
functions returning :class:`~netsquid.components.instructions.Instruction`
 objects or tuples containing instructions and
:class:`~netsquid.qubits.operators.Operator` objects to be used by those
instructions. In short, the gates in this module are intended for backend use
and will utilised directly by the simulation.
"""

# This script defines additional quantum gates to those included natively in
# NetSquid (as of version 1.1.6).

import numpy as np

from netsquid.components import instructions as instr
from netsquid.qubits.operators import Operator, H, T, I, S, Y, create_rotation_op


def make_state_gen_op(alpha, beta):
    """
    For making operators that generate arbitrary, pure, single-qubit states.

    Parameters
    ----------
    alpha, beta : float
        The coefficients of |0> and |1>, respectively, in the state to
        generate.

    Returns
    -------
    state_gen_op : :class:`~netsquid.qubits.operators.Operator`
        An operator describing a fictitious quantum gate which can create an
        arbitrary single qubit gate.
    """
    state_gen_op = Operator(
        "state_generating_op",
        np.array([[alpha, 0], [0, beta]]) @ np.array([[1, 1], [1, -1]]),
    )
    return state_gen_op


def INSTR_ARB_GEN(alpha, beta):
    """
    For generating arbitrary quantum states.

    .. deprecated::
    This function will be deprecated in a future version. It was implemented
    to allow arbitrary quantum states to be generated, however, this is now
    done using :func: `~dqc_simulator.qlib.make_state_gen_op`
    and an instruction :class:`~netsquid.components.instructions.Instruction`
    without an operator in the future. This will avoid the need to bake
    `alpha` and `beta` into the
    :class:`~netsquid.components.qprocessor.QuantumProcessor`.

    Creates :class:`~netsquid.components.instructions.Instruction` that
    generates arbitrary quantum states.

    Parameters
    ----------
    alpha, beta : float
        The coefficients of |0> and |1>, respectively, in the state to
        generate.

    Raises
    ------
    ValueError
        Alerts user to erroneous choice of `alpha` and `beta`, which would
        generate an unnormalised quantum state.

    Returns
    -------
    instruction : :class:`~netsquid.components.instructions.Instruction`
        An instruction that creates arbitrary quantum states.

    """
    # THIS WILL BE DEPRECATED IN FUTURE VERSION
    total_probability_q1 = abs(alpha) ** 2 + abs(beta) ** 2
    if round(total_probability_q1, 3) != 1.000:
        raise ValueError("alpha and beta do not give normalised input to circuit")

    state_gen_op = make_state_gen_op(alpha, beta)
    instruction = instr.IGate("state_gen_gate", state_gen_op)
    return instruction


INSTR_CH = instr.IGate("CH", H.ctrl)  # creates CH gate as instruction

INSTR_CT = instr.IGate("CT", T.ctrl)

INSTR_IDENTITY = instr.IGate("I", operator=I)

INSTR_T_DAGGER = instr.IGate("T_dagger", operator=T.conj)

INSTR_S_DAGGER = instr.IGate("S_dagger", operator=S.conj)


# instructions without operations. The operation will be specified later.
# These instructions should be used when we want to define a PhysicalInstruction
# for an operation dependent on continuous paramters.
INSTR_SINGLE_QUBIT_UNITARY = instr.IGate("single_qubit_unitary", num_positions=1)
INSTR_TWO_QUBIT_UNITARY = instr.IGate("two_qubit_unitary", num_positions=2)
INSTR_SINGLE_QUBIT_NEGLIGIBLE_TIME = instr.IGate(
    "neglibible_time_instr", num_positions=1
)
INSTR_TWO_QUBIT_NEGLIGIBLE_TIME = instr.IGate("neglible_time_2_qubit", num_positions=2)


def INSTR_U(theta, phi, lambda_var, controlled=False):
    """
    (controlled) single qubit unitary in sim backend-readable format.

    Parameters
    ----------
    theta : float
        An angle in radians.
    phi : float
        An angle in radians.
    lambda_var : float
        An angle in radians.
    controlled : bool
        Whether the gate should be controlled (ie, a CU gate is applied rather
        than a U gate) or not. Default is False.

    Returns
    -------
    instructionNop : tuple
        The NetSquid :class:`~netsquid.components.instructions.Instruction`
        and operation :class:`~netsquid.qubits.operators.Operator`
        needed to carry out this gate.
        Here, the instruction essentially indicates all relevant metadata and
        can be used to dictate which noise should be applied to the gate,
        while the operator is the matrix used to apply the actual quantum
        operation defining the gate.
    """
    a11 = np.exp(-1j * (phi + lambda_var) / 2) * np.cos(theta / 2)
    a12 = -np.exp(-1j * (phi - lambda_var) / 2) * np.sin(theta / 2)
    a21 = np.exp(1j * (phi - lambda_var) / 2) * np.sin(theta / 2)
    a22 = np.exp(1j * (phi + lambda_var) / 2) * np.cos(theta / 2)
    op = Operator("single_qubit_unitary_op", np.array([[a11, a12], [a21, a22]]))
    instruction = INSTR_SINGLE_QUBIT_UNITARY
    if controlled:
        op = op.ctrl
        instruction = INSTR_TWO_QUBIT_UNITARY
    elif not isinstance(controlled, bool):
        raise TypeError(f"{controlled} is not of type `bool' ")
    instructionNop = (instruction, op)
    return instructionNop


INSTR_CY = instr.IGate("CY", operator=Y.ctrl)


def _add_options2single_qubit_gate(op, controlled, conjugate):
    instruction = INSTR_SINGLE_QUBIT_UNITARY
    if controlled:
        op = op.ctrl
        instruction = INSTR_TWO_QUBIT_UNITARY
    elif not isinstance(controlled, bool):
        raise TypeError(
            f"The value for controlled ({controlled}) is not of type `bool' "
        )

    if conjugate:
        op = op.conj
    elif not isinstance(conjugate, bool):
        raise TypeError(f"The value for conjugate ({conjugate}) is not of type `bool' ")

    return (instruction, op)


def instrNop_RZ(angle, controlled=False, conjugate=False):
    """
    Defines RZ gate in sim backend-readable format.

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
        The NetSquid :class:`~netsquid.components.instructions.Instruction`
        and operation :class:`~netsquid.qubits.operators.Operator`
        needed to carry out this gate.
        Here, the instruction essentially indicates all relevant metadata and
        can be used to dictate which noise should be applied to the gate,
        while the operator is the matrix used to apply the actual quantum
        operation defining the gate.

    """
    op = create_rotation_op(angle, rotation_axis=(0, 0, 1))
    instructionNop = _add_options2single_qubit_gate(op, controlled, conjugate)
    return instructionNop


instrNop_SX = (
    INSTR_SINGLE_QUBIT_UNITARY,
    Operator("SX", S.conj.arr @ H.arr @ S.conj.arr),
)

instrNop_SXDG = (INSTR_SINGLE_QUBIT_UNITARY, Operator("SXDG", S.arr @ H.arr @ S.arr))

instrNop_CSX = (INSTR_TWO_QUBIT_UNITARY, instrNop_SX[1].ctrl)
