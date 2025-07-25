# -*- coding: utf-8 -*-
# =============================================================================
# Created on Wed Jan 31 12:26:58 2024
# 
# @author: kenny
# =============================================================================
"""
Info on each remote gate scheme.
"""

def get_scheme_info():
#The resource costs associated with implementing a single remote CX using 
#each of the remote gate schemes. The 'num_single_qubit_gates' assumes that all
#measurement results are 1 (the worst case scenario).
    return {'mono' : {'num_epr_pairs' : 0, 
                      'num_cnots' : 1,
                      'num_single_qubit_gates' : 0,
                      'num_measurements' : 0,
                      'num_classical_comms' : 0},
            'cat' : {'num_epr_pairs' : 1, 
                     'num_cnots' : 2,
                     'num_single_qubit_gates' : 3,
                     'num_measurements' : 2,
                     'num_classical_comms' : 2},
            '1tp' : {'num_epr_pairs' : 1, 
                     'num_cnots' : 2,
                     'num_single_qubit_gates' : 3,
                     'num_measurements' : 2,
                     'num_classical_comms' : 2},
            '2tp' : {'num_epr_pairs' : 2, 
                     'num_cnots' : 3,
                     'num_single_qubit_gates' : 6,
                     'num_measurements' : 4,
                     'num_classical_comms' : 4},
            'tp_safe' : {'num_epr_pairs' : 2, 
                         'num_cnots' : 6,
                         'num_single_qubit_gates' : 6,
                         'num_measurements' : 4,
                         'num_classical_comms' : 4}} 
