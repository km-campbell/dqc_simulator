# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 16:17:01 2023

@author: kenny
"""

#NOTE: this module uses code written by pyparsing module author Paul McGuire
#(https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py)
#in accordance with the MIT license. This is marked with an appropriate comment
#at the relevant points in the script.

import abc
import re
import operator

import numpy as np
import pandas
import pyparsing as pp
from netsquid.components import instructions as instr

from dqc_simulator.qlib import gates
from dqc_simulator.util.qasm2ast import qasm2ast, ASTType

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

#useful parsing terms
class QasmParsingElement():
    """ParsingElement defined using the pyparsing package with some additional
    more specific methods"""
    def __init__(self):
        pass
    lpar = pp.Literal('(').suppress()
    rpar = pp.Literal(')').suppress()
    l_sqr_brace = pp.Literal('[').suppress()
    r_sqr_brace = pp.Literal(']').suppress()
    idQasm = pp.Regex(r'[a-z][A-Za-z0-9]*') # id from https://arxiv.org/abs/1707.03429
    real = pp.Regex(r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?')
    nninteger = pp.Regex(r'[1-9]+[0-9]*|0')
    #bidmas
    number = real | nninteger | pp.Keyword('pi') 
    arith_op = pp.one_of(['+', '-', '*', '/', '^'])
    unaryop = pp.one_of(['sin', 'cos', 'tan', 'exp', 'ln', 'sqrt'])
# =============================================================================
#     exp_num_or_word = real | nninteger | pi | idQasm  
# =============================================================================
# =============================================================================
#     params =  pp.original_text_for(pp.nested_expr) #anything (including more
# =============================================================================
                                                   #nested brackets) inside 
                                                   #parentheses
# =============================================================================
#     reg_index_slice = l_sqr_brace + nninteger + r_sqr_brace
#     decl =  (pp.Keyword('qreg') + idQasm + reg_index_slice |
#              pp.Keyword('creg') + idQasm + reg_index_slice ) 
# =============================================================================
# =============================================================================
#     atom = number | pp.Keyword('pi') 
#     exp_ops = [('-', 1, pp.OpAssoc.LEFT), ('^', 2, pp.OpAssoc.RIGHT), 
#                  (pp.one_of(['*', '/']), 2, pp.OpAssoc.LEFT),
#                  (pp.one_of(['+', '-']), 2, pp.OpAssoc.LEFT), 
#                  (unaryop, 1, pp.OpAssoc.LEFT)]
#     exp_qasm = pp.infix_notation(atom, exp_ops, '(', ')')
# =============================================================================
    # use CaselessKeyword for e and pi, to avoid accidentally matching
    # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
    # and CaselessKeyword only match whole words
    
class ExpQasm(QasmParsingElement):
    #slightly modifying code written by pyparsing module author Paul McGuire
    #(https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py)
    #in accordance with the MIT license:
    def __init__(self):
        self.exp_qasmStack = []
        
    def _push_first(self, toks):
        self.exp_qasmStack.append(toks[0])

    def _push_unary_minus(self, toks):
        for t in toks:
            if t == "-":
                self.exp_qasmStack.append("unary -")
            else:
                break
        
    def _insert_fn_argcount_tuple(self, t):
        fn = t.pop(0)
        num_args = len(t[0])
        t.insert(0, (fn, num_args))
        
    def define_grammar(self):
        pi = pp.CaselessKeyword("pi")
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = pp.Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        ident = pp.Word(pp.alphas, pp.alphanums + "_$")
    
        plus, minus, mult, div = map(pp.Literal, "+-*/")
        addop = plus | minus
        multop = mult | div
        expop = pp.Literal("^")
    
        exp_qasm = pp.Forward()
        exp_qasm_list = pp.delimitedList(pp.Group(exp_qasm))
        # add parse action that replaces the function identifier with a (name, number of args) tuple

    
        fn_call = (ident + self.lpar - exp_qasm + self.rpar).setParseAction(
            self._insert_fn_argcount_tuple
        )
        atom = (
            addop[...]
            + (
                (fn_call | pi | fnumber | ident).setParseAction(self._push_first)
                | pp.Group(self.lpar + exp_qasm + self.rpar)
            )
        ).setParseAction(self._push_unary_minus)
    
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = pp.Forward()
        factor <<= atom + (expop + factor).setParseAction(self._push_first)[...]
        term = factor + (multop + factor).setParseAction(self._push_first)[...]
        exp_qasm <<= term + (addop + term).setParseAction(self._push_first)[...]
        return exp_qasm
    #END of code modified from
    #https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py
 
    
# =============================================================================
#     arith_expr = pp.infix_notation(exp_qasm, arith_ops, '(', ')')
#     unary_op_acting = pp.Group(unaryop + lpar + exp_qasm + rpar)
# # =============================================================================
# #     atom = arith_expr | unary_op_acting | number
# # =============================================================================
#     atom = number | arith_expr | unary_op_acting
#     exp_qasm <<= atom 
# =============================================================================
# =============================================================================
#     exp_qasm = unary_op_acting ^ expr_or_number
# =============================================================================
    #facilitating arithmatic combinations of exp_qasm terms:
# =============================================================================
#     exp_qasm = pp.infix_notation(exp_qasm, arith_ops, '(', ')')
# =============================================================================


class NonTerminalInterpreter(QasmParsingElement, metaclass=abc.ABCMeta):   
    @abc.abstractmethod
    def interpret(self, unparsed_terminal_token):
        """
        Should be overwritten with a method interpretting an unparsed string
        corresponding to a terminal token. The terminal token should be of a
        specific non-terminal type, which should be indicated in the subclass 
        name.
        
        Parameters
        ----------
        unparsed_terminal_token : str
            An unparsed string corresponding to a terminal token. The terminal 
            token should be of a specific non-terminal type, which should be 
            indicated in the subclass name.

        Raises
        ------
        NotImplementedError
            Error for if this method is not overwritten.
        """
        raise NotImplementedError("This method should be overwritten when "
                                  "defining a subclass.")
    
class ExpQasmInterpreter(NonTerminalInterpreter):
    def __init__(self):
        pass #just defining the class instance as self
    unaryop_funcs = {'sin' : np.sin, 'cos' : np.cos,'tan' : np.tan,
                     'exp' : np.exp, 'ln' : np.log, 'sqrt' : np.sqrt}
        
    arith_op_funcs = opn = {
                            "+": operator.add,
                            "-": operator.sub,
                            "*": operator.mul,
                            "/": operator.truediv,
                            "^": operator.pow,
                            }
        
# =============================================================================
#     def _do_nothing(self):
#         """A function that does the identity transformation (that is to say 
#         nothing)"""
#         pass
# =============================================================================
    
    def _evaluate_stack(self, s):
        #modifying code written by pyparsing module author Paul McGuire
        #(https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py)
        #in accordance with the MIT license:
        op, num_args = s.pop(), 0
        if isinstance(op, tuple):
            op, num_args = op
        if op == "unary -":
            return -self._evaluate_stack(s)
        if op in self.arith_op_funcs:
            # note: operands are pushed onto the stack in reverse order
            op2 = self._evaluate_stack(s)
            op1 = self._evaluate_stack(s)
            return self.arith_op_funcs[op](op1, op2)
        elif op == "pi":
            return np.pi  # 3.1415926535
        elif op in self.unaryop_funcs:
            # note: args are pushed onto the stack in reverse order
            args = reversed([self._evaluate_stack(s) for _ in range(num_args)])
            return self.unaryop_funcs[op](*args)
        elif op[0].isalpha():
            raise Exception("invalid identifier '%s'" % op)
        else:
            return float(op)
        #END of code modified from 
        #https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py
    
    def interpret(self, exp_qasm_string):
        exp_qasm = ExpQasm()
        exp_qasm_grammar = exp_qasm.define_grammar()
        #The 'ParseAction's a added to the parse_string method in what follows
        #cause it to update the exp_qasmStack
        exp_qasm_grammar.parse_string(exp_qasm_string, parseAll=True)
        return self._evaluate_stack(exp_qasm.exp_qasmStack[:])
        
# =============================================================================
#         #implementing temporary stop-gap approach which ignores most exp_qasm
#         #possibilities
#         if exp_qasm_string == 'pi':
#             exp_qasm_expr = np.pi
#         else:
#             exp_qasm_expr = float(exp_qasm_string)
#         return exp_qasm_expr
#             #TO DO: allow interpretation of any <exp> token defined in the 
#             #openQASM 2.0 paper. See the commented out blocks below for your 
#             #initial attempts
# =============================================================================
# =============================================================================
#         tokens = exp_qasm_token.parse_string(exp_qasm_string)
#         prev_token = None
#         ii = 0
#         op_stack = []
#         num_stack = []
#         #using modified Shunting-yard algorithm 
#         #(see https://inspirnathan.com/posts/155-handling-unary-operations-with-shunting-yard-algorithm/ 
#         #and https://en.wikipedia.org/wiki/Shunting_yard_algorithm#The_algorithm_in_detail)
#         while tokens: #while there are tokens to be read
#             token = tokens[ii]
#             if token == self.number: #due to defi
#                 num_stack.append(token)
#             elif token == self.unaryop:
#                 op_stack.append(token)
#             elif token == arith_op:
#                 while 
# =============================================================================
# =============================================================================
#         parsed_exp_qasm = self.exp_qasm.parse_string(exp_qasm_string)
#         #checking there is only one parameter in param_string
#         if len(parsed_exp_qasm) != 1:
#             raise ValueError(f"{exp_qasm_string} is not the string of a single"
#                              " exp_qasm expression")
#         parsed_exp_qasm = parsed_exp_qasm[0]
#         num_stack = []
#         unaryop_func = self._do_nothing
#         arith_op_func = self._do_nothing
#         for expr in parsed_exp_qasm: #could be terminal token or list
#             if expr == unaryop:
#                 unary_op_name = terminal
#                 unaryop_func = self.unaryop_funcs[unary_op_name]
#             for terminal in expr:
#                 for non_terminal in handler_funcs4non_terminals:
#                     if terminal == self.number:
#                         num_stack.append(number)
#                     elif terminal == self.unaryop:
#                         unary_op_name = terminal
#                         unaryop_func = self.unaryop_funcs[unary_op_name]
#                     elif terminal == self.arithmetic_op: 
#                     #if terminal token is example of non-terminal token 
#                     #(non_terminal will be pyparsing.one_of object):
#                         handler_func = handler_funcs4non_terminals[non_terminal]
#                         evaluated_expr = handler_func(terminal, parsed_exp_qasm)
#                         number = unaryop_func(arith_op_func(evaluated_expr))
#                 #evaluate expr here to convert it to number
#                 unaryop_func = self._do_nothing
#                 arith_op_func = self._do_nothing
#                 
#                 #want numerical value (float) of evaluated expression as  
#                 #overall output from the interpret method.
# =============================================================================
                    
class ArgumentInterpreter(NonTerminalInterpreter):
    def parse_argument_non_terminal(self, argument_terminal):
        """
        Tokenizes the <argument> non-terminal from the grammar specified in
        the openQASM 2.0 paper (https://arxiv.org/abs/1707.03429)
    
        Parameters
        ----------
        argument_terminal : str
            A string contain some terminal token which is an example of the 
            <argument> non-terminal defined in the openQASM 2.0 paper
            (https://arxiv.org/abs/1707.03429).
    
        Returns
        ------
        reg_name : str
            The name of a register (creg or qreg).
        bit_index : None or int
            If argument_terminal represents a (qu)bit, this is the index of 
            that (qu)bit
    
        """
        
        bit_index = None
        if '[' in argument_terminal: #is (qu)bit
            split_bit = argument_terminal.replace(']', '').split('[')
            reg_name = split_bit[0]
            bit_index = split_bit[1]
        elif '[' not in argument_terminal: 
            reg_name = argument_terminal
        return reg_name, bit_index
    
    def interpret(self, argument_terminal): 
        reg_name, bit_index = self.parse_argument_non_terminal(argument_terminal)
        bit_index = int(bit_index)
        return [bit_index, reg_name]
        

# =============================================================================
# class QasmNonTerminal(metaclass=abc.ABCMeta):
#     """Abstract base class for QASM non-terminal symbols. I will also add some
#     additional implicit ones like maths operations whose terminals are 
#     specifically included in the grammar but in reality could all be represented
#     as a single non-terminal symbol"""
#     
#     @abc.abstractmethod
#     def make_sim_readable(self, terminal):
#         """
#         Should be overwritten with method taking same arguments which translates
#         the qasm terminal into something intelligible by the target code.
# 
#         Parameters
#         ----------
#         terminal : str
#             A QASM terminal symbol.
#         """
#         raise NotImplementedError
# 
# class QasmUnaryop(QasmNonTerminal):
#     def __init__(self):
#         self.allowed_ops = {'sin' : np.sin,
#                             'cos' : np.cos,
#                             'tan' : np.tan,
#                             'exp' : np.exp,
#                             'ln' : np.ln,
#                             'sqrt' : np.sqrt}
#         
#     def make_sim_readable(self, op_terminal):
#         """
#         Carry out unary operation and output numerical result understandable
#         by python
#         
#         Parameters
#         ----------
#         op_terminal : str
#             A QASM unaryop terminal symbol. Eg, 'tan(1.2)'.
#             
#         Returns
#         --------
#         float containing result of operation
#         """
#         split_op_str = op_str.replace(')', '').split('(')
#         self.op_name = split_op_str[0]
#         self.op_arg = split_op_str[1]
#         return self.allowed_ops[self.op_name](self.op_arg)
#         
# class QasmMathsExpr(QasmNonTerminal):
#     def __init__(self):
#         self.maths_ops = {"+" : lambda a, b : a + b, "-" : lambda a, b: a - b,
#                           "*" : lambda a, b : a * b, "/" : lambda a, b : a / b,
#                           "^" : lambda a, b : a ^ b}
#     
#     def make_sim_readable(self, op_terminal):
#         """
#         Carry out basic mathematical operation and output as something 
# 
#         Parameters
#         ----------
#         op_terminal : TYPE
#             DESCRIPTION.
# 
#         Returns
#         -------
#         None.
# 
#         """
#         
# 
# class QasmMathsTerms():
#     """Terminals corresponding to the <exp> non-terminal in the openQASM 2.0
#     grammar.
#     <id> terms (see https://arxiv.org/abs/1707.03429) are allowed in the
#     grammar but are not supported here. Floats are supported but are handled
#     elsewhere"""
#     def __init__(self, str4conversion=None):
#         self.str4conversion = str4conversion
#         self.maths_constants = {'pi' : np.pi}
#         
#     def make_sim_readable(self):
#         #maybe make maths_ops class etc and just call the method make_sim_readable
#         #defined in those classes
#         #could then put float there
# 
# 
# class QasmCMD(metaclass=abc.ABCMeta):
#     def __init__(self, name, params, cmd_args, valid_cmds, param_constructors,
#                  valid_arg_types):
#         """
#         Parameters
#         ----------
#         name : str
#             The name of the QASM command.
#         params : list of str
#             Parameters for the QASM command as strings. Further processing may 
#             be needed to convert them to the final datatype given in 
#             valid_param_types
#         cmd_args : type from valid_arg_types
#             Arguments to the QASM command.
#         valid_cmds : dict or 1d-array of str
#             All of the valid commands. For many subclasses, this should contain
#             an appropriate translation into python, eg this is true of the 
#             GateOp subclass.
#         valid_param_types : dict or 1d-array
#             DESCRIPTION.
#         valid_arg_types : dict or 1d-array
#             DESCRIPTION.
# 
#         Returns
#         -------
#         None.
# 
#         """
#         self.name = name
#         self.params = params
#         self.cmd_args = cmd_args 
#         self.valid_cmds = valid_cmds #will be different for different subclasses
#         self.param_constructors = param_constructors #will be different for different subclasses
#         self.valid_arg_types = valid_arg_types #will be different for different subclasses
# 
# # =============================================================================
# #     def check_cmd(self):
# #         if self.name in self.valid_cmds:
# #             pass
# #         else:
# #             raise ValueError(f"{self.name} is not recognised as valid qasm "
# #                              "command (terminal)")
# # =============================================================================
#          
# # =============================================================================
# #     def check_args(self):
# #         #checking if cmd_arg is of type in valid_arg_types
# #         for cmd_arg in self.cmd_args:
# #             valid = any(isinstance(cmd_arg, valid_arg_type) for valid_arg_type in self.valid_arg_types)
# #             if valid == False:
# #                 raise TypeError(f"{cmd_arg} is not a valid argument to the "
# #                                 "{self.name} qasm command")
# #             
# #     def check_params(self):
# #         #checking if param is of type in valid_param_types
# #         for param in self.params:
# #             valid = any(isinstance(param, valid_param_type) for valid_param_type in self.valid_param_types)
# #             if valid == False:
# #                 raise TypeError(f"{param} is not a valid parameter for the "
# #                                 "{self.name} qasm command")
# #                 
# #     def validate_qasm_line(self):
# #         self.check_cmd()
# #         self.check_args()
# #         self.check_params()
# # =============================================================================
#     
#     @abc.abstractmethod
#     def make_sim_readable(self):
#         """Should be overwritten with method which translates the qasm command
#         into something intelligible by the target code."""
#         raise NotImplementedError
#         
#     
#         
# class GateOp(QasmCMD):
#     """A quantum gate operation.
#         name : str
#             The name of the QASM command.
#         params : type from param_constructors
#             Parameters for the QASM command.
#         cmd_args : type from valid_arg_types
#             Arguments to the QASM command.
#         valid_cmds : dict 
#             A dictionary of command names (qopt in the qasm grammar) in qasm
#             and the corresponding gate instructions in NetSquid or 
#             dqc_simulator.
#         valid_arg_types : dict or 1d-array
#             DESCRIPTION.
#     """
#     def __init__(self, name, params, cmd_args, valid_cmds, 
#                  valid_arg_types):
#         super().__init__(name, params, cmd_args, valid_cmds,  
#                          valid_arg_types)
#         #renaming for clarity about what is expected from it (which differs 
#         #from parent class).
#         self.qasm2python_gate_dict = self.valid_cmds 
#         self.param_constructors = [float, ] #FINISH
# 
#     def _get_gate_cmd(self):
#         if self.params == None:
#             gate_cmd = self.qasm2python_gate_dict[self.name]
#         else:
#             for param_constructor in param_constructors:
#                 try:
#                     self.params = [param_constructor(param) for param in self.params]
#                     gate_cmd = self.qasm2python_gate_dict[self.name](*self.params)
#                 except ValueError:
#                     pass #does nothing if the error raised is a ValueError
#     
#     def _split_arg_name_from_index(arg):
#         split_arg = arg.remove(']').split('[')
#         arg_reg = split_arg[0]
#         arg_qindex = int(split_arg)
#         return arg_reg, arg_qindex
#     
#     def _handle_single_qubit_gate(gate_name, params, gate_args, gate_list,
#                                   qasm2python_gate_dict, registers):
#         """
#         Handle single qubit gates
# 
#         Parameters
#         ----------
#         gate_name : str
#             Name of gate.
#         params : list of str or None
#             The parameters for the gate.
#         gate_args : str
#             The QASM arguments (qubit or qubit register) for the gate.
#         gate_list : list of tuples or empty list
#             List of tuples describing quantum gates.
#         qasm2python_gate_dict : dict
#             The names of openQASM 2.0 native and standard header gates and the 
#             corresponding NetSquid/dqc_simulator instruction (where dqc_simulator
#             is the placeholder name for my package)
#         registers : dict
#             The names of the quantum  and classical registers and the number of 
#             qubits/bits each register holds
# 
#         Returns
#         -------
#         gate_list : list of tuples or empty list
#             List of tuples describing quantum gates.
# 
#         """
#         arg = gate_args[0]
#         if '[' in arg: #arg is individual qubit
#             qreg_name, qubit_index = _split_arg_name_from_index(arg)
#             gate_list.append(
#                     (_get_gate_cmd(gate_name, params), 
#                      qubit_index, qreg_name))
#         else: #arg is register of qubits
#             qreg_name = arg
#             for qubit_index in range(registers[qreg_name]):
#                 gate_list.append(
#                     (_get_gate_cmd(gate_name, params), 
#                      qubit_index, qreg_name))
#         return gate_list
#     def translate(self):
# =============================================================================

        

    

#I think that what I want to do is make all types of bracket (ie, [] and ()) 
#merge into the previous word (alphanumeric sequence with no whitespace between
#characters) and then simply split the overall QASM line into a list of these 
#merged words. 

# =============================================================================
# def remove_param_spaces(string):
#     #want to find all words that are between brackets and remove whitespace.
#     #This means they will be part of the previous word and are easier to handle
#     #on a case by case basis
#     #I think you will need regex (python package reg) for this
#     pattern = regex.compile(r'\[ #[ character
#                            (?:', re.VERBOSE) #FINISH!
#     
# # =============================================================================
# #     if '(' in string:
# #         num_open_brackets = string.count('(')
# #         for ii in range(num_open_brackets):
# #             open_bracket_pos = string.find('(')
# # =============================================================================
#             
# 
# def tokenize_line():
#     """The basic idea here is to split a line into a command (or first word as
#     this includes things like the word OPENQASM) and arguments.
#     The command may have parameters, which for now will be kept together in 
#     a block with the command."""
#     lpar = pp.Literal('(').suppress()
#     rpar = pp.Literal(')').suppress()
#     l_sqr_brace = pp.Literal('[').suppress()
#     r_sqr_brace = pp.Literal(']').suppress()
#     idQasm = pp.Regex(r'[a-z][A-Za-z0-9]*') # id from https://arxiv.org/abs/1707.03429
#     real = pp.Regex(r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?')
#     nninteger = pp.Regex(r'[1-9]+[0-9]*|0')
#     arith_op = pp.one_of(['+', '-', '*', '/', '^'])
# # =============================================================================
# #     exp_num_or_word = real | nninteger | pi | idQasm  
# # =============================================================================
# # =============================================================================
# #     params =  pp.original_text_for(pp.nested_expr) #anything (including more
# # =============================================================================
#                                                    #nested brackets) inside 
#                                                    #parentheses
#     reg_index_slice = l_sqr_brace + nninteger + r_sqr_brace
#     decl =  (pp.Keyword('qreg') + idQasm + reg_index_slice |
#              pp.Keyword('creg') + idQasm + reg_index_slice ) 
#     unaryop = pp.one_of(['sin', 'cos', 'tan', 'exp', 'ln', 'sqrt'])
#     exp_qasm = real ^ nninteger ^ pp.Keyword('pi') ^ idQasm 
#     exp_qasm = exp_qasm ^ exp_qasm + arith_op + exp_qasm
#     exp_qasm = exp_qasm ^ lpar + exp_qasm + rpar
#     exp_qasm = exp_qasm ^ unaryop + lpar + exp_qasm + rpar
#     #allowing arithmetic operations on this more complete definition
#     exp_qasm = exp_qasm ^ exp_qasm + arith_op + exp_qasm 
# =============================================================================
    
# =============================================================================
#     # It may actually be easiest to implement the entire Backus Naur form for 
#     # (simply using if pass statements for comments and the header and then
#     # have literals acting on certain sequences of code do certain things in
#     # the manner you were starting to do with classes. I think for now it is 
#     # best to simply pass the barrier literal. You can always implement it later
#     # when how you will partition your circuit is clearer but you are not trying
#     # to support all of openQASM 2.0, just the bits used to create a logical
#     # circuit. Compilation etc, will happen after parsing. 
#     # In short your parser will have the structure 
#     # for line in file
#     #   tokenize_line(line)
#     #   
#     #That said, I think that, initially, you should only support <decl> and 
#     #<uop>
# 
# =============================================================================

#OK: now that you have found nuqasm2 I think that you should let this create an
#AST and then act on that AST. You will most likely need to parse elements from
#op_reg_list, to extract the index from the register name.


    

class DqcCircuit():
    def __init__(self, qregs, cregs, defined_gates, ops):
        """ 
        Parameters
            ----------
            qregs : dict
                The quantum registers and their associated sizes.
            cregs : dict
                The classical registers and their associated sizes.
            defined_gates : dict
                The gates that are defined (ie, built into QASM or declared with a 
                <gatedecl> in accordance with the QASM grammar - this includes 
                gates defined in external files included using an 'include'
                statement in the .qasm code) and their corresponding instruction
                defined within NetSquid or dqc_simulator.qlib.gates.
            gates : list of tuples
                The operations (such as gates, initialisations or measurements)
                in the quantum circuit written in a way dqc_simulator can 
                understand.

            Returns
            -------
            None.
        """
        self.qregs = qregs
        self.cregs = cregs
        self.defined_gates = defined_gates
        self.ops = ops

class Ast2SimReadable(metaclass=abc.ABCMeta):
    """Abstract base class for various converters to simulation readable 
    commands"""
    def __init__(self, ast_c_sect_element, dqc_circuit):
        """
        Parameters
        ----------
        ast_c_sect_element : dict
            An element of the AST's 'c_sect'. This typically corresponds to a 
            parsed line of .qasm source code but in some rare instances it 
            could be multiple lines
            
        dqc_circuit : instance of DqcCircuit defined above
            The specs need to make a circuit that could run on a DQC (it may
            actually be monolithic but is written in a DQC suitable form)

        Returns
        -------
        None.

        """
        self.ast_c_sect_element = ast_c_sect_element 
        self.dqc_circuit = dqc_circuit

    @abc.abstractmethod
    def make_sim_readable(self):
        """
        Should be overwritten with method taking same arguments which translates
        the qasm terminal into something intelligible by the target code.

        Parameters
        ----------
        terminal : str
            A QASM terminal symbol.
            
        Returns
        -------
        Subclasses should overwrite this method to return an updated instance 
        of the DqcCircuit class
        """
        raise NotImplementedError

class AstUnknown(Ast2SimReadable):
    def make_sim_readable(self):
        raise ValueError(f"Unknown element {self.ast_c_sect_element} "
                         "identified while parsing. There may have been an"
                         " error the .qasm file or a failure to recognise the "
                         "issue when parsing.")
        
class AstComment(Ast2SimReadable):
    def make_sim_readable(self):
        return self.dqc_circuit #This ignores comments in the source code,
             #as they are not needed in the gate_list to be interpreted
        
class AstQreg(Ast2SimReadable):
    def make_sim_readable(self):
        qreg_name = self.ast_c_sect_element['qreg_name']
        qreg_number = self.ast_c_sect_element['qreg_num']
        self.dqc_circuit.qregs[qreg_name] = int(qreg_number)
        return self.dqc_circuit

class AstCreg(Ast2SimReadable):
    def make_sim_readable(self):
        creg_name = self.ast_c_sect_element['creg_name']
        creg_number = self.ast_c_sect_element['creg_num']
        self.dqc_circuit.cregs[creg_name] = int(creg_number)
        return self.dqc_circuit

class AstMeasure(Ast2SimReadable):
        
    def make_sim_readable(self):
        print("WARNING: measurement present in .qasm code but ignored")
        return self.dqc_circuit #FOR NOW THIS DOES NOTHING AND MEASUREMENTS
                                #ARE SIMPLY IGNORED. I would like to make this 
                                #optional in the future, so that I can analyse
                                #states at the end of circuits with many 
                                #measurements at the end automatically. That
                                #said, it may be better to just change the 
                                #.qasm source code.
# =============================================================================
#         source_reg = self.ast_c_sect_element['source_reg']
#         target_reg = self.ast_c_sect_element['target_reg']
#         #'source_reg' and 'target_reg' are the relevant keys. 
#         source_reg_name, source_qubit_index = ( 
#             self.tokenize_argument_non_terminal(source_reg))
#         target_reg_name, target_qubit_index = ( 
#             self.tokenize_argument_non_terminal(target_reg))
# # =============================================================================
# #         if source_qubit_index is not None and target_qubit_index is not None:
# # # =============================================================================
# # #             self.dqc_circuit.ops = (instr.INSTR_MEASURE, )
# # # =============================================================================
# # =============================================================================
#         #FINISH!!!!!
# =============================================================================
        
class AstBarrier(Ast2SimReadable):
    def make_sim_readable(self):
        print("WARNING: 'barrier' command present in .qasm code but ignored")
        return self.dqc_circuit #FOR NOW THIS DOES NOTHING AND THE BARRIER 
                                #COMMAND IS SIMPLY IGNORED. 
class AstGateDef(Ast2SimReadable):
    def make_sim_readable(self):
        raise NotImplementedError("Arbitrary gate declarations are not yet "
                                  "supported. Only the openQASM 2.0 native "
                                  "gates and standard header gates can "
                                  "currently be used. I aim to support "
                                  "arbitrary gates in the future")
        #To support this you would need to use the ast['g_sect'] which is 
        #not currently passed to your Ast2SimReadable subclasses. This could 
        #actually done before any of these subclasses are used as all the 
        #relevant info is in ast['g_sect'] already. As such you would also not
        #need to parse the gate info 
        
class AstGate(Ast2SimReadable):
    def make_sim_readable(self):
        #relevant info is 'op' (which is the gate name), 'param_list' (which is
        #the parameters parenthesised in the .qasm line) and 'reg_list' (which 
        #is the arguments for the gate (the <argument> non-terminals in the
        #QASM grammar - you can use your tokenize_argument non-terminals for this).
        #I want to update the dqc_circuit.ops list.
        param_interpreter = ExpQasmInterpreter().interpret
        arg_interpreter = ArgumentInterpreter().interpret
        #the parser has matched absolutely anything inside parentheses preceded 
        #by a non-whitespace character. It then split them using a comma
        #delimiter
        params = self.ast_c_sect_element['param_list']
        args = self.ast_c_sect_element['reg_list']
        gate_name = self.ast_c_sect_element['op']
        interpretted_args = []
        for arg in args:
            interpretted_args = interpretted_args + arg_interpreter(arg)
        if params: #if params is not empty
            for ii, param in enumerate(params):
                params[ii] = param_interpreter(param)
            gate_tuple = (self.dqc_circuit.defined_gates[gate_name](*params),
                              *interpretted_args)
        elif params is None:
            gate_tuple = (self.dqc_circuit.defined_gates[gate_name],
                          *interpretted_args)
        self.dqc_circuit.ops.append(gate_tuple)
        return self.dqc_circuit
        
class AstCtl(Ast2SimReadable):
    def make_sim_readable(self):
        raise NotImplementedError('QASM if statements are not yet supported')
        
class AstCtl2(Ast2SimReadable):
    def make_sim_readable(self):
        raise NotImplementedError('QASM if statements are not yet supported')
        
class AstBlank(Ast2SimReadable):
    def make_sim_readable(self):
        raise NotImplementedError('I am not quite sure what the Blank type '
                                  'in the parser is yet')
        
class AstDeclaration_Qasm_2_0(Ast2SimReadable):
    def make_sim_readable(self):
        return self.dqc_circuit #do nothing. The error raised if this is not
             #the first line of uncommented code in the file should already 
             #have been raised by the parser and so this line should do nothing
             #further
             
        
class AstInclude(Ast2SimReadable):
    def make_sim_readable(self):
        if self.ast_c_sect_element['include'] is None:
            return self.dqc_circuit
        elif self.ast_c_sect_element['include'] == 'qelib1.inc':
            #merging existing dictionary with standard lib ones
            standard_lib = {"u3" : gates.INSTR_U, #alias of U native gate
                             "u2" : lambda phi, lambda_var : gates.INSTR_U(np.pi/2, phi, lambda_var),
                             "u1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var),
                             "cx" : instr.INSTR_CNOT,
                             "id" : gates.INSTR_IDENTITY,
                             "u" : gates.INSTR_U, #alias of U and u3
                             "p" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var), #alias of u1
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
                             "cp" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var, controlled=True), #alias of cu1
                             "cu3" : lambda theta, phi, lambda_var : gates.INSTR_U(theta, phi, lambda_var, controlled=True)}
            self.dqc_circuit.defined_gates.update(standard_lib)
            return self.dqc_circuit
        else:
            raise NotImplementedError("The inclusion of arbitrary files within"
                                      " the QASM code is not yet supported")


