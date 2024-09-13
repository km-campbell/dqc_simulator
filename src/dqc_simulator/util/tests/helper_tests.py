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
    def test_returns_working_function(self):
        def dummy_func(a, b, c):
            return {"a" : a, "b" : b, "c" : c}
        arg_posNvalue_dict = {0: 1, 2 : 2}
        wrapped_func = create_wrapper_with_some_args_fixed(dummy_func, 
                                                           arg_posNvalue_dict)
        self.assertEqual(wrapped_func(-3), {"a" : 1, "b" : -3, "c": 2})










if __name__ == '__main__':
    unittest.main()

