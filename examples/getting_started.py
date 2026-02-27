"""
A useful template for running a full simulation.
"""

import itertools as it

import netsquid as ns
from netsquid.components import instructions as instr
from netsquid.qubits import QFormalism
import numpy as np

from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
from dqc_simulator.hardware.dqc_creation import DQC
from dqc_simulator.hardware.quantum_processors import NoisyQPU
from dqc_simulator.qlib.states import werner_state
from dqc_simulator.software.dqc_control import DQCMasterProtocol
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


def setup_sim(dqc):
    # Retrieving QPU nodes from DQC
    node_0 = dqc.get_node("node_0")
    node_1 = dqc.get_node("node_1")
    node_2 = dqc.get_node("node_2")

    # Identifying the processing qubits that we wish to initialise
    qubits0 = node_0.qmemory.processing_qubit_positions[0:3]
    qubits1 = node_1.qmemory.processing_qubit_positions[0:3]
    qubits2 = node_2.qmemory.processing_qubit_positions[0:3]

    # Defining the gates
    gate_tuples = [
        (instr.INSTR_INIT, qubits0, node_0.name),
        (instr.INSTR_INIT, qubits1, node_1.name),
        (instr.INSTR_INIT, qubits2, node_2.name),
        (instr.INSTR_H, qubits0[0], node_0.name),
        (instr.INSTR_CNOT, qubits0[0], node_0.name, qubits1[0], node_1.name, "cat"),
    ]

    # Setting up the software
    protocol = DQCMasterProtocol(gate_tuples, nodes=dqc.nodes)

    # Preparing data collection
    qubit_indices_2b_checked = [(qubits0[0], node_0), (qubits1[0], node_1)]
    desired_state = np.sqrt(1 / 2) * np.array([[1], [0], [0], [1]])
    dc = get_data_collector(protocol, qubit_indices_2b_checked, desired_state)
    return protocol, dc


def take_experimental_shot(
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
    protocol, dc = setup_sim(dqc)

    # Running the circuit
    protocol.start()
    ns.sim_run()
    fidelity = dc.dataframe["fidelity"].iloc[0]
    return fidelity


print(take_experimental_shot())
print(
    take_experimental_shot(
        F_werner=0.9,
        p_depolar_error_cnot=1e-03,
        single_qubit_gate_error_prob=2e-05,
        meas_error_prob=3e-03,
        memory_depolar_rate=0.055,
    )
)
# Expected result:
# 1.0000....
# 0.8921630426886507
