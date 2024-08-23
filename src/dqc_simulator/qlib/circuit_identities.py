# -*- coding: utf-8 -*-

# =============================================================================
# Created on Tue May  9 15:16:05 2023
# 
# @author: kenny
# =============================================================================
"""Useful circuit identity macros.
"""

from netsquid.components import instructions as instr

from dqc_simulator.qlib.gates import INSTR_T_DAGGER


def two_control_ibm_toffoli_decomp(ctrl_qubit1_index, ctrl_node_name1, 
                                   ctrl_qubit2_index,
                                   ctrl_node_name2, target_qubit_index, 
                                   target_node_name, scheme="cat"):
    """
    A macro for the decomposition of a toffoli, or CCX, gate in terms U, CX, H 
    and T gates.
    
    For direct use by protocols in 
    :mod: `~dqc_simulator.software.dqc_control`.

    Parameters
    ----------
    ctrl_qubit1_index, ctrl_qubit_2_index : int
        The index of the first and second control qubits of the toffoli gate
    ctrl_node_name1, ctrl_node_name2 : str
        The names of the QPU nodes upon which the first and second control 
        qubits of the toffoli gate reside.
    target_qubit_index : int
        The index of the target qubit for the toffoli gate
    target_node_name : str
        DESCRIPTION.
    scheme : str, optional
        The remote gate scheme to use. The default is "cat" (referring to 
        cat-comm (AKA telegate).

    Returns
    -------
    sub_ops : list of tuples
        The gates constituting the decomposed toffoli gate.
        
    Notes
    -----
    This decomposition of the toffoli gate is as specified in the IBM 
    Quantum Experience standard header for openQASM 2.0 [1]_.
    
    References
    ----------
    ..[1] A. W. Cross, L. S. Bishop, J. A. Smolin, and J. M. Gambetta, Open 
        Quantum Assembly Language, arXiv:1707.03429 [quant-ph].

    """
    #INSTR_T_dagger defined in my network.py module
    sub_ops = [(instr.INSTR_H, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit2_index, ctrl_node_name2, target_qubit_index, target_node_name),
               (INSTR_T_DAGGER, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, target_qubit_index, target_node_name),
               (instr.INSTR_T, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit2_index, ctrl_node_name2, target_qubit_index, target_node_name),
               (INSTR_T_DAGGER, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, target_qubit_index, target_node_name),
               (instr.INSTR_T, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_T, target_qubit_index, target_node_name),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_H, target_qubit_index, target_node_name),
               (instr.INSTR_T, ctrl_qubit1_index, ctrl_node_name1),
               (INSTR_T_DAGGER, ctrl_qubit2_index, ctrl_node_name2),
               (instr.INSTR_CNOT, ctrl_qubit1_index, ctrl_node_name1, ctrl_qubit2_index, ctrl_node_name2)]
    if ctrl_node_name1 == ctrl_node_name2 == target_node_name:
        return sub_ops
    else:
        for ii, element in enumerate(sub_ops):
            if len(element) > 3 and element[2] != element[-1]:
                sub_ops[ii] = (*element, scheme)
    return sub_ops

#TO DO: move the following to its own module?
#I think that it probably violates the principle that if a module should only
#change for one reason. See
#https://medium.com/@aserdargun/s-o-l-i-d-design-principles-in-python-e632230d6bbe

#For QASM circuits:

# =============================================================================
# #copy and paste into AstInclude and appropriate places in ast2dqc_circuit_tests
# # then DELETE standard lib when finished making 
# #macros for gates not in it
# standard_lib = {"u3" : gates.INSTR_U, #alias of U native gate
#                  "u2" : lambda phi, lambda_var : gates.INSTR_U(np.pi/2, phi, lambda_var),
#                  "u1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var),
#                  "cx" : instr.INSTR_CNOT,
#                  "id" : gates.INSTR_IDENTITY,
#                  "u0" : gates.INSTR_U(0, 0, 0),
#                  "u" : gates.INSTR_U, #alias of U and u3
#                  "p" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var), #alias of u1
#                  "x" : instr.INSTR_X,
#                  "y" : instr.INSTR_Y,
#                  "z" : instr.INSTR_Z,
#                  "h" : instr.INSTR_H,
#                  "s" : instr.INSTR_S,
#                  "sdg" : gates.INSTR_S_DAGGER,
#                  "t" : instr.INSTR_T,
#                  "tdg" : gates.INSTR_T_DAGGER,
#                  "rx" : lambda theta : gates.INSTR_U(theta, -np.pi/2, np.pi/2),
#                  "ry" : lambda theta : gates.INSTR_U(theta, 0, 0),
#                  "rz" : gates.instrNop_RZ,
#                  "sx" : gates.instrNop_SX,
#                  "sxdg" : gates.instrNop_SXDG,
#                  "cz" : instr.INSTR_CZ,
#                  "cy" : gates.INSTR_CY,
#                  "ch" : gates.INSTR_CH,
#                  "crx" : lambda theta : gates.INSTR_U(theta, -np.pi/2, np.pi/2,
#                                        controlled=True),
#                  "cry" : lambda theta : gates.INSTR_U(theta, 0, 0, 
#                                                       controlled=True),
#                  "crz" : lambda angle : gates.instrNop_RZ(angle, 
#                                                           controlled=True),
#                  "cu1" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var, 
#                                                            controlled=True),
#                  "cp" : lambda lambda_var : gates.INSTR_U(0, 0, lambda_var,
#                                                           controlled=True), #alias of cu1
#                  "cu3" : lambda theta, phi, lambda_var : gates.INSTR_U(
#                                      theta, phi, lambda_var, controlled=True),
#                  "csx" : gates.instrNop_CSX}
# =============================================================================

