"""
Classes to implement qasm2 translation to python data structures.

Notes
-----
This is a modified version of :mod: `~nuqasm2.qasmast`. The modifications are 
mainly to convert from the command line interface used by 
:mod:`~nuqasm2.qasmast` to the typical python interface.

Some of the code is also adapted from the examples module in the pyparsing
package 
"""

# =============================================================================
# Derived from qasmast.py.
# Classes to implement qasm2 translation to python data structures
# Working from _Open Quantum Assembly Language_
# https://arxiv.org/pdf/1707.03429.pdf
# jack j. woehr jwoehr@softwoehr.com po box 51 golden co 80402-0051
# Copyright 2019 Jack Woehr jwoehr@softwoehr.com PO Box 51, Golden, CO 80402-0051.
# Apache-2.0 license -- See LICENSE which you should have received with this code.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES.
# 
# MODIFIED ON 10/10/2023 BY KENNY CAMPBELL elkmc@leeds.ac.uk. I have added the 
# qasm2ast function to wrap some of the functionality in a way convenient for my 
# use case, which is use of the abstract sytax tree (ast) within python rather 
# than accessing it via the command line. The qasm2ast function is modified from
# the do_it function in the nuqasm2/nuqasm2.py script, which has the same 
# copyright info and licensing as above. This useage is in accordance 
# with the apache 2.0 license available at
# licenses_of_code_parts_of_package_are_derived_from/LICENSE4qasm2ast_base_code
# or https://www.apache.org/licenses/LICENSE-2.0
# =============================================================================

from enum import Enum
import re
import datetime
import os
import sys
from functools import wraps

import pyparsing as pp


class QTRegEx():
    """Compiled regular expressions for parsing."""
    COMMENT = re.compile(r"^\s*//")
    INCLUDE = re.compile(r"^\s*include\s+\"\S+\"\s*;")
    EOL_COMMENT = re.compile(r";.*(//.*)")

    CTL_2 = re.compile(r"(\w+)\((\w+)(\W+)(\w+)\)\s+(\w+)\s+(\w+\[\w+\]);")

    QREG = re.compile(r"^\s*qreg\s+\S*\[\d+\]\s*;")
    CREG = re.compile(r"^\s*creg\s+\S*\[\d+\]\s*;")
    MEASURE = re.compile(r"^\s*measure\s+\S+\s*\-\>\s*\S+\s*;")
    BARRIER = re.compile(r"^\s*barrier\s+.*;")
    GATE = re.compile(r"^\s*gate\s+.*")
    # OP = re.compile(r"^\s*\S+\s+\S+\[\d+\]\s*;")
    OP = re.compile(r"^\s*\S+\s+\S+\s*;")

    INCLUDE_TARGET = re.compile(r".*\"(\S+)\"\s*;")
    REG_DECL = re.compile(r".*(\S+)\[(\d+)\].*")
    MEASURE_DECL = re.compile(r"^\s*measure\s+(\S+)\s*\-\>\s*(\S+)\s*;")
    BARRIER_DECL = re.compile(r"\S+\[\d+\]")
    BARRIER_DECL_1 = re.compile(r"\S+\s*[\,;]")
    OP_AND_ARGS = re.compile(r"^\s*(\S+)\s+.*")
    OP_PARAM_LIST = re.compile(r"(\S+)\((.*)\)")
    # OP_REG_LIST = re.compile(r"\S+\[\d+\]")
    OP_REG_LIST = re.compile(r"\s+\S+;")

    START_CURLY = re.compile(r".*\{.*")
    END_CURLY = re.compile(r".*\}.*")
    GATE_DECL = re.compile(r"gate\s+(\S+)\s+(\S*).*")
    GATE_OPS = re.compile(r"gate\s+.*\{(.*)\}")
    GATE_OPS_LIST = re.compile(r"\S+\s+\S+;")
    GATE_OP = re.compile(r"(\w+).*")
    GATE_OP_PARAMS = re.compile(r"\S+\((.*)\).*")
    GATE_OP_REGS = re.compile(r".*\s+(\S+);") #any characters followed by at least
                                              #one whitespace followed by at
                                              #least one non-whitespace character

