# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 11:02:43 2023

@author: kenny
"""

import numpy as np

from netsquid.components import instructions as instr
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.components.models.qerrormodels import (DepolarNoiseModel, 
                                                     DephaseNoiseModel)
from netsquid.components.models.delaymodels import (FibreDelayModel,
                                                    FixedDelayModel)

from dqc_simulator.hardware.noise_models import AnalyticalDepolarisationModel
from dqc_simulator.qlib.gates import (INSTR_ARB_GEN, INSTR_CH, INSTR_CT,
                                      INSTR_T_DAGGER,
                                      INSTR_S_DAGGER,
                                      INSTR_SINGLE_QUBIT_UNITARY, 
                                      INSTR_TWO_QUBIT_UNITARY)

#creating custom instructions


# =============================================================================
# #defining alternative initialisation instruction to replicate doing an x-gate
# #after measurement. (This is useful because it allows the qstate to be reduced
# #after measurement). When implementing physical instructions. The noise and 
# #duration should be kept the same as the x-gate
# INSTR_ALT_INIT = instr.IInit(num_positions=1)
# =============================================================================

def create_processor(alpha=1, beta=0, depolar_rate=0, dephase_rate=0, 
                     num_positions=7, name="quantum_processor"):
    """Factory to create a quantum processor for each end node. The gate 
    durations are too small to be physical. This processor was used for cases
    where gate duration (as long as it was finite to avoid processor busy
    errors) did not matter.

    Has seven memory positions and the physical instructions necessary
    for remote gates using single and two-qubit local gates.

    Parameters
    ----------
    depolar_rate : float
        Depolarization rate of qubits in memory.
    dephase_rate : float
        Dephasing rate of physical measurement instruction.

    Returns
    -------
    :class:`~netsquid.components.qprocessor.QuantumProcessor`
        A quantum processor to specification.

    """
    measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
                                            time_independent=True)
    x_gate_duration = 1
    physical_instructions = [
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False,
                            toplogy = [2, 3, 4, 5, 6]),
        PhysicalInstruction(instr.INSTR_H, duration=1, parallel=True,
                            topology=None),
        PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration,
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=True,
                            topology=None),
        PhysicalInstruction(instr.INSTR_S, duration=1, parallel=True,
                            topology=None),
        PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=True,
                            topology=None),
        PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4,
                            parallel=False),
        PhysicalInstruction(INSTR_CH, duration=4, parallel=True,
                            topology=None),
        PhysicalInstruction(INSTR_CT, duration=4, parallel=True,
                            topology=None),
        PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=True,
                            topology=None),
        PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False,
                            topology=None, quantum_noise_model=None, 
                            apply_q_noise_after=False, discard=True),
        PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
        toplology=[0, 1]),
        PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=True, 
                            topology=None),
        PhysicalInstruction(instr.INSTR_T, duration=1, parallel=True, 
                            topology=None),
        PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=True,
                            topology=None)]
    memory_noise_model = DepolarNoiseModel(depolar_rate=depolar_rate)
    processor = QuantumProcessor(name, num_positions=num_positions,
                                 mem_noise_models=(
                                     [memory_noise_model] * num_positions),
                                 phys_instructions=physical_instructions)
    return processor 


def create_qproc_with_analytical_noise_ionQ_aria_durations(
                                         p_depolar_error_cnot,
                                         comm_qubit_depolar_rate,
                                         data_qubit_depolar_rate,
                                         single_qubit_gate_time=135 * 10**3,
                                         two_qubit_gate_time=600 * 10**3,
                                         measurement_time=300 * 10**3,
                                         alpha=1, beta=0,
                                         num_positions=20,
                                         num_comm_qubits=2):
    
    """
    Uses universal gate sets from Nielsen Chuang. Analytical noise is used.
    Gate durations are taken from averages for single and two-qubit gates on
    IonQ's Aria machine.
    
    Parameters
    ----------
    p_depolar_error_cnot : float
        The probability of a depolarisation error after each CNOT gate.
    
    alpha : float, optional
        Setting for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default 
        is 1.
    beta : float, optional
        Setting for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default
        is 0.

    Returns
    -------
    qprocessor : netsquid.components.qprocessor
        .

    """
    
    num_data_qubits = num_positions - num_comm_qubits
    cnot_depolar_model = AnalyticalDepolarisationModel(
        p_error=p_depolar_error_cnot, time_independent=True)
    comm_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        comm_qubit_depolar_rate, time_independent=False)
    data_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        data_qubit_depolar_rate, time_independent=False)
    #creating processor for all Nodes
    physical_instructions = [
        PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False,
                            toplogy=None),
        PhysicalInstruction(instr.INSTR_H, duration=single_qubit_gate_time, 
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_X, duration=single_qubit_gate_time,
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_Z, duration=single_qubit_gate_time,
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_S, duration=single_qubit_gate_time,
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_CNOT, duration=two_qubit_gate_time,
                            parallel=True, topology=None, 
                            quantum_noise_model=cnot_depolar_model),
        PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), 
                            duration=3, parallel=True),
                                            #duration deliberately negligible
                                            #to approximate ideality for 
                                            #when not interested in how input
                                            #state arrived at
        PhysicalInstruction(instr.INSTR_CS, duration=two_qubit_gate_time, 
                            parallel=True, topology=None),
        PhysicalInstruction(instr.INSTR_MEASURE, duration=measurement_time,
                            parallel=True, topology=None,
                            quantum_noise_model=None, 
                            apply_q_noise_after=False,
                            discard=True),
        PhysicalInstruction(instr.INSTR_DISCARD, 
                            duration=single_qubit_gate_time, parallel=False,
                            toplology=[ii for ii in range(num_comm_qubits)]),
        PhysicalInstruction(instr.INSTR_SWAP, duration=1e-10, 
                            parallel=True, 
                            topology=None), #duration deliberately negligible
                                            #to approximate ideality for 
                                            #TP-safe
        PhysicalInstruction(instr.INSTR_T, duration=single_qubit_gate_time,
                            parallel=True, 
                            topology=None),
        PhysicalInstruction(INSTR_T_DAGGER, duration=single_qubit_gate_time,
                            parallel=True,
                            topology=None)]
    qprocessor = QuantumProcessor(
        "custom_noisy_qprocessor",
        phys_instructions=physical_instructions, 
        num_positions=num_positions, mem_pos_types=["comm"] * num_comm_qubits
        + ["data"] * num_data_qubits, mem_noise_models=
        [comm_qubit_memory_depolar_model] * num_comm_qubits +
        [data_qubit_memory_depolar_model] * num_data_qubits)
    
    #TO DO: figure out if mem_pos_types is actually doing
    #anything - I can find no way to actually access the metadata (which would
    #potentially be a useful thing to do)
    return qprocessor



#following not yet tested!
def create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(   
                                         p_depolar_error_cnot,
                                         comm_qubit_depolar_rate,
                                         data_qubit_depolar_rate,
                                         single_qubit_gate_time=135 * 10**3,
                                         two_qubit_gate_time=600 * 10**3,
                                         measurement_time=600 * 10**4,
                                         alpha=1, beta=0,
                                         num_positions=20,
                                         num_comm_qubits=2):
    num_data_qubits = num_positions - num_comm_qubits
    cnot_depolar_model = AnalyticalDepolarisationModel(
        p_error=p_depolar_error_cnot, time_independent=True)
    comm_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        comm_qubit_depolar_rate, time_independent=False)
    data_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        data_qubit_depolar_rate, time_independent=False)
    #creating processor for all Nodes
    physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False,
                                toplogy=None),
            PhysicalInstruction(instr.INSTR_H, duration=single_qubit_gate_time, 
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(INSTR_S_DAGGER, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=two_qubit_gate_time,
                                parallel=True, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), 
                                duration=3, parallel=True),
                                                #duration deliberately negligible
                                                #to approximate ideality for 
                                                #when not interested in how input
                                                #state arrived at
            PhysicalInstruction(instr.INSTR_MEASURE, duration=measurement_time,
                                parallel=True, topology=None,
                                quantum_noise_model=None, 
                                apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, 
                                duration=single_qubit_gate_time, parallel=False,
                                toplology=[ii for ii in range(num_comm_qubits)]),
# =============================================================================
#             PhysicalInstruction(instr.INSTR_SWAP, duration=1e-10, 
#                                 parallel=True, 
#                                 topology=None), #duration deliberately negligible
#                                                 #to approximate ideality for 
#                                                 #TP-safe. MAYBE REVISIT
# =============================================================================
            PhysicalInstruction(instr.INSTR_T, duration=single_qubit_gate_time,
                                parallel=True, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=single_qubit_gate_time,
                                parallel=True,
                                topology=None),
            PhysicalInstruction(INSTR_SINGLE_QUBIT_UNITARY, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(INSTR_TWO_QUBIT_UNITARY, 
                                duration=two_qubit_gate_time,
                                parallel=True, topology=None)]
    qprocessor = QuantumProcessor(
        "custom_noisy_qprocessor",
        phys_instructions=physical_instructions, 
        num_positions=num_positions, mem_pos_types=["comm"] * num_comm_qubits
        + ["data"] * num_data_qubits, mem_noise_models=
        [comm_qubit_memory_depolar_model] * num_comm_qubits +
        [data_qubit_memory_depolar_model] * num_data_qubits)
    
    qprocessor.add_composite_instruction(instr.INSTR_SWAP, 
                                         [(instr.INSTR_CNOT, (0, 1)),
                                          (instr.INSTR_CNOT, (1, 0)),
                                          (instr.INSTR_CNOT, (0, 1))],
                                         parallel=True, topology=None)
    return qprocessor


def create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(   
                                         p_depolar_error_cnot,
                                         comm_qubit_depolar_rate,
                                         data_qubit_depolar_rate,
                                         single_qubit_gate_time=135 * 10**3,
                                         two_qubit_gate_time=600 * 10**3,
                                         measurement_time=600 * 10**4, 
                                         alpha=1, beta=0,
                                         num_positions=20,
                                         num_comm_qubits=2):
    num_data_qubits = num_positions - num_comm_qubits
    cnot_depolar_model = DepolarNoiseModel(p_depolar_error_cnot, 
                                           time_independent=True)
    comm_qubit_memory_depolar_model = DepolarNoiseModel(comm_qubit_depolar_rate,
                                                        time_independent=False)
    data_qubit_memory_depolar_model = DepolarNoiseModel(data_qubit_depolar_rate,
                                                        time_independent=False)
    #creating processor for all Nodes
    physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False,
                                toplogy=None),
            PhysicalInstruction(instr.INSTR_H, duration=single_qubit_gate_time, 
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(INSTR_S_DAGGER, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=two_qubit_gate_time,
                                parallel=True, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), 
                                duration=3, parallel=True),
                                                #duration deliberately negligible
                                                #to approximate ideality for 
                                                #when not interested in how input
                                                #state arrived at
            PhysicalInstruction(instr.INSTR_MEASURE, duration=measurement_time,
                                parallel=True, topology=None,
                                quantum_noise_model=None, 
                                apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, 
                                duration=single_qubit_gate_time, parallel=False,
                                toplology=[ii for ii in range(num_comm_qubits)]),
# =============================================================================
#             PhysicalInstruction(instr.INSTR_SWAP, duration=1e-10, 
#                                 parallel=True, 
#                                 topology=None), #duration deliberately negligible
#                                                 #to approximate ideality for 
#                                                 #TP-safe
# =============================================================================
            PhysicalInstruction(instr.INSTR_T, duration=single_qubit_gate_time,
                                parallel=True, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=single_qubit_gate_time,
                                parallel=True,
                                topology=None),
            PhysicalInstruction(INSTR_SINGLE_QUBIT_UNITARY, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None),
            PhysicalInstruction(INSTR_TWO_QUBIT_UNITARY, 
                                duration=two_qubit_gate_time,
                                parallel=True, topology=None)]
    qprocessor = QuantumProcessor(
        "custom_noisy_qprocessor",
        phys_instructions=physical_instructions, 
        num_positions=num_positions, mem_pos_types=["comm"] * num_comm_qubits
        + ["data"] * num_data_qubits, mem_noise_models=
        [comm_qubit_memory_depolar_model] * num_comm_qubits +
        [data_qubit_memory_depolar_model] * num_data_qubits)
    
    qprocessor.add_composite_instruction(instr.INSTR_SWAP, 
                                         [(instr.INSTR_CNOT, (0, 1)),
                                          (instr.INSTR_CNOT, (1, 0)),
                                          (instr.INSTR_CNOT, (0, 1))],
                                         parallel=True, topology=None)
    return qprocessor







# =============================================================================
# def create_qproc_with_numerical_noise_ionQ_aria_durations(
#                                          p_depolar_error_cnot,
#                                          comm_qubit_depolar_rate,
#                                          data_qubit_depolar_rate,
#                                          single_qubit_gate_time=135 * 10**3,
#                                          two_qubit_gate_time=600 * 10**3,
#                                          measurement_time=300 * 10**3,
#                                          alpha=1, beta=0):
#     #NEED TO FINISH
#     
# =============================================================================
