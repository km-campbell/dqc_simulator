# -*- coding: utf-8 -*-
"""
Unit tests for dqc_creation.py
"""

import unittest, warnings
import numpy as np

import netsquid as ns
from netsquid.components import instructions as instr
from netsquid.components import (QuantumMemory, QuantumProcessor, 
                                 PhysicalInstruction)
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.nodes import Node, Network, DirectConnection
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
from netsquid.qubits.qformalism import set_qstate_formalism, QFormalism

from dqc_simulator.hardware.connections import ( 
    BlackBoxEntanglingQsourceConnection)
from dqc_simulator.hardware.noise_models import ( 
                                                 AnalyticalDepolarisationModel)
from dqc_simulator.hardware.quantum_processors import create_processor
from dqc_simulator.hardware.dqc_creation import (link_2_qpus,
                                                 create_dqc_network)
from dqc_simulator.qlib.gates import (INSTR_ARB_GEN, INSTR_T_DAGGER, 
                                       INSTR_CH, INSTR_CT)
from dqc_simulator.qlib.states import werner_state

#integrated network tests
# =============================================================================
# #for debugging
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# 
# # =============================================================================
# # # #resetting to default after debugging
# # loggers = simlog.get_loggers()
# # loggers['netsquid'].setLevel(logging.WARNING)
# # =============================================================================
# =============================================================================


