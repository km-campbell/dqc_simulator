import itertools as it

from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
from dqc_simulator.hardware.dqc_creation import DQC
from dqc_simulator.hardware.quantum_processors import NoisyQPU
from dqc_simulator.qlib.states import werner_state

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
    quantum_topology = [(0, 1)]
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