#useful parsing terms
class QasmParsingElement():
    """ParsingElement defined using the pyparsing package with some additional
    more specific methods. I have added this because the RegEx expressions 
    used in the original nuqasm2 code are leading to bugs. For example, only
    the first character of qreg names are being stored under the qreg_name key
    of the ASTType.QREG entries in the AST c_sect."""
    def __init__(self):
        pass
    lpar = pp.Literal('(').suppress()
    rpar = pp.Literal(')').suppress()
    l_sqr_brace = pp.Literal('[').suppress()
    r_sqr_brace = pp.Literal(']').suppress()
    idQasm = pp.Regex(r'[a-z][A-Za-z0-9]*') # id from https://arxiv.org/abs/1707.03429
    real = pp.Regex(r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?')
    nninteger = pp.Regex(r'[1-9]+[0-9]*|0')
    number = real | nninteger | pp.Keyword('pi') 
    arith_op = pp.one_of(['+', '-', '*', '/', '^'])
    unaryop = pp.one_of(['sin', 'cos', 'tan', 'exp', 'ln', 'sqrt'])
    reg_index_slice = l_sqr_brace + nninteger + r_sqr_brace
    decl =  (pp.Keyword('qreg') + idQasm + reg_index_slice |
             pp.Keyword('creg') + idQasm + reg_index_slice ) 
    
# =============================================================================
# # =============================================================================
# #     exp_num_or_word = real | nninteger | pi | idQasm  
# # =============================================================================
# # =============================================================================
# #     params =  pp.original_text_for(pp.nested_expr) #anything (including more
# # =============================================================================
#                                                    #nested brackets) inside 
#                                                    #parentheses
# # =============================================================================
# #     atom = number | pp.Keyword('pi') 
# #     exp_ops = [('-', 1, pp.OpAssoc.LEFT), ('^', 2, pp.OpAssoc.RIGHT), 
# #                  (pp.one_of(['*', '/']), 2, pp.OpAssoc.LEFT),
# #                  (pp.one_of(['+', '-']), 2, pp.OpAssoc.LEFT), 
# #                  (unaryop, 1, pp.OpAssoc.LEFT)]
# #     exp_qasm = pp.infix_notation(atom, exp_ops, '(', ')')
# # =============================================================================
#     # use CaselessKeyword for e and pi, to avoid accidentally matching
#     # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
#     # and CaselessKeyword only match whole words
# =============================================================================

class ASTType(Enum):
    """
    The line types that can be handled by the parser.

    Parameters
    ----------
    source : str
        A line from the  source code (.qasm file) to be parsed.

    Returns
    -------
    :class:`~enum.Enum`
        Enumerator indicating line type.
    """
    UNKNOWN = 0
    COMMENT = 100
    QREG = 20
    CREG = 30
    MEASURE = 40
    BARRIER = 50
    GATE = 60
    OP = 70
    CTL = 80
    CTL_2 = 82
    BLANK = 1000
    DECLARATION_QASM_2_0 = 2000
    INCLUDE = 3000

    @classmethod
    def astType(cls, source):
        """
        Return enum indicating line type
        source is source code
        """
        if source == '':
            return cls.BLANK
        if source == "OPENQASM 2.0;":
            return cls.DECLARATION_QASM_2_0
        x = QTRegEx.COMMENT.search(source)
        if x:
            return cls.COMMENT
        x = QTRegEx.INCLUDE.search(source)
        if x:
            return cls.INCLUDE
        x = QTRegEx.CTL_2.search(source)
        if x:
            if x.group(1) == 'if':
                return cls.CTL_2
        x = QTRegEx.QREG.search(source)
        if x:
            return cls.QREG
        x = QTRegEx.CREG.search(source)
        if x:
            return cls.CREG
        x = QTRegEx.MEASURE.search(source)
        if x:
            return cls.MEASURE
        x = QTRegEx.BARRIER.search(source)
        if x:
            return cls.BARRIER
        x = QTRegEx.GATE.search(source)
        if x:
            return cls.GATE
        x = QTRegEx.OP.search(source)
        if x:
            return cls.OP
        return cls.UNKNOWN

    @classmethod
    def ast_eol_comment(cls, source):
        """
        Handles comments in source code

        Parameters
        ----------
        source : str
            A line from the  source code (.qasm file) to be parsed.

        Returns
        -------
        x : str
            The commented line with leading and trailing spaces removed.
        """
        x = QTRegEx.EOL_COMMENT.search(source)
        if x:
            x = x.group(1).strip()
        return x


class ASTElement():
    """
    A base class for AST elements.
    
    Parameters
    ----------
    filenum : int
        Index of filepath in :class:`T_Sect` 
        filepaths vector.
    linenum : int
        The linenumber of the source code line being parsed.
    ast_type : element of :class:`ASTType`
    source : str
        A line from the  source code (.qasm file) to be parsed.
    save_element_source : bool
        Whether to save the relevant unparsed source code line or not. Default
        is False.
    eol_comment : str or None
        The end of line comment (if there is one).
    """

    def _eol_comment(f):
        """Add another element to the AST if an end-of-line comment present"""
        @wraps(f)
        def wrapped(inst):
            ast = f(inst)
            if inst.eol_comment:
                ast["eol_comment"] = inst.eol_comment
            return ast
        return wrapped

    def __init__(self, filenum, linenum, ast_type, source, save_element_source=False, eol_comment=None):
        """Instance from qasm source code and parse into key:value pairs"""
        self.filenum = filenum
        self.linenum = linenum
        self.ast_type = ast_type
        self.source = source
        self.save_element_source = save_element_source
        self.eol_comment = eol_comment

    @_eol_comment
    def out(self):
        """Returns self as a dict structure"""
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None}

    @staticmethod
    def proc_reg_list(txt):
        """Internal parsing routine for reg list of ops"""
        x = QTRegEx.OP_REG_LIST.findall(txt)
        y = x[0].strip(';')
        y = y.strip()
        return y.split(',')


class ASTElementUnknown(ASTElement):
    """
    ASTElementUnknown
    An unknown ASTElement, unimplemented or error
    Knows linenum, ast_type, source
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementUnknown, self).__init__(
            filenum, linenum, ASTType.UNKNOWN, source, save_element_source, eol_comment)


class ASTElementComment(ASTElement):
    """
    ASTElementComment
    A programmer comment element
    Knows linenum, ast_type, source
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementComment, self).__init__(
            filenum, linenum, ASTType.COMMENT, source, save_element_source, eol_comment)


class ASTElementDeclarationQasm2_0(ASTElement):
    """
    ASTElementDeclarationQasm2_0
    Obligatory declaration
    Knows linenum, ast_type, source
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementDeclarationQasm2_0, self).__init__(
            filenum, linenum, ASTType.DECLARATION_QASM_2_0, source, save_element_source, eol_comment)


class ASTElementInclude(ASTElement):
    """
    For handling openQASM2 include statements.
    Knows linenum, ast_type, source, include
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementInclude, self).__init__(
            filenum, linenum, ASTType.INCLUDE, source, save_element_source, eol_comment)
        x = QTRegEx.INCLUDE_TARGET.search(source)
        self.include = x.group(1)

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'include': self.include}


