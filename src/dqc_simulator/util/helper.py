# -*- coding: utf-8 -*-
# =============================================================================
# Created on Wed Sep 20 14:28:30 2023
#
# @author: kenny
# =============================================================================
"""
Provides helper functions.

The helper functions are intended to smooth the process of working with the
simulator and also aid development.
"""

# This module provides utility functions for smoothing
# the process of working with the simulator.

from enum import Enum
import inspect

import pydynaa
from netsquid.qubits.dmtools import DenseDMRepr
from netsquid.protocols.protocol import Signals
from netsquid.qubits import qubitapi as qapi
from netsquid.util.datacollector import DataCollector


def create_wrapper_with_some_args_fixed(func, args2fix, **kwargs2fix):
    """Bakes in some arguments to a function,

    Parameters
    ----------
    func : function
        The function to create a wrapper for.
    args2fix : dict or None
        The relative postion of the argument (key in dict) that should be fixed
        and the value to fix it to (value in dict).
    kwargs2fix
        The keyword arguments to fix (specified in the normal way not
        aggregated)

    Returns
    -------
    wrapper : function
        A wrapper for `func` which fixes some of the arguments, so that the
        user inputs a reduced set of arguments relative to func.
    """

    def func_wrapper(*unfixed_args, **kwargs):
        if args2fix is None:
            wrapper = func(*unfixed_args, **kwargs2fix, **kwargs)
        else:
            unfixed_arg_iter = iter(unfixed_args)
            num_pos_args4func = len(args2fix) + len([*unfixed_args])
            wrapper = func(
                *(
                    args2fix[ii] if ii in args2fix else next(unfixed_arg_iter)
                    for ii in range(num_pos_args4func)
                ),
                **kwargs2fix,
                **kwargs,
            )
        return wrapper

    return func_wrapper


def filter_kwargs4internal_functions(funcs_with_kwargs, kwargs):
    """
    Filters keyword arguments specified by a parent function for use in calls
    to functions within the definition of the parent function.

    Parameters
    ----------
    funcs_with_kwargs : list or tuple of functions
        The internal functions needing keyword arguments
    kwargs : dict
        The keyword arguments.

    Returns
    -------
    sorted_kwargs : dict of dicts
        The kwargs for each different function. Key is function and values are
        kwargs to be unpacked in each function call.
    """
    sorted_kwargs = {}
    for func in funcs_with_kwargs:
        # making list of positional and keyword arguments
        arg_names = list(inspect.signature(func).parameters)
        # filtering for only the kwargs and associating them with their values
        kwargs4func = {
            arg_name: kwargs[arg_name] for arg_name in arg_names if arg_name in kwargs
        }
        sorted_kwargs[func] = kwargs4func
    return sorted_kwargs


# =============================================================================
# #_idx for debugging only REMOVE ONCE debugged
# from netsquid.qubits.qubit import Qubit
# def _idx(qubits):
#     # This helper function is always executed together with _qrepr, so we skip safety checks
#     # and combining.
#     if isinstance(qubits, Qubit):
#         return qubits.qstate.indices_of([qubits])
#     elif isinstance(qubits, list):
#         return qubits[0].qstate.indices_of(qubits)
#     else:
#         raise TypeError("The qubits must be given as a list or a single Qubit.")
# =============================================================================


def get_data_collector(master_protocol, qubit_indices_2b_checked, desired_state):
    """Sets up data collector for arbitrary simulation.

    Parameters
    ----------
    master_protocol: :class:netsquid.protocols.protocol.Protocol
        Protocol to run the DQC circuit.
    qubits_2b_checked: list of tuples of form (list of indices, node)
        The qubits whose state should be checked against a known state
    desired_state: :class:numpy.ndarray
        The ideal state which the actual state should be compared to. Can be
        given as a ket vector or density matrix regardless of the formalism
        being worked with

    Returns
    -------
    dc : :class:`~netsquid.util.datacollector.DataCollector`
        Data collector to record fidelity.
    """

    def collect_fidelity_data(evexpr):
        # defining which protocol you wish to sample the event expression from
        # (CorrectionProtocol)
        qubits_2b_checked = []
        for qubit_node_tuple in qubit_indices_2b_checked:
            if isinstance(qubit_node_tuple[0], int):
                qubit_indices = [qubit_node_tuple[0]]
            elif isinstance(qubit_node_tuple[0], list):
                qubit_indices = qubit_node_tuple[0]
            else:
                raise TypeError(
                    f"{qubit_node_tuple} not of correct form."
                    "The first element of each tuple must be qubit"
                    " index or list of qubit indices"
                )
            node = qubit_node_tuple[-1]
            qubits = node.qmemory.pop(qubit_indices)
            qubits_2b_checked = qubits_2b_checked + qubits

        fidelity = qapi.fidelity(qubits_2b_checked, desired_state, squared=True)

        for qubit in qubits_2b_checked:
            qapi.discard(qubit)
        return {"fidelity": fidelity}

    dc = DataCollector(collect_fidelity_data)
    dc.collect_on(
        pydynaa.EventExpression(
            source=master_protocol, event_type=Signals.FINISHED.value
        )
    )
    return dc


