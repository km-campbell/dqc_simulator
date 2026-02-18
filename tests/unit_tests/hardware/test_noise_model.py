# -*- coding: utf-8 -*-
"""
Created on Fri May 19 15:01:04 2023

@author: kenny
"""

import unittest

import netsquid as ns
import numpy as np
import pydynaa
import pandas
from netsquid.util.datacollector import DataCollector
from netsquid.protocols.protocol import Signals
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
from netsquid.qubits.qformalism import set_qstate_formalism, QFormalism
from netsquid.components import instructions as instr
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.models.qerrormodels import (DepolarNoiseModel,
                                                     DephaseNoiseModel)
from netsquid.components.models.delaymodels import (FibreDelayModel,
                                                    FixedDelayModel)

from dqc_simulator.hardware.noise_models import ( 
                                              AnalyticalDepolarisationModel)
from dqc_simulator.qlib.gates import (INSTR_ARB_GEN, INSTR_CH, INSTR_CT, 
                                      INSTR_T_DAGGER, INSTR_IDENTITY)


class TestAnalyticalDepolarisationModelWorksOnGates(unittest.TestCase):
    def test_entangling_gate_with_10_percent_error(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        p_depolar_error_cnot = 0.1
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0, 1])
        prog.apply(instr.INSTR_H, [0])
        prog.apply(instr.INSTR_CNOT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        desired_state = np.array([[(2 - p_depolar_error_cnot)/4, 0, 0, (1-p_depolar_error_cnot)/2],
                                  [0, p_depolar_error_cnot/4, 0, 0],
                                  [0, 0, p_depolar_error_cnot/4, 0],
                                  [(1-p_depolar_error_cnot)/2, 0, 0, (2 - p_depolar_error_cnot)/4]], 
                                 dtype=complex)
        fidelity = qapi.fidelity([qubit0, qubit1], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_entangling_gate_with_extra_qubit(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        p_depolar_error_cnot = 0.5
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0, 1, 2])
        prog.apply(instr.INSTR_H, [0])
        prog.apply(instr.INSTR_CNOT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        qubit2, = processor.pop(2)
        desired_state = np.diag(np.array([(2-p_depolar_error_cnot)/4, 
                                 0, p_depolar_error_cnot/4, 
                                 0, p_depolar_error_cnot/4, 0,
                                 (2-p_depolar_error_cnot)/4, 0],
                                         dtype=complex))
        desired_state[0, -2] = (1 - p_depolar_error_cnot)/2
        desired_state[-2, 0] = (1 - p_depolar_error_cnot)/2
        fidelity = qapi.fidelity([qubit0, qubit1, qubit2], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_entangling_gate_with_combined_input_state(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        p_depolar_error_cnot = 0.5
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        processor.execute_instruction(instr.INSTR_INIT, [0, 1, 2], physical=False)
        processor.execute_instruction(instr.INSTR_H, [0], physical=False)
        processor.execute_instruction(instr.INSTR_CNOT, [0, 2], physical=False)
        processor.execute_instruction(instr.INSTR_CNOT, [0, 2], physical=False)
        prog.apply(instr.INSTR_CNOT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        qubit2, = processor.pop(2)
        desired_state = np.diag(np.array([(2-p_depolar_error_cnot)/4, 
                                 0, p_depolar_error_cnot/4, 
                                 0, p_depolar_error_cnot/4, 0,
                                 (2-p_depolar_error_cnot)/4, 0],
                                         dtype=complex))
        desired_state[0, -2] = (1 - p_depolar_error_cnot)/2
        desired_state[-2, 0] = (1 - p_depolar_error_cnot)/2
        fidelity = qapi.fidelity([qubit0, qubit1, qubit2], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_recover_ideal_case_when_error_0(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1/np.sqrt(2)
        beta=1/np.sqrt(2)
        num_positions=7
        p_depolar_error_cnot = 0.0
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0, 1, 2])
        prog.apply(instr.INSTR_H, [0])
        prog.apply(instr.INSTR_CNOT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        qubit2, = processor.pop(2)
        desired_state = (alpha * np.kron(ks.s0, np.kron(ks.s0, ks.s0)) +
                         beta * np.kron(ks.s1, np.kron(ks.s1, ks.s0)))
        fidelity = qapi.fidelity([qubit0, qubit1, qubit2], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_02_entangling_gate(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        p_depolar_error_cnot = 0.5
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        processor.execute_instruction(instr.INSTR_INIT, [0, 1, 2], physical=False)
        processor.execute_instruction(instr.INSTR_H, [0], physical=False)
        prog.apply(instr.INSTR_CNOT, [0, 2])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        qubit2, = processor.pop(2)
        desired_state = np.diag(np.array([(2-p_depolar_error_cnot)/4, 
                                 p_depolar_error_cnot/4, 0,
                                 0, p_depolar_error_cnot/4,
                                 (2-p_depolar_error_cnot)/4, 
                                 0, 0], dtype=complex))
        desired_state[0, -3] = (1 - p_depolar_error_cnot)/2
        desired_state[-3, 0] = (1 - p_depolar_error_cnot)/2
        fidelity = qapi.fidelity([qubit0, qubit1, qubit2], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_02_entangling_gate_with_012_combined(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        p_depolar_error_cnot = 0.5
        cnot_depolar_model = AnalyticalDepolarisationModel(p_error=p_depolar_error_cnot)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=None,
                                     phys_instructions=physical_instructions)
        prog = QuantumProgram()
        processor.execute_instruction(instr.INSTR_INIT, [0, 1, 2], physical=False)
        processor.execute_instruction(instr.INSTR_H, [0], physical=False)
        processor.execute_instruction(instr.INSTR_CNOT, [0, 1], physical=False)
        processor.execute_instruction(instr.INSTR_CNOT, [0, 1], physical=False)
        prog.apply(instr.INSTR_CNOT, [0, 2])
        processor.execute_program(prog)
        ns.sim_run(1000)
        qubit0, = processor.pop(0)
        qubit1, = processor.pop(1)
        qubit2, = processor.pop(2)
        desired_state = np.diag(np.array([(2-p_depolar_error_cnot)/4, 
                                 p_depolar_error_cnot/4, 0,
                                 0, p_depolar_error_cnot/4,
                                 (2-p_depolar_error_cnot)/4, 
                                 0, 0], dtype=complex))
        desired_state[0, -3] = (1 - p_depolar_error_cnot)/2
        desired_state[-3, 0] = (1 - p_depolar_error_cnot)/2
        fidelity = qapi.fidelity([qubit0, qubit1, qubit2], desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        


class TestAnalyticalDepolarisationModelCanApplyMemoryDecoherence(unittest.TestCase):
    def test_get_ideal_result4one_qubit_when_error_rate_0(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        depol_rate = 0. 
        memory_noise_model = AnalyticalDepolarisationModel(
            p_error=depol_rate, time_independent=False)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=None),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=memory_noise_model,
                                     phys_instructions=physical_instructions)
        processor.execute_instruction(instr.INSTR_INIT, [0], physical=True)
        ns.sim_run(100)
        qubit, = processor.pop(0)
        fidelity = qapi.fidelity(qubit, ks.s0)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_can_degrade_qubit_over_10s_with_error_rate_0point1Hz(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        depol_rate = 1/10 #Hz
        memory_noise_model = AnalyticalDepolarisationModel(
            p_error=depol_rate, time_independent=False)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=0, parallel=False,
                                toplogy = None), #setting duration to zero
                                                 #means you can't have any
                                                 #subsequent gates without
                                                 #processor busy error
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=None),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=memory_noise_model,
                                     phys_instructions=physical_instructions)
        prog=QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0])
        processor.execute_program(prog)
        ns.sim_run(10**10) #running for 10s
        qubit, = processor.peek(0)
        desired_state = np.array([[(1 + np.exp(-1))/2, 0],
                                  [0, (1 - np.exp(-1))/2]])
        fidelity = qapi.fidelity(qubit, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_can_degrade_2_qubits_over_10s_with_error_rate_0point1Hz(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        depol_rate = 1/10 #Hz
        memory_noise_model = AnalyticalDepolarisationModel(
            p_error=depol_rate, time_independent=False)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=0, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=None),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=memory_noise_model,
                                     phys_instructions=physical_instructions)
        prog=QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(10**10) #running for 10s
        qubits = processor.peek([0, 1])
        desired_state = 1/4 * np.diag([(1 + np.exp(-1))**2, 
                                       (1 + np.exp(-1))*(1 - np.exp(-1)), 
                                       (1 + np.exp(-1))*(1 - np.exp(-1)),
                                       (1 - np.exp(-1))**2])
        fidelity = qapi.fidelity(qubits, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_can_give_correct_result4_10_qubits(self):
        import functools as ft
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=10
        depol_rate = 1/10 #Hz
# =============================================================================
#             depol_rate=0
# =============================================================================
        memory_noise_model = AnalyticalDepolarisationModel(
            p_error=depol_rate, time_independent=False)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=0, parallel=False, toplogy = None),
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=None),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=memory_noise_model,
                                     phys_instructions=physical_instructions)
        prog=QuantumProgram()
        prog.apply(instr.INSTR_INIT, [ii for ii in range(10)])
        processor.execute_program(prog)
        ns.sim_run(10**10) #running for 10s
        qubits = processor.peek([ii for ii in range(10)])
        single_qubit_desired_state = np.array([[(1 + np.exp(-1))/2, 0],
                                  [0, (1 - np.exp(-1))/2]])
        ten_qubit_desired_state = ft.reduce(
            np.kron, [single_qubit_desired_state] * 10)
        fidelity = qapi.fidelity(qubits, ten_qubit_desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
        
    def test_decoherence_starts_after_initialisation(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        alpha=1 
        beta=0
        num_positions=7
        depol_rate = 1/10 #Hz
        memory_noise_model = AnalyticalDepolarisationModel(
            p_error=depol_rate, time_independent=False)
        #creating processor for all Nodes
        x_gate_duration = 1
        physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=10**9, parallel=False,
                                toplogy = None), #artificially long for 
            PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
                                quantum_noise_model=None),
            PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
            PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
            PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
            PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
                                quantum_noise_model=None, apply_q_noise_after=False,
                                discard=True),
            PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
            toplology=[0, 1]),
            PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
                                topology=None),
            PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
                                topology=None),
            PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
                                topology=None)]
        processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
                                     mem_noise_models=memory_noise_model,
                                     phys_instructions=physical_instructions)
        prog=QuantumProgram()
        prog.apply(instr.INSTR_INIT, [0])
        processor.execute_program(prog)
        ns.sim_run(10**10 + 10**9) #running for 11s. 1s for initialisation and
                                   #10s for subsequent depolarisation. 
        qubit, = processor.peek(0)
        desired_state = np.array([[(1 + np.exp(-1))/2, 0],
                                  [0, (1 - np.exp(-1))/2]]) 
            #the desired state assumes 10s depolarisation at rate of 1/10 Hz
            #if depolarisation occurs during decoherence this will not be the
            #right state and the test will fail
        fidelity = qapi.fidelity(qubit, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)
            
            