class ASTElementQReg(ASTElement):
    """
    For handling qreg declarations.
    Knows linenum, ast_type, source, qreg_name, qreg_num
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementQReg, self).__init__(
            filenum, linenum, ASTType.QREG, source, save_element_source, eol_comment)
        parsed_line = QasmParsingElement.decl.parse_string(self.source)
        self.qreg_name = parsed_line[1]
        self.qreg_num = parsed_line[2]
        #commented out block below is the original nuqasm2 code. It fails to 
        #correctly parse multi-character register names and instead only
        #retrieves the last character of the name
# =============================================================================
#         x = QTRegEx.REG_DECL.match(self.source)
#         self.qreg_name = x.group(1)
#         self.qreg_num = x.group(2)
# =============================================================================

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'qreg_name': self.qreg_name, 'qreg_num': self.qreg_num}


class ASTElementCReg(ASTElement):
    """
    For handling creg declarations.
    Knows linenum, ast_type, source, creg_name, creg_num
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementCReg, self).__init__(
            filenum, linenum, ASTType.CREG, source, save_element_source, eol_comment)
        parsed_line = QasmParsingElement.decl.parse_string(self.source)
        self.creg_name = parsed_line[1]
        self.creg_num = parsed_line[2]
        #commented out block below is the original nuqasm2 code. It fails to 
        #correctly parse multi-character register names and instead only
        #retrieves the last character of the name
# =============================================================================
#         x = QTRegEx.REG_DECL.match(self.source)
#         self.creg_name = x.group(1)
#         self.creg_num = x.group(2)
# =============================================================================

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'creg_name': self.creg_name, 'creg_num': self.creg_num}


class ASTElementMeasure(ASTElement):
    """
    For handing measure commands.
    Knows linenum, ast_type, source, source_reg, target_reg
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementMeasure, self).__init__(
            filenum, linenum, ASTType.MEASURE, source, save_element_source, eol_comment)
        x = QTRegEx.MEASURE_DECL.match(self.source)
        self.source_reg = x.group(1)
        self.target_reg = x.group(2)

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'source_reg': self.source_reg, 'target_reg': self.target_reg}


class ASTElementBarrier(ASTElement):
    """
    For handling barrier commands.
    Knows linenum, ast_type, source, reg_list
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementBarrier, self).__init__(
            filenum, linenum, ASTType.BARRIER, source, save_element_source, eol_comment)
        x = QTRegEx.BARRIER_DECL.findall(self.source)
        if not x:  # e.g., qiskit-terra/examples/qasm/entangled_registers.qasm
            x = QTRegEx.BARRIER_DECL_1.findall(self.source)
            x[0] = x[0].rstrip(';')
        self.reg_list = x[0].split(',')

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'reg_list': self.reg_list}


