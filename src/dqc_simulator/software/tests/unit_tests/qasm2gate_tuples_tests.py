"""
Tests for qasm2gate_tuples module
"""

import itertools as it
import unittest

from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
from dqc_simulator.hardware.dqc_creation import DQC
from dqc_simulator.hardware.quantum_processors import NoisyQPU
from dqc_simulator.qlib.states import werner_state
from dqc_simulator.software.qasm2gate_tuples import qasm2gate_tuples

class Test_qasm2gate_tuples(unittest.TestCase):
    def setUp(self):
        # Defining QPU
        qpu_class = NoisyQPU
        kwargs4qpu = {'p_depolar_error_cnot' : 0,
                       'single_qubit_gate_error_prob' : 0,
                       'meas_error_prob' : 0,
                       'comm_qubit_depolar_rate' : 0,
                       'proc_qubit_depolar_rate' : 0,
                       'single_qubit_gate_time' : 135 * 10**3,
                       'two_qubit_gate_time' : 600 * 10**3,
                       'measurement_time' : 600 * 10**4,
                       'num_positions' : 10,
                       'num_comm_qubits' : 2}
        
        # Defining connection
        entangling_connection_class = BlackBoxEntanglingQsourceConnection
        F_werner = 1
        kwargs4conn = {'delay' : 1e9/182, #in ns
                       'state4distribution' : werner_state(F_werner)}
        
        # Defining DQC network
        num_qpus = 3
        quantum_topology = list(it.combinations(range(3), 2))
        classical_topology = list(it.combinations(range(3), 2))
        self.dqc = DQC(entangling_connection_class, num_qpus,
                  quantum_topology, classical_topology,
                  qpu_class=qpu_class,
                  **kwargs4qpu, **kwargs4conn)
        
    def test_on_ghz_circuit(self):
        filepath = 'ghz_indep_qiskit_5.qasm'
        scheme = 'cat'
        gate_tuples = qasm2gate_tuples(self.dqc, filepath, scheme, 
                                       include_path='.')
        print(gate_tuples)
# =============================================================================
#         expected_output = 
#         self.assertEqual(gate_tuples, expected_output)
# =============================================================================

