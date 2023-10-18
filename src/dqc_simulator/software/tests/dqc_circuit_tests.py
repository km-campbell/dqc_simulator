# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 14:28:24 2023

@author: kenny
"""

import unittest

from dqc_simulator.software.dqc_circuit import DqcCircuit


class Test_qregs2nodes(unittest.TestCase):
    def setUp(self):
        self.qregs = {'qreg1' : 1, 'qreg2' : 2}
        self.cregs = dict()
        self.defined_gates = dict()
        self.ops = [['u', 0, 'qreg1'],
               ['cx', 0, 'qreg1', 1, 'qreg2']]
    def test_conversion_strategy_monolithic(self):
        dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.defined_gates,
                                 self.ops, qreg2node_lookup=None, 
                                 circuit_type=None)
        dqc_circuit.qregs2nodes('monolithic')
        desired_output = [['u', 0, 'monolithic_processor'], 
                          ['cx', 0, 'monolithic_processor', 1,
                           'monolithic_processor']]
        with self.subTest():
            self.assertEqual(dqc_circuit.ops, desired_output)
        with self.subTest():
            self.assertEqual(dqc_circuit.circuit_type, 'monolithic')
            
    def test_conversion_strategy_auto(self):
        dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.defined_gates,
                                 self.ops, qreg2node_lookup=None, 
                                 circuit_type=None)
        dqc_circuit.qregs2nodes('auto')
        desired_output = [['u', 0, 'placeholder'], 
                          ['cx', 0, 'placeholder', 1,
                           'placeholder']]
        with self.subTest():
            self.assertEqual(dqc_circuit.ops, desired_output)
        with self.subTest():
            self.assertEqual(dqc_circuit.circuit_type, 'prepped4partitioning')

    def test_conversion_strategy_manual(self):
        qreg2node_lookup = {'qreg1' : 'node_0', 'qreg2' : 'node_1'}
        dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.defined_gates,
                                 self.ops, qreg2node_lookup=qreg2node_lookup, 
                                 circuit_type=None)
        dqc_circuit.qregs2nodes('manual')
        desired_output = [['u', 0, 'node_0'], 
                          ['cx', 0, 'node_0', 1,
                           'node_1']]
        with self.subTest():
            self.assertEqual(dqc_circuit.ops, desired_output)
        with self.subTest():
            self.assertEqual(dqc_circuit.circuit_type, 'partitioned')
            
            
# =============================================================================
# class Test_partition(unittest.TestCase):
#     def setUp(self):
#         self.qregs = {'qreg1' : 1, 'qreg2' : 2}
#         self.cregs = dict()
#         self.defined_gates = dict()
#         self.ops = [['u', 0, 'qreg1'],
#                ['cx', 0, 'qreg1', 1, 'qreg2']]
#     
#     def 
# =============================================================================

if __name__ == '__main__':
    unittest.main()
        