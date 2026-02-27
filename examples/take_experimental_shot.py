import netsquid as ns
from netsquid.qubits import QFormalism

from setup_hardware import setup_hardware
from setup_sim import setup_sim

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
