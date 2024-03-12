# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 11:57:03 2024

@author: kenny
"""

import unittest

from netsquid.components import instructions as instr

from dqc_simulator.software.compilers import sort_greedily_by_node_and_time


class Test_sort_greedily_by_node_and_time(unittest.TestCase):
    #NOTE: actual implementations of the following would replace strings 
    #describing gate instructions with a subclass of
    #netsquid.components.instruction.Instruction
    def setUp(self):
        self.compiler = sort_greedily_by_node_and_time
    
    def test_can_add_single_qubit_gates(self):
        gate_tuples = [("x", 3, 'node_0'), ("y", 2, 'node_0')]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0' : [[("x", 3), ("y", 2)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_local_two_qubit_gates(self):
        gate_tuples = [("CX", 2, "node_0", 3, "node_0"),  
                       ("CX", 1, "node_1", 2, "node_1"),
                       ("RX", 1, "node_0", 2, "node_0"),
                       ("RY", 1, "node_1", 2, "node_1")]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0' : [[("CX", 2, 3), ("RX", 1, 2)]],
                           'node_1' : [[("CX", 1, 2), ("RY", 1, 2)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_cat_cx(self):
        #NOTE: remote gates do not work with string as first element of 
        #gate_tuple because it is tested whether an instruction is given for
        #remote gates
        gate_tuples = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "cat")]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0': [[(2, 'node_1', 'cat', 'entangle'), 
                                       (2, 'node_1', 'cat', 'disentangle_end')]], 
                           'node_1': [[('node_0', 'cat', 'correct'),
                                       (instr.INSTR_CNOT, -1, 4), 
                                       (4, 'node_0', 'cat', 'disentangle_start')]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_block_cat(self):
        gate_tuples = [([(instr.INSTR_CNOT, -1, "node_1", 4, "node_1"),
                         (instr.INSTR_X, 3, "node_1"),
                         (instr.INSTR_CNOT, -1, "node_1", 2, "node_1")],
                        2, "node_0", 4, "node_1", "cat")]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0': [[(2, 'node_1', 'cat', 'entangle'),
                                       (2, 'node_1', 'cat', 'disentangle_end')]],
                           'node_1': [[('node_0', 'cat', 'correct'),
                                       (instr.INSTR_CNOT, -1, 'node_1', 4, 'node_1'),
                                       (instr.INSTR_X, 3, 'node_1'), 
                                       (instr.INSTR_CNOT, -1, 'node_1', 2, 'node_1'), 
                                       (4, 'node_0', 'cat', 'disentangle_start')]]}
        self.assertEqual(updated_node_op_dict, expected_output)

    def test_can_add_tp_risky_cx(self):
        gate_tuples = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "tp_risky")]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')]],
                           'node_1': [[('node_0', 'tp', 'correct'), 
                                       (instr.INSTR_CNOT, -1, 4)]]}
        self.assertEqual(updated_node_op_dict, expected_output)
        
    def test_can_add_tp_safe_cx(self):
        gate_tuples = [(instr.INSTR_CNOT, 2, "node_0", 4, "node_1", "tp_safe")]
        updated_node_op_dict = self.compiler(gate_tuples)
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')],
                                      [('node_1', 'tp', 'correct4tele_only'),
                                       (instr.INSTR_SWAP, -1, 2)]],
                           'node_1': [[('node_0', 'tp', 'correct'), 
                                       (instr.INSTR_CNOT, -1, 4)],
                                      [(-1, 'node_0', 'tp', 'bsm')]]}
        self.assertEqual(updated_node_op_dict, expected_output)

    def test_can_add_block_tp_safe(self):
        gate_tuples = [([(instr.INSTR_CNOT, -1, "node_1", 4, "node_1"),
                         (instr.INSTR_X, 3, "node_1"),
                         (instr.INSTR_CNOT, -1, "node_1", 2, "node_1")],
                        2, "node_0", 4, "node_1", "tp_safe")]
        updated_node_op_dict = self.compiler(gate_tuples)
        #TO DO: THIS may need changed if you adjust how TP-safe works
        expected_output = {'node_0': [[(2, 'node_1', 'tp', 'bsm')],
                                      [('node_1', 'tp', 'correct4tele_only'), 
                                       (instr.INSTR_SWAP, -1, 2)]],
                           'node_1': [[('node_0', 'tp', 'correct'),
                                       (instr.INSTR_CNOT, -1, 'node_1', 4, 'node_1'),
                                       (instr.INSTR_X, 3, 'node_1'),
                                       (instr.INSTR_CNOT, -1, 'node_1', 2, 'node_1')],
                                      [(-1, 'node_0', 'tp', 'bsm')]]}
        self.assertEqual(updated_node_op_dict, expected_output)













if __name__ == '__main__':
    unittest.main()