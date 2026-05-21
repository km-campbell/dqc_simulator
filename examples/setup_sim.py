from dqc_simulator.software.compilers import (
    sort_many_qpus_greedily_by_node_and_time as default_compiler,
)
from dqc_simulator.software.compiler_preprocessing import (
    preprocess_qasm_to_compilable_monolithic as preprocess,
)
from dqc_simulator.software.dqc_control import DQCMasterProtocol
from dqc_simulator.software.partitioner import (
    first_come_first_served_qubits_to_qpus as allocate,
    partition_gate_tuples as partition,
)


def setup_sim(dqc, circuit_filepath):
    # Retrieving QPU nodes from DQC
    nodes = list(dqc.nodes.values())

    # import .qasm file and convert to gate_tuples for monolithic_circuit
    include_path = "."  # assuming qelib1.inc is in current working directory
    monolithic_circuit = preprocess(circuit_filepath, include_path=include_path)
    monolithic_circuit = monolithic_circuit.ops  # gate_tuples

    # Determine allocation of processing qubits to QPUs
    old_to_new_lookup, proc_qubit_allocation4each_qpu = allocate(
        monolithic_circuit, list(dqc.nodes.values())
    )

    # Partition according to the previously defined qubit allocation
    scheme = "cat"  # the remote gate scheme to use
    partitioned_gate_tuples = partition(
        monolithic_circuit,
        dqc,  # defined earlier in tutorial
        scheme,
        old_to_new_lookup,
        proc_qubit_allocation4each_qpu,
    )
    # Setting up the software
    protocol = DQCMasterProtocol(
        partitioned_gate_tuples, nodes=dqc.nodes, compiler_func=default_compiler
    )
    return protocol, nodes
