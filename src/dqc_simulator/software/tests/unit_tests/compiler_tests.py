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
                                              order_pairs,
                                              find_consecutive_gate,
                                              find_consecutive_remote_gates)
from dqc_simulator.qlib.circuits import ( 
    produce_partitioned_circuit_from_fig4_in_autocomm_paper)
from dqc_simulator.qlib.gates import INSTR_T_DAGGER


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
        
    def test_can_handle_single_qubit_subroutine(self):
        partitioned_gates = [(instr.INSTR_INIT, 2, 'node_0'),
                             (instr.INSTR_MEASURE, 2, 'node_0', 'logging')]
        updated_node_op_dict = self.compiler(partitioned_gates)
        expected_output = {'node_0' : [[(instr.INSTR_INIT, 2),
                                        (instr.INSTR_MEASURE, 2, 'logging')]]}
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

class Test_find_consecutive_gate(unittest.TestCase):
    def test_realises_autocomm_paper_8a_blocks1and2_not_consecutive(self):
        #test circuit is start of circuit from fig. 8a of AutoComm paper
        #(up to block 2)
        partitioned_gates = [(instr.INSTR_T, 2, 'node_1'), 
                            (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'),
                            (INSTR_T_DAGGER, 2, 'node_1'),
                            (instr.INSTR_T, 3, 'node_1'),
                            (instr.INSTR_T, 3, 'node_2'),
                            (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1')]
        nxt_gate = find_consecutive_gate(partitioned_gates, 
                                         (instr.INSTR_CNOT, 2, 'node_0', 2,
                                          'node_1'),
                                         1)
        expected_output = (INSTR_T_DAGGER, 2, 'node_1')
        self.assertEqual(nxt_gate, expected_output)
    
    def test_identifies_different_cnots_as_consecutive(self):
        gate0 = (instr.INSTR_CNOT, 2, 'node_1', 3, 'node_0')
        gate1 = (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1')
        partitioned_gates = [gate0, gate1]
        nxt_gate = find_consecutive_gate(partitioned_gates,
                                         gate0,
                                         0)
        self.assertEqual(nxt_gate, gate1)

class Test_find_consecutive_remote_gates(unittest.TestCase):
    def test_gets_same_result_as_autocomm_paper8a(self):
        #Circuit from fig. 4 of AutoComm paper:
        partitioned_gates = ( 
            produce_partitioned_circuit_from_fig4_in_autocomm_paper())
        #the remote gates associated with the qubit-node pair that has the most
        #remote gates:
        filtered_remote_gates = [((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 1),
                                 ((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 5),
                                 ((instr.INSTR_CNOT, 3, 'node_0', 2, 'node_1'), 27),
                                 ((instr.INSTR_CNOT, 2, 'node_1', 3, 'node_0'), 33),
                                 ((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 35)]
        burst_comm_blocks = find_consecutive_remote_gates(partitioned_gates,
                                                          filtered_remote_gates)
        #from figure 8a of AutoComm paper:
        expected_output = [[((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 1)],
                           [((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 5)],
                           [((instr.INSTR_CNOT, 3, 'node_0', 2, 'node_1'), 27)],
                           [((instr.INSTR_CNOT, 2, 'node_1', 3, 'node_0'), 33),
                            ((instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1'), 35)]]
        self.assertEqual(burst_comm_blocks, expected_output)







if __name__ == '__main__':
    unittest.main()