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

#This module provides utility functions for smoothing 
#the process of working with the simulator.



import inspect

import pydynaa
from netsquid.qubits.dmtools import DenseDMRepr
from netsquid.protocols.protocol import Signals
from netsquid.qubits import qubitapi as qapi
from netsquid.util.datacollector import DataCollector
from netsquid.qubits.dmutil import reorder_dm

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
            wrapper = func(*(args2fix[ii] if ii in args2fix else next(unfixed_arg_iter)
                             for ii in range(num_pos_args4func)), 
                           **kwargs2fix, 
                           **kwargs)
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
        The keyword argument.

    Returns
    -------
    sorted_kwargs : dict of dicts
        The kwargs for each different function. Key is function and values are
        kwargs to be unpacked in each function call.
    """
    sorted_kwargs = {}
    for func in funcs_with_kwargs:
        #making list of positional and keyword arguments
        arg_names = list(inspect.signature(func).parameters) 
        #filtering for only the kwargs and associating them with their values
        kwargs4func = {arg_name : kwargs[arg_name] for arg_name in arg_names 
                       if arg_name in kwargs}
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


def get_data_collector(master_protocol, qubit_indices_2b_checked,
                       desired_state):
    """ Sets up data collector for arbitrary simulation.

    Parameters
    ----------
    master_protocol: :class: netsquid.protocols.protocol.Protocol
        Protocol to run the DQC circuit.
    qubits_2b_checked: list of tuples of form (list of indices, node)
        The qubits whose state should be checked against a known state
    desired_state: :class: numpy.ndarray
        The ideal state which the actual state should be compared to. Can be
        given as a ket vector or density matrix regardless of the formalism 
        being worked with

    Returns
    -------
    dc : :class:`~netsquid.util.datacollector.DataCollector`
        Data collector to record fidelity.
    """
    def collect_fidelity_data(evexpr):
        #defining which protocol you wish to sample the event expression from 
        #(CorrectionProtocol)
        qubits_2b_checked = []
        for qubit_node_tuple in qubit_indices_2b_checked:
            if type(qubit_node_tuple[0]) == int:
                qubit_indices = [qubit_node_tuple[0]]
            elif type(qubit_node_tuple[0]) == list:
                qubit_indices = qubit_node_tuple[0]
            else:
                raise TypeError(f"{qubit_node_tuple} not of correct form."
                                "The first element of each tuple must be qubit"
                                " index or list of qubit indices")
            node = qubit_node_tuple[-1]
            qubits = node.qmemory.pop(qubit_indices)
            qubits_2b_checked = qubits_2b_checked + qubits

# =============================================================================
#         #Re-ordering qubits_2b_checked to match the ordering of qubits in the
#         #qstate of any combined qubits. This is needed to avoid errors in the 
#         #call to qapi.fidelity. I do this only in cases where all data
#         #qubits are being looked at as otherwise this may fail when I have just
#         #one qubit of interest but it was combined with others at some point
#         #in the circuit (even if entanglement is destroyed, the combination
#         #may persist).
#         print(f"pre-combo {qubits_2b_checked[0].qstate}")
#         print(f"pre-combo {qubits_2b_checked[0].qstate.qrepr}")
#         print(f"pre-combo {qubits_2b_checked}")
#         qapi.combine_qubits(qubits_2b_checked)
#         indices = qubits_2b_checked[0].qstate.indices_of(qubits_2b_checked)
#         print(f"idx before if is {_idx(qubits_2b_checked)}")
#         if qubits_2b_checked[0].qstate.num_qubits == len(indices):
#         #if number of qubits in qstate == number of qubits being checked:
#             #re-ordering:
#             reordered_indices = list(indices)
#             reordered_indices.sort()
#             index_mapping = {key:value for (key, value) in zip(indices, reordered_indices)}
#             qubits_2b_checked = [qubits_2b_checked[index_mapping[ii]] for ii in reordered_indices]
#         print(qubits_2b_checked[0].qstate.qrepr)
#         print(qubits_2b_checked)
#         print(f"idx after if {_idx(qubits_2b_checked)}")
# =============================================================================
        fidelity = qapi.fidelity(qubits_2b_checked, desired_state, 
                                 squared=True)
# =============================================================================
#         import numpy as np # for debugging only
#         print(f"desired state is {desired_state} with dimensions {np.shape(desired_state)}")
#         from netsquid.qubits.dmtools import DenseDMRepr #for debugging
#         fidelity = qubits[0].qstate.qrepr.fidelity(DenseDMRepr(dm=desired_state), 
#                                                    squared=True) #for debugging
# =============================================================================
        for qubit in qubits_2b_checked:
            qapi.discard(qubit)
        return {"fidelity": fidelity}

    dc = DataCollector(collect_fidelity_data)
    dc.collect_on(pydynaa.EventExpression(source=master_protocol,
                                          event_type=Signals.FINISHED.value))
    return dc


def get_data_collector4dm(master_protocol, qubit_indices_2b_checked,
                          desired_state):
    """Creates a data collector with a specific configuration.
    
    Sets up :class:`~netsquid.util.datacollector.DataCollector` for simulation 
    in which `qubits_indices_2b_checked` share a dm. This avoids the 
    sensitivity to the ordering of the qubits to 
    be checked in the list produced below but at the cost of requiring desired
    state to be a density matrix.

    Parameters
    ----------
    master_protocol: :class: `~netsquid.protocols.protocol.Protocol`
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
        #defining which protocol you wish to sample the event expression from 
        #(CorrectionProtocol)
        qubits_2b_checked = []
        for qubit_node_tuple in qubit_indices_2b_checked:
            if type(qubit_node_tuple[0]) == int:
                qubit_indices = [qubit_node_tuple[0]]
            elif type(qubit_node_tuple[0]) == list:
                qubit_indices = qubit_node_tuple[0]
            else:
                raise TypeError(f"{qubit_node_tuple} not of correct form."
                                "The first element of each tuple must be qubit"
                                " index or list of qubit indices")
            node = qubit_node_tuple[-1]
            qubits = node.qmemory.pop(qubit_indices)
            qubits_2b_checked = qubits_2b_checked + qubits
        qapi.combine_qubits(qubits_2b_checked)
        fidelity = qubits[0].qstate.qrepr.fidelity(DenseDMRepr(dm=desired_state), 
                                                   squared=True) #for debugging
        for qubit in qubits_2b_checked:
            qapi.discard(qubit)
        return {"fidelity": fidelity}

    dc = DataCollector(collect_fidelity_data)
    dc.collect_on(pydynaa.EventExpression(source=master_protocol,
                                          event_type=Signals.FINISHED.value))
    return dc