# =============================================================================
# class TestImpactOfIdentityAsDelay(unittest.TestCase):
#     def test_idenity_does_not_change_state(self):
#             ns.sim_reset()
#             set_qstate_formalism(QFormalism.DM)
#             alpha=1 
#             beta=0
#             num_positions=7
#             #creating processor for all Nodes
#             x_gate_duration = 1
#             physical_instructions = [
#                 PhysicalInstruction(INSTR_IDENTITY, duration = 10**9,
#                                     parallel=True, toplogy=None), #for making
#                     #qubit sit in memory doing nothing for 10s
#                 PhysicalInstruction(instr.INSTR_INIT, duration=1, parallel=False, toplogy = None),
#                 PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
#                                     quantum_noise_model=None),
#                 PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
#                 PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
#                                     quantum_noise_model=None, apply_q_noise_after=False,
#                                     discard=True),
#                 PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
#                 toplology=[0, 1]),
#                 PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
#                                     topology=None)]
#             processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
#                                          mem_noise_models=None,
#                                          phys_instructions=physical_instructions)
#             prog=QuantumProgram()
#             prog.apply(instr.INSTR_INIT, [0, 1])
#             prog.apply(INSTR_IDENTITY, [0])
#             processor.execute_program(prog)
#             ns.sim_run(10 * 10**9 + 1) #running for at most 10s + 1ns
#             qubits = processor.peek([0, 1])
#             print(f"qubit {qubits[0]} has state"
#                   f" {ns.qubits.reduced_dm(qubits[0])} and qubit {qubits[1]}"
#                   f" has state {ns.qubits.reduced_dm(qubits[1])}")
#             fidelity = qapi.fidelity(qubits, np.kron(ks.s0, ks.s0))
#             self.assertAlmostEqual(fidelity, 1.00000, 5)
#             
#     def test_identity_does_not_change_state_when_there_is_mem_decoherence(self):
#             ns.sim_reset()
#             set_qstate_formalism(QFormalism.DM)
#             alpha=1 
#             beta=0
#             num_positions=7
#             depol_rate = 1/10 #Hz
#             memory_noise_model = AnalyticalDepolarisationModel(
#                 p_error=depol_rate, time_independent=False)
#             #creating processor for all Nodes
#             x_gate_duration = 1
#             physical_instructions = [
#                 PhysicalInstruction(INSTR_IDENTITY, duration = 10**9,
#                                     parallel=True, toplogy=None), #for making
#                     #qubit sit in memory doing nothing for 10s
#                 PhysicalInstruction(instr.INSTR_INIT, duration=1, parallel=False, toplogy = None),
#                 PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
#                                     quantum_noise_model=None),
#                 PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
#                 PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
#                                     quantum_noise_model=None, apply_q_noise_after=False,
#                                     discard=True),
#                 PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
#                 toplology=[0, 1]),
#                 PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
#                                     topology=None)]
#             processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
#                                          mem_noise_models=memory_noise_model,
#                                          phys_instructions=physical_instructions)
#             prog=QuantumProgram()
#             prog.apply(instr.INSTR_INIT, [0, 1])
#             prog.apply(INSTR_IDENTITY, [0])
# # =============================================================================
# #             prog.apply(INSTR_IDENTITY, [1])
# # =============================================================================
#             processor.execute_program(prog)
#             ns.sim_run(10 * 10**9 + 1) #running for 10s + 1 ns
#             q1, q2 = processor.peek([0, 1])
#             fidelity = qapi.fidelity(q1, q2.qstate.dm)
#             self.assertAlmostEqual(fidelity, 1.00000, 5)
#             #adding prog.apply(INSTR_IDENITY, [1]) avoids the failure, 
#             #inidicating that the issue is indeed caused by the presence of the 
#             #idenity acting on one qubit but not the other. This is suprising,
#             #given that there is no noise model on the identity, so all it 
#             #should contribute is time. It should be noted that the discrepancy
#             #caused by the identity is slight 0.00017466087052198098 difference
#             #from what it should be. This may be due to a rounding error but
#             #this seems to be a large error for that. When I print out the 
#             #state of each qubit (inside the decoherence model), I find that
#             #the discrepancy caused by the idenity is the same regardless
#             #of which qubit it is applied to. The presence of the idenity 
#             #changes the state of a qubit from [[0.66643554+0.j 0.        +0.j]
#             #[0.        +0.j 0.33356446+0.j]] to 
#             #[[0.68393972+0.j 0.        +0.j]
#             #[0.        +0.j 0.31606028+0.j]]. I do not yet understand why 
#             #this is occuring. The discrepancy seems far to small to be due to
#             #decoherence only being applied to one qubit but there is no issue
#             #at all when decoherence is not applied anywhere. The issue only
#             #occurs when memory decoherence is present.
#             
#     def test_identity_does_not_change_state_when_there_is_mem_decoherence_in_10_qubit_system(self):
#             import functools as ft
#             ns.sim_reset()
#             set_qstate_formalism(QFormalism.DM)
#             alpha=1 
#             beta=0
#             num_positions=10
#             depol_rate = 1/10 #Hz
# # =============================================================================
# #             depol_rate=0
# # =============================================================================
#             memory_noise_model = AnalyticalDepolarisationModel(
#                 p_error=depol_rate, time_independent=False)
#             #creating processor for all Nodes
#             x_gate_duration = 1
#             physical_instructions = [
#                 PhysicalInstruction(INSTR_IDENTITY, duration = 10**9,
#                                     parallel=True, toplogy=None), #for making
#                     #qubit sit in memory doing nothing for 10s
#                 PhysicalInstruction(instr.INSTR_INIT, duration=1, parallel=False, toplogy = None),
#                 PhysicalInstruction(instr.INSTR_H, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_X, duration=x_gate_duration, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_Z, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_S, duration=1, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CNOT, duration=4, parallel=False, topology=None, 
#                                     quantum_noise_model=None),
#                 PhysicalInstruction(INSTR_ARB_GEN(alpha, beta), duration=4, parallel=False),
#                 PhysicalInstruction(INSTR_CH, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(INSTR_CT, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_CS, duration=4, parallel=False, topology=None),
#                 PhysicalInstruction(instr.INSTR_MEASURE, duration=7, parallel=False, topology=None,
#                                     quantum_noise_model=None, apply_q_noise_after=False,
#                                     discard=True),
#                 PhysicalInstruction(instr.INSTR_DISCARD, duration=3, parallel=False,
#                 toplology=[0, 1]),
#                 PhysicalInstruction(instr.INSTR_SWAP, duration = 12, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(instr.INSTR_T, duration=1, parallel=False, 
#                                     topology=None),
#                 PhysicalInstruction(INSTR_T_DAGGER, duration=1, parallel=False,
#                                     topology=None)]
#             processor = QuantumProcessor("noisy_processor", num_positions=num_positions,
#                                          mem_noise_models=memory_noise_model,
#                                          phys_instructions=physical_instructions)
#             prog=QuantumProgram()
#             prog.apply(instr.INSTR_INIT, [ii for ii in range(10)])
#             prog.apply(INSTR_IDENTITY, [0], physical=True)
# # =============================================================================
# #             prog.apply(INSTR_IDENTITY, [1])
# # =============================================================================
#             processor.execute_program(prog)
#             ns.sim_run(10 * 10**9 + 1) #running for 10s + 1ns (1ns for
#                                        #initialisation)
#             qubits = processor.peek([ii for ii in range(10)])
#             print(f"qubits have state {ns.qubits.reduced_dm(qubits)}")
#             single_qubit_desired_state = np.array([[(1 + np.exp(-1))/2, 0],
#                                       [0, (1 - np.exp(-1))/2]])
#             ten_qubit_desired_state = ft.reduce(
#                 np.kron, [single_qubit_desired_state] * 10)
#             print(f"desired state is {ten_qubit_desired_state}")
#             fidelity = qapi.fidelity(qubits, ten_qubit_desired_state)
#             self.assertAlmostEqual(fidelity, 1.00000, 5)
#             #See comment under previous test for more context on why this is 
#             #failing. I should note that the magnitude of the discrepancy has
#             #increased by an order of magnitude when I increased the number of
#             #qubits from 2 (in prev test) to 10 (in this one). This suggests
#             #the issue must be addressed to avoid a large error in big circuits.
#             #Note, I have only looked at the identity because applying other 
#             #gates should change things (even if the gates cancel) as the 
#             #decohorence means the input to sequential gates will change.
# =============================================================================
                





if __name__ == '__main__':
    unittest.main()
