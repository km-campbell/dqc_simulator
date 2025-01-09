# -*- coding: utf-8 -*-
# =============================================================================
# Created on Fri Sep 13 10:41:42 2024
# 
# @author: kenny
# =============================================================================

import unittest

import netsquid as ns
from netsquid.protocols import Protocol
import pydynaa

from dqc_simulator.util.helper import (
    create_wrapper_with_some_args_fixed,
    filter_kwargs4internal_functions,
    get_data_collector_for_mid_sim_instr_output,
    QDCSignals)

#for debugging
# =============================================================================
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# # =============================================================================
# # loggers['netsquid'].setLevel(logging.WARNING)
# # =============================================================================
# =============================================================================

class TestCreateWrapper(unittest.TestCase):
    """
    Tests create_wrapper_with_some_args_fixed
    """
    def dummy_func(self, a, b, c, **kwargs):
        pos_args =  {"a" : a, "b" : b, "c" : c}
        return {**pos_args, **kwargs}
    
    def test_wraps_positional_args(self):
        arg_posNvalue_dict = {0: 1, 2 : 2}
        wrapped_func = create_wrapper_with_some_args_fixed(self.dummy_func, 
                                                           arg_posNvalue_dict)
        self.assertEqual(wrapped_func(-3), {"a" : 1, "b" : -3, "c": 2})
        
    def test_wraps_keyword_args(self):
        wrapped_func = create_wrapper_with_some_args_fixed(self.dummy_func,
                                                           None,
                                                           d=4)
        self.assertEqual(wrapped_func(1, -3, 2, e=5),
                         {"a" : 1, "b" : -3, "c": 2, "d" : 4, "e" : 5})
    def test_wraps_positional_and_keyword_args_at_same_time(self):
        arg_posNvalue_dict = {0: 1, 2 : 2}
        wrapped_func = create_wrapper_with_some_args_fixed(self.dummy_func, 
                                                           arg_posNvalue_dict,
                                                           d=4)
        self.assertEqual(wrapped_func(-3, e=5),
                         {"a" : 1, "b" : -3, "c": 2, "d" : 4, "e" : 5})

class Test_filter_kwargs4internal_functions(unittest.TestCase):
    def child_func1(self, a, b=2, c=3):
        return {'a' : a, 'b' : b, 'c' : c}
    
    def child_func2(self, d, e=4, f=5):
        return {'d' : d, 'e' : e, 'f' : f}
    
    def parent_func_role(self, **kwargs):
        return kwargs
    
    def test_output_as_expected_for_two_sets_of_kwargs(self):
        kwargs_from_parent = self.parent_func_role(b=2, c=3, e=4, f=5)
        actual_output = filter_kwargs4internal_functions([self.child_func1,
                                                          self.child_func2], 
                                                         kwargs_from_parent)
        expected_output = {self.child_func1 : {'b' : 2, 'c' : 3},
                           self.child_func2 : {'e' : 4, 'f' : 5}}
        self.assertEqual(actual_output, expected_output)
        

class Test_get_data_collector_for_mid_sim_instr_output(unittest.TestCase):
    class DummyProtocol(Protocol):
        def __init__(self, name):
            super().__init__(name)
            self.add_signal(QDCSignals.RESULT_PRODUCED)
        
        def run(self):
            while True:
                self.send_signal(QDCSignals.RESULT_PRODUCED, 
                                result='some_result')
# =============================================================================
#                 #for DEBUG ONLY
#                 dummy_entity = pydynaa.Entity()
#                 dummy_entity._schedule_now(QDCSignals.RESULT_PRODUCED.value)
# =============================================================================
                break
                
    def test_signal_detected_from_DummyProtocol(self):
        ns.sim_reset()
        protocol = self.DummyProtocol('dummy_protocol')
        dc = get_data_collector_for_mid_sim_instr_output()
        protocol.start()
        ns.sim_run(1e9)
        #checking DataFrame is not empty
        with self.subTest('DataFrame is empty'):
            self.assertFalse(dc.dataframe.empty, msg='DataFrame is empty')
        #checking correct result is received
        with self.subTest('Result is wrong'):
            self.assertEqual(dc.dataframe['result'][0], 'some_result')
            
        #TO DO: write subtest to check signal is correct (has value 'some_result')
        




if __name__ == '__main__':
    unittest.main()

