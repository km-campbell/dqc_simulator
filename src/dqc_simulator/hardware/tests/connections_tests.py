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
    
# =============================================================================
#     def test_can_distribute_3pairs_of_entangled_qubits(self):
# =============================================================================
        
        





#running all class derived from the unittest.TestCase parent class
if __name__ == '__main__':
    unittest.main()