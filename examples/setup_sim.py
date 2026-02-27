from netsquid.components import instructions as instr
import numpy as np

from dqc_simulator.software.dqc_control import DQCMasterProtocol
from dqc_simulator.util.helper import get_data_collector

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