class ASTElementOp(ASTElement):
    """
    For handling openQASM2 gate operations and subgate operations (AKA operators).
    Knows linenum, ast_type, source, op, param_list, reg_list
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementOp, self).__init__(
            filenum, linenum, ASTType.OP, source, save_element_source, eol_comment)
        x = QTRegEx.OP_AND_ARGS.match(self.source)
        op_and_args = x.group(1)
        x = QTRegEx.OP_PARAM_LIST.match(op_and_args)

        self.param_list = None
        if x:
            self.op = x.group(1)
            self.param_list = x.group(2).split(',')
        else:
            self.op = op_and_args

        self.reg_list = self.proc_reg_list(self.source)

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'op': self.op,
                'param_list': self.param_list, 'reg_list': self.reg_list}


class ASTElementCtl2(ASTElement):
    """
    Control-flow with binary operator.
    Knows linenum, ast_type, source, ctl, expression_op,
    expression_param_list, op, param_list, reg_list
    """

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementCtl2, self).__init__(
            filenum, linenum, ASTType.CTL_2, source, save_element_source, eol_comment)
        x = QTRegEx.CTL_2.match(self.source)
        self.ctl = x.group(1)
        self.expression_op = x.group(3)
        self.expression_param_list = [x.group(2), x.group(4)]

        op_and_args = x.group(5)
        x = QTRegEx.OP_PARAM_LIST.match(op_and_args)

        self.param_list = None
        if x:
            self.op = x.group(1)
            self.param_list = x.group(2).split(',')
        else:
            self.op = op_and_args

        self.reg_list = self.proc_reg_list(self.source)

    @ASTElement._eol_comment
    def out(self):
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type,
                'source': self.source if self.save_element_source else None,
                'ctl': self.ctl,
                'expression_op': self.expression_op,
                'expression_param_list': self.expression_param_list,
                'op': self.op,
                'param_list': self.param_list, 'reg_list': self.reg_list}


class ASTElementGateDefinitionPlaceholder(ASTElement):
    """So something will show up in the c_sect when a gate definition starts"""

    def __init__(self, filenum, linenum, source, save_element_source=False, eol_comment=None):
        super(ASTElementGateDefinitionPlaceholder, self).__init__(
            filenum, linenum, ASTType.GATE, None, None)

    @ASTElement._eol_comment
    def out(self):
        """Returns self as a dict structure"""
        return {'filenum': self.filenum, 'linenum': self.linenum, 'type': self.ast_type}


class Gate_Operation():
    """
    One operation in a gate operation list.
    
    Parameters
    ----------
    op : str
        The gate name.
    op_param_list : list of str
        List of parameter values for the gate.
    op_reg_list : list of str
        The names of the quantum registers to act on.
        
    Attributes
    ----------
    operation : dict
        Dict of the input parameters.
        
    Notes
    -----
    I think that there is an issue with the output of op_reg_list inherrited 
    from the original :mod: `~nuqasm2.qasmast` 
    code. The output is the name of the declared qreg for native openQASM 2 
    gates but is the name of the qubit arguments given for gates defined in 
    standard header.
    """

    def __init__(self, op, op_param_list, op_reg_list):
        """
        Init operation step.

        Instance structures filled in by :class:`QasmTranslator`
        op
             operator
        op_param_list : list
            parameter list for operator
        op_param_list : list
            register list for operator
        """
        self. operation = {
            'op': op,
            'op_param_list': op_param_list,
            'op_reg_list': op_reg_list
        }


class Gate_Definition():
    """    
    User gate definition.
    
    Parameters
    ----------
    source : str
        The line to be parsed from the source file.
    filenum : int
        Index of filepath in :class:`T_Sect` filepaths vector.
    linenum : int
        Line number in source file
    param_list : list of str
        Vector of gate parameter names
    ops_raw_list : list of str
        Vecotr of operations as expressed in source code.
    ops_list : list of dict
        Vector of :class:`Gate_Operation` (translated operations)
        
    Attributes
    ----------
    gate_definition : dict
        Dictionary of the input paramters.
    """

    def __init__(self, source, filenum, linenum, param_list, ops_raw_list, 
                 ops_list):
        """
        Instance structures filled in by :class:`QasmTranslator`.
        """
        self.gate_definition = {
            'source': source,
            'filenum': filenum,
            'linenum': linenum,
            'param_list': param_list,
            'ops_raw_list': ops_raw_list,
            'ops_list': ops_list}


# #########################
# Translation unit sections
# #########################


class Source_Body():
    """
    Source code body with file number of source file.
    
    Parameters
    ----------
    filenum : int
        Index of filepath in :class:`T_Sect` filepaths vector.
    source : str
        The line to be parsed from the source file.
        
    Attributes
    ----------
    source_body : dict
        Dictionary of the input paramters.
    """

    def __init__(self, filenum, source):
        """
        Instance structures filled in by QasmTranslator
        """
        self.source_body = {
            'filenum': filenum,
            'source': source
        }


class T_Sect():
    """
    Translation overhead section of output AST.
    
    Parameters
    ----------
    name : str
        The name of the translation unit. Default value is 'main'.
    
    Attributes
    ----------
    t_sect : dict
        The t_sect of the AST. Will be filled in by :class:`QasmTranslator`.
    """

    def __init__(self, name):
        """Instance structures filled in by :class:`QasmTranslator`."""
        self.t_sect = {
            'name': name,
            'filepaths': [],
            'datetime_start': None,
            'datetime_finish': None
        }

    def append_filepath(self, filepath):
        """Append to filepaths returning index of latest append"""
        idx = len(self.t_sect['filepaths'])
        self.t_sect['filepaths'].append(filepath)
        return idx


class C_Sect():
    """
    Code section of output AST.
    
    Attributes
    ----------
    c_sect : list
        The c_sect of the output AST. Vector of :class:`ASTElement`.
    """

    def __init__(self):
        """
        Instance structures filled in by QasmTranslator
        Vector of ASTElement
        """
        self.c_sect = []


class G_Sect():
    """
    User gate definition section of output AST
    
    Attributes
    ----------
    g_sect : list
        The user gate section of the output AST, to be filled in by 
        :class:`QasmTranslator`.
        
    """

    def __init__(self):
        """Instance structures filled in by QasmTranslator"""
        self.g_sect = []


class S_Sect():
    """
    Source code section of output AST.
    
    Attributes
    ----------
    s_sect : list
        Vector of :class:`Source_Body` to be filled in by 
        :class:`QasmTranslator`.
    """

    def __init__(self):
        """Instance structures filled in by QasmTranslator"""
        self.s_sect = []

    def append(self, sourcebody):
        """
        Appends the source body to the s_sect
        
        Appends `sourcebody` to :attr: `S_Sect.s_sect`.

        Parameters
        ----------
        sourcebody : dict
            As generated by :attr: `Source_Body.source_body`.
        """
        self.s_sect.append(sourcebody)


# ##################################
# Pushable frames for source nesting
# ##################################


class Source_Frame():
    """
    A pushable frame defining the source we are processing
    
    Parameters
    ----------
    filenum : int
        Index of filepath in :attr: `T_Sect.t_sect` filepaths vector.
    qasmsourcelines : list of str
        List of the lines from the source code (.qasm) file.
    
    Attributes
    ----------
    linenum : int
        The index of a line from the source code file.
    """

    def __init__(self, filenum, qasmsourcelines):
        """
        Init counter to 0
        """
        self.filenum = filenum
        self.qasmsourcelines = qasmsourcelines
        self.linenum = 0

    def next(self):
        """ Return next source line and increment counter"""
        source = None
        if self.linenum < len(self.qasmsourcelines):
            source = self.qasmsourcelines[self.linenum]
            self.linenum += 1
        return source

    def nth_qasmline(self, n):
        """Return nth qasm source line"""
        return self.qasmsourcelines[n] if n < len(self.qasmsourcelines) else None


class Source_Frame_Stack():
    """
    Stack of source frames so we can nest into include files
    
    Attributes
    ----------
    frames : list
        The stack.
    """

    def __init__(self):
        """Create the stack"""
        self.frames = []

    def push(self, filenum, qasmsourcelines):
        """
        Create and push a frame
        
        Parameters
        ----------
        filenum : int
            Index of filepath in :attr: `T_Sect.t_sect` filepaths vector.
        qasmsourcelines : list of str
            List of the lines from the source code (.qasm) file.
        """
        self.frames.append(Source_Frame(filenum, qasmsourcelines))

    def pop(self):
        """Lose top frame"""
        self.frames.pop()

    def tos(self):
        """Return top frame"""
        return self.frames[-1]

    def next(self):
        """Return next line in source from top frame or None"""
        return self.filenum(), self.linenum(), self.tos().next()

    def depth(self):
        """Depth of stack"""
        return len(self.frames)

    def linenum(self):
        """Return linenum of current tos"""
        return self.tos().linenum

    def filenum(self):
        """Return linenum of current tos"""
        return self.tos().filenum

    def nth_qasmline(self, n):
        return self.tos().nth_qasmline(n)


# ##############
# The Translator
# ##############


class QasmTranslator():
    """
    Translation of a Qasm unit.
    
    Does not read in from file, expects code handed to it.
    
    Parameters
    ----------
    qasmsourcelines : list of str
        List of the lines from the source code (.qasm) file.
    name : str
        User-defined name for translation unit.
    filepath : str or None
        The filepath to the source code file (informational only). Default 
        value is None.
    no_unknown : bool
        True if an unknown element is encountered. Default value is False.
    save_pgm_source : bool
        True if program source should be embedded in output. Default value is 
        False
    save_element_source : bool
        True if element source should be embedded in output. Default value is 
        False.
    save_gate_source : bool
        True if user gate source should be embedded in output. Default value 
        is False.
    save_gate_decls : bool
        True if gate declaration should be noted in c_sect. Default value is 
        False.
    include_path : str
        Path to include in file search. Default value is '.' (current 
        working directory).
        
    Attributes
    ----------
    t_sect : :class:`T_Sect`
    c_sect : :class:`C_Sect`
    g_sect : :class:`G_Sect`
    s_sect : :class:`S_Sect`
    translation : dict
        Dictionary containing all of the sections (t_sect, c_sect, etc).
    source_frame_stack : :class:`Source_Frame_Stack`
    """

    def __init__(self, qasmsourcelines,
                 name='main',
                 filepath=None,
                 no_unknown=False,
                 save_pgm_source=False, save_element_source=False,
                 save_gate_source=False,
                 show_gate_decls=False,
                 include_path='.'):
        """
        Init from source lines in an array.
        Does not read in from file, expects code handed to it.
        qasmsourcelines = the source code
        name = user-defined name for translation unit
        no_unknown = True if raises on unknown element
        filepath = source code filepath (informational only)
        save_pgm_source = True if program source should be embedded in output
        save_element_source = True if element source should be embedded in output
        save_gate_source = True if user gate source should be embedded in output
        show_gate_decls = True if gate declaration should be noted in c_sect
        include_path is path for include file search
        """

        # Control factors
        self.no_unknown = no_unknown
        self.save_pgm_source = save_pgm_source
        self.save_element_source = save_element_source
        self.save_gate_source = save_gate_source
        self.show_gate_decls = show_gate_decls
        self.include_path = include_path

        # Init sections
        self.t_sect = T_Sect(name)
        self.c_sect = C_Sect()
        self.g_sect = G_Sect()

        if save_pgm_source is None:
            self.s_sect = None
        else:
            self.s_sect = S_Sect()

        self.translation = {
            't_sect': self.t_sect.t_sect,
            'c_sect': self.c_sect.c_sect,
            'g_sect': self.g_sect.g_sect,
            's_sect': self.s_sect.s_sect
        }

        # Prepare to process initial source
        self.source_frame_stack = Source_Frame_Stack()
        self.push_source(filepath, qasmsourcelines)

    @staticmethod
    def fromFileHandle(file_handle, name='main', filepath=None, datetime=None,
                       no_unknown=False,
                       save_pgm_source=False, save_element_source=False,
                       save_gate_source=False,
                       show_gate_decls=False,
                       include_path='.'):
        """
        Instance QasmTranslator from a file handle reading in all lines.
        
        Does not close file handle.
        
        Parameters
        ----------
        qasmsourcelines : list of str
            List of the lines from the source code (.qasm) file.
        name : str
            User-defined name for translation unit.
        filepath : str or None
            The filepath to the source code file (informational only). Default 
            value is None.
        no_unknown : bool
            True if an unknown element is encountered. Default value is False.
        save_pgm_source : bool
            True if program source should be embedded in output. Default value is 
            False
        save_element_source : bool
            True if element source should be embedded in output. Default value is 
            False.
        save_gate_source : bool
            True if user gate source should be embedded in output. Default value 
            is False.
        save_gate_decls : bool
            True if gate declaration should be noted in c_sect. Default value is 
            False.
        include_path : str
            Path to include in file search. Default value is '.' (current 
            working directory).
            
        Returns
        -------
        qt : :class:`QasmTranslator`
        """
        qasmsourcelines = []
        for line in file_handle:
            qasmsourcelines.append(line.strip())
        qt = QasmTranslator(qasmsourcelines, name=name, filepath=filepath,
                            no_unknown=no_unknown,
                            save_pgm_source=save_pgm_source,
                            save_element_source=save_element_source,
                            save_gate_source=save_gate_source,
                            show_gate_decls=show_gate_decls,
                            include_path=include_path)
        return qt

    @staticmethod
    def fromFile(filepath, name='main',
                 no_unknown=False,
                 save_pgm_source=False, save_element_source=False,
                 save_gate_source=False,
                 show_gate_decls=False,
                 include_path='.'):
        """
        Create parser given filepath.
        
        Creates :class:`QasmTranslator` given filepath. Opens file indicated 
        by `filepath`, reads in all lines and closes file.

        filepath : str or None
            The filepath to the source code file (informational only). Default 
            value is None.
        name : str
            User-defined name for translation unit.
        no_unknown : bool
            True if an unknown element is encountered. Default value is False.
        save_pgm_source : bool
            True if program source should be embedded in output. Default value is 
            False
        save_element_source : bool
            True if element source should be embedded in output. Default value is 
            False.
        save_gate_source : bool
            True if user gate source should be embedded in output. Default value 
            is False.
        save_gate_decls : bool
            True if gate declaration should be noted in c_sect. Default value is 
            False.
        include_path : str
            Path to include in file search. Default value is '.' (current 
            working directory).
            
        Returns
        -------
        qt : :class:`QasmTranslator`
        """
        if not os.path.exists(filepath) or not os.access(filepath, os.R_OK):
            raise Qasm_Cannot_Read_File_Exception(None, None, None, None, filepath)
        qasmsourcelines = []
        file_handle = open(filepath, 'r')
        for line in file_handle:
            qasmsourcelines.append(line.strip())
        file_handle.close()
        qt = QasmTranslator(qasmsourcelines, name=name, filepath=filepath,
                            no_unknown=no_unknown,
                            save_pgm_source=save_pgm_source,
                            save_element_source=save_element_source,
                            save_gate_source=save_gate_source,
                            show_gate_decls=show_gate_decls,
                            include_path=include_path)
        return qt

    def push_source(self, filepath, qasmsourcelines):
        """Add filepath, push source frame stack, and save source if wanted"""
        filenum = self.t_sect.append_filepath(filepath)
        self.source_frame_stack.push(filenum, qasmsourcelines)
        if self.save_pgm_source:
            self.s_sect.append(Source_Body(
                filenum, qasmsourcelines).source_body)

    def filenum(self):
        """Return the current filenum"""
        return self.source_frame_stack.filenum()

    def linenum(self):
        """Return the current linenum"""
        return self.source_frame_stack.linenum()

    def nth_qasmline(self, n):
        """Return nth line in current source or None"""
        return self.source_frame_stack.nth_qasmline(n)

    def find_include(self, filepath):
        """
        Search include path for filepath
        Return completed filepath if found else None
        """
        found = None
        include_dirs = self.include_path.split(os.pathsep)
        for idir in include_dirs:
            ipath = idir + os.path.sep + filepath
            if os.path.exists(ipath):
                found = ipath
                break
        return found

    def push_include(self, filepath):
        """Open an include file, read it, close it, push source"""
        found = self.find_include(filepath)
        if not found:
            raise Qasm_Cannot_Find_File_Exception(self.filenum(),
                                                  self.get_nth_filepath(
                                                      self.filenum()),
                                                  self.linenum() - 1,
                                                  self.nth_qasmline(
                                                      self.linenum() - 1),
                                                  filepath)
        filepath = found
        if not os.access(filepath, os.R_OK):
            raise Qasm_Cannot_Read_File_Exception(self.filenum(),
                                                  self.get_nth_filepath(
                                                      self.filenum()),
                                                  self.linenum() - 1,
                                                  self.nth_qasmline(
                                                      self.linenum() - 1),
                                                  filepath)
        qasmsourcelines = []
        file_handle = open(filepath, 'r')
        for line in file_handle:
            qasmsourcelines.append(line.strip())
        file_handle.close()
        self.push_source(filepath, qasmsourcelines)

    def append_ast(self, ast):
        """
        Internal routine to append to the AST
        """
        self.translation['c_sect'].append(ast)

    def append_user_gate(self, user_gate):
        """Append a user gate definition to the user_gates output list"""
        self.translation['g_sect'].append(user_gate)

    def user_gate_definition(self, filenum, linenum, txt):
        """Internal routine to parse and append a user gate definition"""
        txt = txt.strip()
        gate_decl = QTRegEx.GATE_DECL.match(txt)
        gate_name = gate_decl.group(1)
        possible_gate_params = gate_name.split('(')
        gate_param_list = None
        if len(possible_gate_params) > 1:
            gate_param_list = possible_gate_params[1].strip(') ').split(',')
        gate_regs = gate_decl.group(2).strip("{}") # watch out for no space before '{' !!
        gate_reg_list = gate_regs.split(',')
        gate_ops = QTRegEx.GATE_OPS.match(txt)
        gate_ops_raw_list = QTRegEx.GATE_OPS_LIST.findall(gate_ops.group(1))
        gate_ops_list = []
        for op_raw in gate_ops_raw_list:
            op_raw = op_raw.strip()
            op = QTRegEx.GATE_OP.match(op_raw).group(1)
            op_params = QTRegEx.GATE_OP_PARAMS.match(op_raw)
            if op_params:
                op_param_list = op_params.group(1).split(',')
            else:
                op_param_list = None
            op_regs = QTRegEx.GATE_OP_REGS.match(op_raw)
            if op_regs:
                op_reg_list = op_regs.group(1).split(',')
            else:
                op_reg_list = None
            gate_ops_list.append({'op': op,
                                  'op_param_list': op_param_list,
                                  'op_reg_list': op_reg_list})
        gate = {'source': txt if self.save_gate_source else None,
                'filenum': filenum,
                'linenum': linenum, 'gate_name': gate_name,
                'gate_param_list': gate_param_list,
                'gate_ops_raw_list': gate_ops_raw_list,
                'gate_ops_list': gate_ops_list,
                'gate_reg_list': gate_reg_list}

        self.append_user_gate(gate)

    def translate(self):
        """
        Translate the qasm source into the desired representation.

        Use `get_translation()` method to retrieve the translated 
        source.
        """
        self.get_t_sect()[
            'datetime_start'] = datetime.datetime.now().isoformat()
        seen_noncomment = False
        parsing_gate = False
        gate_def = ''
        gate_start_line = None
        gate_start_linenum = None
        seen_open_curly = False

        while self.source_frame_stack.depth():
            filenum, linenum, line = self.source_frame_stack.next()
            if line is None:
                self.source_frame_stack.pop()
                continue
            astElement = None
            line = line.strip()
            line = line.replace(', ', ',')
            line = line.replace(' ;', ';')
            eolComment = ASTType.ast_eol_comment(line)

            if parsing_gate:
                if not seen_open_curly:
                    x = QTRegEx.START_CURLY.search(line)
                    if not x:
                        raise Qasm_Gate_Missing_Open_Curly_Exception(filenum,
                                                                     self.get_nth_filepath(
                                                                         filenum),
                                                                     linenum,
                                                                     gate_start_line,
                                                                     gate_start_linenum)
                    else:
                        seen_open_curly = True
                        gate_def = gate_def + line + ' '
                        x = QTRegEx.END_CURLY.search(line)
                        if x:
                            self.user_gate_definition(
                                gate_start_linenum, gate_def)
                            parsing_gate = False
                            gate_def = ''
                            gate_start_line = None
                            gate_start_linenum = None
                            seen_open_curly = False
                else:
                    gate_def = gate_def + line + ' '
                    x = QTRegEx.END_CURLY.search(line)
                    if x:
                        self.user_gate_definition(
                            filenum, gate_start_linenum, gate_def)
                        parsing_gate = False
                        gate_def = ''
                        gate_start_line = None
                        gate_start_linenum = None
                        seen_open_curly = False

                continue

            astElement = ASTElementUnknown(filenum, linenum, line)
            astType = ASTType.astType(line)
            if astType == ASTType.BLANK:
                continue
            if not seen_noncomment and astType != ASTType.COMMENT:
                if astType == ASTType.DECLARATION_QASM_2_0:
                    seen_noncomment = True
                else:
                    raise Qasm_Declaration_Absent_Exception(
                        filenum, self.get_nth_filepath(filenum), linenum, line)

            # Now step thru types
            if astType == ASTType.COMMENT:
                astElement = ASTElementComment(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            elif astType == ASTType.DECLARATION_QASM_2_0:
                astElement = ASTElementDeclarationQasm2_0(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            if astType == ASTType.INCLUDE:
                astElement = ASTElementInclude(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
                self.push_include(astElement.out()['include'])
            elif astType == ASTType.CTL_2:
                astElement = ASTElementCtl2(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            elif astType == ASTType.QREG:
                astElement = ASTElementQReg(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            elif astType == ASTType.CREG:
                astElement = ASTElementCReg(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            elif astType == ASTType.MEASURE:
                astElement = ASTElementMeasure(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            elif astType == ASTType.BARRIER:
                astElement = ASTElementBarrier(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)

            elif astType == ASTType.GATE:
                if self.show_gate_decls:
                    astElement = ASTElementGateDefinitionPlaceholder(
                        filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
                    self.append_ast(astElement.out())
                parsing_gate = True
                gate_start_line = line
                gate_start_linenum = linenum
                gate_def = line + ' '
                x = QTRegEx.START_CURLY.search(line)
                if x:
                    seen_open_curly = True
                    x = QTRegEx.END_CURLY.search(line)
                    if x:
                        self.user_gate_definition(
                            filenum, gate_start_linenum, gate_def)
                        parsing_gate = False
                        gate_def = ''
                        gate_start_line = None
                        gate_start_linenum = None
                        seen_open_curly = False
                continue

            elif astType == ASTType.OP:
                astElement = ASTElementOp(
                    filenum, linenum, line, self.save_element_source, eol_comment=eolComment)
            if type(astElement) is ASTElementUnknown and self.no_unknown:
                raise Qasm_Unknown_Element_Exception(filenum,
                                                     self.get_nth_filepath(
                                                         filenum),
                                                     linenum,
                                                     line)
            self.append_ast(astElement.out())

        if parsing_gate:
            raise Qasm_Incomplete_Gate_Exception(
                filenum,
                self.get_nth_filepath(filenum),
                linenum,
                gate_start_line,
                gate_start_linenum)

        self.t_sect.t_sect['datetime_finish'] = datetime.datetime.now(
        ).isoformat()

    def get_translation(self):
        """Retrieve translation created by `translate()` method"""
        return self.translation

    # #########################
    # Access Methods for Output
    # #########################

    def get_t_sect(self):
        """Return translation unit section"""
        return self.translation['t_sect']

    def get_c_sect(self):
        """Return code section"""
        return self.translation['c_sect']

    def get_g_sect(self):
        """Return gate decl section"""
        return self.translation['g_sect']

    def get_s_sect(self):
        """Return source section"""
        return self.translation['s_sect']

    def get_filepaths(self):
        """Retrieve filepaths"""
        return self.get_t_sect()['filepaths']

    def get_nth_filepath(self, n):
        """Retrieve nth filepath entry"""
        return self.get_filepaths()[n] if n < len(self.get_filepaths()) else None

    def get_datetime_start(self):
        """Retrieve datetime from translation created by `translate()` method"""
        return self.get_t_sect()['datetime_start']

    def get_datetime_finish(self):
        """Retrieve datetime from translation created by `translate()` method"""
        return self.get_t_sect()['datetime_finish']

    def get_nth_ast(self, n):
        """Retrieve nth element in c_sect from translation created by `translate()` method"""
        return self.get_c_sect()[n]

    def get_nth_ast_type(self, n):
        """
        Retrieve AST type of nth c_sect element
        from translation created by `translate()` method
        """
        return self.get_nth_ast(n)['type']

    def get_nth_ast_source(self, n):
        """
        Retrieve source code of nth AST element
        from translation created by `translate()` method
        """
        return self.get_nth_ast(n)['source']

    def get_source(self, filenum):
        """
        Retrieve original source code of qasm file
        number n that was translated by `translate()` method.
        """
        return self.get_s_sect()[filenum] if filenum < len(self.get_s_sect()) else None

    def get_nth_user_gate(self, index):
        """
        Get nth user_gate definition
        from translation created by `translate()` method
        """
        return self.get_g_sect()[index]


# ##########
# Exceptions
# ##########


class Qasm_Exception(Exception):
    """Base class for Qasm exceptions"""

    def __init__(self, filenum, filename, linenum, line):
        super(Qasm_Exception, self).__init__()
        self.filenum = filenum
        self.filename = filename
        self.linenum = linenum
        self.line = line
        self.message = "Qasm_Exception"
        self.errcode = 10

    def errpacket(self):
        ex = {'message': self.message,
              'filenum': self.filenum,
              'filename': self.filename,
              'linenum': self.linenum,
              'line': self.line,
              'errcode': self.errcode
              }
        return ex


class Qasm_Declaration_Absent_Exception(Qasm_Exception):
    """QASM2.0 Declaration not first non-blank non-comment line"""

    def __init__(self, filenum, filename, linenum, line):
        super(Qasm_Declaration_Absent_Exception,
              self).__init__(filenum, filename, linenum, line)
        self.message = "QASM2.0 Declaration not first non-blank non-comment line"
        self.errcode = 20


class Qasm_Unknown_Element_Exception(Qasm_Exception):
    """Unknown element"""

    def __init__(self, filenum, filename, linenum, line):
        super(Qasm_Unknown_Element_Exception, self).__init__(
            filenum, filename, linenum, line)
        self.message = "Unknown element"
        self.errcode = 30


class Qasm_Incomplete_Gate_Exception(Qasm_Exception):
    """Gate definition incomplete"""

    def __init__(self, filenum, filename, linenum, line, start_linenum):
        super(Qasm_Incomplete_Gate_Exception, self).__init__(
            filenum, filename, linenum, line)
        self.message = "Gate definition incomplete"
        self.errcode = 40
        self.start_linenum = start_linenum

    def errpacket(self):
        ex = {'message': self.message,
              'filenum': self.filenum,
              'filename': self.filename,
              'linenum': self.linenum,
              'line': self.line,
              'start_linenum': self.start_linenum,
              'errcode': self.errcode
              }
        return ex


class Qasm_Gate_Missing_Open_Curly_Exception(Qasm_Exception):
    """Gate definition incomplete"""

    def __init__(self, filenum, filename, linenum, line, start_linenum):
        super(Qasm_Gate_Missing_Open_Curly_Exception, self).__init__(
            filenum, filename, linenum, line)
        self.message = "Gate definition missing open curly brace"
        self.errcode = 45
        self.start_linenum = start_linenum

    def errpacket(self):
        ex = {'message': self.message,
              'filenum': self.filenum,
              'filename': self.filename,
              'linenum': self.linenum,
              'line': self.line,
              'start_linenum': self.start_linenum,
              'errcode': self.errcode
              }
        return ex


class Qasm_Cannot_Find_File_Exception(Qasm_Exception):
    """File read error"""

    def __init__(self, filenum, filename, linenum, line, filepath):
        super(Qasm_Cannot_Find_File_Exception, self).__init__(
            filenum, filename, linenum, line)
        self.message = "Cannot find file."
        self.errcode = 50
        self.filepath = filepath

    def errpacket(self):
        ex = {'message': self.message,
              'filenum': self.filenum,
              'filename': self.filename,
              'linenum': self.linenum,
              'line': self.line,
              'filepath': self.filepath,
              'errcode': self.errcode
              }
        return ex


class Qasm_Cannot_Read_File_Exception(Qasm_Exception):
    """File read error"""

    def __init__(self, filenum, filename, linenum, line, filepath):
        super(Qasm_Cannot_Read_File_Exception, self).__init__(
            filenum, filename, linenum, line)
        self.message = "Cannot read file."
        self.errcode = 55
        self.filepath = filepath

    def errpacket(self):
        ex = {'message': self.message,
              'filenum': self.filenum,
              'filename': self.filename,
              'linenum': self.linenum,
              'line': self.line,
              'filepath': self.filepath,
              'errcode': self.errcode
              }
        return ex
    
    


def qasm2ast(filepath, name='main',
             save_pgm_source=False, save_element_source=False,
             save_gate_source=False, show_gate_decls=False,
             include_path='.'):
    """
    Parses a .qasm source file to an abstract syntax tree.

    Parameters
    ----------
    filepaths : list
        The filepaths to the QASM code.
    name : str, optional
        A name for the translation unit (QasmTranslator. The default is 'main'.
    save_pgm_source : bool, optional
        Whether to include program source in AST. The default is False.
    save_element_source : bool, optional
        Whether to include element (typically a line of QASM code) in AST. The 
        default is False.
    save_gate_source : bool, optional
        Whether to include gate source in AST output. The default is False.
    show_gate_decls : bool, optional
        Whether to include gate gate declerations in AST output. The default is 
        False.
    include_path : str, optional
        Path to include in file search. Default value is '.' (current 
        working directory).

    Returns
    -------
    ast : dict of dicts
        An abstract syntax tree (AST) parsed from the QASM
        code given by the filename from filepath. The filename is the key
        for the dictionary.
    """
    
    def _handle_error(err, erring_filepath):
        """Print out exception packet"""
        print("Error: " + erring_filepath)
        x = err.errpacket()
        print(x)
        raise Exception("")
        
    qt = None
    try:
        qt = QasmTranslator.fromFile(filepath,
                                     name=name,
                                     no_unknown=False, #altered from original script
                                     save_pgm_source=save_pgm_source,
                                     save_element_source=save_element_source,
                                     save_gate_source=save_gate_source,
                                     show_gate_decls=show_gate_decls,
                                     include_path=include_path)
        qt.translate()

    except Qasm_Exception as ex:
        _handle_error(ex, filepath)

    translated_ast = qt.get_translation()
    return translated_ast


# =============================================================================
#     filename = os.path.basename(filepath)
#     asts[filename] = translated_ast
# =============================================================================

# fin
