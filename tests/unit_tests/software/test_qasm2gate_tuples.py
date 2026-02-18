"""
Tests for qasm2gate_tuples module
"""

import itertools as it
from pathlib import Path
import unittest

from netsquid.components import instructions as instr

from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
from dqc_simulator.hardware.dqc_creation import DQC
from dqc_simulator.hardware.quantum_processors import NoisyQPU
from dqc_simulator.qlib.states import werner_state
from dqc_simulator.software.qasm2gate_tuples import qasm2gate_tuples

directory_path = (
    Path(__file__).parents[2] / "MQT_benchmarking_circuits/"
).as_posix() + "/"  # path to benchmark circuits
include_path = Path(__file__).parent.as_posix()  # path to parent directory


class Test_qasm2gate_tuples(unittest.TestCase):
    def setUp(self):
        # Defining QPU
        qpu_class = NoisyQPU
        kwargs4qpu = {
            "p_depolar_error_cnot": 0,
            "single_qubit_gate_error_prob": 0,
            "meas_error_prob": 0,
            "comm_qubit_depolar_rate": 0,
            "proc_qubit_depolar_rate": 0,
            "single_qubit_gate_time": 135 * 10**3,
            "two_qubit_gate_time": 600 * 10**3,
            "measurement_time": 600 * 10**4,
            "num_positions": 10,
            "num_comm_qubits": 2,
        }

        # Defining connection
        entangling_connection_class = BlackBoxEntanglingQsourceConnection
        F_werner = 1
        kwargs4conn = {
            "delay": 1e9 / 182,  # in ns
            "state4distribution": werner_state(F_werner),
        }

        # Defining DQC network
        num_qpus = 3
        quantum_topology = list(it.combinations(range(3), 2))
        classical_topology = list(it.combinations(range(3), 2))
        self.dqc = DQC(
            entangling_connection_class,
            num_qpus,
            quantum_topology,
            classical_topology,
            qpu_class=qpu_class,
            **kwargs4qpu,
            **kwargs4conn,
        )

    def test_on_ghz_circuit(self):
        # assuming that working directory is repo root
        filepath = directory_path + "ghz_indep_qiskit_5.qasm"
        scheme = "cat"
        gate_tuples = qasm2gate_tuples(
            self.dqc, filepath, scheme, include_path=include_path
        )
        expected_output = [
            (instr.INSTR_INIT, [2, 3], "node_0"),
            (instr.INSTR_INIT, [2, 3], "node_1"),
            (instr.INSTR_INIT, [2], "node_2"),
            (instr.INSTR_H, 2, "node_2"),
            (instr.INSTR_CNOT, 2, "node_2", 3, "node_1", "cat"),
            (instr.INSTR_CNOT, 3, "node_1", 2, "node_1"),
            (instr.INSTR_CNOT, 2, "node_1", 3, "node_0", "cat"),
            (instr.INSTR_CNOT, 3, "node_0", 2, "node_0"),
        ]
        self.assertEqual(gate_tuples, expected_output)


if __name__ == "__main__":
    unittest.main()