def ast2sim_readable(ast):
    qregs = dict()
    cregs = dict()
    native_qasm_gates = {"U" : gates.INSTR_U, "CX" : instr.INSTR_CNOT}
    ops4circuit = []
    dqc_circuit = DqcCircuit(qregs, cregs, native_qasm_gates, ops4circuit)
    #implementing functions from <exp> in openQASM 2.0's grammar
    ast_types2sim_types_lookup = {ASTType.UNKNOWN : AstUnknown, 
                                  ASTType.COMMENT : AstComment,
                                  ASTType.QREG : AstQreg,
                                  ASTType.CREG : AstCreg,
                                  ASTType.MEASURE : AstMeasure,
                                  ASTType.BARRIER : AstBarrier,
                                  ASTType.GATE : AstGateDef,
                                  ASTType.OP : AstGate,
                                  ASTType.CTL : AstCtl,
                                  ASTType.CTL_2 : AstCtl2,
                                  ASTType.BLANK : AstBlank,
                                  ASTType.DECLARATION_QASM_2_0 : AstDeclaration_Qasm_2_0,
                                  ASTType.INCLUDE : AstInclude}
    for ast_c_sect_element in ast['c_sect']:
        ast2sim_readable_converter = ast_types2sim_types_lookup[ast_c_sect_element['type']](ast_c_sect_element, dqc_circuit)  
        #updating dqc_circuit object with new information
        dqc_circuit = ast2sim_readable_converter.make_sim_readable() 
    return dqc_circuit




