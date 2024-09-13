# -*- coding: utf-8 -*-
# =============================================================================
# Created on Fri Sep 13 10:41:42 2024
# 
# @author: kenny
# =============================================================================

import unittest

from dqc_simulator.util.helper import create_wrapper_with_some_args_fixed


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








if __name__ == '__main__':
    unittest.main()

