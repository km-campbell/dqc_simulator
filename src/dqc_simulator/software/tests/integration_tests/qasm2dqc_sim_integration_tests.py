# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 09:55:37 2023

@author: kenny
"""

#integration tests to determine if the circuits can be run.

import unittest

import netsquid as ns

from dqc_simulator.hardware.dqc_creation import create_dqc_network
from dqc_simulator.hardware.quantum_processors import (
        create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates)    
from dqc_simulator.software.compilers import sort_greedily_by_node_and_time
from dqc_simulator.software.compiler_preprocessing import ( 
                                preprocess_qasm_to_compilable_bipartitioned)
from dqc_simulator.software.dqc_control import dqcMasterProtocol


#integrated network tests
#for debugging
from netsquid.util import simlog
import logging
loggers = simlog.get_loggers()
loggers['netsquid'].setLevel(logging.DEBUG)
# =============================================================================
# loggers['netsquid'].setLevel(logging.WARNING)
# =============================================================================

#TO DO: convert all tests copied and pasted from the ast2dqc_circuit_tests.py 
#to the integration tests in which the circuits are actually run
#using classes, functions and methods from dqc_simulator.software.dqc_control



class Test_can_run_sim_from_qasm_file(unittest.TestCase):
    """Testing using circuits from MQTBench"""
    def setUp(self):
        self.directory_path = ('/home/kenny/coding_projects/dqc_simulation/' + 
                          'MQT_benchmarking_circuits/scalable_5to10_qubits/')
        
    def _run_dqc_circuit(self, filename):
        ns.sim_reset()
        filepath = self.directory_path + filename
        dqc_circuit = preprocess_qasm_to_compilable_bipartitioned(
                                                        filepath, 
                                                        scheme='tp_safe',
                                                        include_path='.')
        p_depolar_error_cnot = 0
        comm_qubit_depolar_rate = 0
        data_qubit_depolar_rate = 0
        network = create_dqc_network(
                        p_depolar_error_cnot,
                        comm_qubit_depolar_rate,
                        data_qubit_depolar_rate,
                        state4distribution=None, #ks.b00 defined in function body
                        node_list=None,
                        num_nodes=2,
                        node_distance=2e-3, ent_dist_rate=0,
                        quantum_topology = None, 
                        classical_topology = None,
                        create_classical_2way_link=True,
                        create_entangling_link=True,
                        nodes_have_ebit_ready=False,
                        node_comm_qubits_free=None, #[0, 1] defined in function body
                        node_comm_qubit_positions=None, #(0, 1) defined in function body
                        custom_qprocessor_func=create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates,
                        name="linear network")
        protocol = dqcMasterProtocol(dqc_circuit.ops, network, 
                                    compiler_func=sort_greedily_by_node_and_time)
        protocol.start()
        ns.sim_run()
        return network
        
    def test_with_ae_indep_qiskit_5(self):
       network = self._run_dqc_circuit('ae_indep_qiskit_5.qasm')
        
# =============================================================================
#     def test_with_dj_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('dj_indep_qiskit_5.qasm')
#         
#     def test_with_ghz_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('ghz_indep_qiskit_5.qasm')
#         
#     def test_with_graphstate_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('graphstate_indep_qiskit_5.qasm')
# 
#     def test_with_grover_noancilla_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('grover-noancilla_indep_qiskit_5.qasm')
#         
# # =============================================================================
# #     def test_portfolioqaoa_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('portfolioqaoa_indep_qiskit_5.qasm')
# #         #RAISES ERROR because rzz is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# # =============================================================================
#     def test_portfoliovqe_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('portfoliovqe_indep_qiskit_5.qasm')
#     
# # =============================================================================
# #     def test_qaoa_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qaoa_indep_qiskit_5.qasm')
# #         #RAISES ERROR because rzz is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #         
# #     def test_qft_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qft_indep_qiskit_5.qasm')
# #         #RAISES ERROR because swap gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #     
# #     def test_qftentangled_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qftentangled_indep_qiskit_5.qasm')
# #         #RAISES ERROR because swap gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# # =============================================================================
#         
#     def test_qnn_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('qnn_indep_qiskit_5.qasm')
# 
# # =============================================================================
# #     def test_qpeexact_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qpeexact_indep_qiskit_5.qasm')
# #         #RAISES ERROR because swap gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #         
# #     def test_qpeinexact_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qpeinexact_indep_qiskit_5.qasm')
# #         #RAISES ERROR because swap gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #         
# #     def test_qwalk_noancilla_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qwalk-noancilla_indep_qiskit_5.qasm')
# #         #RAISES ERROR because ccx gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #         
# #     def test_qwalk_v_chain_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('qwalk-v-chain_indep_qiskit_5.qasm')
# #         #RAISES ERROR because rccx gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# #         
# #     def test_random_indep_qiskit_5(self):
# #        network = self._run_dqc_circuit('random_indep_qiskit_5.qasm')
# #         #RAISES ERROR because rzz gate is not defined in your standard library.
# #         #I think I will wait until I can define macros with a <gatedecl> to 
# #         #fix this
# # 
# # =============================================================================
#     def test_realamprandom_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('realamprandom_indep_qiskit_5.qasm')
# 
#     def test_su2random_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('su2random_indep_qiskit_5.qasm')
# 
#     def test_twolocalrandom_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('twolocalrandom_indep_qiskit_5.qasm')
# 
#     def test_vqe_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('vqe_indep_qiskit_5.qasm')
# 
#     def test_wstate_indep_qiskit_5(self):
#        network = self._run_dqc_circuit('wstate_indep_qiskit_5.qasm')
# =============================================================================
        
        
if __name__ == '__main__':
    unittest.main()