"""
Unit(ish) tests of dqc_control.py and some fast integration tests.

Some of these tests are arguably fast integration tests because the
protocols in dqc_control are inherently meant to control other things and it is
challenging to say anything meaningful about dqc_control if they do not do so.
Where things from other modules are used, they should have been tested
elsewhere and what is being tested here is whether protocols in dqc_control
correctly control them.
"""

import unittest

import netsquid as ns
import pydynaa
import numpy as np
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
from netsquid.components import instructions as instr
from netsquid.qubits.qformalism import set_qstate_formalism
from netsquid.qubits.qformalism import QFormalism

from dqc_simulator.hardware.dqc_creation import create_dqc_network
from dqc_simulator.software.dqc_control import (
    dqcMasterProtocol,
    UnfinishedQuantumCircuitError,
)
from dqc_simulator.util.helper import get_data_collector_for_mid_sim_instr_output

# for debugging
# =============================================================================
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# # =============================================================================
# # loggers['netsquid'].setLevel(logging.WARNING)
# # =============================================================================
# =============================================================================


class TestDqcMasterProtocol(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        self.network = create_dqc_network(
            state4distribution=ks.b00,
            node_list=None,
            num_qpus=2,
            node_distance=4e-3,
            quantum_topology=None,
            classical_topology=None,
            want_classical_2way_link=True,
            want_entangling_link=True,
            name="linear network",
            num_comm_qubits=3,
        )
        self.node_0 = self.network.get_node("node_0")
        self.node_1 = self.network.get_node("node_1")
        self.sim_runtime = 1e9

    def test_can_implement_gates_locally_on_2_qpus(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_X, 2, "node_0"),
            (instr.INSTR_X, 2, "node_1"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, nodes=self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_0,) = self.node_0.qmemory.pop(2)
        (qubit_node_1,) = self.node_1.qmemory.pop(2)
        with self.subTest(msg="node_0 in incorrect state"):
            fidelity = qapi.fidelity(qubit_node_0, ks.s1)
            self.assertAlmostEqual(fidelity, 1.0, 5)
        with self.subTest(msg="node_1 in incorrect state"):
            fidelity = qapi.fidelity(qubit_node_1, ks.s1)
            self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_implement_remote_CNOT_gate_with_cat(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_H, 2, "node_0"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "cat"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_0,) = self.node_0.qmemory.pop(2)
        (qubit_node_1,) = self.node_1.qmemory.pop(2)
        fidelity = qapi.fidelity([qubit_node_0, qubit_node_1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_implement_teleportation_to_comm_qubit(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_H, 2, "node_0"),
            ([], 2, "node_0", 0, "node_1", "teleport_only"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_1,) = self.node_1.qmemory.pop(0)
        fidelity = qapi.fidelity([qubit_node_1], ks.h0)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_implement_remote_CNOT_gate_with_tp_safe(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_H, 2, "node_0"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_0,) = self.node_0.qmemory.pop(2)
        (qubit_node_1,) = self.node_1.qmemory.pop(2)
        fidelity = qapi.fidelity([qubit_node_0, qubit_node_1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_implement_consecutive_remote_CNOTs_with_cat(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_H, 2, "node_0"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "cat"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "cat"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "cat"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_0,) = self.node_0.qmemory.pop(2)
        (qubit_node_1,) = self.node_1.qmemory.pop(2)
        fidelity = qapi.fidelity([qubit_node_0, qubit_node_1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_implement_consecutive_remote_CNOTs_with_tp_safe(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_H, 2, "node_0"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        protocol.check_quantum_circuit_finished()
        (qubit_node_0,) = self.node_0.qmemory.pop(2)
        (qubit_node_1,) = self.node_1.qmemory.pop(2)
        fidelity = qapi.fidelity([qubit_node_0, qubit_node_1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_check_quantum_circuit_finished(self):
        class BrokenDqcMasterProtocolCopy(dqcMasterProtocol):
            """
            An exact copy of dqcMasterProtocol except that the run method is
            overridden to stop all of the time slices being evaluated. Ie, an
            artificial bug has been added.
            """

            def run(self):
                for qpu_name in self.qpu_op_dict:
                    self.subprotocols[f"{qpu_name}_OS"].start()
                # initialising dummy event expression
                dummy_entity = pydynaa.Entity()
                evtype_dummy = pydynaa.EventType("dummy_event", "dummy event")
                evexpr_dummy = pydynaa.EventExpression(
                    source=dummy_entity, event_type=evtype_dummy
                )
                expr = evexpr_dummy
                dummy_entity._schedule_now(evtype_dummy)

                # finding max length of dictionary entry
                longest_list_in_qpu_op_dict = max(self.qpu_op_dict.values(), key=len)
                # the artificial bug is added in the next line. We apply floor
                # division to halve the number of time slices
                max_num_time_slices = len(longest_list_in_qpu_op_dict) // 2
                while True:
                    for time_slice in range(max_num_time_slices):
                        for qpu_name in self.qpu_op_dict:
                            # if QPU still has instructions to carry out:
                            if time_slice < len(self.qpu_op_dict[qpu_name]):
                                # strictly less than because python indexes from 0
                                # signalling subprotocols to start the next time slice
                                self.send_signal(self.start_time_slice_label)
                                # waiting on subprotocols to complete time slice
                                expr = expr & self.await_signal(
                                    self.subprotocols[f"{qpu_name}_OS"],
                                    self.finished_time_slice_label,
                                )
                        yield expr
                        # re-initialising
                        expr = evexpr_dummy
                        dummy_entity._schedule_now(evtype_dummy)
                    break  # exiting outer while loop once for loops are done

        # dummy class definition is now finished!
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_INIT, 2, "node_1"),
            (instr.INSTR_H, 2, "node_0"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
            (instr.INSTR_CNOT, 2, "node_0", 2, "node_1", "tp_safe"),
        ]
        # the above gate_tuples will be split into different time slices by the
        # compiler, causing the artificial bug to become relevant
        protocol = BrokenDqcMasterProtocolCopy(gate_tuples, self.network.nodes)
        protocol.start()
        self.assertRaises(
            UnfinishedQuantumCircuitError, protocol.check_quantum_circuit_finished
        )
        # TO DO: run some more tests on this method to protect against false
        # positives

    def test_logged_instr(self):
        ancilla_qubit_index = 2
        gate_tuples = [
            (instr.INSTR_INIT, ancilla_qubit_index, "node_0"),
            (instr.INSTR_MEASURE, ancilla_qubit_index, "node_0", "logged"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        dc = get_data_collector_for_mid_sim_instr_output()
        protocol.start()
        ns.sim_run(self.sim_runtime)
        # checking DataFrame is not empty
        with self.subTest("DataFrame is empty"):
            self.assertFalse(dc.dataframe.empty, msg="DataFrame is empty")
        # checking result is correct
        with self.subTest("Result is wrong"):
            self.assertEqual(dc.dataframe["result"][0], 0)
        # checking index of ancilla qubit measured is correct
        with self.subTest("Ancilla qubit index is wrong"):
            self.assertEqual(
                dc.dataframe["ancilla_qubit_index"][0], ancilla_qubit_index
            )

    def test_multiple_logged_measurements(self):
        gate_tuples = [
            (instr.INSTR_INIT, 2, "node_0"),
            (instr.INSTR_X, 2, "node_0"),
            (instr.INSTR_MEASURE, 2, "node_0", "logged"),
            (instr.INSTR_X, 2, "node_0"),
            (instr.INSTR_MEASURE, 2, "node_0", "logged"),
            (instr.INSTR_X, 2, "node_0"),
            (instr.INSTR_MEASURE, 2, "node_0", "logged"),
        ]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        dc = get_data_collector_for_mid_sim_instr_output()
        protocol.start()
        ns.sim_run(self.sim_runtime)
        # checking DataFrame is not empty
        with self.subTest("DataFrame is empty"):
            self.assertFalse(dc.dataframe.empty, msg="DataFrame is empty")
        # checking result is correct
        with self.subTest("Result is wrong"):
            self.assertEqual(list(dc.dataframe["result"])[0:3], [1, 0, 1])
        # checking index of ancilla qubit measured is correct
        with self.subTest("Ancilla qubit index is wrong"):
            self.assertEqual(list(dc.dataframe["ancilla_qubit_index"])[0:3], [2, 2, 2])

    def test_ent_distribution(self):
        gate_tuples = [("node_0", "node_1", "distribute_ebit")]
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        (q0,) = self.node_0.qmemory.pop([0])
        (q1,) = self.node_1.qmemory.pop([0])
        # Checking state is correct
        desired_state = np.sqrt(1 / 2) * (np.kron(ks.s0, ks.s0) + np.kron(ks.s1, ks.s1))
        fidelity = qapi.fidelity([q0, q1], desired_state)
        self.assertAlmostEqual(fidelity, 1.0)

    def test_multiple_ent_distributions(self):
        gate_tuples = [("node_0", "node_1", "distribute_ebit")] * 3
        protocol = dqcMasterProtocol(gate_tuples, self.network.nodes)
        protocol.start()
        ns.sim_run(self.sim_runtime)
        node0_qubits = self.node_0.qmemory.pop([0, 1, 2])
        node1_qubits = self.node_1.qmemory.pop([0, 1, 2])
        # Checking state is correct
        desired_state = np.sqrt(1 / 2) * (np.kron(ks.s0, ks.s0) + np.kron(ks.s1, ks.s1))

        # Testing first pair
        with self.subTest("First pair in wrong state"):
            fidelity = qapi.fidelity([node0_qubits[0], node1_qubits[0]], desired_state)
            self.assertAlmostEqual(fidelity, 1.0)
        # Testing second pair
        with self.subTest("Second pair in wrong state"):
            fidelity = qapi.fidelity([node0_qubits[1], node1_qubits[1]], desired_state)
            self.assertAlmostEqual(fidelity, 1.0)
        # Testing third pair
        with self.subTest("Third pair in wrong state"):
            fidelity = qapi.fidelity([node0_qubits[2], node1_qubits[2]], desired_state)
            self.assertAlmostEqual(fidelity, 1.0)


# NOTE:
# Local protocols, such as node protocols can signal to a normal Protocol but
# not a LocalProtocol. Failure to distinguish between these causes errors
# Also, you need to use & (AND) rather than the lower case and. Similarly, you
# must use | (OR) rather than the the lower case or.

# running all class derived from the unittest.TestCase parent class:
if __name__ == "__main__":
    unittest.main()
