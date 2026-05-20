"""This is similar to from_monolithic_circuit.py but has been adapted to collect data from multiple circuits"""

import functools as ft
import itertools as it


import netsquid as ns
from netsquid.qubits import QFormalism, qubitapi as qapi
import numpy as np
import pandas as pd

from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
from dqc_simulator.hardware.dqc_creation import DQC
from dqc_simulator.hardware.quantum_processors import NoisyQPU
from dqc_simulator.qlib.states import werner_state
from dqc_simulator.software.compiler_preprocessing import (
    preprocess_qasm_to_compilable_monolithic as preprocess,
)
from dqc_simulator.software.dqc_control import DQCMasterProtocol
from dqc_simulator.software.partitioner import (
    first_come_first_served_qubits_to_qpus as allocate,
    partition_gate_tuples as partition,
)
from dqc_simulator.util.helper import get_data_collector


def setup_hardware(
    F_werner=1,
    p_depolar_error_cnot=0,
    single_qubit_gate_error_prob=0,
    meas_error_prob=0,
    memory_depolar_rate=0,
):
    ent_dist_rate = 182  # Hz

    # Defining QPU
    qpu_class = NoisyQPU
    kwargs4qpu = {
        "p_depolar_error_cnot": p_depolar_error_cnot,
        "single_qubit_gate_error_prob": single_qubit_gate_error_prob,
        "meas_error_prob": meas_error_prob,
        "comm_qubit_depolar_rate": memory_depolar_rate,
        "proc_qubit_depolar_rate": memory_depolar_rate,
        "single_qubit_gate_time": 135 * 10**3,
        "two_qubit_gate_time": 600 * 10**3,
        "measurement_time": 600 * 10**4,
        "num_positions": 10,
        "num_comm_qubits": 2,
    }

    # Defining connection
    entangling_connection_class = BlackBoxEntanglingQsourceConnection
    kwargs4conn = {
        "delay": 1e9 / ent_dist_rate,  # 1e9 used because ent_dist_rate in Hz
        "state4distribution": werner_state(F_werner),
    }

    # Setting up the hardware
    num_qpus = 3
    quantum_topology = list(it.combinations(range(3), 2))
    classical_topology = list(it.combinations(range(3), 2))
    dqc = DQC(
        entangling_connection_class,
        num_qpus,
        quantum_topology,
        classical_topology,
        qpu_class=qpu_class,
        **kwargs4qpu,
        **kwargs4conn,
    )
    return dqc


def setup_software(dqc, circuit_filepath):
    # Retrieving QPU nodes from DQC
    nodes = list(dqc.nodes.values())

    # import .qasm file and convert to gate_tuples for monolithic_circuit
    include_path = "."  # assuming qelib1.inc is in current working directory
    dqc_circuit = preprocess(circuit_filepath, include_path=include_path)
    monolithic_circuit = dqc_circuit.ops  # gate_tuples

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
    protocol = DQCMasterProtocol(partitioned_gate_tuples, nodes=dqc.nodes)
    return protocol, nodes


def setup_data_collection(protocol, nodes, desired_state):
    # Preparing data collection
    qubit_indices_2b_checked = [
        (nodes[0].qmemory.processing_qubit_positions[0:2], nodes[0]),
        (nodes[1].qmemory.processing_qubit_positions[0:2], nodes[1]),
        (nodes[2].qmemory.processing_qubit_positions[0], nodes[2]),
    ]
    dc = get_data_collector(protocol, qubit_indices_2b_checked, desired_state)
    return dc


def take_experimental_shot(
    circuit_filepath,
    F_werner=1,
    p_depolar_error_cnot=0,
    single_qubit_gate_error_prob=0,
    meas_error_prob=0,
    memory_depolar_rate=0,
):
    # Setting the formalism used to the density matrix formalism
    ns.set_qstate_formalism(QFormalism.DM)

    # Restting the state of the simulation (this is good practice)
    ns.sim_reset()

    # Setting up the hardware, software and data collection
    dqc = setup_hardware(
        F_werner=F_werner,
        p_depolar_error_cnot=p_depolar_error_cnot,
        single_qubit_gate_error_prob=single_qubit_gate_error_prob,
        meas_error_prob=meas_error_prob,
        memory_depolar_rate=memory_depolar_rate,
    )
    protocol, nodes = setup_software(dqc, circuit_filepath)

    # Running the circuit
    protocol.start()
    ns.sim_run()

    qubits_2b_checked = []
    for node in nodes:
        positions = node.qmemory.processing_qubit_positions
        qubits = node.qmemory.pop(positions)
        qubits_2b_checked += [qubit for qubit in qubits if qubit is not None]
    return qubits_2b_checked


def run_experiment(
    F_werner=1,
    p_depolar_error_cnot=0,
    single_qubit_gate_error_prob=0,
    meas_error_prob=0,
    memory_depolar_rate=0,
):
    # Choosing circuits to use
    circuit_filepaths = [
        "ghz_indep_qiskit_5.qasm"  # assuming this is in current working directory
    ]

    for circuit in circuit_filepaths:
        # Run ideal shot
        ideal_qubits = take_experimental_shot(circuit)
        actual_qubits = take_experimental_shot(
            circuit,
            F_werner=F_werner,
            p_depolar_error_cnot=p_depolar_error_cnot,
            single_qubit_gate_error_prob=single_qubit_gate_error_prob,
            meas_error_prob=meas_error_prob,
            memory_depolar_rate=memory_depolar_rate,
        )
        desired_state = qapi.reduced_dm(ideal_qubits)
        fidelity = qapi.fidelity(actual_qubits, desired_state, squared=True)
    
    


run_experiment(
    F_werner=0.9,
    p_depolar_error_cnot=1e-03,
    single_qubit_gate_error_prob=2e-05,
    meas_error_prob=3e-03,
    memory_depolar_rate=0.055,
)

# print(take_experimental_shot())
# print(
#     take_experimental_shot(
        # F_werner=0.9,
        # p_depolar_error_cnot=1e-03,
        # single_qubit_gate_error_prob=2e-05,
        # meas_error_prob=3e-03,
        # memory_depolar_rate=0.055,
#     )
# )
# Expected result:
# 1.0000000000000002 # note slightly greater than 1 due to floating point error
# 0.7928258818055854
