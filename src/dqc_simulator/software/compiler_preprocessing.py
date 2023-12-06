# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 09:08:30 2023

@author: kenny
"""

from netsquid.components import instructions as instr

from dqc_simulator.software.qasm2ast import qasm2ast
from dqc_simulator.software.ast2dqc_circuit import (Ast2DqcCircuitTranslator,
                                                    QasmTwoUniversalSet)
from dqc_simulator.software.partitioner import bisect_circuit

def preprocess_qasm_to_compilable_bipartitioned(
                                    filepath, scheme,
                                    native_gates=QasmTwoUniversalSet.gates,
                                    include_path='.'):
    ast = qasm2ast(filepath, include_path=include_path)
    interpreter = Ast2DqcCircuitTranslator(ast, native_gates=native_gates)
    dqc_circuit = interpreter.ast2dqc_circuit()
    bisect_circuit(dqc_circuit)
    dqc_circuit.add_scheme_to_2_qubit_gates(scheme)
    node_init_commands = []
    for node_name in dqc_circuit.node_sizes:
        new_commands = [instr.INSTR_INIT, 
                        [ii for ii in range(dqc_circuit.node_sizes[node_name])],
                         node_name]
        node_init_commands.append(new_commands)
    dqc_circuit.ops = node_init_commands + dqc_circuit.ops
    return dqc_circuit

def preprocess_qasm_to_compilable_monolithic(
                            filepath, include_path='.',
                            native_gates=QasmTwoUniversalSet.gates):
    ast = qasm2ast(filepath, include_path=include_path)
    interpreter = Ast2DqcCircuitTranslator(ast, native_gates=native_gates)
    dqc_circuit = interpreter.ast2dqc_circuit()
# =============================================================================
#     dqc_circuit = Ast2DqcCircuitTranslator(ast).ast2dqc_circuit()
# =============================================================================
    #TO DO: add change node name and qubit indices of dqc_circuit.ops
    for ii, gate_spec in enumerate(dqc_circuit.ops):
        qreg1 = dqc_circuit.qregs[gate_spec[2]]
        index1 = gate_spec[1] + qreg1['starting_index']
        gate_spec[1] = index1
        if len(gate_spec) >= 5:
            qreg2 = dqc_circuit.qregs[gate_spec[4]]
            index2 = gate_spec[3] + qreg2['starting_index']
            gate_spec[3] = index2
        dqc_circuit.ops[ii] = gate_spec

    dqc_circuit.replace_qreg_names(node_0_name='monolithic_qc',
                                   node_1_name='monolithic_qc')

    total_num_qubits = 0
    for qreg_name in dqc_circuit.qregs:
        qreg = dqc_circuit.qregs[qreg_name]
        total_num_qubits = qreg['size'] + total_num_qubits
    node_init_cmd = [(instr.INSTR_INIT, list(range(total_num_qubits)), 
                      'monolithic_qc')]
    dqc_circuit.ops = node_init_cmd + dqc_circuit.ops
    return dqc_circuit