#defining some useful strings
lpar = '('
rpar = ')'
plus = '+'
over2 = '/2'
minus = ''

#BELOW are for the U, CU universal set

#added u0, sx, sxdg, csx



# =============================================================================
# class StandardLibMacros():
#     """ Macros for the gates in the openQASM 2.0 standard library (using the
#         library defined in MQT bench as of November 2023 rather than the less 
#         extensive library defined in the original propasal for openQASM 2.0),
#         which are not in 
#         the {U, CU} set, (ie, not 1 or 2-qubit gates). I am using this under the 
#         assumption that the gate times and error will not be that different between
#         different single qubit gates and that the difference between a CX and 
#         CU gate will be negligible relative to the difference between a single
#         -qubit gate and a two-qubit gate.
#     """
#     
# =============================================================================

#want list of dicts with entries 'subgate_name', 'subgate_params', 'subgate_args'

#The following macros use poor variable names like a, b, c, etc. This is 
#because they were being manually copied by hand from the openQASM 2.0 
#specification and it was easier to avoid mistakes when using the same notation
#they did

def cz_macro(a, b):
    """
    Macro for CZ gate in terms of H and CX.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    h_gate = {'name' : 'h', 'params' : None, 'args' : [b]}
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a, b]}
    subgates = [h_gate, cx_gate, h_gate]
    return subgates
    
def cy_macro(a, b):
    """
    Macro for CY gate in terms of CX, S and S^dagger.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    subgates = [{'name' : 'sdg', 'params' : None, 'args' : [b]},
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                {'name' : 's', 'params' : None, 'args' : [b]}]
    return subgates

def swap_macro(parent_arg1, parent_arg2):
    """
    Macro for swap gate in terms of CX gates.

    Parameters
    ----------
    parent_arg1 : str
        The first of the arguments provided in the call of the SWAP gate.
    parent_arg2 : str
        The second argument provided in the call of the SWAP gate.

    Returns
    -------
    list of dict
        List of the subgates in the macro.

    """
    common_entries = {'name' : 'cx', 'params' : None}
    subgate1 = {**common_entries,
                'args' : [parent_arg1, parent_arg2]}
    subgate2 = {**common_entries,
                'args' : [parent_arg2, parent_arg1]}
    return [subgate1, subgate2, subgate1]

