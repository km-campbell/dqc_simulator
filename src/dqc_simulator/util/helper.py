# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 14:28:30 2023

@author: kenny
"""

#This module provides utility functions for smoothing 
#the process of working with the simulator.

import pydynaa

import numpy as np 

from netsquid.qubits.dmtools import DenseDMRepr
from netsquid.protocols.protocol import Signals
from netsquid.qubits import qubitapi as qapi
from netsquid.util.datacollector import DataCollector
from netsquid.qubits.dmutil import reorder_dm

def get_data_qubit_indices(node, num_indices):
    """ A convenience function for obtaining the indices of data qubits for a
    given node.
    
    INPUT: node: netsquid.nodes.Node object
            The node whose data qubits should be recovered.
           num_indices: int
           The number of data qubit indices requested
    
    OUTPUT: list of the indices requested
    """
    starting_data_qubit_index = len(node.comm_qubit_positions)
    end = starting_data_qubit_index + num_indices
    index_list = [ii for ii in range(starting_data_qubit_index, end)]
    return index_list

#_idx for debugging only REMOVE ONCE debugged
from netsquid.qubits.qubit import Qubit
def _idx(qubits):
    # This helper function is always executed together with _qrepr, so we skip safety checks
    # and combining.
    if isinstance(qubits, Qubit):
        return qubits.qstate.indices_of([qubits])
    elif isinstance(qubits, list):
        return qubits[0].qstate.indices_of(qubits)
    else:
        raise TypeError("The qubits must be given as a list or a single Qubit.")


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
    """ Sets up data collector for simulation in which qubits_indices_2b_checked
    share a dm. This avoids the sensitivity to the ordering of the qubits to 
    be checked in the list produced below but at the cost of requiring desired
    state to be a density matrix.

    Parameters
    ----------
    master_protocol: :class: netsquid.protocols.protocol.Protocol
        Protocol to run the DQC circuit.
    qubits_2b_checked: list of tuples of form (list of indices, node)
        The qubits whose state should be checked against a known state
    desired_state: :class: numpy.ndarray
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