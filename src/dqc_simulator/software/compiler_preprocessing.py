# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 09:08:30 2023

@author: kenny
"""

from netsquid.components import instructions as instr

from dqc_simulator.software.qasm2ast import qasm2ast
from dqc_simulator.software.ast2dqc_circuit import ast2dqc_circuit
from dqc_simulator.software.partitioner import bisect_circuit

def preprocess_qasm_to_compilable_bipartitioned(filepath, scheme,
                                                include_path='.'):
    ast = qasm2ast(filepath, include_path=include_path)
    dqc_circuit = ast2dqc_circuit(ast)
    bisect_circuit(dqc_circuit)
    dqc_circuit.add_scheme_to_2_qubit_gates(scheme)
    node_init_commands = []
    for node_name in dqc_circuit.node_sizes:
        new_commands = [[instr.INSTR_INIT, 
                        [ii for ii in range(dqc_circuit.node_sizes[node_name])],
                         node_name]]
        node_init_commands.append(new_commands)
    dqc_circuit.ops = node_init_commands + dqc_circuit.ops
    return dqc_circuit