def ch_macro(a, b):
    """
    Macro for CH gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    subgates = [{'name': 'h', 'params': None, 'args' : [b]},
                {'name' : 'sdg', 'params' : None, 'args' : [b]},
                {'name' : 'cx', 'params': None, 'args' : [a,b]},
                {'name' : 'h', 'params' : None, 'args' : [b]},
                {'name' : 't', 'params' : None, 'args' : [b]},
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                {'name' : 't', 'params' : None, 'args' : [b]},
                {'name': 'h', 'params': None, 'args' : [b]},
                {'name' : 's', 'params' : None, 'args' : [b]},
                {'name' : 'x', 'params' : None, 'args' : [b]},
                {'name' : 's', 'params' : None, 'args' : [a]}]
    return subgates

def ccx_macro(a, b, c):
    """
    macro for ccx gate, as defined in MQT bench's version of the openQASM 2.0
    standard library (qelib1.inc)

    Parameters
    ----------
    a : str
        First uninterpretted argument of parent gate.
    b : str
        Second uninterpretted argument of parent gate.
    c : str
        Third uninterpretted argument of parent gate.

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.

    """
    cx_common_entries = {'name' : 'cx', 'params' : None}
    subgates = [{'name' : 'h', 'params' : None, 'args' : [c]}, 
                {**cx_common_entries, 'args' : [b, c]},
                {'name' : 'tdg', 'params' : None, 'args' : [c]},
                {**cx_common_entries, 'args' : [a, c]},
                {'name' : 't', 'params' : None, 'args' : [c]},
                {**cx_common_entries, 'args' : [b, c]},
                {'name' : 'tdg', 'params' : None, 'args' : [c]},
                {**cx_common_entries, 'args' : [a, c]},
                {'name' : 't', 'params' : None, 'args' : [b]},
                {'name' : 't', 'params' : None, 'args' : [c]},
                {'name' : 'h', 'params' : None, 'args' : [c]},
                {**cx_common_entries, 'args' : [a, b]},
                {'name' : 't', 'params' : None, 'args' : [a]},
                {'name' : 'tdg', 'params' : None, 'args' : [b]},
                {**cx_common_entries, 'args' : [a, b]}]
    return subgates 
    
def cswap_macro(a, b, c):
    """
    Macro for cswap gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    a : int
        Control qubit index
    b : int
        Index of first qubit to be swapped
    c : int
        Index of second qubit to be swapped

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [c, b]}
    subgates = [cx_gate, *ccx_macro(a, b, c), cx_gate]
    return subgates

