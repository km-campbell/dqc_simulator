# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 15:06:00 2023

@author: kenny
"""

import abc
import math


def bisect_circuit(dqc_circuit, comm_qubits_per_node=2):
    """
    Bisects a circuit into two nodes, node_0 and node_1. For circuits with odd
    numbers of qubits, node_0 will be given the extra qubit. It also adds,
    communication qubits to each node. It is assumed that all indices of the 
    qubits in the input dqc_circuit are intended to be data qubits (so if the
    input circuit is already partitioned in some way, then this function is
    not appropriate to provide an additional bisection.)
    """
    #helper functions:
    def _assign_qubit_to_node(qubit_index, qreg_name,
                              node1starting_index):
            starting_index = (dqc_circuit.qregs[qreg_name]['starting_index'] +
                              comm_qubits_per_node)
            updated_qubit_index = qubit_index + starting_index
            node_name = 'node_0'
            if updated_qubit_index >= node1starting_index:
                updated_qubit_index = (updated_qubit_index - 
                                       node1starting_index + 
                                       comm_qubits_per_node)
                node_name = 'node_1'
            return updated_qubit_index, node_name
            
    #main body:
    total_num_qubits = 2 * comm_qubits_per_node
    for qreg_name in dqc_circuit.qregs:
        qreg = dqc_circuit.qregs[qreg_name]
        total_num_qubits = qreg['size'] + total_num_qubits
    node_0_size = math.ceil(total_num_qubits/2) #ceiling division
    node_1_size = total_num_qubits - node_0_size
    node1starting_index = node_0_size #as indexing starts from zero
    for gate_spec in dqc_circuit.ops:
        qubit_index1 = gate_spec[1]
        qreg_name1 = gate_spec[2]
        updated_qubit_index, node_name = _assign_qubit_to_node(
                                                    qubit_index1,
                                                    qreg_name1,
                                                    node1starting_index)
        gate_spec[1] = updated_qubit_index
        gate_spec[2] = node_name
        if len(gate_spec) >= 5:
            qubit_index2 = gate_spec[3]
            qreg_name2 = gate_spec[4]
            updated_qubit_index, node_name = _assign_qubit_to_node(
                                                    qubit_index2, 
                                                    qreg_name2,
                                                    node1starting_index)
            gate_spec[3] = updated_qubit_index
            gate_spec[4] = node_name
    
    dqc_circuit.node_sizes = {'node_0' : node_0_size, 'node_1' : node_1_size}
    dqc_circuit.circuit_type = 'partitioned'


                