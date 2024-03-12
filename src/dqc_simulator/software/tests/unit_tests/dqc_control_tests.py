# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 15:15:00 2023

@author: kenny
"""

import functools as ft
import unittest

import netsquid as ns
import pydynaa
import numpy as np
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
from netsquid.components import instructions as instr
from netsquid.nodes import Node, Network
from netsquid.qubits.qformalism import set_qstate_formalism
from netsquid.qubits.qformalism import QFormalism
from netsquid.protocols import Protocol
from netsquid.protocols.protocol import Signals

from dqc_simulator.hardware.dqc_creation import (link_2_nodes, 
                                                 create_dqc_network)
from dqc_simulator.hardware.quantum_processors import (
                                                create_processor,
                                                INSTR_ARB_GEN)
from dqc_simulator.qlib.states import werner_state
from dqc_simulator.software.compilers import sort_greedily_by_node_and_time
from dqc_simulator.software.dqc_control import (
                          HandleCommBlockForOneNodeProtocol, 
                          EntangleLinkedNodesProtocol,
                          dqcMasterProtocol)




#integrated network tests
#for debugging
from netsquid.util import simlog
import logging
loggers = simlog.get_loggers()
# =============================================================================
# loggers['netsquid'].setLevel(logging.DEBUG)
# =============================================================================
loggers['netsquid'].setLevel(logging.WARNING)


class Test_entangling(unittest.TestCase):
    """ 
    Testing EntangleLinkedNodesProtocol does what it should. Note it is sensible to 
    also test the link_2_nodes function separately
    """
    #defining code to be used at the start of all subsequent test functions
    #in the class. Anything defined this way must be prepended with self. in 
    #the functions using this because the setUp defines them as an object of 
    #function
    def setUp(self):
        #setting up sim and network
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        self.Werner_State = werner_state(0.5)
# =============================================================================
#         self.F = 0.5
#         self.Werner_State = (self.F * np.outer(ks.b00, np.transpose(ks.b00)) + 
#                         (1-self.F)/3 * np.outer(ks.b01, np.transpose(ks.b01)) + 
#                         (1-self.F)/3 * np.outer(ks.b10, np.transpose(ks.b10)) + 
#                         (1-self.F)/3 * np.outer(ks.b11, np.transpose(ks.b11)))
# =============================================================================
        #setting up network with no noise
        self.network = Network("test_network")
        alpha = 1/np.sqrt(3)
        beta = np.sqrt(2/3)
        depolar_rate = 0
        dephase_rate = 0
        self.node_a = Node("Alice", qmemory=create_processor(alpha, beta, depolar_rate, dephase_rate))
        self.node_b = Node("Bob", qmemory=create_processor(alpha, beta, depolar_rate, dephase_rate))
        self.network.add_nodes([self.node_a, self.node_b])
        link_2_nodes(self.network, self.node_a,
                     self.node_b, state4distribution=self.Werner_State, 
                    node_distance=4e-3,
                    create_classical_2way_link=True,
                    create_entangling_link=True)
        self.cycle_runtime = 200 #ns
        self.charlie = self.network.get_node("Charlie_Alice<->Bob")
        self.protocol = EntangleLinkedNodesProtocol(self.charlie)
        
    def test_alice_can_request_0_0_entangling_gate(self):
        self.protocol.start()
        self.node_a.ports["request_entanglement_Alice<->Bob"].tx_output((0, 0))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)

    def test_alice_can_request_1_0_entangling_gate(self):
        self.protocol.start()
        self.node_a.ports["request_entanglement_Alice<->Bob"].tx_output((1, 0))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
    def test_alice_can_request_0_1_entangling_gate(self):
        self.protocol.start()
        self.node_a.ports["request_entanglement_Alice<->Bob"].tx_output((0, 1))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([1])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_can_request_1_1_entangling_gate(self):
        self.protocol.start()
        self.node_a.ports["request_entanglement_Alice<->Bob"].tx_output((1, 1))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([1])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_bob_can_request_0_0_entangling_gate(self):
        self.protocol.start()
        self.node_b.ports["request_entanglement_Alice<->Bob"].tx_output((0, 0))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)

    def test_bob_can_request_1_0_entangling_gate(self):
        self.protocol.start()
        self.node_b.ports["request_entanglement_Alice<->Bob"].tx_output((1, 0))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_bob_can_request_0_1_entangling_gate(self):
        self.protocol.start()
        self.node_b.ports["request_entanglement_Alice<->Bob"].tx_output((0, 1))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([1])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_bob_can_request_1_1_entangling_gate(self):
        self.protocol.start()
        self.node_b.ports["request_entanglement_Alice<->Bob"].tx_output((1, 1))
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([1])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_and_bob_can_each_request_their_own_qubit_0_0(self):
        self.protocol.start()
        port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
        port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
        port_alice.tx_output(0)
        port_bob.tx_output(0)
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_and_bob_can_each_request_their_own_qubit_1_0(self):
        self.protocol.start()
        port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
        port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
        port_alice.tx_output(1)
        port_bob.tx_output(0)
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_and_bob_can_each_request_their_own_qubit_0_1(self):
        self.protocol.start()
        port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
        port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
        port_alice.tx_output(0)
        port_bob.tx_output(1)
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([0])
        qubit_b, = self.node_b.qmemory.pop([1])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_and_bob_can_each_request_their_own_qubit_1_1(self):
        self.protocol.start()
        port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
        port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
        port_alice.tx_output(1)
        port_bob.tx_output(0)
        ns.sim_run(self.cycle_runtime)
        qubit_a, = self.node_a.qmemory.pop([1])
        qubit_b, = self.node_b.qmemory.pop([0])
        fidelity = qapi.fidelity([qubit_a, qubit_b], 
                                 werner_state(0.5), squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_alice_alone_cannot_trigger_entanglement(self):
        self.protocol.start()
        port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
        port_alice.tx_output(0)
        ns.sim_run(self.cycle_runtime)
        alice_qubits = self.node_a.qmemory.pop([0, 1, 2, 3, 4, 5, 6])
        bob_qubits = self.node_b.qmemory.pop([0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(alice_qubits, [None]*7)
        self.assertEqual(bob_qubits, [None]*7)
        
    def test_bob_alone_cannot_trigger_entanglement(self):
        self.protocol.start()
        port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
        port_bob.tx_output(0)
        ns.sim_run(self.cycle_runtime)
        alice_qubits = self.node_a.qmemory.pop([0, 1, 2, 3, 4, 5, 6])
        bob_qubits = self.node_b.qmemory.pop([0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(alice_qubits, [None]*7)
        self.assertEqual(bob_qubits, [None]*7)
        
# =============================================================================
#     def test_odd_num_entanglement_request_does_not_overtrigger(self):
#         self.protocol.start()
#         port_alice = self.node_a.ports["request_entanglement_Alice<->Bob"]
#         port_bob = self.node_b.ports["request_entanglement_Alice<->Bob"]
#         
# =============================================================================
        

class IntegrationTestEntangleLinkdeNodesProtocolAndcreate_dqc_network(unittest.TestCase):
    def test_can_distribute_arbitrary_state(self):
        ns.sim_reset()
        network = create_dqc_network(state4distribution=werner_state(0.5),
                                     node_list=None, num_nodes=2,
                                     node_distance=4e-3,
                                     quantum_topology = None, 
                                     classical_topology = None,
                                     create_classical_2way_link=True,
                                     create_entangling_link=True,
                                     nodes_have_ebit_ready=False,
                                     node_comm_qubits_free=[0, 1],
                                     node_comm_qubit_positions=[0, 1],
                                     name="linear network")
        alice = network.get_node("node_0")
        bob = network.get_node("node_1")
        port_alice = alice.ports["request_entanglement_node_0<->node_1"]
        port_bob = bob.ports["request_entanglement_node_0<->node_1"]
        charlie = network.get_node("Charlie_node_0<->node_1")
        entangling_protocol = EntangleLinkedNodesProtocol(charlie)
        entangling_protocol.start()
        port_alice.tx_output(0)
        port_bob.tx_output(0)
        ns.sim_run(1000)
        alice_qubit, = alice.qmemory.pop(0)
        bob_qubit, = bob.qmemory.pop(0)
        fidelity = qapi.fidelity([alice_qubit, bob_qubit],
                                 werner_state(0.5))
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_can_distribute_arbitrary_state_by_specifiying_topology(self):
        #TO DO: identify why this occassionally fails and fix
        ns.sim_reset()
        quantum_topology = [(0,1)]
        network = create_dqc_network(state4distribution=werner_state(0.5),
                                     node_list=None, num_nodes=2,
                                     node_distance=4e-3,
                                     quantum_topology = quantum_topology, 
                                     classical_topology = None,
                                     create_classical_2way_link=False,
                                     create_entangling_link=False,
                                     nodes_have_ebit_ready=False,
                                     node_comm_qubits_free=[0, 1],
                                     node_comm_qubit_positions=[0, 1],
                                     name="linear network")
        alice = network.get_node("node_0")
        bob = network.get_node("node_1")
        port_alice = alice.ports["request_entanglement_node_0<->node_1"]
        port_bob = bob.ports["request_entanglement_node_0<->node_1"]
        charlie = network.get_node("Charlie_node_0<->node_1")
        entangling_protocol = EntangleLinkedNodesProtocol(charlie)
        entangling_protocol.start()
        port_alice.tx_output(0)
        port_bob.tx_output(0)
        ns.sim_run(1000)
        alice_qubit, = alice.qmemory.pop(0)
        bob_qubit, = bob.qmemory.pop(0)
        fidelity = qapi.fidelity([alice_qubit, bob_qubit],
                                 werner_state(0.5))
        self.assertAlmostEqual(fidelity, 1.000, 3)
        

class TestHandleCommBlockForOneNodeProtocol(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        self.cycle_runtime = 200

    def test_can_do_cat_comm_remote_cnot_without_disentanglement(self):
        #making 2 node linear network:
        alpha = 1/np.sqrt(2)
        beta = 1j/np.sqrt(2)
        network = create_dqc_network(
                           state4distribution=ks.b00,
                           node_list=None,num_nodes=2,
                           quantum_topology = None, 
                           classical_topology = None,
                           create_classical_2way_link=True,
                           create_entangling_link=True, name="linear network")
        node_a = network.get_node("node_0")
        node_b = network.get_node("node_1")
# =============================================================================
#         print(f"node_a has {node_a.comm_qubits_free} comm_qubits_free")
#         print(f"node_b has {node_b.comm_qubits_free} comm_qubits_free")
#         print(f"node_a has ebit_ready attribute with value {node_a.ebit_ready}")
#         print(f"node_b has ebit_ready attribute with value {node_b.ebit_ready}")
#         print(f"node_a has {node_a.comm_qubit_positions} comm-qubit positions")
#         print(f"node_b has {node_b.comm_qubit_positions} comm-qubit positions")
# =============================================================================
        node_a.ebit_ready=False
        node_b.ebit_ready=False
        node_a.comm_qubits_free=[0, 1]
        node_b.comm_qubits_free = [0, 1]
        node_a.comm_qubit_positions = [0, 1]
        node_b.comm_qubit_positions = [0, 1]
        charlie = network.get_node("Charlie_node_0<->node_1")
        #first three gates in what follows dictate state to be teleported
        gate_tuples4node_a = [(instr.INSTR_INIT, 2), (instr.INSTR_H, 2),
                              (instr.INSTR_S, 2),
                              (2, node_b.name, "cat", "entangle")]  #(data_qubit_index, other_node, scheme, role)
        gate_tuples4node_b = [(instr.INSTR_INIT, 2), 
                              (2, node_a.name, "cat", "correct"),
                              (instr.INSTR_CNOT, 0, 2)]     
        node_a_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_a, 
                                                     node=node_a)
        node_b_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_b, 
                                                     node=node_b)
        charlie_protocol = EntangleLinkedNodesProtocol(charlie)
        charlie_protocol.start()
        node_a_protocol.start()
        node_b_protocol.start()
        ns.sim_run(200)
        alice_data_qubit, = node_a.qmemory.pop(2) 
        bob_comm_qubit, = node_b.qmemory.pop(0)
        bob_data_qubit, = node_b.qmemory.pop(2)
        desired_state_ket = (alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0))
                            + beta * np.kron(ks.s1, np.kron(ks.s1, ks.s1)))
        fidelity = qapi.fidelity([alice_data_qubit, bob_comm_qubit, 
                                  bob_data_qubit], 
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_can_do_cat_remote_cnot(self):
        #making 2 node linear network:
        alpha = 1/np.sqrt(2)
        beta = 1j/np.sqrt(2)
        network = create_dqc_network(state4distribution=ks.b00,
                                     node_list=None,num_nodes=2,
                           node_distance=4e-3, quantum_topology = None, 
                           classical_topology = None,
                           create_classical_2way_link=True,
                           create_entangling_link=True, name="linear network")
        node_a = network.get_node("node_0")
        node_b = network.get_node("node_1")
        charlie = network.get_node("Charlie_node_0<->node_1")
        node_a.ebit_ready=False
        node_b.ebit_ready=False
        node_a.comm_qubits_free=[0, 1]
        node_b.comm_qubits_free = [0, 1]
        node_a.comm_qubit_positions = [0, 1]
        node_b.comm_qubit_positions = [0, 1]
        #first three gates in what follows dictate state to be teleported
        gate_tuples4node_a = [(instr.INSTR_INIT, 2), (instr.INSTR_H, 2),
                              (instr.INSTR_S, 2),
                              (2, node_b.name, "cat", "entangle"),
                              (2, node_b.name, "cat", "disentangle_end")]
        gate_tuples4node_b = [(instr.INSTR_INIT, 2), 
                              (2, node_a.name, "cat", "correct"),
                              (instr.INSTR_CNOT, 0, 2),
                              (node_a.name, "cat", "disentangle_start")]
        node_a_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_a, 
                                                     node=node_a)
        node_b_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_b, 
                                                     node=node_b)
        charlie_protocol = EntangleLinkedNodesProtocol(charlie)
        charlie_protocol.start()
        node_a_protocol.start()
        node_b_protocol.start()
        ns.sim_run(200)
# =============================================================================
#         print(f"On node_a {node_a.qmemory.peek([0, 1, 2])}")
#         print(f"On node_b {node_b.qmemory.peek([0, 1, 2])}")
# =============================================================================
        alice_data_qubit, = node_a.qmemory.pop(2) 
        #retrieving data qubit on Bob's processor
        bob_data_qubit, = node_b.qmemory.pop(2)
        desired_state_ket = (alpha * np.kron(ks.s0, ks.s0)
                            + beta * np.kron(ks.s1, ks.s1))
        fidelity = qapi.fidelity([alice_data_qubit, bob_data_qubit], 
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def tests_can_do_larger_remote_gate(self):
        #making 2 node linear network:
        alpha = 1/np.sqrt(2)
        beta = 1j/np.sqrt(2)
        network = create_dqc_network(state4distribution=ks.b00,
                                     node_list=None,num_nodes=2,
                           node_distance=4e-3, quantum_topology = None, 
                           classical_topology = None,
                           create_classical_2way_link=True,
                           create_entangling_link=True, name="linear network")
        node_a = network.get_node("node_0")
        node_b = network.get_node("node_1")
        node_a.ebit_ready=False
        node_b.ebit_ready=False
        node_a.comm_qubits_free=[0, 1]
        node_b.comm_qubits_free = [0, 1]
        node_a.comm_qubit_positions = [0, 1]
        node_b.comm_qubit_positions = [0, 1]
        charlie = network.get_node("Charlie_node_0<->node_1")
        #first three gates in what follows dictate state to be teleported
        gate_tuples4node_a = [(instr.INSTR_INIT, 2), (instr.INSTR_H, 2),
                              (instr.INSTR_S, 2),
                              (2, node_b.name, "cat", "entangle"),
                              (2, node_b.name, "cat", "disentangle_end")]
        gate_tuples4node_b = [(instr.INSTR_INIT, 2), (instr.INSTR_INIT, 3),
                              (instr.INSTR_INIT, 4),
                              (2, node_a.name, "cat", "correct"),
                              (instr.INSTR_CNOT, 0, 2), 
                              (instr.INSTR_CNOT, 2, 3),
                              (instr.INSTR_CNOT, 3, 4),
                              (node_a.name, "cat", "disentangle_start")]
        node_a_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_a, 
                                                     node=node_a)
        node_b_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_b, 
                                                     node=node_b)
        charlie_protocol = EntangleLinkedNodesProtocol(charlie)
        charlie_protocol.start()
        node_a_protocol.start()
        node_b_protocol.start()
        ns.sim_run(200)
# =============================================================================
#         print(f"On node_a {node_a.qmemory.peek([0, 1, 2])}")
#         print(f"On node_b {node_b.qmemory.peek([0, 1, 2])}")
# =============================================================================
        alice_data_qubit = node_a.qmemory.pop(2) 
        #retrieving data qubit on Bob's processor
        bob_data_qubits = node_b.qmemory.pop([2, 3, 4])
        qubits = alice_data_qubit + bob_data_qubits
        lst0 = [ks.s0] * 4
        lst1 = [ks.s1] * 4
        desired_state_ket = (alpha * ft.reduce(np.kron, lst0)
                            + beta * ft.reduce(np.kron, lst1))
        fidelity = qapi.fidelity(qubits, 
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_can_do_one_tp_remote_cnot_with_adjacent_node(self):
        #making 2 node linear network:
        alpha = 1/np.sqrt(2)
        beta = 1j/np.sqrt(2)
        network = create_dqc_network(state4distribution=ks.b00,
                                          node_list=None,num_nodes=2,
                           node_distance=4e-3, quantum_topology = None, 
                           classical_topology = None,
                           create_classical_2way_link=True,
                           create_entangling_link=True, name="linear network")
        node_a = network.get_node("node_0")
        node_b = network.get_node("node_1")
        node_a.ebit_ready=False
        node_b.ebit_ready=False
        node_a.comm_qubits_free=[0, 1]
        node_b.comm_qubits_free = [0, 1]
        node_a.comm_qubit_positions = [0, 1]
        node_b.comm_qubit_positions = [0, 1]
        charlie = network.get_node("Charlie_node_0<->node_1")
        #first three gates in what follows dictate state to be teleported
        gate_tuples4node_a = [(instr.INSTR_INIT, 2), (instr.INSTR_H, 2),
                              (instr.INSTR_S, 2),
                              (2, node_b.name, "tp", "bsm")]     #(data_qubit_index, other_node, scheme, role)
        gate_tuples4node_b = [(instr.INSTR_INIT, 2), 
                              (2, node_a.name, "tp", "correct"),
                              (instr.INSTR_CNOT, 0, 2)]     
        node_a_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_a, 
                                                     node=node_a)
        node_b_protocol = HandleCommBlockForOneNodeProtocol(gate_tuples4node_b, 
                                                     node=node_b)
        charlie_protocol = EntangleLinkedNodesProtocol(charlie)
        charlie_protocol.start()
        node_a_protocol.start()
        node_b_protocol.start()
        ns.sim_run(200)
# =============================================================================
#         print(f"On node_a {node_a.qmemory.peek([0, 1, 2])}")
#         print(f"On node_b {node_b.qmemory.peek([0, 1, 2])}")
# =============================================================================
        teleported_qubit, = node_b.qmemory.pop(0) 
        #retrieving data qubit on Bob's processor
        bob_local_qubit, = node_b.qmemory.pop(2) 
        desired_state_ket = (alpha * np.kron(ks.s0, ks.s0)
                            + beta * np.kron(ks.s1, ks.s1))
# =============================================================================
#         print(ns.qubits.reduced_dm([teleported_qubit, bob_local_qubit]))
#         print(desired_state_ket)
# =============================================================================
        fidelity = qapi.fidelity([teleported_qubit, bob_local_qubit], 
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        



class TestDQCmasterProtocolWithGreedyCompiler(unittest.TestCase):
    """Integration tests of dqcMasterProtocol with the compiler set to 
    sort_greedily_by_node_and_time
    """
    def setUp(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        #making 3 node linear network:
        self.alpha = 1/np.sqrt(2)
        self.beta = 1j/np.sqrt(2)
        self.network = create_dqc_network(state4distribution=ks.b00,
                                          node_list=None, num_nodes=3,
                           node_distance=4e-3, quantum_topology = None, 
                           classical_topology = None,
                           create_classical_2way_link=True,
                           create_entangling_link=True,
                           nodes_have_ebit_ready=False,
                           node_comm_qubits_free=[0, 1],
                           node_comm_qubit_positions=[0,1],
                           name="linear network")
        #if node_comm_qubits_free is not explicitly specified then the tests don't
        #work. I HAVEN'T GOT THE VAGUEST IDEA WHY
        self.node_a = self.network.get_node("node_0")
        self.node_b = self.network.get_node("node_1")
        self.node_c = self.network.get_node("node_2")

        for node in [self.node_a, self.node_b, self.node_c]:
            node.ebit_ready = False
            node.comm_qubits_free = [0, 1]
            node.comm_qubit_positions = [0, 1]
#UNCOMMENT ABOVE for loop TO GET TESTS TO WORK
# =============================================================================
#         self.charlie_ab = self.network.get_node("Charlie_node_0<->node_1")
#         self.charlie_bc = self.network.get_node("Charlie_node_1<->node_2")
# # =============================================================================
# #         for node in [self.node_a, self.node_b, self.node_c]:
# #             print(f"for {node.name}, ebit_ready is {node.ebit_ready}")
# #             print(f"for {node.name}, comm_qubits free is {node.comm_qubits_free}")
# #             print(f"for {node.name}, comm_qubit_positions is {node.comm_qubit_positions}")
# # =============================================================================
#         self.charlie_ab_protocol = EntangleLinkedNodesProtocol(self.charlie_ab)
#         self.charlie_bc_protocol = EntangleLinkedNodesProtocol(self.charlie_bc)
# =============================================================================
        self.cycle_runtime = 400
        #if I don't manually set the attributes 
        
    def test_can_do_one_remote_cnot_with_cat_comm(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"), 
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "cat")]
# =============================================================================
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
# =============================================================================
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        node_a = self.network.get_node("node_0")
        node_b = self.network.get_node("node_1")
        alice_data_qubit, = node_a.qmemory.pop(2) 
        #retrieving data qubit on Bob's processor
        bob_data_qubit, = node_b.qmemory.pop(2)
# =============================================================================
#         print(f"the state you have is {ns.qubits.reduced_dm([alice_data_qubit, bob_data_qubit])}")
# =============================================================================
        desired_state_ket = (self.alpha * np.kron(ks.s0, ks.s0)
                            + self.beta * np.kron(ks.s1, ks.s1))
# =============================================================================
#         print(f"desired state is {ns.qubits.ketutil.ket2dm(desired_state_ket)}")
# =============================================================================
        fidelity = qapi.fidelity([alice_data_qubit, bob_data_qubit], 
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
    
    def test_can_do_two_remote_cnots_with_cat_comm(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"), 
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_INIT, 2, "node_2"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "cat"),
                       (instr.INSTR_CNOT, 2, "node_1", 2,
                        "node_2", "cat")]
        node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        node_a = self.network.get_node("node_0")
        node_b = self.network.get_node("node_1")
        node_c = self.network.get_node("node_2")
        node_a_data_qubit, = node_a.qmemory.pop(2)
        node_b_data_qubit, = node_b.qmemory.pop(2)
        node_c_data_qubit, = node_c.qmemory.pop(2)
        desired_state_ket = (self.alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0))
                             + self.beta * np.kron(ks.s1, np.kron(ks.s1, ks.s1)))
        fidelity = qapi.fidelity([node_a_data_qubit, node_b_data_qubit, 
                                  node_c_data_qubit],
                                 desired_state_ket, squared=False)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_can_do_tp_remote_cnot_then_teleport_back(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"),
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "tp_risky"),
                       ([], -1, "node_1", -1,
                        "node_0", "tp_risky")]
# =============================================================================
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
# =============================================================================
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
# =============================================================================
#         print(f"on Alice {self.node_a.qmemory.peek([0, 1, 2])}")
#         print(f"on Bob {self.node_b.qmemory.peek([0, 1, 2])}")
# =============================================================================
        node_a = self.network.get_node("node_0")
        node_b = self.network.get_node("node_1")
        alice_comm_qubit, = node_a.qmemory.pop(0)
        logical_target_qubit, = node_b.qmemory.pop(2)
        desired_state_ket = (self.alpha * np.kron(ks.s0, ks.s0)
                            + self.beta * np.kron(ks.s1, ks.s1))
# =============================================================================
#         print(f"desired state is {ns.qubits.ketutil.ket2dm(desired_state_ket)}")
#         print(f"the actual state is {ns.qubits.reduced_dm([alice_comm_qubit, logical_target_qubit])}")
# =============================================================================
        fidelity = qapi.fidelity([alice_comm_qubit, logical_target_qubit],
                                 desired_state_ket)
        self.assertEqual(round(fidelity, 3), 1.000)
        #NOTE at the moment you are teleporting back to the comm-qubit not the 
        #original but this could be solved with a simple swap gate followed by
        #reinitialising the comm-qubit or something similar
        
    def test_can_do_two_remote_cnots_with_tp_comm(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"),
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_INIT, 2, "node_2"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "tp_risky"),
                       ([], -1 , "node_1", -1, "node_0", "tp_risky"),
                       (instr.INSTR_CNOT, 2, "node_1", 2,
                        "node_2", "tp_risky"),
                       ([], -1, "node_2", -1, "node_1", "tp_risky")]
        node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
# =============================================================================
#         self.charlie_ab_protocol.start()
#         self.charlie_bc_protocol.start()
# =============================================================================
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        desired_state_ket = (self.alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0))
                            + self.beta * np.kron(ks.s1, np.kron(ks.s1, ks.s1)))
        node_a = self.network.get_node("node_0")
        node_b = self.network.get_node("node_1")
        node_c = self.network.get_node("node_2")
        node_a_comm_qubit, = node_a.qmemory.pop(0)
        node_b_comm_qubit, = node_b.qmemory.pop(0)
        node_c_data_qubit, = node_c.qmemory.pop(2)
        fidelity = qapi.fidelity([node_a_comm_qubit, node_b_comm_qubit,
                                  node_c_data_qubit],
                                 desired_state_ket)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_can_do_two_logical_cnots_over_different_nodes_manually(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"),
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_INIT, 2, "node_2"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "tp_risky"),
                       ([], -1 , "node_1", 2, "node_0", "free_comm_qubit_with_tele"),
                       (instr.INSTR_CNOT, 2, "node_1", 2,
                        "node_2", "tp_risky"),
                       ([],-1, "node_2", 2, "node_1", "free_comm_qubit_with_tele")]
# =============================================================================
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
# =============================================================================
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
# =============================================================================
#         self.charlie_ab_protocol.start()
#         self.charlie_bc_protocol.start()
# =============================================================================
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        desired_state_ket = (self.alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0))
                            + self.beta * np.kron(ks.s1, np.kron(ks.s1, ks.s1)))
        node_a_data_qubit, = self.node_a.qmemory.pop(2)
        node_b_data_qubit, = self.node_b.qmemory.pop(2)
        node_c_data_qubit, = self.node_c.qmemory.pop(2)
        fidelity = qapi.fidelity([node_a_data_qubit, node_b_data_qubit,
                                  node_c_data_qubit],
                                 desired_state_ket)
        self.assertEqual(round(fidelity, 3), 1.000)

    def test_tp_safe_costs_no_comm_qubits_overall(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"),
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "tp_safe")]
# =============================================================================
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
# =============================================================================
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
# =============================================================================
#         print(f"on Alice {self.node_a.qmemory.peek([0, 1, 2])}")
#         print(f"on Bob {self.node_b.qmemory.peek([0, 1, 2])}")
# =============================================================================
        node_a = self.network.get_node("node_0")
        node_b = self.network.get_node("node_1")
        alice_comm_qubit, = node_a.qmemory.pop(0)
        comm_qubits_free_at_end = (len(node_a.comm_qubits_free) + 
                                len(node_b.comm_qubits_free))
        comm_qubits_free_at_beginning = (len(node_a.comm_qubit_positions)
                                         + len(node_b.comm_qubit_positions))
        net_comm_qubits_used = (comm_qubits_free_at_end - 
                                comm_qubits_free_at_beginning)
        #NOTE at the moment you are teleporting back to the comm-qubit not the 
        #original but this could be solved with a simple swap gate followed by
        #reinitialising the comm-qubit or something similar
        self.assertAlmostEqual(net_comm_qubits_used, 0)

    def test_can_do_two_logical_cnots_over_different_nodes_automatically(self):
        gate_tuples = [(instr.INSTR_INIT, 2, "node_0"),
                       (instr.INSTR_INIT, 2, "node_1"),
                       (instr.INSTR_INIT, 2, "node_2"),
                       (instr.INSTR_H, 2, "node_0"), 
                       (instr.INSTR_S, 2, "node_0"),
                       (instr.INSTR_CNOT, 2, "node_0", 2, 
                        "node_1", "tp_safe"),
                       (instr.INSTR_CNOT, 2, "node_1", 2,
                        "node_2", "tp_safe")]
# =============================================================================
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
# =============================================================================
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
# =============================================================================
#         self.charlie_ab_protocol.start()
#         self.charlie_bc_protocol.start()
# =============================================================================
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        desired_state_ket = (self.alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0))
                            + self.beta * np.kron(ks.s1, np.kron(ks.s1, ks.s1)))
        node_a_data_qubit, = self.node_a.qmemory.pop(2)
        node_b_data_qubit, = self.node_b.qmemory.pop(2)
        node_c_data_qubit, = self.node_c.qmemory.pop(2)
        fidelity = qapi.fidelity([node_a_data_qubit, node_b_data_qubit,
                                  node_c_data_qubit],
                                 desired_state_ket)
        self.assertEqual(round(fidelity, 3), 1.000)
        
    def test_can_run_many_single_qubit_gates_with_one_command(self):
        gate_tuples = [(instr.INSTR_INIT, [2, 3, 4, 5], "node_0")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network,
                          compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        qubits = self.node_a.qmemory.pop([2, 3, 4, 5])
        qubit_array = np.asarray(qubits, dtype=object)
        mask = (qubit_array == None)
        self.assertEqual(list(mask), [False] * 4)
        
    #TO DO: test new scheme: tp_block 
    
    #TO DO: add test that you can perform a fused communication block (ie, 
    #several gates using one call of Cat-comm or two teleportations)
    
        
#right now remote gate operations have to be done at a different time from everything else
#this could potentially be changed by accessing the measurement results later but you would
#need to ensure this happened before the next remote gate

#NOTE: 
#Local protocols, such as node protocols can signal to a normal Protocol but 
#not a LocalProtocol. Failure to distinguish between these causes errors
#Also, you need to use & (AND) rather than the lower case and. Similarly, you 
#must use | (OR) rather than the the lower case or.

#running all class derived from the unittest.TestCase parent class:
if __name__ == '__main__':
    unittest.main()
        
