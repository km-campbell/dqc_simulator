# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 14:28:24 2023

@author: kenny
"""

import unittest

from dqc_simulator.software.dqc_circuit import DqcCircuit


# =============================================================================
# class Test_qregs2nodes(unittest.TestCase):
#     def setUp(self):
#         self.qregs = {'qreg1' : 1, 'qreg2' : 2}
#         self.cregs = dict()
#         self.native_gates = dict()
#         self.ops = [['u', 0, 'qreg1'],
#                ['cx', 0, 'qreg1', 1, 'qreg2']]
#     def test_conversion_strategy_monolithic(self):
#         dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.native_gates,
#                                  self.ops, qreg2node_lookup=None,
#                                  circuit_type=None)
#         dqc_circuit.qregs2nodes('monolithic')
#         desired_output = [['u', 0, 'monolithic_processor'],
#                           ['cx', 0, 'monolithic_processor', 1,
#                            'monolithic_processor']]
#         with self.subTest():
#             self.assertEqual(dqc_circuit.ops, desired_output)
#         with self.subTest():
#             self.assertEqual(dqc_circuit.circuit_type, 'monolithic')
#
#     def test_conversion_strategy_auto(self):
#         dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.native_gates,
#                                  self.ops, qreg2node_lookup=None,
#                                  circuit_type=None)
#         dqc_circuit.qregs2nodes('auto')
#         desired_output = [['u', 0, 'placeholder'],
#                           ['cx', 0, 'placeholder', 1,
#                            'placeholder']]
#         with self.subTest():
#             self.assertEqual(dqc_circuit.ops, desired_output)
#         with self.subTest():
#             self.assertEqual(dqc_circuit.circuit_type, 'prepped4partitioning')
#
#     def test_conversion_strategy_manual(self):
#         qreg2node_lookup = {'qreg1' : 'node_0', 'qreg2' : 'node_1'}
#         dqc_circuit = DqcCircuit(self.qregs, self.cregs, self.native_gates,
#                                  self.ops, qreg2node_lookup=qreg2node_lookup,
#                                  circuit_type=None)
#         dqc_circuit.qregs2nodes('manual')
#         desired_output = [['u', 0, 'node_0'],
#                           ['cx', 0, 'node_0', 1,
#                            'node_1']]
#         with self.subTest():
#             self.assertEqual(dqc_circuit.ops, desired_output)
#         with self.subTest():
#             self.assertEqual(dqc_circuit.circuit_type, 'partitioned')
# =============================================================================


class Test_add_scheme_to_2_qubit_gates(unittest.TestCase):
    def setUp(self):
        qregs = dict()
        cregs = dict()
        native_gates = dict()
        ops = [["u", 1, "node_0"], ["cx", 0, "node_0", 1, "node_1"]]
        self.dqc_circuit = DqcCircuit(
            qregs, cregs, native_gates, ops, qreg2node_lookup=None, circuit_type=None
        )

    def test_on_adds_to_two_qubit_gate_only(self):
        desired_output = [
            ["u", 1, "node_0"],
            ["cx", 0, "node_0", 1, "node_1", "tp_safe"],
        ]
        self.dqc_circuit.add_scheme_to_2_qubit_gates("tp_safe")
        self.assertEqual(self.dqc_circuit.ops, desired_output)

    def test_scheme_attr_updated(self):
        self.dqc_circuit.add_scheme_to_2_qubit_gates("tp_safe")
        self.assertEqual(self.dqc_circuit.scheme, "tp_safe")

    def test_adds_to_remote_gate_only(self):
        # overwriting ops so that now there is one local two-qubit gate and one
        # non-local
        self.dqc_circuit.ops = [
            ["cx", 0, "node_0", 1, "node_1"],
            ["cx", 0, "node_0", 1, "node_0"],
        ]
        self.dqc_circuit.add_scheme_to_2_qubit_gates("tp_safe")
        desired_output = [
            ["cx", 0, "node_0", 1, "node_1", "tp_safe"],
            ["cx", 0, "node_0", 1, "node_0"],
        ]
        self.assertEqual(self.dqc_circuit.ops, desired_output)


if __name__ == "__main__":
    unittest.main()
