# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 11:57:03 2024

@author: kenny
"""

import unittest

from netsquid.components import instructions as instr

from dqc_simulator.software.compilers import (sort_greedily_by_node_and_time,
                                              find_qubit_node_pairs,
                                              find_node_node_pairs,
                                              find_pairs,
                                              order_pairs)


class Test_sort_greedily_by_node_and_time(unittest.TestCase):
    #NOTE: actual implementations of the following would replace strings 
    #describing gate instructions with a subclass of
    #netsquid.components.instruction.Instruction
    def setUp(self):
        self.compiler = sort_greedily_by_node_and_time
    
    def test_can_add_single_qubit_gates(self):
        partitioned_gates = [("x", 3, 'node_0'), ("y", 2, 'node_0')]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0' : [[("x", 3), ("y", 2)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_local_two_qubit_gates(self):
        partitioned_gates = [("CX", 2, "node_0", 3, "node_0"),  
                       ("CX", 1, "node_1", 2, "node_1"),
                       ("RX", 1, "node_0", 2, "node_0"),
                       ("RY", 1, "node_1", 2, "node_1")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0' : [[("CX", 2, 3), ("RX", 1, 2)]],
                           'node_1' : [[("CX", 1, 2), ("RY", 1, 2)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_cat_cx(self):
        #NOTE: remote gates do not work with string as first element of 
        #gate_tuple because it is tested whether an instruction is given for
        #remote gates
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "cat")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0': [[(2, 'node_1', 'cat', 'entangle'), 
                                       (2, 'node_1', 'cat', 'disentangle_end')]], 
                           'node_1': [[('node_0', 'cat', 'correct'),
                                       (instr.INSTR_CNOT, -1, 4), 
                                       (4, 'node_0', 'cat', 'disentangle_start')]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_block_cat(self):
        partitioned_gates = [([(instr.INSTR_CNOT, -1, "node_1", 4, "node_1"),
                         (instr.INSTR_X, 3, "node_1"),
                         (instr.INSTR_CNOT, -1, "node_1", 2, "node_1")],
                        2, "node_0", 4, "node_1", "cat")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0': [[(2, 'node_1', 'cat', 'entangle'),
                                       (2, 'node_1', 'cat', 'disentangle_end')]],
                           'node_1': [[('node_0', 'cat', 'correct'),
                                       (instr.INSTR_CNOT, -1, 'node_1', 4, 'node_1'),
                                       (instr.INSTR_X, 3, 'node_1'), 
                                       (instr.INSTR_CNOT, -1, 'node_1', 2, 'node_1'), 
                                       (4, 'node_0', 'cat', 'disentangle_start')]]}
        self.assertEqual(updated_node_op_dict, expected_output)

    def test_can_add_tp_risky_cx(self):
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "tp_risky")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')]],
                           'node_1': [[('node_0', 'tp', 'correct'), 
                                       (instr.INSTR_CNOT, -1, 4)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    
# =============================================================================
#     def test_can_add_tp_safe_cx(self):
#         #using deprecated method of TP-safe
#         partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "tp_safe")]
#         updated_node_op_dict = self.compiler(partitioned_gates)
#         expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')],
#                                       [('node_1', 'tp', 'correct4tele_only'),
#                                        (instr.INSTR_SWAP, -1, 2)]],
#                            'node_1': [[('node_0', 'tp', 'correct'), 
#                                        (instr.INSTR_CNOT, -1, 4)],
#                                       [(-1, 'node_0', 'tp', 'bsm')]]}
#         self.assertEqual(updated_node_op_dict, expected_output)
# =============================================================================
        
    def test_can_add_cx_tp_safe(self):
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "tp_safe")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')], 
                                      [(2, 'node_1', 'tp', 'swap_then_correct')]],
                           'node_1': [[('node_0', 'tp', 'correct'),
                                       (instr.INSTR_CNOT, -1, 4)], 
                                      [(-1, 'node_0', 'tp', 'bsm')]]}
        self.assertEqual(updated_node_op_dict, expected_output)

    def test_can_add_block_tp_safe(self):
        partitioned_gates = [([(instr.INSTR_CNOT, -1, "node_1", 4, "node_1"),
                         (instr.INSTR_X, 3, "node_1"),
                         (instr.INSTR_CNOT, -1, "node_1", 2, "node_1")],
                        2, "node_0", 4, "node_1", "tp_safe")]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')],
                                      [(2, 'node_1', 'tp', 'swap_then_correct')]], 
                           'node_1': [[('node_0', 'tp', 'correct'), 
                                       (instr.INSTR_CNOT, -1, 'node_1', 4, 'node_1'),
                                       (instr.INSTR_X, 3, 'node_1'), 
                                       (instr.INSTR_CNOT, -1, 'node_1', 2, 'node_1')],
                                      [(-1, 'node_0', 'tp', 'bsm')]]}
        self.assertEqual(updated_node_op_dict, expected_output)


class Test_find_qubit_node_pairs(unittest.TestCase):
    def test_adds_single_gate(self):
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 3, "node_1",
                              "placeholder")]
        qubit_node_pairs = find_qubit_node_pairs(partitioned_gates)
        expected_output = {(2, 'node_0', 'node_1'): [((instr.INSTR_CNOT, 2,
                                                      'node_0', 3, 'node_1',
                                                      'placeholder'), 0)], 
                           (3, 'node_1', 'node_0'): [((instr.INSTR_CNOT, 2, 
                                                      'node_0', 3, 'node_1', 
                                                      'placeholder'), 0)]}
        self.assertEqual(qubit_node_pairs, expected_output)
    def test_adds_single_gate_from_many(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        qubit_node_pairs = find_qubit_node_pairs(partitioned_gates)
        expected_output = {(2, 'node_0', 'node_1'): [((instr.INSTR_CNOT, 2,
                                                      'node_0', 3, 'node_1',
                                                      'placeholder'), 1)], 
                           (3, 'node_1', 'node_0'): [((instr.INSTR_CNOT, 2, 
                                                      'node_0', 3, 'node_1', 
                                                      'placeholder'), 1)]}
        self.assertEqual(qubit_node_pairs, expected_output)
    
    def test_adds_multiple_gates(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_0", "placeholder"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        qubit_node_pairs = find_qubit_node_pairs(partitioned_gates)
        expected_output = {(2, 'node_0', 'node_1'): 
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1',
                                  'placeholder'), 1),
                                ((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)], 
                           (3, 'node_1', 'node_0'):
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1', 
                                  'placeholder'), 1)],
                           (4, 'node_1', 'node_0') : 
                                [((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)],
                           (2, "node_1", "node_0") :
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_0", 
                                  "placeholder"), 4)],
                            (4, "node_0", "node_1") :
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_0", 
                                   "placeholder"), 4)]}
        self.assertEqual(qubit_node_pairs, expected_output)
        
class Test_find_node_node_pairs(unittest.TestCase):
    def test_adds_single_gate(self):
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 3, "node_1",
                              "placeholder")]
        node_node_pairs = find_node_node_pairs(partitioned_gates)
        expected_output = {('node_0', 'node_1'): [((instr.INSTR_CNOT, 2,
                                                      'node_0', 3, 'node_1',
                                                      'placeholder'), 0)]}
        self.assertEqual(node_node_pairs, expected_output)
        
    def test_adds_two_gates_to_same_entry(self):
        partitioned_gates = [(instr.INSTR_CNOT, 2, "node_0", 3, "node_1",
                              "placeholder"), 
                             (instr.INSTR_CNOT, 2, "node_1", 3, "node_0",
                                                   "placeholder"), ]
        node_node_pairs = find_node_node_pairs(partitioned_gates)
        expected_output = {('node_0', 'node_1'): 
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1',
                                  'placeholder'), 0),
                                ((instr.INSTR_CNOT, 2, "node_1", 3, "node_0",
                                  "placeholder"), 1)]}
        self.assertEqual(node_node_pairs, expected_output)
        
    def test_adds_single_gate_from_many(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        node_node_pairs = find_node_node_pairs(partitioned_gates)
        expected_output = {('node_0', 'node_1'): [((instr.INSTR_CNOT, 2,
                                                      'node_0', 3, 'node_1',
                                                      'placeholder'), 1)]}
        self.assertEqual(node_node_pairs, expected_output)
    
    def test_adds_multiple_gates(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_2", "placeholder"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        node_node_pairs = find_node_node_pairs(partitioned_gates)
        expected_output = {('node_0', 'node_1'): 
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1',
                                  'placeholder'), 1),
                                ((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)], 
                            ('node_1', 'node_2'):
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_2", 
                                  "placeholder"), 4)]}
        self.assertEqual(node_node_pairs, expected_output)
        
class Test_find_pairs(unittest.TestCase):
    def test_qubit_node_option(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_0", "placeholder"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        qubit_node_pairs = find_pairs(partitioned_gates, 'qubit_node')
        expected_output = {(2, 'node_0', 'node_1'): 
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1',
                                  'placeholder'), 1),
                                ((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)], 
                           (3, 'node_1', 'node_0'):
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1', 
                                  'placeholder'), 1)],
                           (4, 'node_1', 'node_0') : 
                                [((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)],
                           (2, "node_1", "node_0") :
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_0", 
                                  "placeholder"), 4)],
                            (4, "node_0", "node_1") :
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_0", 
                                   "placeholder"), 4)]}
        self.assertEqual(qubit_node_pairs, expected_output)
    
    def test_node_node_option(self):
        partitioned_gates = [(instr.INSTR_X, 2, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_0", 3, "node_1","placeholder"),
                             (instr.INSTR_Z, 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_1"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_2", "placeholder"),
                             (instr.INSTR_CNOT, 2, "node_0", 4, "node_0"),
                             (instr.INSTR_CNOT, 2, "node_1", 4, "node_1")]
        node_node_pairs = find_pairs(partitioned_gates, 'node_node')
        expected_output = {('node_0', 'node_1'): 
                               [((instr.INSTR_CNOT, 2,'node_0', 3, 'node_1',
                                  'placeholder'), 1),
                                ((instr.INSTR_CNOT, 2, "node_0", 4, "node_1"), 3)], 
                            ('node_1', 'node_2'):
                                [((instr.INSTR_CNOT, 2, "node_1", 4, "node_2", 
                                  "placeholder"), 4)]}
        self.assertEqual(node_node_pairs, expected_output)

class Test_order_remote_gates(unittest.TestCase):
    def test_in_descending_order(self):
        a_dict = {'smaller_entry' : [1], 'larger_entry' : [2, 3, 4, 4]}
        sorted_dict = order_pairs(a_dict)
        expected_output = {'larger_entry' : [2, 3, 4, 4],
                           'smaller_entry' : [1]}
        self.assertEqual(sorted_dict, expected_output)










if __name__ == '__main__':
    unittest.main()