class Test_link_2_qpus(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        self.qpu0 = Node("qpu0", 
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.qpu1 = Node("qpu1",
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.qpu0port_name = self.qpu0.connection_port_name(self.qpu1.ID,
                                        label="entangling")
        self.qpu1port_name = self.qpu1.connection_port_name(self.qpu0.ID,
                                        label="entangling")
        self.network = Network("network", nodes=[self.qpu0, self.qpu1])
        self.sim_runtime = 100
        
    def test_can_distribute_pair_of_entangled_qubits_triggered_by_qpu0(self):
        #this test uses the default settings
        link_2_qpus(self.network, self.qpu0, self.qpu1)
        self.qpu0.ports[self.qpu0port_name].tx_output("ENT_REQUEST")
        ns.sim_run(self.sim_runtime)
        qubit_qpu0, = self.qpu0.qmemory.pop(0)
        qubit_qpu1, = self.qpu1.qmemory.pop(0)
        fidelity = qapi.fidelity([qubit_qpu0, qubit_qpu1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)

    def test_can_distribute_pair_of_entangled_qubits_triggered_by_qpu1(self):
        #this test uses the default settings
        link_2_qpus(self.network, self.qpu0, self.qpu1)
        self.qpu1.ports[self.qpu1port_name].tx_output("ENT_REQUEST")
        ns.sim_run(self.sim_runtime)
        qubit_qpu0, = self.qpu0.qmemory.pop(0)
        qubit_qpu1, = self.qpu1.qmemory.pop(0)
        fidelity = qapi.fidelity([qubit_qpu0, qubit_qpu1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)
        
    #the following test previously failed but the error message suggested the
    #output was right. Need to think on this.
    def test_can_create_only_entangling_link(self):
        link_2_qpus(self.network, self.qpu0, self.qpu1, 
                    want_classical_2way_link=False,
                    want_entangling_link=True)
        with self.subTest(msg="wrong number of entangling connections"):
            self.assertEqual(len(self.network.connections), 1)
        with self.subTest(msg="wrong type of connection"):
            self.assertIsInstance(list(self.network.connections.values())[0],
                                  BlackBoxEntanglingQsourceConnection)
            
    def test_can_create_only_classical_link(self):
        link_2_qpus(self.network, self.qpu0, self.qpu1, 
                    want_classical_2way_link=True,
                    want_entangling_link=False)
        with self.subTest(msg="wrong number of entangling connections"):
            self.assertEqual(len(self.network.connections), 1)
        with self.subTest(msg="wrong type of connection"):
            self.assertIsInstance(list(self.network.connections.values())[0],
                                  DirectConnection)
    
    

# =============================================================================
# #I think rx_output is deleted if not immediately used. You can test this with
# #your old network, which you know works.
# class Test_link_2_qpus(unittest.TestCase):
#     """ 
#     Testing that the link_2_qpus functions does what its name suggests
#     """
#     #defining code to be used at the start of all subsequent test functions
#     #in the class. Anything defined this way must be prepended with self. in 
#     #the functions using this because the setUp defines them as an object of 
#     #function
#     def setUp(self):
#         ns.sim_reset()
#         self.F = 0.5
#         self.Werner_State = (self.F * np.outer(ks.b00, np.transpose(ks.b00)) + 
#                         (1-self.F)/3 * np.outer(ks.b01, np.transpose(ks.b01)) + 
#                         (1-self.F)/3 * np.outer(ks.b10, np.transpose(ks.b10)) + 
#                         (1-self.F)/3 * np.outer(ks.b11, np.transpose(ks.b11)))
#         self.alpha = 1/np.sqrt(3)
#         self.beta =np.sqrt(2/3)
#         self.depolar_rate=0
#         self.dephase_rate=0
#         #setting up network with no noise
#         self.network = Network("test_network")
#         self.node_a = Node("Alice", qmemory=create_processor())
#         self.node_b = Node("Bob", qmemory=create_processor(
#             self.alpha, self.beta, self.depolar_rate, self.dephase_rate))
#         self.network.add_nodes([self.node_a, self.node_b])
#     def test_right_num_nodes(self):
#         link_2_qpus(self.network, self.node_a, self.node_b)
#         self.assertEqual(len(self.network.nodes), 3) #Should have Alice, Bob and 
#                                                 #Charlie
#     def test_can_create_only_classical_link(self):
#         link_2_qpus(self.network, self.node_a, self.node_b, 
#                      state4distribution=ks.b00, 
#                      node_distance=4e-3, 
#                      want_classical_2way_link=True,
#                      want_entangling_link=False)
#         self.assertEqual(len(self.network.connections), 1)
#     def test_can_create_only_quantum_link(self):
#         link_2_qpus(self.network, self.node_a, self.node_b, 
#                      state4distribution=ks.b00, 
#                      node_distance=4e-3, 
#                      want_classical_2way_link=False,
#                      want_entangling_link=True)
#         #NOTE: desired result will change from 2 to 1 when code refactored
#         self.assertEqual(len(self.network.connections), 2)
#     def test_can_create_quantum_and_classical_link(self):
#         link_2_qpus(self.network, self.node_a, self.node_b, 
#                      state4distribution=ks.b00, 
#                      node_distance=4e-3, 
#                      want_classical_2way_link=True,
#                      want_entangling_link=True)
#         #NOTE: desired result will change from 3 to 2 when code refactored.
#         self.assertEqual(len(self.network.connections), 3)
#     #TO DO: once code is refactored make some tests more akin to what you have
#     #for connections_tests. As the default behaviour is to use the connection 
#     #(BlackBoxEntanglingQsourceConnection) from there, it some of the tests 
#     #could be the same but with a different set up (due to the fact that some
#     #of the setup is now happening within link_2_nodes)
# =============================================================================
    



#TO DO: update tests below to reflect refactor
# =============================================================================
# class TestCreateDQCNetwork(unittest.TestCase):
#     def setUp(self):
#         ns.sim_reset()
#         set_qstate_formalism(QFormalism.DM)
#     def test_right_num_connections_2_node_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=2,
#                                   node_distance=4e-3,
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=True, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 3)
#     
#     def test_right_num_nodes_2_node_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=2,
#                                   node_distance=4e-3, 
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=True, 
#                                   name="linear network")
#         self.assertEqual(len(network.nodes), 3)
#         
#     def test_right_num_connections_3_node_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=3,
#                                   node_distance=4e-3,
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=True, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 6)
#         
#     def test_right_num_connections_4_node_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=True, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 9)
#     
#     def test_can_create_4_node_classical_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=False, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 3)
# 
#     def test_can_create_4_node_quantum_linear_network(self):
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3,
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=True, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 6)
#     
#     def test_can_manually_create_4_node_network(self):
#         classical_topology = [(0, 1), (1, 2), (2, 3)]
#         quantum_topology = [(0, 1), (1, 2), (2, 3)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 9)
# 
#     def test_can_manually_create_4_node_classical_network(self):
#         classical_topology = [(0, 1), (1, 2), (2, 3)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = None, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 3)
#         
#     def test_can_manually_create_4_node_quantum_network(self):
#         quantum_topology = [(0, 1), (1, 2), (2, 3)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="linear network")
#         self.assertEqual(len(network.connections), 6)
#         
#     
#     def test_can_still_create_4_node_quantum_network_with_wrong_num_nodes_if_topology_defined(self):
#             quantum_topology = [(0, 1), (1, 2), (2, 3)]
#             network = create_dqc_network(state4distribution=ks.b00, 
#                                          node_list=None, num_qpus=2,
#                                       node_distance=4e-3, 
#                                       quantum_topology = quantum_topology, 
#                                       classical_topology = None,
#                                       want_classical_2way_link=False,
#                                       want_entangling_link=False, 
#                                       name="linear network")
#             self.assertEqual(len(network.connections), 6)
#             #SHOULD SEE WARNING if this works (see test below)
# 
#     def test_warning_raised_if_num_nodes_does_not_match_topology(self):
#         quantum_topology = [(0, 1), (1, 2), (2, 3)]
#         with self.assertWarns(UserWarning, msg="WARNING: num_qpus was "
#                               "overwritten because there were not enough nodes "
#                               "to realise the requested topology"):
#             create_dqc_network(state4distribution=ks.b00, 
#                                node_list=None, num_qpus=2,
#                                 node_distance=4e-3, 
#                                 quantum_topology = quantum_topology, 
#                                 classical_topology = None,
#                                 want_classical_2way_link=False,
#                                 want_entangling_link=False, 
#                                 name="linear network")
#             
#     def test_can_still_create_4_node_classical_network_with_wrong_num_nodes_if_topology_defined(self):
#             classical_topology = [(0, 1), (1, 2), (2, 3)]
#             network = create_dqc_network(state4distribution=ks.b00, 
#                                          node_list=None, num_qpus=2,
#                                       node_distance=4e-3, 
#                                       quantum_topology = None, 
#                                       classical_topology = classical_topology,
#                                       want_classical_2way_link=False,
#                                       want_entangling_link=False, 
#                                       name="linear network")
#             self.assertEqual(len(network.connections), 3)
#             #SHOULD SEE WARNING if this works (see test below)
#             
#     def test_warning_raised_if_wrong_num_qpus_for_classical_topology(self):
#             classical_topology = [(0, 1), (1, 2), (2, 3)]
#             with self.assertWarns(UserWarning, msg="WARNING: num_qpus was "
#                                   "overwritten because there were not enough nodes "
#                                   "to realise the requested topology"):
#                 create_dqc_network(state4distribution=ks.b00, 
#                                    node_list=None, num_qpus=2,
#                                    node_distance=4e-3, 
#                                    quantum_topology = None, 
#                                    classical_topology = classical_topology,
#                                    want_classical_2way_link=False,
#                                    want_entangling_link=False, 
#                                    name="linear network")
#             
#     def test_arbitrary_network_can_be_realised(self):
#         classical_topology = [(3, 2), (5, 6)]
#         quantum_topology = [(1, 2)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=7,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="arbitrary network")
#         self.assertEqual(len(network.connections), 4)
# 
#     def test_circular_network_can_be_realised(self):
#         classical_topology = [(0, 1), (1, 2), (2, 3), (3, 0)]
#         quantum_topology = [(0, 1), (1, 2), (2, 3), (3, 0)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=4,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="circular network")
#         self.assertEqual(len(network.connections), 12)
#         
#     def test_nodes_have_ebit_ready_property(self):
#         classical_topology = [(3, 2), (5, 6)]
#         quantum_topology = [(1, 2)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=7,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="arbitrary network")
#         node_dict = dict(network.nodes)
#         del node_dict["Charlie_node_1<->node_2"]
#         for node_key in node_dict:
#             node = node_dict[node_key]
#             self.assertEqual(node.ebit_ready, False)
#         
#     def test_nodes_have_comm_qubits_free_property(self):
#         classical_topology = [(3, 2), (5, 6)]
#         quantum_topology = [(1, 2)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=7,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="arbitrary network")
#         node_dict = dict(network.nodes)
#         del node_dict["Charlie_node_1<->node_2"]
#         for node_key in node_dict:
#             node = node_dict[node_key]
#             self.assertEqual(node.comm_qubits_free, [0, 1])
#             
#     def test_nodes_have_comm_qubit_positions_property(self):
#         classical_topology = [(3, 2), (5, 6)]
#         quantum_topology = [(1, 2)]
#         network = create_dqc_network(state4distribution=ks.b00, 
#                                      node_list=None, num_qpus=7,
#                                   node_distance=4e-3, 
#                                   quantum_topology = quantum_topology, 
#                                   classical_topology = classical_topology,
#                                   want_classical_2way_link=False,
#                                   want_entangling_link=False, 
#                                   name="arbitrary network")
#         node_dict = dict(network.nodes)
#         del node_dict["Charlie_node_1<->node_2"]
#         for node_key in node_dict:
#             node = node_dict[node_key]
#             self.assertEqual(node.comm_qubit_positions, (0, 1))
#             
#     def test_can_use_custom_processor(self):
#         def create_noisy_processor():
#             alpha = 1/np.sqrt(3)
#             beta = np.sqrt(2/3)
#             num_positions=7
#             p_depolar_error_cnot = 0.1
#             cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
#             #creating processor for all Nodes
#             x_gate_duration = 1
#             physical_instructions = [
#                 PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = [2, 3, 4, 5, 6]),
#                 PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
#                                     quantum_noise_model=cnot_depolar_model),
#                 PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
#                 PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
#                                     quantum_noise_model=None, apply_q_noise_after=False,
#                                     discard=True),
#                 PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
#                 toplology=[0, 1]),
#                 PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
#                                     topology=None)]
#             qprocessor = QuantumProcessor(
#                         "some_arbitrary_name", phys_instructions=physical_instructions, 
#                         num_positions=num_positions, mem_noise_models=None)
#             return qprocessor
#         F_werner = 1.0
#         state4distribution = werner_state(F_werner)
#         network = create_dqc_network(state4distribution=state4distribution, 
#                                      node_list=None, num_qpus=2,
#                                   node_distance=4e-3, 
#                                   quantum_topology = None, 
#                                   classical_topology = None,
#                                   want_classical_2way_link=True,
#                                   want_entangling_link=True,
#                                   nodes_have_ebit_ready=False,
#                                   node_comm_qubits_free=[0, 1],
#                                   node_comm_qubit_positions=(0, 1),
#                                   custom_qprocessor_func=create_noisy_processor,
#                                   name="noisy_network")
# =============================================================================




#TO DO: Figure out the mystery described in the comments of
#test_nodes_have_comm_qubits_free_property. It is easily worked around but I 
#do not understand the behaviour occuring at all!!!
            
#running all class derived from the unittest.TestCase parent class
if __name__ == '__main__':
    unittest.main()



