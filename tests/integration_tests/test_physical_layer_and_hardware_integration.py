# -*- coding: utf-8 -*-
# =============================================================================
# Created on Wed Sep 25 12:58:33 2024
#
# @author: kenny
# =============================================================================
"""
Integration tests for the physical layer software and the hardware to be acted
on.
"""

import unittest

import netsquid as ns
from netsquid.components import QuantumMemory
from netsquid.nodes import Network, Node
from netsquid.protocols import NodeProtocol
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi

from dqc_simulator.hardware.connections import (
    create_classical_fibre_link,
    create_midpoint_heralded_entangling_link,
    create_black_box_central_source_entangling_link,
)
from dqc_simulator.hardware.quantum_processors import QPU
from dqc_simulator.software.physical_layer import (
    AbstractCentralSourceEntangleProtocol,
    MidpointHeraldingProtocol,
)

# for debugging
# =============================================================================
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# # =============================================================================
# # #resetting to default after debugging
# # loggers = simlog.get_loggers()
# # loggers['netsquid'].setLevel(logging.WARNING)
# # =============================================================================
# =============================================================================


class _DummySuperprotocol(NodeProtocol):
    """
    Filling in for
    :class:`dqc_simulator.software.dqc_control.InterpreterProtocol`.
    """

    def __init__(
        self,
        node=None,
        name=None,
        role=None,
        other_node_name=None,
        comm_qubit_indices=None,
        ready4ent=None,
        num_entanglements2generate=1,
        entanglement_type2generate="bell_pair",
    ):
        super().__init__(node, name)
        self.ent_request_label = "ENT_REQUEST"
        self.add_signal(self.ent_request_label)
        self.role = role
        self.other_node_name = other_node_name
        self.comm_qubit_indices = comm_qubit_indices
        self.ready4ent = ready4ent
        self.num_entanglements2generate = num_entanglements2generate
        self.entanglement_type2generate = entanglement_type2generate

    def run(self):
        while True:
            yield self.await_timer(duration=5)
            self.send_signal(
                self.ent_request_label,
                result=(
                    self.role,
                    self.other_node_name,
                    self.comm_qubit_indices,
                    self.num_entanglements2generate,
                    self.entanglement_type2generate,
                ),
            )
            break


class TestAbstractEntanglingConnectionAndAbstractCentralSourceEntangleProtocol(
    unittest.TestCase
):
    """
    Integration tests of AbstractCentralSourceEntangleProtocol with
    BlackBoxEntanglingQsourceConnection.
    """

    def setUp(self):
        ns.sim_reset()
        self.node0 = Node("node0", qmemory=QuantumMemory("qmemory", num_positions=3))
        self.node1 = Node("node1", qmemory=QuantumMemory("qmemory", num_positions=3))
        self.network = Network("network", nodes=[self.node0, self.node1])
        # establishing quantum connection
        create_black_box_central_source_entangling_link(
            self.network,
            self.node0,
            self.node1,
            state4distribution=ks.b00,
            ent_dist_rate=182,
        )
        # establishing classical connection
        create_classical_fibre_link(
            self.network, self.node0, self.node1, length=2e-3, label="extra_classical"
        )
        self.node0_superprotocol = _DummySuperprotocol(
            name="node0superprotocol",
            node=self.node0,
            role=None,
            other_node_name="node1",
            comm_qubit_indices=[1],
            ready4ent=None,
        )
        self.node1_superprotocol = _DummySuperprotocol(
            name="node1superprotocol",
            node=self.node1,
            role=None,
            other_node_name="node0",
            comm_qubit_indices=[1],
            ready4ent=None,
        )
        self.node0_protocol = AbstractCentralSourceEntangleProtocol(node=self.node0)
        self.node1_protocol = AbstractCentralSourceEntangleProtocol(node=self.node1)
        # note in actual implementations, the following two lines would be done
        # inside higher-level protocols
        self.node0_protocol.superprotocol = self.node0_superprotocol
        self.node1_protocol.superprotocol = self.node1_superprotocol
        self.sim_runtime = 1e9

    def test_can_distribute_pair_of_entangled_qubits_with_node0_as_client(self):
        self.node0_superprotocol.role = "client"
        self.node0_superprotocol.ready4ent = True
        self.node1_superprotocol.role = "server"
        self.node1_superprotocol.ready4ent = True
        self.node0_protocol.start()
        self.node1_protocol.start()
        self.node0_superprotocol.start()
        self.node1_superprotocol.start()
        ns.sim_run(self.sim_runtime)
        (qubit_node0,) = self.node0.qmemory.pop(1)
        (qubit_node1,) = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_distribute_pair_of_entangled_qubits_with_node1_as_client(self):
        self.node1_superprotocol.role = "client"
        self.node1_superprotocol.ready4ent = True
        self.node0_superprotocol.role = "server"
        self.node0_superprotocol.ready4ent = True
        self.node0_protocol.start()
        self.node1_protocol.start()
        self.node0_superprotocol.start()
        self.node1_superprotocol.start()
        ns.sim_run(self.sim_runtime)
        (qubit_node0,) = self.node0.qmemory.pop(1)
        (qubit_node1,) = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_access_deterministic_property(self):
        with self.subTest(msg="deterministic property incorrect for node0"):
            self.assertEqual(self.node0_protocol.deterministic, True)
        with self.subTest(msg="deterministic property incorrect for node1"):
            self.assertEqual(self.node1_protocol.deterministic, True)

    def test_deterministic_property_is_read_only(self):
        def _write_deterministic_property(protocol):
            protocol.deterministic = False

        with self.subTest(msg="deterministic property writeable for node0"):
            self.assertRaises(
                TypeError, _write_deterministic_property, self.node0_protocol
            )
        with self.subTest(msg="deterministic property writeabel for node1"):
            self.assertRaises(
                TypeError, _write_deterministic_property, self.node1_protocol
            )


