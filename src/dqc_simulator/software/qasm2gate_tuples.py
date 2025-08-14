"""
Tools to convert a monolithic quantum circuit specified in openQASM 2.0 to 
gate tuples representing a partitioned quantum circuit.

References
----------
.. [1] A Cross, et al, Open Quantum Assembly Language, arXiv:1707.03429.
"""

# from dqc_simulator.software.ast2dqc_circuit import Ast2DqcCircuitTranslator
from dqc_simulator.software.compiler_preprocessing import ( 
    preprocess_qasm_to_compilable_monolithic as preprocess)
from dqc_simulator.software.partitioner import (
   first_come_first_served_qubits_to_qpus as allocate,
   partition_gate_tuples as partition)

def qasm2gate_tuples(dqc, filepath, scheme, include_path='.'):
    """
    Converts a monolithic quantum circuit specified in openQASM 2.0 to 
    gate tuples representing a partitioned quantum circuit.
    
    dqc : :class:`dqc_simulator.hardware.dqc_creation.DQC`
        A DQC network.
    filepath : str
        The path to the .qasm file.
    scheme : str
        The type of remote gate to use. Allowed values are 'cat', '1tp', 
        '2tp', and 'tp_safe'.
    include_path : str
        The path to the directory containing any include (.inc) files imported 
        in the .qasm file. See [1]_. The default is '.', which looks in the 
        current working directory.
    """
    # import .qasm file and convert to gate_tuples for monolithic_circuit
    dqc_circuit = preprocess(filepath, include_path=include_path)
    monolithic_circuit = dqc_circuit.ops # gate_tuples
    
    # Determine allocation of processing qubits to QPUs
    old_to_new_lookup, proc_qubit_allocation4each_qpu = allocate(
       monolithic_circuit, list(dqc.nodes.values()))
    
    # Partition according to the previously defined qubit allocation
    partitioned_gate_tuples = partition(monolithic_circuit,
                                        dqc, # defined earlier in tutorial
                                        scheme,
                                        old_to_new_lookup,
                                        proc_qubit_allocation4each_qpu)
    return partitioned_gate_tuples
    
    