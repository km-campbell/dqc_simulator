# -*- coding: utf-8 -*-
"""
Created on Wed Oct 11 11:24:31 2023

@author: kenny
"""

import unittest

import numpy as np
from netsquid.components import instructions as instr

from dqc_simulator.software.dqc_circuit import DqcCircuit
from dqc_simulator.software.qasm2ast import qasm2ast
from dqc_simulator.software.ast2dqc_circuit import (
                                                 ArgumentInterpreter,
                                                 AstComment,
                                                 AstCreg, AstGate, AstQreg,
                                                 AstUnknown, ast2sim_readable,
                                                 QasmParsingElement)
from dqc_simulator.qlib import gates


# =============================================================================
# class TestQasmParsingElement(unittest.TestCase):
#     def test_exp_qasm(self):
#         pe = QasmParsingElement()
#         str1 = 'sin(pi/2 + 0.1) - cos ( 1.53)'
#         str2 = '1 + 2'
#         str3 = '(1 + 2)/3'
#         str4 = '1 * 3 + 1'
#         str5 = 'sin(sin(0.1) + cos(1.2))'
#         print(f"Using exp_qasm grammar {str1} parses to "
#               f"{pe.exp_qasm.parse_string(str1)}")
#         print(f"Using exp_qasm grammar {str2} parses to "
#               f" {pe.exp_qasm.parse_string(str2)}")
#         print(f"Using exp_qasm grammar {str3} parses to "
#               f" {pe.exp_qasm.parse_string(str3)}")
#         print(f"Using exp_qasm grammar {str4} parses to "
#               f" {pe.exp_qasm.parse_string(str4)}")
#         print(f"Using exp_qasm grammar {str5} parses to "
#               f" {pe.exp_qasm.parse_string(str5)}")
# =============================================================================
        

class TestNonTerminalInterpreter(unittest.TestCase):
    def test_ArgumentInterpreter_interprets_argument_correctly(self):
        argument_string = 'q[1]'
        interpreter = ArgumentInterpreter()
        qubit_index, reg_name = interpreter.interpret(argument_string)
        with self.subTest():
            self.assertEqual(reg_name, 'q')
        with self.subTest():
            self.assertEqual(qubit_index, 1)
            
    

class TestAst2SimReadableSubclasses(unittest.TestCase):
    def setUp(self):
        self.qregs = dict()
        self.cregs = dict()
        self.defined_gates = {  
                            "U" : gates.INSTR_U,
                            "CX" : instr.INSTR_CNOT,
                            "u3" : gates.INSTR_U,
                            "u2" : lambda phi, lambda_var : gates.INSTR_U(np.pi/2, phi, lambda_var),
                            "u1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var),
                            "cx" : instr.INSTR_CNOT,
                            "id" : gates.INSTR_IDENTITY,
                            "x" : instr.INSTR_X,
                            "y" : instr.INSTR_Y,
                            "z" : instr.INSTR_Z,
                            "h" : instr.INSTR_H,
                            "s" : instr.INSTR_S,
                            "sdg" : gates.INSTR_S_DAGGER,
                            "t" : instr.INSTR_T,
                            "tdg" : gates.INSTR_T_DAGGER,
                            "rx" : lambda theta : gates.INSTR_U(theta, -np.pi/2, np.pi/2),
                            "ry" : lambda theta : gates.INSTR_U(theta, 0, 0),
                            "rz" : gates.INSTR_RZ,
                            "cz" : instr.INSTR_CZ,
                            "cy" : gates.INSTR_CY,
                            "ch" : gates.INSTR_CH,
                            "ccx" : instr.INSTR_CCX,
                            "crz" : lambda angle : gates.INSTR_RZ(angle, controlled=True),
                            "cu1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var, controlled=True),
                            "cu3" : lambda theta, phi, lambda_var : gates.INSTR_U(theta, phi, lambda_var, controlled=True)}
        self.gates4circuit = []
        self.dqc_circuit = DqcCircuit(self.qregs, self.cregs, 
                                      self.defined_gates, self.gates4circuit)
        
    def test_AstComment_does_not_raise_error_when_make_sim_readable_called(self):
        mock_ast_c_sect_element = {}
        converter = AstComment(mock_ast_c_sect_element, self.dqc_circuit)
        updated_dqc_circuit = converter.make_sim_readable()
        
    def test_AstUnknown_raises_ValueError_when_make_sim_readable_called(self):
        mock_ast_c_sect_element = {}
        converter = AstComment(mock_ast_c_sect_element, self.dqc_circuit)
        converter.make_sim_readable()
        self.assertRaises(ValueError)
        
    def test_qreg_attribute_updated_by_AstQreg(self):
        mock_ast_c_sect_element = {'qreg_name' : 'q', 'qreg_num' : '5'}
        converter = AstQreg(mock_ast_c_sect_element, self.dqc_circuit)
        updated_dqc_circuit = converter.make_sim_readable()
        self.assertEqual(updated_dqc_circuit.qregs['q'], {'size' : 5, 
                                                          'starting_index' : 0})
        
    def test_qreg_starting_index_updated_by_AstQreg(self):
        mock_ast_c_sect_element = {'qreg_name' : 'q', 'qreg_num' : '5'}
        converter = AstQreg(mock_ast_c_sect_element, self.dqc_circuit)
        updated_dqc_circuit = converter.make_sim_readable()
        mock_ast_c_sect_element = {'qreg_name' : 'qreg2', 'qreg_num' : '9'}
        converter = AstQreg(mock_ast_c_sect_element, self.dqc_circuit)
        updated_dqc_circuit = converter.make_sim_readable()
        self.assertEqual(updated_dqc_circuit.qregs['qreg2'], {'size' : 9, 
                                                          'starting_index' : 5})
        
    def test_creg_attribute_updated_by_AstCreg(self):
        mock_ast_c_sect_element = {'creg_name' : 'c', 'creg_num' : '5'}
        converter = AstCreg(mock_ast_c_sect_element, self.dqc_circuit)
        updated_dqc_circuit = converter.make_sim_readable()
        self.assertEqual(updated_dqc_circuit.cregs['c'], 5)
        
    def test_ops_attributed_updated_by_AstGate_4_single_qubit_gate(self):
        with self.subTest():
            mock_ast_c_sect_element = {'op' : 'rx', 'param_list' : ['1'],
                                       'reg_list' : ['q[3]']}
            converter = AstGate(mock_ast_c_sect_element, self.dqc_circuit)
            updated_dqc_circuit = converter.make_sim_readable()
            desired_gate_spec = [gates.INSTR_U(1, -np.pi/2, np.pi/2), 3, 'q'] 
            self.assertEqual(updated_dqc_circuit.ops[0], desired_gate_spec)
            #I think that this fail is a false negative because of the fact 
            #that I have defined one gate via a lambda function and one not.
