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
from netsquid.nodes import Node
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi

from dqc_simulator.hardware.connections import ( 
    create_classical_fibre_connection,
    BlackBoxEntanglingQsourceConnection)
from dqc_simulator.software.physical_layer import ( 
    AbstractCentralSourceEntangleProtocol)

#for debugging
# =============================================================================
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# =============================================================================
# =============================================================================
# 
# #resetting to default after debugging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.WARNING)
# =============================================================================


#TO DO: think about moving these integration tests somewhere else in the file
#structure.



class TestAbstractEntanglingConnectionAndSoftware(unittest.TestCase):
    """
    Integration tests of AbstractCentralSourceEntangleProtocol with
    BlackBoxEntanglingQsourceConnection.
    """
    def setUp(self):
        ns.sim_reset()
        self.node0 = Node("node0", 
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.node1 = Node("node1",
                          qmemory=QuantumMemory("qmemory", num_positions=3))
        self.quantum_connection = BlackBoxEntanglingQsourceConnection(
                                      delay=10,
                                      state4distribution=ks.b00)
        self.node0qport_name = self.node0.connection_port_name(
                                        self.node1.name,
                                        label="entangling")
        self.node1qport_name = self.node1.connection_port_name(
                                                        self.node0.name,
                                                        label="entangling")
        self.node0.connect_to(self.node1, self.quantum_connection,
                              local_port_name=self.node0qport_name,
                              remote_port_name=self.node1qport_name)
        #establishing classical connection
        self.node0cport_name = self.node0.connection_port_name(
                                        self.node1.name,
                                        label="classical")
        self.node1cport_name = self.node1.connection_port_name(
                                                        self.node0.name,
                                                        label="classical")
        self.classical_connection = create_classical_fibre_connection(
                                              name='classical_fibre',
                                              length=2e-3)
        self.node0.connect_to(self.node1, self.classical_connection,
                              local_port_name=self.node0cport_name,
                              remote_port_name=self.node1cport_name)
        self.node0_protocol = AbstractCentralSourceEntangleProtocol(
                                    node=self.node0,
                                    role=None,
                                    other_node_name="node1",
                                    comm_qubit_indices=[1],
                                    ready4ent=None)
        self.node1_protocol = AbstractCentralSourceEntangleProtocol(
                                    node=self.node1,
                                    other_node_name="node0",
                                    comm_qubit_indices=[1],
                                    ready4ent=None)
        #note in actual implementations, the comm_qubit_index would be set by
        #the link layer and the protocols would be started by the link layer
        self.sim_runtime = 100
        
# =============================================================================
#         node=None, name=None, role=None, other_node_name=None,
#                      comm_qubit_indices=None, ready4ent=True
# =============================================================================
        
    #TO DO: update the next two tests when handshake added
    def test_can_distribute_pair_of_entangled_qubits_with_node0_as_client(self):
        self.node0_protocol.role='client'
        self.node0_protocol.ready4ent=True
        self.node1_protocol.role='server'
        self.node1_protocol.ready4ent=True
        self.node0_protocol.start()
        self.node1_protocol.start()
        ns.sim_run(self.sim_runtime)
        qubit_node0, = self.node0.qmemory.pop(1)
        qubit_node1, = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)
        
    def test_can_distribute_pair_of_entangled_qubits_with_node1_as_client_as_client(self):
        self.node1_protocol.role = 'client'
        self.node1_protocol.ready4ent = True
        self.node0_protocol.role = 'server'
        self.node0_protocol.ready4ent = True
        self.node0_protocol.start()
        self.node1_protocol.start()
        ns.sim_run(self.sim_runtime)
        qubit_node0, = self.node0.qmemory.pop(1)
        qubit_node1, = self.node1.qmemory.pop(1)
        fidelity = qapi.fidelity([qubit_node0, qubit_node1], ks.b00)
        self.assertAlmostEqual(fidelity, 1.0, 5)
        











if __name__ == '__main__':
    unittest.main()