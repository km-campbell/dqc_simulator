# -*- coding: utf-8 -*-
"""
Created on Tue May  9 15:19:27 2023

@author: kenny
"""

import unittest
import functools as ft

import netsquid as ns
import numpy as np
from netsquid.components import instructions as instr
from netsquid.qubits import ketstates as ks
from netsquid.qubits import qubitapi as qapi
from netsquid.nodes import Node, Network
from netsquid.qubits.qformalism import set_qstate_formalism, QFormalism

from dqc_simulator.hardware.dqc_creation import create_dqc_network
from dqc_simulator.software.dqc_control import (
    dqcMasterProtocol, sort_greedily_by_node_and_time)
from dqc_simulator.qlib.circuit_identities import ( 
    two_control_ibm_toffoli_decomp)
from dqc_simulator.util.helper import get_data_qubit_indices

class TestToffoliDecomp(unittest.TestCase):
    def setUp(self):
        ns.sim_reset()
        set_qstate_formalism(QFormalism.DM)
        self.network = create_dqc_network(
                                  state4distribution=ks.b00, 
                                  node_list=None, num_qpus=2,
                                  node_distance=4e-3, quantum_topology = None, 
                                  classical_topology = None,
                                  want_classical_2way_link=True,
                                  want_entangling_link=True,
                                  nodes_have_ebit_ready=False,
                                  num_comm_qubits=2,
                                  name="linear network")
        self.node_a = self.network.get_node("node_0")
        self.node_b = self.network.get_node("node_1")
        self.cycle_runtime = 1e9
        
    def test_both_controls_on_1_flips_target(self):
        #single local quantum computing node
        ctrl_qubit1_index, ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:3])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = ctrl_node_name1
        target_node_name = ctrl_node_name1
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_a.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_a.name),
                       (instr.INSTR_X, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_X, ctrl_qubit2_index, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name)]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run()
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_a.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_a.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s1, ks.s1))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_first_control_only_not_enough(self):
        #single local quantum computing node
        ctrl_qubit1_index, ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:3])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = ctrl_node_name1
        target_node_name = ctrl_node_name1
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_a.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_a.name),
                       (instr.INSTR_X, ctrl_qubit1_index, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name)]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run()
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_a.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_a.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_second_control_only_not_enough(self):
        #single local quantum computing node
        ctrl_qubit1_index, ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:3])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = ctrl_node_name1
        target_node_name = ctrl_node_name1
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_a.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_a.name),
                       (instr.INSTR_X, ctrl_qubit2_index, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name)]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run()
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_a.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_a.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s0, np.kron(ks.s1, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_double_zero_control_does_not_change_target(self):
        #single local quantum computing node
        ctrl_qubit1_index, ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:3])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = ctrl_node_name1
        target_node_name = ctrl_node_name1
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_a.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name)]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run()
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_a.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_a.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s0, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_remote_gate_ctrl_11(self):
        #single local quantum computing node
        ctrl_qubit1_index = self.node_a.qmemory.processing_qubit_positions[0]
        ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:2])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = self.node_b.name
        target_node_name = self.node_b.name
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_b.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_b.name),
                       (instr.INSTR_X, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_X, ctrl_qubit2_index, self.node_b.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name,
                                                     scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_b.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_b.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s1, ks.s1))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_remote_gate_ctrl_10(self):
        #single local quantum computing node
        ctrl_qubit1_index = self.node_a.qmemory.processing_qubit_positions[0]
        ctrl_qubit2_index, target_qubit_index = (
            self.node_a.qmemory.processing_qubit_positions[:2])
        ctrl_node_name1 = self.node_a.name
        ctrl_node_name2 = self.node_b.name
        target_node_name = self.node_b.name
        gate_tuples = [(instr.INSTR_INIT, ctrl_qubit1_index, self.node_a.name),
                       (instr.INSTR_INIT, ctrl_qubit2_index, self.node_b.name),
                       (instr.INSTR_INIT, target_qubit_index, self.node_b.name),
                       (instr.INSTR_X, ctrl_qubit1_index, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(ctrl_qubit1_index,
                                                     ctrl_node_name1,
                                                     ctrl_qubit2_index, 
                                                     ctrl_node_name2, 
                                                     target_qubit_index,
                                                     target_node_name,
                                                     scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_a.qmemory.pop(ctrl_qubit1_index)
        ctrl_qubit2, = self.node_b.qmemory.pop(ctrl_qubit2_index)
        target_qubit, = self.node_b.qmemory.pop(target_qubit_index)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_remote_gate_in_schor_error_correction_code_ctrl00(self):
        #single local quantum computing node
        q1, q2, q3, q4, q5 = self.node_a.qmemory.processing_qubit_positions[:5]
        gate_tuples = [(instr.INSTR_INIT, [q1, q2, q3, q4, q5], self.node_a.name),
                       (instr.INSTR_INIT, [q1, q2, q3, q4], self.node_b.name),
                       *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
                                                       q5, self.node_a.name,
                                                       q4, self.node_a.name,
                                                       scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_a.qmemory.pop(q1)
        ctrl_qubit2, = self.node_a.qmemory.pop(q5)
        target_qubit, = self.node_b.qmemory.pop(q4)
        desired_state_ket = np.kron(ks.s0, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_remote_gate_in_schor_error_correction_code_ctrl_10(self):
        #single local quantum computing node
        q1, q2, q3, q4, q5 = self.node_a.qmemory.processing_qubit_positions[:5]
        gate_tuples = [(instr.INSTR_INIT, [q1, q2, q3, q4, q5], self.node_a.name),
                       (instr.INSTR_INIT, [q1, q2, q3, q4], self.node_b.name),
                       (instr.INSTR_X, q1, self.node_b.name),
                       *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
                                                       q5, self.node_a.name,
                                                       q4, self.node_a.name,
                                                       scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_b.qmemory.pop(q1)
        ctrl_qubit2, = self.node_a.qmemory.pop(q5)
        target_qubit, = self.node_a.qmemory.pop(q4)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
    def test_remote_gate_in_schor_error_correction_code_ctrl_01(self):
        #single local quantum computing node
        q1, q2, q3, q4, q5 = self.node_a.qmemory.processing_qubit_positions[:5]
        gate_tuples = [(instr.INSTR_INIT, [q1, q2, q3, q4, q5], self.node_a.name),
                       (instr.INSTR_INIT, [q1, q2, q3, q4], self.node_b.name),
                       (instr.INSTR_X, q5, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
                                                       q5, self.node_a.name,
                                                       q4, self.node_a.name,
                                                       scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_b.qmemory.pop(q1)
        ctrl_qubit2, = self.node_a.qmemory.pop(q5)
        target_qubit, = self.node_a.qmemory.pop(q4)
        desired_state_ket = np.kron(ks.s0, np.kron(ks.s1, ks.s0))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
    
    def test_remote_gate_in_schor_error_correction_code_ctrl_11(self):
        #single local quantum computing node
        q1, q2, q3, q4, q5 = self.node_a.qmemory.processing_qubit_positions[:5]
        gate_tuples = [(instr.INSTR_INIT, [q1, q2, q3, q4, q5], self.node_a.name),
                       (instr.INSTR_INIT, [q1, q2, q3, q4], self.node_b.name),
                       (instr.INSTR_X, q1, self.node_b.name),
                       (instr.INSTR_X, q5, self.node_a.name),
                       *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
                                                       q5, self.node_a.name,
                                                       q4, self.node_a.name,
                                                       scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        ctrl_qubit1, = self.node_b.qmemory.pop(q1)
        ctrl_qubit2, = self.node_a.qmemory.pop(q5)
        target_qubit, = self.node_a.qmemory.pop(q4)
        desired_state_ket = np.kron(ks.s1, np.kron(ks.s1, ks.s1))
        fidelity = qapi.fidelity([ctrl_qubit1, ctrl_qubit2, target_qubit],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        
# =============================================================================
#     def test_remote_gate_in_schor_error_correction_code_for_H00_initial_state(self):
#         #single local quantum computing node
#         q1, q2, q3, q4, q5 = get_data_qubit_indices(self.node_a, 5)
#         gate_tuples = [(instr.INSTR_INIT, [q1, q2, q3, q4, q5], self.node_a.name),
#                        (instr.INSTR_INIT, [q1, q2, q3, q4], self.node_b.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q4, self.node_a.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q2, self.node_b.name, "cat"),
#                        (instr.INSTR_H, q1, self.node_a.name),
#                        (instr.INSTR_H, q4, self.node_a.name),
#                        (instr.INSTR_H, q2, self.node_b.name),
#                        *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
#                                                        q5, self.node_a.name,
#                                                        q4, self.node_a.name,
#                                                        scheme="cat")]
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
#         master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
#                                             compiler_func=sort_greedily_by_node_and_time)
#         master_protocol.start()
#         ns.sim_run(self.cycle_runtime)
#         alice_q1, =  self.node_a.qmemory.peek(q1)
#         alice_q4, = self.node_a.qmemory.peek(q4)
#         bob_q2, = self.node_b.qmemory.peek(q2)
#         
#         alice_q2, = self.node_a.qmemory.peek(q2)
#         alice_q3, = self.node_a.qmemory.peek(q3)
#         alice_q5, = self.node_a.qmemory.peek(q5)
#         bob_q1, = self.node_b.qmemory.peek(q1)
#         bob_q3, = self.node_b.qmemory.peek(q3)
#         bob_q4, = self.node_b.qmemory.peek(q4)
# # =============================================================================
# #         error_corrected_qubit, = alice.qmemory.peek(q1)
# # =============================================================================
#         print(f"the error corrected qubit has state {alice_q1.qstate.qrepr}")
#         print(f"alice q2 has state {alice_q2.qstate.qrepr} and reduced dm {ns.qubits.reduced_dm(alice_q2)}")
#         print(f"alice q3 has state {ns.qubits.reduced_dm(alice_q3)}")
#         print(f"alice q4 has state {ns.qubits.reduced_dm(alice_q4)}")
#         print(f"alice q5 has state {ns.qubits.reduced_dm(alice_q5)}")
#         print(f"bob q1 has state {ns.qubits.reduced_dm(bob_q1)}")
#         print(f"bob q2 has state {ns.qubits.reduced_dm(bob_q2)}")
#         print(f"bob q3 has state {ns.qubits.reduced_dm(bob_q3)}")
#         print(f"bob q4 has state {ns.qubits.reduced_dm(bob_q4)}")
# # =============================================================================
# #         qubits = alice.qmemory.pop([q1, q2, q3, q4, q5]) + bob.qmemory.pop([q1, q2, q3, q4])
# # =============================================================================
#         alice_comm_qubits = self.node_a.qmemory.peek([0, 1])
#         bob_comm_qubits = self.node_b.qmemory.peek([0, 1])
#         print(f"Alice's comm-qubits are {alice_comm_qubits}")
#         print(f"Bob's comm-qubits are {bob_comm_qubits}")
#         print(f"The collective state of Alice and Bob's comm-qubits is {ns.qubits.reduced_dm([alice_comm_qubits[0], bob_comm_qubits[0]])}")
# # =============================================================================
# #         qubits = (self.node_a.qmemory.pop([q1, q2, q3, q4, q5]) + 
# #                   self.node_b.qmemory.pop([q1, q2, q3, q4]))
# # =============================================================================
#         ctrl_qubit1, = self.node_b.qmemory.pop([q1])
#         ctrl_qubit2, = self.node_a.qmemory.pop([q5])
#         target_qubit, = self.node_a.qmemory.pop([q4])
#         plus_state = (1/np.sqrt(2))*(ks.s0 + ks.s1)
# # =============================================================================
# #         desired_state_ket = ft.reduce(np.kron, [plus_state, ks.s0, ks.s0] * 3)
# # =============================================================================
#         desired_state_ket = np.kron(plus_state, np.kron(ks.s0, ks.s0))
#         print(f"the actual state is {ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1])} with dimensions {np.shape(ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1]))}")
#         print(f"the desired state is {ns.qubits.ketutil.ket2dm(desired_state_ket)} with dimensions {np.shape(ns.qubits.ketutil.ket2dm(desired_state_ket))}")
#         fidelity = qapi.fidelity([target_qubit, ctrl_qubit2, ctrl_qubit1],
#                                  desired_state_ket)
#         self.assertAlmostEqual(fidelity, 1.000, 3)
#         #I think that the issue may be with how how the states of the two nodes
#         #are being combined in the tests rather than the states themselves. 
# 
#     def test_remote_gate_in_schor_error_correction_code_for_H00_initial_state_with_all_qubits_combined(self):
#         #single local quantum computing node
#         q1, q2, q3, q4, q5 = get_data_qubit_indices(self.node_a, 5)
#         alice_qubits = ns.qubits.create_qubits(5)
#         bob_qubits = ns.qubits.create_qubits(4)
#         qubits = alice_qubits + bob_qubits
#         qapi.combine_qubits(qubits)
#         print(f"the qstate of Alice's first qubit is {alice_qubits[0].qstate.qrepr}")
#         self.node_a.qmemory.put(alice_qubits, positions=[q1, q2, q3, q4, q5])
#         self.node_b.qmemory.put(bob_qubits, positions=[q1, q2, q3, q4])
#         gate_tuples = [(instr.INSTR_H, q1, self.node_a.name),
#                        (instr.INSTR_H, q4, self.node_a.name),
#                        (instr.INSTR_H, q2, self.node_b.name),
#                        *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
#                                                        q5, self.node_a.name,
#                                                        q4, self.node_a.name,
#                                                        scheme="cat")]
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
#         master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
#                                             compiler_func=sort_greedily_by_node_and_time)
#         master_protocol.start()
#         ns.sim_run(self.cycle_runtime)
#         alice_q1, =  self.node_a.qmemory.peek(q1)
#         alice_q4, = self.node_a.qmemory.peek(q4)
#         bob_q2, = self.node_b.qmemory.peek(q2)
#         
#         alice_q2, = self.node_a.qmemory.peek(q2)
#         alice_q3, = self.node_a.qmemory.peek(q3)
#         alice_q5, = self.node_a.qmemory.peek(q5)
#         bob_q1, = self.node_b.qmemory.peek(q1)
#         bob_q3, = self.node_b.qmemory.peek(q3)
#         bob_q4, = self.node_b.qmemory.peek(q4)
# # =============================================================================
# #         error_corrected_qubit, = alice.qmemory.peek(q1)
# # =============================================================================
#         print(f"the error corrected qubit has state {alice_q1.qstate.qrepr} with reduced dm {ns.qubits.reduced_dm(alice_q1)}")
#         print(f"alice q2 has state {alice_q2.qstate.qrepr} and reduced dm {ns.qubits.reduced_dm(alice_q2)}")
#         print(f"alice q3 has state {ns.qubits.reduced_dm(alice_q3)}")
#         print(f"alice q4 has state {ns.qubits.reduced_dm(alice_q4)}")
#         print(f"alice q5 has state {ns.qubits.reduced_dm(alice_q5)}")
#         print(f"bob q1 has state {ns.qubits.reduced_dm(bob_q1)}")
#         print(f"bob q2 has state {ns.qubits.reduced_dm(bob_q2)}")
#         print(f"bob q3 has state {ns.qubits.reduced_dm(bob_q3)}")
#         print(f"bob q4 has state {ns.qubits.reduced_dm(bob_q4)}")
# # =============================================================================
# #         qubits = alice.qmemory.pop([q1, q2, q3, q4, q5]) + bob.qmemory.pop([q1, q2, q3, q4])
# # =============================================================================
#         alice_comm_qubits = self.node_a.qmemory.peek([0, 1])
#         bob_comm_qubits = self.node_b.qmemory.peek([0, 1])
#         print(f"Alice's comm-qubits are {alice_comm_qubits}")
#         print(f"Bob's comm-qubits are {bob_comm_qubits}")
#         print(f"The collective state of Alice and Bob's comm-qubits is {ns.qubits.reduced_dm([alice_comm_qubits[0], bob_comm_qubits[0]])}")
# # =============================================================================
# #         qubits = (self.node_a.qmemory.pop([q1, q2, q3, q4, q5]) + 
# #                   self.node_b.qmemory.pop([q1, q2, q3, q4]))
# # =============================================================================
#         ctrl_qubit1, = self.node_b.qmemory.pop([q1])
#         ctrl_qubit2, = self.node_a.qmemory.pop([q5])
#         target_qubit, = self.node_a.qmemory.pop([q4])
#         plus_state = (1/np.sqrt(2))*(ks.s0 + ks.s1)
# # =============================================================================
# #         desired_state_ket = ft.reduce(np.kron, [plus_state, ks.s0, ks.s0] * 3)
# # =============================================================================
#         desired_state_ket = np.kron(plus_state, np.kron(ks.s0, ks.s0))
#         print(f"the actual state is {ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1])} with dimensions {np.shape(ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1]))}")
#         print(f"the desired state is {ns.qubits.ketutil.ket2dm(desired_state_ket)} with dimensions {np.shape(ns.qubits.ketutil.ket2dm(desired_state_ket))}")
#         fidelity = qapi.fidelity([target_qubit, ctrl_qubit2, ctrl_qubit1],
#                                  desired_state_ket)
#         self.assertAlmostEqual(fidelity, 1.000, 3)
#         #This test shows that the issue is not simply with the states being 
#         #combined but with some feature of the remote CNOTS themselves
# =============================================================================
        
    def test_toffoli_makes_no_difference(self):
        q1, q2, q3, q4, q5 = self.node_a.qmemory.processing_qubit_positions[:5]
        alice_qubits = ns.qubits.create_qubits(5)
        bob_qubits = ns.qubits.create_qubits(4)
        qubits = alice_qubits + bob_qubits
        qapi.combine_qubits(qubits)
        self.node_a.qmemory.put(alice_qubits, positions=[q1, q2, q3, q4, q5])
        self.node_b.qmemory.put(bob_qubits, positions=[q1, q2, q3, q4])
        gate_tuples = [(instr.INSTR_H, q1, self.node_a.name),
                       (instr.INSTR_H, q4, self.node_a.name),
                       (instr.INSTR_H, q2, self.node_b.name),
                       *two_control_ibm_toffoli_decomp(q1, self.node_b.name,
                                                       q5, self.node_a.name,
                                                       q4, self.node_a.name,
                                                       scheme="cat")]
        master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
                                            compiler_func=sort_greedily_by_node_and_time)
        master_protocol.start()
        ns.sim_run(self.cycle_runtime)
        alice_q1, =  self.node_a.qmemory.peek(q1)
        alice_q4, = self.node_a.qmemory.peek(q4)
        bob_q2, = self.node_b.qmemory.peek(q2)
        
        alice_q2, = self.node_a.qmemory.peek(q2)
        alice_q3, = self.node_a.qmemory.peek(q3)
        alice_q5, = self.node_a.qmemory.peek(q5)
        bob_q1, = self.node_b.qmemory.peek(q1)
        bob_q3, = self.node_b.qmemory.peek(q3)
        bob_q4, = self.node_b.qmemory.peek(q4)
# =============================================================================
#         error_corrected_qubit, = alice.qmemory.peek(q1)
# =============================================================================
# =============================================================================
#         qubits = alice.qmemory.pop([q1, q2, q3, q4, q5]) + bob.qmemory.pop([q1, q2, q3, q4])
# =============================================================================
        alice_comm_qubits = self.node_a.qmemory.peek([0, 1])
        bob_comm_qubits = self.node_b.qmemory.peek([0, 1])
# =============================================================================
#         qubits = (self.node_a.qmemory.pop([q1, q2, q3, q4, q5]) + 
#                   self.node_b.qmemory.pop([q1, q2, q3, q4]))
# =============================================================================
        ctrl_qubit1, = self.node_b.qmemory.pop([q1])
        ctrl_qubit2, = self.node_a.qmemory.pop([q5])
        target_qubit, = self.node_a.qmemory.pop([q4])
        plus_state = (1/np.sqrt(2))*(ks.s0 + ks.s1)
# =============================================================================
#         desired_state_ket = ft.reduce(np.kron, [plus_state, ks.s0, ks.s0] * 3)
# =============================================================================
        desired_state_ket = np.kron(plus_state, np.kron(ks.s0, ks.s0))
        fidelity = qapi.fidelity([target_qubit, ctrl_qubit2, ctrl_qubit1],
                                 desired_state_ket)
        self.assertAlmostEqual(fidelity, 1.000, 3)
        #This test shows that the issue is not simply with the states being 
        #combined but with some feature of the remote CNOTS themselves

# =============================================================================
#     def test_remote_cnots_give_same_state_as_prev_test(self):
#         #single local quantum computing node
#         q1, q2, q3, q4, q5 = get_data_qubit_indices(self.node_a, 5)
#         alice_qubits = ns.qubits.create_qubits(5)
#         bob_qubits = ns.qubits.create_qubits(4)
#         qubits = alice_qubits + bob_qubits
#         qapi.combine_qubits(qubits)
#         print(f"the qstate of Alice's first qubit is {alice_qubits[0].qstate.qrepr}")
#         self.node_a.qmemory.put(alice_qubits, positions=[q1, q2, q3, q4, q5])
#         self.node_b.qmemory.put(bob_qubits, positions=[q1, q2, q3, q4])
#         gate_tuples = [(instr.INSTR_H, q1, self.node_a.name),
#                        (instr.INSTR_H, q4, self.node_a.name),
#                        (instr.INSTR_H, q2, self.node_b.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q2, self.node_a.name),
#                        (instr.INSTR_CNOT, q4, self.node_a.name, q5, self.node_a.name),
#                        (instr.INSTR_CNOT, q2, self.node_b.name, q3, self.node_b.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q3, self.node_a.name),
#                        (instr.INSTR_CNOT, q4, self.node_a.name, q1, self.node_b.name, "cat"),
#                        (instr.INSTR_CNOT, q2, self.node_b.name, q4, self.node_b.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q2, self.node_a.name),
#                        (instr.INSTR_CNOT, q4, self.node_a.name, q5, self.node_a.name),
#                        (instr.INSTR_CNOT, q2, self.node_b.name, q3, self.node_b.name),
#                        (instr.INSTR_CNOT, q1, self.node_a.name, q3, self.node_a.name),
#                        (instr.INSTR_CNOT, q4, self.node_a.name, q1, self.node_b.name, "cat"),
#                        (instr.INSTR_CNOT, q2, self.node_b.name, q4, self.node_b.name)]
#         node_op_dict = sort_greedily_by_node_and_time(gate_tuples)
#         print(f"node_op_dict is {node_op_dict}")
#         master_protocol = dqcMasterProtocol(gate_tuples, self.network, 
#                                             compiler_func=sort_greedily_by_node_and_time)
#         master_protocol.start()
#         ns.sim_run(self.cycle_runtime)
#         alice_q1, =  self.node_a.qmemory.peek(q1)
#         alice_q4, = self.node_a.qmemory.peek(q4)
#         bob_q2, = self.node_b.qmemory.peek(q2)
#         alice_q2, = self.node_a.qmemory.peek(q2)
#         alice_q3, = self.node_a.qmemory.peek(q3)
#         alice_q5, = self.node_a.qmemory.peek(q5)
#         bob_q1, = self.node_b.qmemory.peek(q1)
#         bob_q3, = self.node_b.qmemory.peek(q3)
#         bob_q4, = self.node_b.qmemory.peek(q4)
# # =============================================================================
# #         error_corrected_qubit, = alice.qmemory.peek(q1)
# # =============================================================================
#         print(f"the error corrected qubit has state {alice_q1.qstate.qrepr} with reduced dm {ns.qubits.reduced_dm(alice_q1)}")
#         print(f"alice q2 has state {alice_q2.qstate.qrepr} and reduced dm {ns.qubits.reduced_dm(alice_q2)}")
#         print(f"alice q3 has state {ns.qubits.reduced_dm(alice_q3)}")
#         print(f"alice q4 has state {ns.qubits.reduced_dm(alice_q4)}")
#         print(f"alice q5 has state {ns.qubits.reduced_dm(alice_q5)}")
#         print(f"bob q1 has state {ns.qubits.reduced_dm(bob_q1)}")
#         print(f"bob q2 has state {ns.qubits.reduced_dm(bob_q2)}")
#         print(f"bob q3 has state {ns.qubits.reduced_dm(bob_q3)}")
#         print(f"bob q4 has state {ns.qubits.reduced_dm(bob_q4)}")
# # =============================================================================
# #         qubits = alice.qmemory.pop([q1, q2, q3, q4, q5]) + bob.qmemory.pop([q1, q2, q3, q4])
# # =============================================================================
#         alice_comm_qubits = self.node_a.qmemory.peek([0, 1])
#         bob_comm_qubits = self.node_b.qmemory.peek([0, 1])
#         print(f"Alice's comm-qubits are {alice_comm_qubits}")
#         print(f"Bob's comm-qubits are {bob_comm_qubits}")
#         print(f"The collective state of Alice and Bob's comm-qubits is {ns.qubits.reduced_dm([alice_comm_qubits[0], bob_comm_qubits[0]])}")
# # =============================================================================
# #         qubits = (self.node_a.qmemory.pop([q1, q2, q3, q4, q5]) + 
# #                   self.node_b.qmemory.pop([q1, q2, q3, q4]))
# # =============================================================================
#         ctrl_qubit1, = self.node_b.qmemory.pop([q1])
#         ctrl_qubit2, = self.node_a.qmemory.pop([q5])
#         target_qubit, = self.node_a.qmemory.pop([q4])
#         plus_state = (1/np.sqrt(2))*(ks.s0 + ks.s1)
# # =============================================================================
# #         desired_state_ket = ft.reduce(np.kron, [plus_state, ks.s0, ks.s0] * 3)
# # =============================================================================
#         desired_state_ket = np.kron(plus_state, np.kron(ks.s0, ks.s0))
#         print(f"the actual state is {ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1])} with dimensions {np.shape(ns.qubits.reduced_dm([target_qubit, ctrl_qubit2, ctrl_qubit1]))}")
#         print(f"the desired state is {ns.qubits.ketutil.ket2dm(desired_state_ket)} with dimensions {np.shape(ns.qubits.ketutil.ket2dm(desired_state_ket))}")
#         fidelity = qapi.fidelity([target_qubit, ctrl_qubit2, ctrl_qubit1],
#                                  desired_state_ket)
#         self.assertAlmostEqual(fidelity, 1.000, 3)
# =============================================================================

#running all class derived from the unittest.TestCase parent class
if __name__ == '__main__':
    unittest.main()
        