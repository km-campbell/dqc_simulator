# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 15:41:19 2023

@author: kenny
"""

import unittest

from dqc_simulator.software.compiler_preprocessing import ( 
                                preprocess_qasm_to_compilable_bipartitioned)
                                             

#TO DO: have proper test rather than just printing



class Test_preprocess_qasm_to_compilable_bipartitioned(unittest.TestCase):
    """Testing using circuits from MQTBench"""
    def setUp(self):
        self.directory_path = ('/home/kenny/coding_projects/dqc_simulation/' + 
                          'MQT_benchmarking_circuits/scalable_5to10_qubits/')
        
    def _get_dqc_circuit(self, filename):
        filepath = self.directory_path + filename
        dqc_circuit = preprocess_qasm_to_compilable_bipartitioned(
                                                        filepath, 
                                                        scheme='tp_safe',
                                                        include_path='.')
        print(dqc_circuit.ops)
        return dqc_circuit
        
    def test_with_ae_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('ae_indep_qiskit_5.qasm')
        
    def test_with_dj_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('dj_indep_qiskit_5.qasm')
        
    def test_with_ghz_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('ghz_indep_qiskit_5.qasm')
        
    def test_with_graphstate_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('graphstate_indep_qiskit_5.qasm')

    def test_with_grover_noancilla_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('grover-noancilla_indep_qiskit_5.qasm')
        
# =============================================================================
#     def test_portfolioqaoa_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('portfolioqaoa_indep_qiskit_5.qasm')
#         #RAISES ERROR because rzz is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
# =============================================================================
    def test_portfoliovqe_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('portfoliovqe_indep_qiskit_5.qasm')
    
# =============================================================================
#     def test_qaoa_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qaoa_indep_qiskit_5.qasm')
#         #RAISES ERROR because rzz is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#         
#     def test_qft_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qft_indep_qiskit_5.qasm')
#         #RAISES ERROR because swap gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#     
#     def test_qftentangled_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qftentangled_indep_qiskit_5.qasm')
#         #RAISES ERROR because swap gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
# =============================================================================
        
    def test_qnn_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qnn_indep_qiskit_5.qasm')

# =============================================================================
#     def test_qpeexact_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qpeexact_indep_qiskit_5.qasm')
#         #RAISES ERROR because swap gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#         
#     def test_qpeinexact_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qpeinexact_indep_qiskit_5.qasm')
#         #RAISES ERROR because swap gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#         
#     def test_qwalk_noancilla_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qwalk-noancilla_indep_qiskit_5.qasm')
#         #RAISES ERROR because ccx gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#         
#     def test_qwalk_v_chain_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('qwalk-v-chain_indep_qiskit_5.qasm')
#         #RAISES ERROR because rccx gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
#         
#     def test_random_indep_qiskit_5(self):
#         dqc_circuit = self._get_dqc_circuit('random_indep_qiskit_5.qasm')
#         #RAISES ERROR because rzz gate is not defined in your standard library.
#         #I think I will wait until I can define macros with a <gatedecl> to 
#         #fix this
# 
# =============================================================================
    def test_realamprandom_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('realamprandom_indep_qiskit_5.qasm')

    def test_su2random_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('su2random_indep_qiskit_5.qasm')

    def test_twolocalrandom_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('twolocalrandom_indep_qiskit_5.qasm')

    def test_vqe_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('vqe_indep_qiskit_5.qasm')

    def test_wstate_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('wstate_indep_qiskit_5.qasm')
        
        
if __name__ == '__main__':
    unittest.main()