# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 14:28:30 2023

@author: kenny
"""

#This module provides utility functions for smoothing 
#the process of working with the simulator.


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
            elif type(qubit_node_tuple[0]) == list():
                qubit_indices = qubit_node_tuple[0]
            else:
                raise TypeError("first element of each tuple must be qubit "
                                "index or list of qubit indices")
            node = qubit_node_tuple[-1]
            qubits = node.qmemory.pop(qubit_indices)
            qubits_2b_checked = qubits_2b_checked + qubits
            
        fidelity = qapi.fidelity(qubits_2b_checked, 
                                 desired_state, squared=True)
        for qubit in qubits_2b_checked:
            qapi.discard(qubit)
        return {"fidelity": fidelity}

    dc = DataCollector(collect_fidelity_data)
    dc.collect_on(pydynaa.EventExpression(source=master_protocol,
                                          event_type=Signals.FINISHED.value))
    return dc