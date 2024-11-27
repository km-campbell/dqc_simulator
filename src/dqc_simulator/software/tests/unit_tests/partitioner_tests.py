# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 10:55:16 2023

@author: kenny
"""

import unittest

from netsquid.components import instructions as instr
from netsquid.nodes import Network, Node

from dqc_simulator.hardware.quantum_processors import ( 
    create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates)
from dqc_simulator.qlib.circuits import get_ghz_gate_tuples
from dqc_simulator.software.dqc_circuit import DqcCircuit
from dqc_simulator.software.partitioner import (
    bisect_circuit, first_come_first_served_qubits_to_qpus,
    partition_gate_tuples)

class Test_bisect_circuit(unittest.TestCase):
    def test_qregs_all_given_own_node(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5}}
        cregs = dict()
        native_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 3, 'qreg1', 4, 'qreg2']]
        dqc_circuit = DqcCircuit(qregs, cregs, native_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit, comm_qubits_per_node=2)
        desired_ops = [['u', 3, 'node_0'], ['cx', 5, 'node_0', 5, 'node_1']]
        self.assertEqual(dqc_circuit.ops, desired_ops)
    
    def test_more_qregs_than_nodes(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5},
                 'qreg3' : {'size' : 3, 'starting_index' : 11}}
        cregs = dict()
        native_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 0, 'qreg2', 2, 'qreg3']]
        dqc_circuit = DqcCircuit(qregs, cregs, native_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit)
        desired_ops = [['u', 3, 'node_0'], ['cx', 7, 'node_0', 8, 'node_1']]
        self.assertEqual(dqc_circuit.ops, desired_ops)
        
    def test_odd_num_qubits(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5},
                 'qreg3' : {'size' : 4, 'starting_index' : 11}}
        cregs = dict()
        native_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 0, 'qreg2', 3, 'qreg3']]
        dqc_circuit = DqcCircuit(qregs, cregs, native_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit)
        desired_ops = [['u', 3, 'node_0'], ['cx', 7, 'node_0', 8, 'node_1']]
        #desired_ops should be unchanged from prev test despite change to
        #ops as the extra qubit should go on node_0
        self.assertEqual(dqc_circuit.ops, desired_ops)


class Test_first_come_first_served_qubits_to_qpus(unittest.TestCase):
    def test_with_4qpus_4proc_qubits(self):
        qpu_nodes = [
            Node(f'node_{ii}', 
                 qmemory=create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(
                                                 p_depolar_error_cnot=0,
                                                 comm_qubit_depolar_rate=0,
                                                 proc_qubit_depolar_rate=0,
                                                 single_qubit_gate_time=135 * 10**3,
                                                 two_qubit_gate_time=600 * 10**3,
                                                 measurement_time=600 * 10**4,
                                                 alpha=1, beta=0,
                                                 num_positions=20,
                                                 num_comm_qubits=2))
                for ii in range(4)]
        gate_tuples = get_ghz_gate_tuples(num_qubits=4)
        old_to_new_lookup = first_come_first_served_qubits_to_qpus(gate_tuples, 
                                                        qpu_nodes)
        desired_output = {ii : (2, node.name) for ii, node in enumerate(qpu_nodes)}
        self.assertEqual(old_to_new_lookup, desired_output)
        
    def test_with_4qpus_5proc_qubits(self):
        qpu_nodes = [
            Node(f'node_{ii}', 
                 qmemory=create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(
                                                 p_depolar_error_cnot=0,
                                                 comm_qubit_depolar_rate=0,
                                                 proc_qubit_depolar_rate=0,
                                                 single_qubit_gate_time=135 * 10**3,
                                                 two_qubit_gate_time=600 * 10**3,
                                                 measurement_time=600 * 10**4,
                                                 alpha=1, beta=0,
                                                 num_positions=20,
                                                 num_comm_qubits=2))
                for ii in range(4)]
        gate_tuples = get_ghz_gate_tuples(num_qubits=5)
        old_to_new_lookup = first_come_first_served_qubits_to_qpus(gate_tuples, 
                                                        qpu_nodes)
        desired_output = {0 : (2, 'node_0'), 1 : (3, 'node_0')}
        desired_output.update({ii+2 : (2, node.name) for ii, node in enumerate(qpu_nodes[1:])})
        self.assertEqual(old_to_new_lookup, desired_output)
            
    def test_with_4qpus_10proc_qubits(self):
        qpu_nodes = [
            Node(f'node_{ii}', 
                 qmemory=create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(
                                                 p_depolar_error_cnot=0,
                                                 comm_qubit_depolar_rate=0,
                                                 proc_qubit_depolar_rate=0,
                                                 single_qubit_gate_time=135 * 10**3,
                                                 two_qubit_gate_time=600 * 10**3,
                                                 measurement_time=600 * 10**4,
                                                 alpha=1, beta=0,
                                                 num_positions=20,
                                                 num_comm_qubits=2))
                for ii in range(4)]
        gate_tuples = get_ghz_gate_tuples(num_qubits=10)
        old_to_new_lookup = first_come_first_served_qubits_to_qpus(gate_tuples, 
                                                        qpu_nodes)
        qpu0_allocation = {ii : (ii+2, 'node_0') for ii in range(3)}
        qpu1_allocation = {ii + 3 : (ii + 2, 'node_1') for ii in range(3)}
        qpu2_allocation = {ii + 6 : (ii + 2, 'node_2') for ii in range(2)}
        qpu3_allocation = {ii + 8 : (ii + 2, 'node_3') for ii in range(2)}
        desired_output = {**qpu0_allocation, **qpu1_allocation,
                          **qpu2_allocation, **qpu3_allocation}
        self.assertEqual(old_to_new_lookup, desired_output)

class Test_partition_gate_tuples_with_first_come_first_served_qubits_to_qpus(
        unittest.TestCase):
    def setUp(self):
        self.qubit2qpu_allocator = first_come_first_served_qubits_to_qpus
    def test_with_4qpus_10proc_qubits(self):
        num_qpus = 4
        num_qubits = 10
        scheme = 'cat'
        qpu_nodes = [
                    Node(f'node_{ii}', 
                         qmemory=create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(
                                                         p_depolar_error_cnot=0,
                                                         comm_qubit_depolar_rate=0,
                                                         proc_qubit_depolar_rate=0,
                                                         single_qubit_gate_time=135 * 10**3,
                                                         two_qubit_gate_time=600 * 10**3,
                                                         measurement_time=600 * 10**4,
                                                         alpha=1, beta=0,
                                                         num_positions=20,
                                                         num_comm_qubits=2))
                        for ii in range(num_qpus)]
        network = Network('qdc', nodes=qpu_nodes)
        gate_tuples = get_ghz_gate_tuples(num_qubits)
        partitioned_gate_tuples = partition_gate_tuples(gate_tuples, network, 
                                                        scheme, 
                                                        self.qubit2qpu_allocator)
        desired_output = [(instr.INSTR_INIT, [2, 3, 4], 'node_0'),
                          (instr.INSTR_INIT, [2, 3, 4], 'node_1'),
                          (instr.INSTR_INIT, [2, 3], 'node_2'),
                          (instr.INSTR_INIT, [2, 3], 'node_3'),
                          (instr.INSTR_H, 2, 'node_0'),
                          (instr.INSTR_CNOT, 2, 'node_0', 3, 'node_0'),
                          (instr.INSTR_CNOT, 3, 'node_0', 4, 'node_0'),
                          (instr.INSTR_CNOT, 4, 'node_0', 2, 'node_1', scheme),
                          (instr.INSTR_CNOT, 2, 'node_1', 3, 'node_1'),
                          (instr.INSTR_CNOT, 3, 'node_1', 4, 'node_1'),
                          (instr.INSTR_CNOT, 4, 'node_1', 2, 'node_2', scheme),
                          (instr.INSTR_CNOT, 2, 'node_2', 3, 'node_2'),
                          (instr.INSTR_CNOT, 3, 'node_2', 2, 'node_3', scheme),
                          (instr.INSTR_CNOT, 2, 'node_3', 3, 'node_3')]
        self.assertEqual(partitioned_gate_tuples, desired_output)





if __name__ == '__main__':
    unittest.main()