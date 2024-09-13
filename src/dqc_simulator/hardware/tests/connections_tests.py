# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu Sep 12 09:45:58 2024
# 
# @author: kenny
# =============================================================================


import unittest

import netsquid as ns
from netsquid.components import QuantumMemory
from netsquid.nodes import Node
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
import numpy as np

from dqc_simulator.hardware.connections import ( 
    BlackBoxEntanglingQsourceConnection)

#for debugging
from netsquid.util import simlog
import logging
loggers = simlog.get_loggers()
loggers['netsquid'].setLevel(logging.DEBUG)

# =============================================================================
# # #resetting to default after debugging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.WARNING)
# =============================================================================

class TestBlackBoxEntanglingQsourceConnection(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        self.node0 = Node("node0", 
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.node1 = Node("node1",
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.connection = BlackBoxEntanglingQsourceConnection(
                              delay=10,
                              state4distribution=ks.b00)
        self.node0.connect_to(self.node1, self.connection, label="entangling")
        self.node0port_name = self.node0.connection_port_name(self.node1.ID,
                                        label="entangling")
        self.node1port_name = self.node1.connection_port_name(self.node0.ID,
                                        label="entangling")
        self.node0.ports[self.node0port_name].forward_input(
            self.node0.qmemory.ports["qin"])
        self.node1.ports[self.node1port_name].forward_input(
            self.node1.qmemory.ports["qin"])
        self.sim_runtime = 100
    
    def test_can_distribute_pair_of_entangled_qubits_triggered_by_node0(self):
        self.node0.ports[self.node0port_name].tx_output("ENT_REQUEST")
        ns.sim_run(self.sim_runtime)
        qubit_node0, = self.node0.qmemory.pop(0)
        qubit_node1, = self.node1.qmemory.pop(0)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)
        
    def test_can_distribute_pair_of_entangled_qubits_triggered_by_node1(self):
        self.node1.ports[self.node1port_name].tx_output("ENT_REQUEST")
        ns.sim_run(self.sim_runtime)
        qubit_node0, = self.node0.qmemory.pop(0)
        qubit_node1, = self.node1.qmemory.pop(0)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)
    







#Commented out block below is an experiment to see if you can distribute 
#multiple entangled pairs at once. The results show that while you can 
#distribute multiple pairs at the same time, the pairs go to the same nodes
#(ie, the entangled qubits are on the same node, which is useless to me)
# =============================================================================
# from netsquid.qubits import set_qstate_formalism, QFormalism
# class TestExtensions2BlackBoxEntanglingQsourceConnection(unittest.TestCase):
#     def setUp(self):
#         ns.sim_reset()
#         set_qstate_formalism(QFormalism.DM)
#         self.node0 = Node("node0", 
#                           qmemory=QuantumMemory("qmemory", num_positions=3))
#         self.node1 = Node("node1",
#                           qmemory=QuantumMemory("qmemory", num_positions=3))
#         state4distribution=np.kron(ks.b00, np.kron(ks.b00, ks.b00))
#         self.connection = BlackBoxEntanglingQsourceConnection(
#                               delay=10,
#                               state4distribution=state4distribution)
#         self.node0.connect_to(self.node1, self.connection, label="entangling")
#         self.node0port_name = self.node0.connection_port_name(self.node1.ID,
#                                         label="entangling")
#         self.node1port_name = self.node1.connection_port_name(self.node0.ID,
#                                         label="entangling")
#         self.node0.ports[self.node0port_name].forward_input(
#             self.node0.qmemory.ports["qin"])
#         self.node1.ports[self.node1port_name].forward_input(
#             self.node1.qmemory.ports["qin"])
#         self.sim_runtime = 100
#     def test_can_distribute_3pairs_of_entangled_qubits(self):
#         self.node1.ports[self.node1port_name].tx_output("ENT_REQUEST")
#         ns.sim_run(self.sim_runtime)
#         qubit0_node0, qubit1_node0, qubit2_node0 = self.node0.qmemory.pop([0, 1, 2])
#         qubit0_node1, qubit1_node1, qubit2_node1 = self.node1.qmemory.pop([0, 1, 2])
# # =============================================================================
# #         print(f"qubit0_node0 has qstate {qubit0_node0.qstate.qrepr}")
# #         print(f"qubit1_node0 has qstate.qrepr {qubit1_node0.qstate.qrepr}")
# #         print(f"qubit2_node0 has qstate {qubit2_node0.qstate.qrepr}")
# #         print(f"qubit0_node1 has qstate.qrepr {qubit0_node1.qstate.qrepr}")
# #         print(f"qubit1_node1 has qstate.qrepr {qubit1_node1.qstate.qrepr}")
# #         print(f"qubit2_node1 has qstate.qrepr(qubit2_node1.qstate.qrepr")
# # =============================================================================
#         with self.subTest(msg="first pair not entangled"):
#             fidelity = qapi.fidelity([qubit0_node0, qubit0_node1], ks.b00)
#             self.assertAlmostEqual(fidelity, 1.0, 5)
#         with self.subTest(msg="second pair not entangled"):
#             fidelity = qapi.fidelity([qubit1_node0, qubit1_node1], ks.b00)
#             self.assertAlmostEqual(fidelity, 1.0, 5)
#         with self.subTest(msg="third pair not entangled"):
#             fidelity = qapi.fidelity([qubit2_node0, qubit2_node1], ks.b00)
#             self.assertAlmostEqual(fidelity, 1.0, 5)
#         with self.subTest(msg="first pair on node0"):
#             fidelity = qapi.fidelity([qubit0_node0, qubit1_node0], ks.b00)
#             self.assertAlmostEqual(fidelity, 1.0, 5)
# =============================================================================




#running all class derived from the unittest.TestCase parent class
if __name__ == '__main__':
    unittest.main()