# =============================================================================
# def qasm2sim_readable(filepath):
#     registers = dict()
#     qasm2python_gate_dict = {"U" : gates.INSTR_U,
#                              "CX" : instr.INSTR_CNOT}
#     #implementing functions from <exp> in openQASM 2.0's grammar
#     exp_dict = {"pi" : np.pi, "exp" : np.exp}
#     
#         
#     
#     def _handle_two_qubit_gate(gate_name, params, gate_args, gate_list,
#                                   qasm2python_gate_dict, registers):
#         arg1 = gate_args[0]
#         arg2 = gate_args[1]
#         if '[' in arg1 and '[' in arg2:
#             arg1_reg, arg1_qindex = _split_arg_name_from_index(arg1)
#             arg2_reg, arg2_qindex = _split_arg_name_from_index(arg2)
#             gate_list.append(
#                     (_get_gate_cmd(gate_name, params), arg1_qindex, 
#                      arg1_reg, arg2_qindex, arg2_reg))
#         elif '[' not in arg1 and '[' not in arg2:
#             if registers[arg1] != registers[arg2]:
#                 raise ValueError("registers {arg1} and {arg2} have different "
#                                  f" sizes. Their sizes are {registers[arg1]} "
#                                  f"and {registers[arg2]}, respectively.")
#             else:
#                 for ii in range(registers[arg2]):
#                     gate_list.append(
#                         (_get_gate_cmd(gate_name, params), ii, arg1, ii, arg2))
#         elif '[' in arg1 and '[' not in arg2:
#             arg1_reg, arg1_qindex = _split_arg_name_from_index(arg1)
#             for ii in range(registers[arg2]):
#                 gate_list.append(
#                     (_get_gate_cmd(gate_name, params), arg1_qindex, arg1_reg, 
#                      ii, arg2))
#         elif '[' not in arg1 and '[' in arg2:
#             arg2_reg, arg2_qindex = _split_arg_name_from_index(arg2)
#             for ii in range(registers[arg1]):
#                 gate_list.append(
#                     (_get_gate_cmd(gate_name, params), ii, arg1, arg2_qindex,
#                      arg2_reg))
#                 
#                 
#     with open(filepath, 'r') as file:
#         
#         for line in file:
#             word_list = line.split() #TO DO: replace with something using pyparsers parse_string
#             first_word = word_list[0]
#             params = None
#             gate_list = []
#             if '(' in first_word:
#                 split_first_word = first_word.split('(', 1)
#                 first_word = split_first_word[0]
#                 params = split_first_word[1].replace(')', '').split(',') #params should now be list of parameters 
#             if first_word == 'OPENQASM':
#                 pass
#             elif first_word == '//':
#                 pass
#             elif first_word == 'include':
#                 #standard header is so ubiquitous that it makes sense to handle
#                 #it as its own case
#                 if word_list[1] == "qelib1.inc":
#                     standard_lib = {"u3" : gates.INSTR_U,
#                                      "u2" : lambda phi, lambda_var : gates.INSTR_U(np.pi/2, phi, lambda_var),
#                                      "u1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var),
#                                      "cx" : instr.INSTR_CNOT,
#                                      "id" : gates.INSTR_IDENTITY,
#                                      "x" : instr.INSTR_X,
#                                      "y" : instr.INSTR_Y,
#                                      "z" : instr.INSTR_Z,
#                                      "h" : instr.INSTR_H,
#                                      "s" : instr.INSTR_S,
#                                      "sdg" : gates.INSTR_S_DAGGER,
#                                      "t" : instr.INSTR_T,
#                                      "tdg" : gates.INSTR_T_DAGGER,
#                                      "rx" : lambda theta : gates.INSTR_U(theta, -np.pi/2, np.pi/2),
#                                      "ry" : lambda theta : gates.INSTR_U(theta, 0, 0),
#                                      "rz" : gates.INSTR_RZ,
#                                      "cz" : instr.INSTR_CZ,
#                                      "cy" : gates.INSTR_CY,
#                                      "ch" : gates.INSTR_CH,
#                                      "ccx" : instr.INSTR_CCX,
#                                      "crz" : lambda angle : gates.INSTR_RZ(angle, controlled=True),
#                                      "cu1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var, controlled=True),
#                                      "cu3" : lambda theta, phi, lambda_var : gates.INSTR_U(theta, phi, lambda_var, controlled=True)}
#                     qasm2python_gate_dict.update(standard_lib) 
#                 else:
#                     pass #TO DO: add ability to include files
#             elif first_word == 'qreg' or first_word == 'creg':
#                 reg_def = word_list[1].split('[')
#                 reg_name = reg_def[0]
#                 reg_size = reg_def[1].split(']')[0]
#                 registers[reg_name] = int(reg_size)
#             elif first_word == 'barrier':
#                 pass #TO DO: replace pass with relevant code
#             elif first_word == 'measure':
#                 pass #TO DO: replace pass with relevant code
#             elif first_word in qasm2python_gate_dict: #first_word is quantum gate
#                 gate_args = word_list[1::]
#                 if len(gate_args) == 1:
#                     _handle_single_qubit_gate(first_word, params, gate_args,
#                                               gate_list, qasm2python_gate_dict,
#                                               registers)
#                 elif len(gate_args) == 2:
#                     _handle_two_qubit_gate(first_word, params, gate_args, 
#                                            gate_list, qasm2python_gate_dict, 
#                                            registers)
#                 elif first_word == "ccx":
#                     pass #TO DO: NEED TO IMPLEMENT something here
#                     
#     return gate_list
# =============================================================================
                    
                        
                            
                                    
                            
                    
                    
                    
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
            