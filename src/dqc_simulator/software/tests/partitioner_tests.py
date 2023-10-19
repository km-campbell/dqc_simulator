# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 10:55:16 2023

@author: kenny
"""

import unittest

from dqc_simulator.software.dqc_circuit import DqcCircuit
from dqc_simulator.software.partitioner import bisect_circuit

class Test_bisect_circuit(unittest.TestCase):
    def test_qregs_all_given_own_node(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5}}
        cregs = dict()
        defined_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 3, 'qreg1', 4, 'qreg2']]
        dqc_circuit = DqcCircuit(qregs, cregs, defined_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit)
        desired_ops = [['u', 1, 'node_0'], ['cx', 3, 'node_0', 4, 'node_1']]
        self.assertEqual(dqc_circuit.ops, desired_ops)
    
    def test_more_qregs_than_nodes(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5},
                 'qreg3' : {'size' : 3, 'starting_index' : 11}}
        cregs = dict()
        defined_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 0, 'qreg2', 2, 'qreg3']]
        dqc_circuit = DqcCircuit(qregs, cregs, defined_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit)
        desired_ops = [['u', 1, 'node_0'], ['cx', 5, 'node_0', 7, 'node_1']]
        self.assertEqual(dqc_circuit.ops, desired_ops)
        
    def test_odd_num_qubits(self):
        qregs = {'qreg1' : {'size' : 5, 'starting_index' : 0},
                 'qreg2' : {'size' : 6, 'starting_index' : 5},
                 'qreg3' : {'size' : 4, 'starting_index' : 11}}
        cregs = dict()
        defined_gates = dict()
        ops = [['u', 1, 'qreg1'], ['cx', 0, 'qreg2', 3, 'qreg3']]
        dqc_circuit = DqcCircuit(qregs, cregs, defined_gates, ops,
                     qreg2node_lookup=None, circuit_type=None)
        bisect_circuit(dqc_circuit)
        desired_ops = [['u', 1, 'node_0'], ['cx', 5, 'node_0', 7, 'node_1']]
        #desired_ops should be unchanged from prev test despite change to
        #ops as the extra qubit should go on node_0
        self.assertEqual(dqc_circuit.ops, desired_ops)









if __name__ == '__main__':
    unittest.main()