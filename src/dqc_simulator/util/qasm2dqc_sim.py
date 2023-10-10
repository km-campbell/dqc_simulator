# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 16:17:01 2023

@author: kenny
"""

import abc
import re

import numpy as np
import pandas
import pyparsing as pp
from netsquid.components import instructions as instr

from dqc_simulator.qlib import gates

#Note a key difference between my code and a proper QISKIT parser is that I 
#implement the standard library gates primarily as built in gates (ie, as literals) rather than
#building them from openQASM's two native gate sets as macros whose expansion 
#is deferred until runtime (which is what is
#done by openQASM 2.0). This means that all of my gates are basically
# implemented as native
#gates. This aligns with NetSquid's platform agnostic philosophy. I feel that 
#any breaking down of gates into subroutines, should be done for specific 
#platforms and included in compilation (not just at runtime). All of this means
#I am not parsing openQASM 2.0 but rather directly converting it to something 
#else

class QasmNonTerminal(metaclass=abc.ABCMeta):
    """Abstract base class for QASM non-terminal symbols. I will also add some
    additional implicit ones like maths operations whose terminals are 
    specifically included in the grammar but in reality could all be represented
    as a single non-terminal symbol"""
    
    @abc.abstractmethod
    def make_sim_readable(self, terminal):
        """
        Should be overwritten with method taking same arguments which translates
        the qasm terminal into something intelligible by the target code.

        Parameters
        ----------
        terminal : str
            A QASM terminal symbol.
        """
        raise NotImplementedError

class QasmUnaryop(QasmNonTerminal):
    def __init__(self):
        self.allowed_ops = {'sin' : np.sin,
                            'cos' : np.cos,
                            'tan' : np.tan,
                            'exp' : np.exp,
                            'ln' : np.ln,
                            'sqrt' : np.sqrt}
        
    def make_sim_readable(self, op_terminal):
        """
        Carry out unary operation and output numerical result understandable
        by python
        
        Parameters
        ----------
        op_terminal : str
            A QASM unaryop terminal symbol. Eg, 'tan(1.2)'.
            
        Returns
        --------
        float containing result of operation
        """
        split_op_str = op_str.replace(')', '').split('(')
        self.op_name = split_op_str[0]
        self.op_arg = split_op_str[1]
        return self.allowed_ops[self.op_name](self.op_arg)
        
class QasmMathsExpr(QasmNonTerminal):
    def __init__(self):
        self.maths_ops = {"+" : lambda a, b : a + b, "-" : lambda a, b: a - b,
                          "*" : lambda a, b : a * b, "/" : lambda a, b : a / b,
                          "^" : lambda a, b : a ^ b}
    
    def make_sim_readable(self, op_terminal):
        """
        Carry out basic mathematical operation and output as something 

        Parameters
        ----------
        op_terminal : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        

class QasmMathsTerms():
    """Terminals corresponding to the <exp> non-terminal in the openQASM 2.0
    grammar.
    <id> terms (see https://arxiv.org/abs/1707.03429) are allowed in the
    grammar but are not supported here. Floats are supported but are handled
    elsewhere"""
    def __init__(self, str4conversion=None):
        self.str4conversion = str4conversion
        self.maths_constants = {'pi' : np.pi}
        
    def make_sim_readable(self):
        #maybe make maths_ops class etc and just call the method make_sim_readable
        #defined in those classes
        #could then put float there