# =============================================================================
#         with self.subTest():
#             mock_ast_c_sect_element = {'op' : 'rx', 'param_list' : ['pi/3'],
#                                        'reg_list' : ['q[3]']}
#             converter = AstGate(mock_ast_c_sect_element, self.dqc_circuit)
#             updated_dqc_circuit = converter.make_sim_readable()
#             desired_gate_tuple = (gates.INSTR_U(np.pi/3, -np.pi/2, np.pi/2), 
#                                   3, 'q') 
#             self.assertEqual(updated_dqc_circuit.ops[0], desired_gate_tuple)
# =============================================================================

class Test_ast2sim_readable(unittest.TestCase):
    """Testing using circuits from MQTBench. The following aren't currently
    proper tests, they just confirm that no errors are raised"""
    def setUp(self):
        self.directory_path = ('/home/kenny/coding_projects/dqc_simulation/' + 
                          'MQT_benchmarking_circuits/scalable_5to10_qubits/')
        
    def _get_dqc_circuit(self, filename):
        filepath = self.directory_path + filename
        ast = qasm2ast(filepath)
        dqc_circuit = ast2sim_readable(ast)
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
        
    def test_portfolioqaoa_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('portfolioqaoa_indep_qiskit_5.qasm')
        #RAISES ERROR because rzz is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
    def test_portfoliovqe_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('portfoliovqe_indep_qiskit_5.qasm')
    
    def test_qaoa_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qaoa_indep_qiskit_5.qasm')
        #RAISES ERROR because rzz is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_qft_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qft_indep_qiskit_5.qasm')
        #RAISES ERROR because swap gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
    
    def test_qftentangled_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qftentangled_indep_qiskit_5.qasm')
        #RAISES ERROR because swap gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_qnn_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qnn_indep_qiskit_5.qasm')

    def test_qpeexact_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qpeexact_indep_qiskit_5.qasm')
        #RAISES ERROR because swap gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_qpeinexact_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qpeinexact_indep_qiskit_5.qasm')
        #RAISES ERROR because swap gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_qwalk_noancilla_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qwalk-noancilla_indep_qiskit_5.qasm')
        #RAISES ERROR because ccx gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_qwalk_v_chain_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('qwalk-v-chain_indep_qiskit_5.qasm')
        #RAISES ERROR because rccx gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this
        
    def test_random_indep_qiskit_5(self):
        dqc_circuit = self._get_dqc_circuit('random_indep_qiskit_5.qasm')
        #RAISES ERROR because rzz gate is not defined in your standard library.
        #I think I will wait until I can define macros with a <gatedecl> to 
        #fix this

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

    #13 of the circuits can run as-is


if __name__ == '__main__':
    unittest.main()