def get_data_collector4dm(master_protocol, qubit_indices_2b_checked, desired_state):
    """Creates a data collector with a specific configuration.

    Sets up :class:`~netsquid.util.datacollector.DataCollector` for simulation
    in which `qubits_indices_2b_checked` share a dm. This avoids the
    sensitivity to the ordering of the qubits to
    be checked in the list produced below but at the cost of requiring desired
    state to be a density matrix.

    Parameters
    ----------
    master_protocol: :class:`~netsquid.protocols.protocol.Protocol`
        Protocol to run the DQC circuit.
    qubits_2b_checked: list of tuples of form (list of indices, node)
        The qubits whose state should be checked against a known state
    desired_state: array
        The ideal state which the actual state should be compared to. Must be
        given as a density matrix.

    Returns
    -------
    :class:`~netsquid.util.datacollector.DataCollector`
        Data collector to record fidelity.
    """

    def collect_fidelity_data(evexpr):
        # defining which protocol you wish to sample the event expression from
        # (CorrectionProtocol)
        qubits_2b_checked = []
        for qubit_node_tuple in qubit_indices_2b_checked:
            if isinstance(qubit_node_tuple[0], int):
                qubit_indices = [qubit_node_tuple[0]]
            elif isinstance(qubit_node_tuple[0], list):
                qubit_indices = qubit_node_tuple[0]
            else:
                raise TypeError(
                    f"{qubit_node_tuple} not of correct form."
                    "The first element of each tuple must be qubit"
                    " index or list of qubit indices"
                )
            node = qubit_node_tuple[-1]
            qubits = node.qmemory.pop(qubit_indices)
            qubits_2b_checked = qubits_2b_checked + qubits
        qapi.combine_qubits(qubits_2b_checked)
        fidelity = qubits[0].qstate.qrepr.fidelity(
            DenseDMRepr(dm=desired_state), squared=True
        )  # for debugging
        for qubit in qubits_2b_checked:
            qapi.discard(qubit)
        return {"fidelity": fidelity}

    dc = DataCollector(collect_fidelity_data)
    dc.collect_on(
        pydynaa.EventExpression(
            source=master_protocol, event_type=Signals.FINISHED.value
        )
    )
    return dc


class QDCSignals(Enum):
    """
    Specialist signals for use in a quantum data centre (QDC).
    """

    RESULT_PRODUCED = pydynaa.EventType(
        "result_produced", "result of instruction produced and ready to be logged."
    )


def get_data_collector_for_mid_sim_instr_output():
    """
    For collecting instruction output generated during the sim.

    This collects results generated by the `result_produced_evexpr` inside
    the _logged_instr method, which indicates that an instruction has produced
    a result that should be logged. This is most likely a measurement result
    from a measurement instruction.

    Returns
    -------
    :class:`~netsquid.util.datacollector.DataCollector`
        Data collector to record the output of an instruction (most likely a
        measurement result from a measurement instruction).
    """

    def collect_instruction_output(evexpr):
        protocol = evexpr.triggered_events[-1].source
        result_and_index = protocol.get_signal_result(QDCSignals.RESULT_PRODUCED)
        result = result_and_index[0]
        ancilla_qubit_index = result_and_index[1]
        return {"result": result, "ancilla_qubit_index": ancilla_qubit_index}

    dc = DataCollector(collect_instruction_output)
    dc.collect_on(
        [pydynaa.EventExpression(event_type=QDCSignals.RESULT_PRODUCED.value)]
    )
    return dc
