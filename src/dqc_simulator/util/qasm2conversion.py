# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 16:17:01 2023

@author: kenny
"""

import numpy as np
import pandas
from netsquid.components import instructions as instr

from dqc_simulator.qlib import gates

#Note a key difference between my code and a proper QISKIT parser is that I 
#implement the standard library gates primarily as built in gates rather than
#building them from openQASM's two native gate sets as macros whose expansion 
#is deferred until runtime (which is what is
#done by openQASM 2.0). This means that all of my gates are basically
# implemented as native
#gates. This aligns with NetSquid's platform agnostic philosophy. I feel that 
#any breaking down of gates into subroutines, should be done for specific 
#platforms and included in compilation (not just at runtime)

def qasm2sim_readable(filepath):
    registers = dict()
    qasm2python_gate_dict = {"U" : gates.INSTR_U,
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
    
    def _get_gate_cmd(gate_name, params):
        if params == None:
            gate_cmd = qasm2python_gate_dict[gate_name]
        else:
            params = [float(ii) for ii in params]
            #WARNING: above line assumes params is list of 
            #numeric strings. This is a limiting assumption but 
            #should work for MQT Bench produced .qasm files.
            gate_cmd = qasm2python_gate_dict[gate_name](*params)
    
    def _split_arg_name_from_index(arg):
        split_arg = arg.remove(']').split('[')
        arg_reg = split_arg[0]
        arg_qindex = int(split_arg1)
        return arg_reg, arg_qindex
    
    def _handle_single_qubit_gate(gate_name, params, gate_args, gate_list):
        """
        Handle single qubit gates

        Parameters
        ----------
        gate_name : str
            Name of gate.
        params : list of str or None
            The parameters for the gate.
        gate_args : str
            The QASM arguments (qubit or qubit register) for the gate.
        gate_list : list of tuples or empty list
            List of tuples describing quantum gates.
        qasm2python_gate_dict : dict
            The names of openQASM 2.0 native and standard header gates and the 
            corresponding NetSquid/dqc_simulator instruction (where dqc_simulator
            is the placeholder name for my package)
        registers : dict
            The names of the quantum  and classical registers and the number of 
            qubits/bits each register holds

        Returns
        -------
        gate_list : list of tuples or empty list
            List of tuples describing quantum gates.

        """
        arg = gate_args[0]
        if '[' in arg: #arg is individual qubit
            qreg_name, qubit_index = _split_arg_name_from_index(arg)
            gate_list.append(
                    (_get_gate_cmd(gate_name, params), 
                     qubit_index, qreg_name))
        else: #arg is register of qubits
            qreg_name = arg
            for qubit_index in range(registers[qreg_name]):
                gate_list.append(
                    (_get_gate_cmd(gate_name, params), 
                     qubit_index, qreg_name))
        return gate_list
    
    def _handle_two_qubit_gate(gate_name, params, gate_args, gate_list,
                                  qasm2python_gate_dict, registers):
        arg1 = gate_args[0]
        arg2 = gate_args[1]
        if '[' in arg1 and '[' in arg2:
            arg1_reg, arg1_qindex = _split_arg_name_from_index(arg1)
            arg2_reg, arg2_qindex = _split_arg_name_from_index(arg2)
            gate_list.append(
                    (_get_gate_cmd(gate_name, params), arg1_qindex, 
                     arg1_reg, arg2_qindex, arg2_reg))
        elif '[' not in arg1 and '[' not in arg2:
            if registers[arg1] != registers[arg2]:
                raise ValueError("registers {arg1} and {arg2} have different "
                                 f" sizes. Their sizes are {registers[arg1]} "
                                 f"and {registers[arg2]}, respectively.")
            else:
                for ii in range(registers[arg2]):
                    gate_list.append(
                        (_get_gate_cmd(gate_name, params), ii, arg1, ii, arg2))
        elif '[' in arg1 and '[' not in arg2:
            arg1_reg, arg1_qindex = _split_arg_name_from_index(arg1)
            for ii in range(registers[arg2]):
                gate_list.append(
                    (_get_gate_cmd(gate_name, params), arg1_qindex, arg1_reg, 
                     ii, arg2))
        elif '[' not in arg1 and '[' in arg2:
            arg2_reg, arg2_qindex = _split_arg_name_from_index(arg2)
            for ii in range(registers[arg1]):
                gate_list.append(
                    (_get_gate_cmd(gate_name, params), ii, arg1, arg2_qindex,
                     arg2_reg))
                
                
    with open(filepath, 'r') as file:
        
        for line in file:
            word_list = line.split()
            first_word = word_list[0]
            params = None
            gate_list = []
            if '(' in first_word:
                split_first_word = first_word.split('(', 1)
                first_word = split_first_word[0]
                params = split_first_word[1].replace(')', '').split(',') #params should now be list of parameters 
            if first_word == 'OPENQASM':
                pass
            elif first_word == '//':
                pass
            elif first_word == 'qreg' or first_word == 'creg':
                reg_def = word_list[1].split('[')
                reg_name = reg_def[0]
                reg_size = reg_def[1].split(']')[0]
                registers[reg_name] = int(reg_size)
            elif first_word == 'barrier':
                pass #TO DO: replace pass with relevant code
            elif first_word == 'measure':
                pass #TO DO: replace pass with relevant code
            elif first_word in qasm2python_gate_dict: #first_word is quantum gate
                gate_args = word_list[1::]
                if len(gate_args) == 1:
                    _handle_single_qubit_gate(first_word, params, gate_args,
                                              gate_list, qasm2python_gate_dict,
                                              registers)
                elif len(gate_args) == 2:
                    _handle_two_qubit_gate(first_word, params, gate_args, 
                                           gate_list, qasm2python_gate_dict, 
                                           registers)
                elif first_word == "ccx":
                    #FINISH
                    
                    
                        
                            
                                    
                            
                    
                    
                    
        #do not need to close file if you use 'with open()' rather than just
        #'open()'
                    
                           
#TO DO: GENERALISE code by fixing WARNING comments

#TO DO:FIGURE out how to handle case where different qregs are on the same node and so 
#the qreg name does not correspond to the node name, like you have been assuming.
#This can be done at the end (potentially in the compiler) but if not in a 
#post-processing step where the number of different qregs is evaluated and they
#are assigned to nodes. In cases where there is only 1 qreg, you can automatically
#say the circuit is monolithic.
            
            
            