class TestMiddleHeraldedConnectionAndMidpointHeraldingProtocol(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        self.node0 = Node(
            "node0",
            qmemory=QPU(
                "qpu_node0",
                num_positions=5,
                num_comm_qubits=2,
                fallback_to_nonphysical=True,
            ),
        )
        self.node1 = Node(
            "node1",
            qmemory=QPU(
                "qpu_node1",
                num_positions=5,
                num_comm_qubits=2,
                fallback_to_nonphysical=True,
            ),
        )
        self.network = Network("network", nodes=[self.node0, self.node1])
        # The connection created by the following has no noise by default.
        create_midpoint_heralded_entangling_link(self.network, self.node0, self.node1)
        # establishing classical connections
        create_classical_fibre_link(
            self.network, self.node0, self.node1, length=2e-3, label="classical"
        )
        create_classical_fibre_link(
            self.network, self.node0, self.node1, length=2e-3, label="extra_classical"
        )
        self.node0_superprotocol = _DummySuperprotocol(
            name="node0superprotocol",
            node=self.node0,
            role=None,
            other_node_name="node1",
            comm_qubit_indices=[1],
            ready4ent=None,
        )
        self.node1_superprotocol = _DummySuperprotocol(
            name="node1superprotocol",
            node=self.node1,
            role=None,
            other_node_name="node0",
            comm_qubit_indices=[1],
            ready4ent=None,
        )
        max_num_ent_attempts = 100
        self.node0_protocol = MidpointHeraldingProtocol(
            node=self.node0, max_num_ent_attempts=max_num_ent_attempts
        )
        self.node1_protocol = MidpointHeraldingProtocol(
            node=self.node1, max_num_ent_attempts=max_num_ent_attempts
        )
        # note in actual implementations, the following two lines would be done
        # inside higher-level protocols
        self.node0_protocol.superprotocol = self.node0_superprotocol
        self.node1_protocol.superprotocol = self.node1_superprotocol
        self.sim_runtime = 100

    def test_can_access_deterministic_property(self):
        with self.subTest(msg="deterministic property incorrect for node0"):
            self.assertEqual(self.node0_protocol.deterministic, False)
        with self.subTest(msg="deterministic property incorrect for node1"):
            self.assertEqual(self.node1_protocol.deterministic, False)

    def test_deterministic_property_is_read_only(self):
        def _write_deterministic_property(protocol):
            protocol.deterministic = True

        with self.subTest(msg="deterministic property writeable for node0"):
            self.assertRaises(
                TypeError, _write_deterministic_property, self.node0_protocol
            )
        with self.subTest(msg="deterministic property writeabel for node1"):
            self.assertRaises(
                TypeError, _write_deterministic_property, self.node1_protocol
            )

    def test_can_distribute_pair_of_entangled_qubits_with_node0_as_client(self):
        self.node0_superprotocol.role = "client"
        self.node0_superprotocol.ready4ent = True
        self.node1_superprotocol.role = "server"
        self.node1_superprotocol.ready4ent = True
        self.node0_protocol.start()
        self.node1_protocol.start()
        self.node0_superprotocol.start()
        self.node1_superprotocol.start()
        ns.sim_run(self.sim_runtime)
        (qubit_node0,) = self.node0.qmemory.pop(1)
        (qubit_node1,) = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_distribute_pair_of_entangled_qubits_with_node1_as_client(self):
        self.node0_superprotocol.role = "server"
        self.node0_superprotocol.ready4ent = True
        self.node1_superprotocol.role = "client"
        self.node1_superprotocol.ready4ent = True
        self.node0_protocol.start()
        self.node1_protocol.start()
        self.node0_superprotocol.start()
        self.node1_superprotocol.start()
        ns.sim_run(self.sim_runtime)
        (qubit_node0,) = self.node0.qmemory.pop(1)
        (qubit_node1,) = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)


if __name__ == "__main__":
    unittest.main()