def crx_macro(lambda_var, a, b):
    """    
    Macro for CRX gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    lambda_var : float
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    subgates = [{'name' : 'u1', 'params' : ['pi/2'], 'args' : [b]},
                {'name' : 'cx', 'params' : None, 'args' : [a,b]},
                {'name' : 'u3', 
                 'params' : [minus + lambda_var + over2, '0', '0'],
                 'args' : [b]},
                {'name' : 'cx', 'params' : None, 'args' : [a,b]},
                {'name' : 'u3',
                 'params' : [lambda_var + '/2', '-pi/2', '0'],
                 'args' : [b]}]
    return subgates

def cry_macro(lambda_var, a, b):
    """    
    Macro for CRY gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    lambda_var : float
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a,b]}
    subgates = [{'name' : 'ry', 'params' : [lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'ry', 'params' : [minus + lambda_var + over2], 
                 'args' : [b]},
                cx_gate]
    return subgates

def crz_macro(lambda_var, a, b):
    """    
    Macro for CRX gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    lambda_var : float
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a,b]}
    subgates = [{'name' : 'rz', 'params' : [lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'rz', 'params' : [minus + lambda_var + over2], 
                 'args' : [b]},
                cx_gate]
    return subgates
    
def cu1_macro(lambda_var, a, b):
    """    
    Macro for CU1 gate defined in IBM quantum experience standard header.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    lambda_var : float
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a,b]}
    subgates = [{'name' : 'u1', 'params' : [lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'u1', 'params' : [minus + lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'u1', 'params' : [lambda_var + over2], 
                             'args' : [b]}]
    return subgates
    
def cp_macro(lambda_var, a, b):
    """    
    Macro for CP gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    lambda_var : float
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a,b]}
    subgates = [{'name' : 'p', 'params' : [lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'p', 'params' : [minus + lambda_var + over2], 
                 'args' : [b]},
                cx_gate,
                {'name' : 'p', 'params' : [lambda_var + over2], 
                             'args' : [b]}]
    return subgates
    
def cu3_macro(theta, phi, lambda_var, c, t):
    """    
    Macro for CU3 gate defined by IBM standard header.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    theta : float
    lambda_var : float
    c : int
        Control qubit index
    t : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    subgates = [{'name' : 'u1', 
                 'params' : [lpar + lambda_var + plus + phi + ')/2'],
                 'args' : [c]},
                {'name' : 'u1', 
                 'params' : [lpar + lambda_var + '-' + phi + ')/2'],
                 'args' : [t]},
                {'name' : 'cx', 'params' : None, 'args' : [c, t]},
                {'name' : 'u3', 
                 'params' : ['-' + theta + '/2', '0',
                             '-(' + phi + '+' + lambda_var + ')/2'],
                 'args' : [t]},
                {'name' : 'cx', 'params' : None, 'args' : [c, t]},
                {'name' : 'u3', 
                 'params' : [theta + '/2', phi, '0'],
                 'args' : [t]}]
    return subgates

def csx_macro(a, b):
    """    
    Macro for CSX gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    a : int
        Control qubit index
    b : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    h_gate = {'name' : 'h', 'params' : None, 'args' : [b]}
    subgates = [h_gate, *cu1_macro('pi/2', a, b), h_gate]
    return subgates

def cu_macro(theta, phi, lambda_var, gamma, c, t):
    """    
    Macro for CU gate.
    
    For internal use by :mod: `~dqc_simulator.software.ast2dqc_circuit`. 
    Further compilation will be needed before the output can be interpretted
    by the simulator itself.
    
    Parameters
    ----------
    theta : float
    phi : float
    lambda_var : float
    c : int
        Control qubit index
    t : int
        Target qubit index

    Returns
    -------
    subgates : list of dicts
        The gates comprising the macro.
    """
    subgates = [{'name' : 'p', 'params' : [gamma], 'args' : [c]},
                {'name' : 'p', 
                 'params' : [lpar + lambda_var + plus + phi + rpar + over2],
                 'args' : [c]},
                 {'name' : 'p', 
                  'params' : [lpar + lambda_var + minus + phi + rpar + over2],
                  'args' : [t]},
                 {'name' : 'cx', 'params' : None, 'args' : [c, t]},
                 {'name' : 'u', 
                  'params' : [minus + theta + over2, '0', 
                              minus + lpar + lambda_var + rpar + over2],
                  'args' : [t]},
                 {'name' : 'cx', 'params' : None, 'args' : [c, t]},
                 {'name' : 'u',
                  'params' : [theta + over2, phi, '0'], 
                  'args' : [t]}]
    return subgates


def rxx_macro(theta, a, b):
    h_gate = {'name' : 'h', 'params' : None, 'args' : [b]}
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a, b]}
    subgates = [{'name' : 'u3', 'params' : ['pi/2', theta, '0'],
                 'args' : [a]},
                h_gate, cx_gate,
                {'name' : 'u1', 'params' : ['-' + theta], 'args' : [b]},
                cx_gate, h_gate,
                {'name' : 'u2', 'params' : ['-pi', 'pi-' + theta],
                 'args' : [a]}]
    return subgates 

def rzz_macro(theta, a, b):
    cx_gate = {'name' : 'cx', 'params' : None, 'args' : [a, b]}
    subgates = [cx_gate, 
                {'name' : 'u1', 'params' : [theta], 'args' : [b]},
                cx_gate]
    return subgates

def rccx_macro(a, b, c):
    subgates = [{'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [c]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [a, c]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [c]},
                {'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [c]}]
    return subgates
    
def rc3x_macro(a, b, c, d):
    subgates = [{'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [d]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [d]},
                {'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [a, d]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [b, d]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [a, d]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [b, d]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [d]},
                {'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [d]},
                {'name' : 'u1', 'params' : ['pi/4'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'u1', 'params' : ['-pi/4'], 'args' : [d]},
                {'name' : 'u2', 'params' : ['0', 'pi'], 'args' : [d]}]
    return subgates

def c3x_macro(a, b, c, d):
    subgates = [{'name' : 'h', 'params' : None, 'args' : [d]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [a]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [b]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [c]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [b]},
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [a, c]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [c]},
                {'name' : 'cx', 'params' : None, 'args' : [a, c]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [b, d]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [a, d]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [b, d]},
                {'name' : 'p', 'params' : ['pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [c, d]},
                {'name' : 'p', 'params' : ['-pi/8'], 'args' : [d]},
                {'name' : 'cx', 'params' : None, 'args' : [a, d]},
                {'name' : 'h', 'params' : None, 'args' : [d]}]
    return subgates

def c3sqrtx_macro(a, b, c, d):
    h_gate = {'name' : 'h', 'params' : None, 'args' : [d]}
    subgates = [h_gate,
                *cu1_macro('pi/8', a, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                h_gate,
                *cu1_macro('-pi/8', b, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [a, b]},
                h_gate,
                *cu1_macro('pi/8', b, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                h_gate,
                *cu1_macro('-pi/8', c, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [a, c]},
                h_gate,
                *cu1_macro('pi/8', c, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [b, c]},
                h_gate,
                *cu1_macro('-pi/8', c, d),
                h_gate,
                {'name' : 'cx', 'params' : None, 'args' : [a, c]},
                h_gate,
                *cu1_macro('pi/8', c, d),
                h_gate]
    return subgates

def c4x_macro(a, b, c, d, e):
    h_gate = {'name' : 'h', 'params' : None, 'args' : [e]}
    subgates = [h_gate,
                *cu1_macro('pi/2', d, e),
                h_gate,
                *c3x_macro(a, b, c, d),
                h_gate,
                *cu1_macro('-pi/2', d, e),
                h_gate,
                *c3x_macro(a, b, c, d),
                *c3sqrtx_macro(a, b, c, e)]
    return subgates

