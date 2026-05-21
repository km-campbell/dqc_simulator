"""The experimental setup for multiple_monolithic_circuits.py"""

import netsquid as ns
from netsquid.qubits import QFormalism, qubitapi as qapi

from setup_hardware import setup_hardware
from setup_sim import setup_sim


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
    protocol, nodes = setup_sim(dqc, circuit_filepath)

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
    # Choosing circuits to use (assuming the files are in the current working
    # directory)
    circuit_filepaths = [
        "ghz_5qubits.qasm",  # GHZ generation circuit
        "grover_5qubits.qasm",  # Grover algorithm
        "qft_5qubits.qasm",  # QFT
    ]

    data = {}
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
        data[circuit] = fidelity
    return data


print(
    run_experiment(
        F_werner=0.99,
        p_depolar_error_cnot=1e-03,
        single_qubit_gate_error_prob=2e-05,
        meas_error_prob=3e-03,
        memory_depolar_rate=0.055,
    )
)

# Expected result:
# {'ghz_5qubits.qasm': 0.9570522876374276,
# 'grover_5qubits.qasm': 0.1071574284590638,
# 'qft_5qubits.qasm': 0.6470482939691747}