class QasmCMD(metaclass=abc.ABCMeta):
    def __init__(self, name, params, cmd_args, valid_cmds, param_constructors,
                 valid_arg_types):
        """
        Parameters
        ----------
        name : str
            The name of the QASM command.
        params : list of str
            Parameters for the QASM command as strings. Further processing may 
            be needed to convert them to the final datatype given in 
            valid_param_types
        cmd_args : type from valid_arg_types
            Arguments to the QASM command.
        valid_cmds : dict or 1d-array of str
            All of the valid commands. For many subclasses, this should contain
            an appropriate translation into python, eg this is true of the 
            GateOp subclass.
        valid_param_types : dict or 1d-array
            DESCRIPTION.
        valid_arg_types : dict or 1d-array
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.name = name
        self.params = params
        self.cmd_args = cmd_args 
        self.valid_cmds = valid_cmds #will be different for different subclasses
        self.param_constructors = param_constructors #will be different for different subclasses
        self.valid_arg_types = valid_arg_types #will be different for different subclasses

# =============================================================================
#     def check_cmd(self):
#         if self.name in self.valid_cmds:
#             pass
#         else:
#             raise ValueError(f"{self.name} is not recognised as valid qasm "
#                              "command (terminal)")
# =============================================================================
         
# =============================================================================
#     def check_args(self):
#         #checking if cmd_arg is of type in valid_arg_types
#         for cmd_arg in self.cmd_args:
#             valid = any(isinstance(cmd_arg, valid_arg_type) for valid_arg_type in self.valid_arg_types)
#             if valid == False:
#                 raise TypeError(f"{cmd_arg} is not a valid argument to the "
#                                 "{self.name} qasm command")
#             
#     def check_params(self):
#         #checking if param is of type in valid_param_types
#         for param in self.params:
#             valid = any(isinstance(param, valid_param_type) for valid_param_type in self.valid_param_types)
#             if valid == False:
#                 raise TypeError(f"{param} is not a valid parameter for the "
#                                 "{self.name} qasm command")
#                 
#     def validate_qasm_line(self):
#         self.check_cmd()
#         self.check_args()
#         self.check_params()
# =============================================================================
    
    @abc.abstractmethod
    def make_sim_readable(self):
        """Should be overwritten with method which translates the qasm command
        into something intelligible by the target code."""
        raise NotImplementedError
        
    
        
class GateOp(QasmCMD):
    """A quantum gate operation.
        name : str
            The name of the QASM command.
        params : type from param_constructors
            Parameters for the QASM command.
        cmd_args : type from valid_arg_types
            Arguments to the QASM command.
        valid_cmds : dict 
            A dictionary of command names (qopt in the qasm grammar) in qasm
            and the corresponding gate instructions in NetSquid or 
            dqc_simulator.
        valid_arg_types : dict or 1d-array
            DESCRIPTION.
    """
    def __init__(self, name, params, cmd_args, valid_cmds, 
                 valid_arg_types):
        super().__init__(name, params, cmd_args, valid_cmds,  
                         valid_arg_types)
        #renaming for clarity about what is expected from it (which differs 
        #from parent class).
        self.qasm2python_gate_dict = self.valid_cmds 
        self.param_constructors = [float, ] #FINISH

    def _get_gate_cmd(self):
        if self.params == None:
            gate_cmd = self.qasm2python_gate_dict[self.name]
        else:
            for param_constructor in param_constructors:
                try:
                    self.params = [param_constructor(param) for param in self.params]
                    gate_cmd = self.qasm2python_gate_dict[self.name](*self.params)
                except ValueError:
                    pass #does nothing if the error raised is a ValueError
    
    def _split_arg_name_from_index(arg):
        split_arg = arg.remove(']').split('[')
        arg_reg = split_arg[0]
        arg_qindex = int(split_arg)
        return arg_reg, arg_qindex
    
    def _handle_single_qubit_gate(gate_name, params, gate_args, gate_list,
                                  qasm2python_gate_dict, registers):
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
    def translate(self):

        
#I think that what I want to do is make all types of bracket (ie, [] and ()) 
#merge into the previous word (alphanumeric sequence with no whitespace between
#characters) and then simply split the overall QASM line into a list of these 
#merged words. 

def remove_param_spaces(string):
    #want to find all words that are between brackets and remove whitespace.
    #This means they will be part of the previous word and are easier to handle
    #on a case by case basis
    #I think you will need regex (python package reg) for this
    pattern = regex.compile(r'\[ #[ character
                           (?:', re.VERBOSE) #FINISH!
    
# =============================================================================
#     if '(' in string:
#         num_open_brackets = string.count('(')
#         for ii in range(num_open_brackets):
#             open_bracket_pos = string.find('(')
# =============================================================================
            

def tokenize_line():
    """The basic idea here is to split a line into a command (or first word as
    this includes things like the word OPENQASM) and arguments.
    The command may have parameters, which for now will be kept together in 
    a block with the command."""
    lpar = pp.Literal('(').suppress()
    rpar = pp.Literal(')').suppress()
    l_sqr_brace = pp.Literal('[').suppress()
    r_sqr_brace = pp.Literal(']').suppress()
    idQasm = pp.Regex(r'[a-z][A-Za-z0-9]*') # id from https://arxiv.org/abs/1707.03429
    real = pp.Regex(r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?')
    nninteger = pp.Regex(r'[1-9]+[0-9]*|0')
    arith_op = pp.one_of(['+', '-', '*', '/', '^'])
# =============================================================================
#     exp_num_or_word = real | nninteger | pi | idQasm  
# =============================================================================
# =============================================================================
#     params =  pp.original_text_for(pp.nested_expr) #anything (including more
# =============================================================================
                                                   #nested brackets) inside 
                                                   #parentheses
    reg_index_slice = l_sqr_brace + nninteger + r_sqr_brace
    decl =  (pp.Keyword('qreg') + idQasm + reg_index_slice |
             pp.Keyword('creg') + idQasm + reg_index_slice ) 
    unaryop = pp.one_of(['sin', 'cos', 'tan', 'exp', 'ln', 'sqrt'])
    expQasm = real ^ nninteger ^ pp.Keyword('pi') ^ idQasm 
    expQasm = expQasm ^ expQasm + arith_op + expQasm
    expQasm = expQasm ^ lpar + expQasm + rpar
    expQasm = expQasm ^ unaryop + lpar + expQasm + rpar
    #allowing arithmetic operations on this more complete definition
    expQasm = expQasm ^ expQasm + arith_op + expQasm 
    
    # It may actually be easiest to implement the entire Backus Naur form for 
    # (simply using if pass statements for comments and the header and then
    # have literals acting on certain sequences of code do certain things in
    # the manner you were starting to do with classes. I think for now it is 
    # best to simply pass the barrier literal. You can always implement it later
    # when how you will partition your circuit is clearer but you are not trying
    # to support all of openQASM 2.0, just the bits used to create a logical
    # circuit. Compilation etc, will happen after parsing. 
    # In short your parser will have the structure 
    # for line in file
    #   tokenize_line(line)
    #   
    #That said, I think that, initially, you should only support <decl> and 
    #<uop>


#OK: now that you have found nuqasm2 I think that you should let this create an
#AST and then act on that AST. You will most likely need to parse elements from
#op_reg_list, to extract the index from the register name.
    

#TO DO: make GateDecl class and many other classes inheriting from QasmCMD
#These classes are essentially taking the place of first_word in the if loops
#below 

#TO DO: refactor below to be in terms of classes so that you don't have so many
#if else loops.
def qasm2sim_readable(filepath):
    registers = dict()
    qasm2python_gate_dict = {"U" : gates.INSTR_U,
                             "CX" : instr.INSTR_CNOT}
    #implementing functions from <exp> in openQASM 2.0's grammar
    exp_dict = {"pi" : np.pi, "exp" : np.exp}
    
        
    
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
            word_list = line.split() #TO DO: replace with something using pyparsers parse_string
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
            elif first_word == 'include':
                #standard header is so ubiquitous that it makes sense to handle
                #it as its own case
                if word_list[1] == "qelib1.inc":
                    standard_lib = {"u3" : gates.INSTR_U,
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
                    qasm2python_gate_dict.update(standard_lib) 
                else:
                    pass #TO DO: add ability to include files
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
                    pass #TO DO: NEED TO IMPLEMENT something here
                    
    return gate_list
                    
                        
                            
                                    
                            
                    
                    
                    
        #do not need to close file if you use 'with open()' rather than just
        #'open()'
                    
                           
#TO DO: GENERALISE code by fixing WARNING comments

#TO DO:FIGURE out how to handle case where different qregs are on the same node and so 
#the qreg name does not correspond to the node name, like you have been assuming.
#This can be done at the end (potentially in the compiler) but if not in a 
#post-processing step where the number of different qregs is evaluated and they
#are assigned to nodes. In cases where there is only 1 qreg, you can automatically
#say the circuit is monolithic.

#TO DO: add ability to handle include statements
            
            
            
#Cases not handled:
#   1) Where bracket is 
            