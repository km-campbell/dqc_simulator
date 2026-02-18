"""
Created on Wed Aug 16 16:37:05 2023

@author: kenny
"""

import functools as ft
import unittest

import netsquid as ns
import numpy as np
from netsquid.components import instructions as instr
from netsquid.components import QuantumProcessor
from netsquid.components.qprogram import QuantumProgram
from netsquid.qubits import (
    ketstates as ks,
    qubitapi as qapi,
    set_qstate_formalism,
    QFormalism,
)

from dqc_simulator.hardware.quantum_processors import (
    create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates,
    QPU,
)

# for debugging
# =============================================================================
# from netsquid.util import simlog
# import logging
# loggers = simlog.get_loggers()
# loggers['netsquid'].setLevel(logging.DEBUG)
# # =============================================================================
# # #resetting to default after debugging
# # loggers = simlog.get_loggers()
# # loggers['netsquid'].setLevel(logging.WARNING)
# # =============================================================================
#
# =============================================================================


class TestQPU(unittest.TestCase):
    def test_QPU_is_valid_subclass_of_QuantumProcessor(self):
        # I have found in the past that subclassing can be more complicated than
        # expected when abstract base classes are involved and so it pays to
        # explicitly check
        is_subclass = issubclass(QPU, QuantumProcessor)
        self.assertIs(is_subclass, True)

    def test_different_types_of_qubit_in_correct_places(self):
        qpu = QPU("qpu", num_positions=20, num_comm_qubits=5)
        with self.subTest(msg="comm-qubits not in right place"):
            self.assertEqual(qpu.comm_qubit_positions, [0, 1, 2, 3, 4])
        with self.subTest(msg="processing qubits not in right place"):
            self.assertEqual(
                qpu.processing_qubit_positions, [ii for ii in range(5, 20)]
            )
        with self.subTest(msg="photon emission positions not in right place"):
            self.assertEqual(qpu.photon_positions, [20, 21, 22, 23, 24])

    def test_can_correctly_instantiate_comm_qubits_free(self):
        qpu = QPU("qpu", num_positions=20, num_comm_qubits=5)
        self.assertEqual(qpu.comm_qubits_free, qpu.comm_qubit_positions)

    def test_correct_num_real_positions(self):
        qpu = QPU("qpu", num_positions=20, num_comm_qubits=5)
        self.assertEqual(qpu.num_real_positions, 20)


class Test_create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(
    unittest.TestCase
):
    def setUp(self):
        set_qstate_formalism(QFormalism.DM)
        ns.sim_reset()

    def test_can_apply_mem_depol2comm_qubits(self):
        p_depolar_error_cnot = 0.0
        comm_qubit_depolar_rate = 1 / 10  # Hz
        proc_qubit_depolar_rate = 0.0
        processor = (
            create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(
                p_depolar_error_cnot=p_depolar_error_cnot,
                comm_qubit_depolar_rate=comm_qubit_depolar_rate,
                proc_qubit_depolar_rate=proc_qubit_depolar_rate,
                num_comm_qubits=2,
            )
        )
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [ii for ii in range(7)])
        processor.execute_program(prog)
        ns.sim_run(10**10 + 3)  # running for 10s + 3ns (the 3ns is the
        # initialisation time and may need updated later)
        qubits = processor.peek([ii for ii in range(7)])
        desired_state4each_comm_qubit = np.diag(
            [(1 + np.exp(-1)) / 2, (1 - np.exp(-1)) / 2]
        )
        desired_state = ft.reduce(
            np.kron,
            [desired_state4each_comm_qubit] * 2 + [ns.qubits.ketutil.ket2dm(ks.s0)] * 5,
        )
        fidelity = qapi.fidelity(qubits, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)

    def test_can_apply_mem_depol2data_qubits(self):
        p_depolar_error_cnot = 0.0
        comm_qubit_depolar_rate = 0.0
        proc_qubit_depolar_rate = 1 / 10  # Hz
        processor = (
            create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(
                p_depolar_error_cnot=p_depolar_error_cnot,
                comm_qubit_depolar_rate=comm_qubit_depolar_rate,
                proc_qubit_depolar_rate=proc_qubit_depolar_rate,
            )
        )
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [ii for ii in range(7)])
        processor.execute_program(prog)
        ns.sim_run(10**10 + 3)  # running for 10s + 3ns (the 3ns is the
        # initialisation time and may need updated later)
        qubits = processor.peek([ii for ii in range(7)])
        desired_state4each_data_qubit = np.diag(
            [(1 + np.exp(-1)) / 2, (1 - np.exp(-1)) / 2]
        )
        desired_state = ft.reduce(
            np.kron,
            [ns.qubits.ketutil.ket2dm(ks.s0)] * 2 + [desired_state4each_data_qubit] * 5,
        )
        fidelity = qapi.fidelity(qubits, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)

    def test_can_do_10percent_cnot_depol_on_comm_qubits(self):
        p_depolar_error_cnot = 0.1
        comm_qubit_depolar_rate = 0.0
        proc_qubit_depolar_rate = 0.0
        processor = (
            create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(
                p_depolar_error_cnot=p_depolar_error_cnot,
                comm_qubit_depolar_rate=comm_qubit_depolar_rate,
                proc_qubit_depolar_rate=proc_qubit_depolar_rate,
            )
        )
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [ii for ii in range(7)])
        prog.apply(instr.INSTR_H, [0])
        prog.apply(instr.INSTR_CNOT, [0, 1])
        processor.execute_program(prog)
        ns.sim_run(10**10 + 3)  # running for 10s + 3ns (the 3ns is the
        # initialisation time and may need updated later)
        qubits = processor.peek([ii for ii in range(7)])
        desired_state4comm_qubits = np.array(
            [
                [(2 - p_depolar_error_cnot) / 4, 0, 0, (1 - p_depolar_error_cnot) / 2],
                [0, p_depolar_error_cnot / 4, 0, 0],
                [0, 0, p_depolar_error_cnot / 4, 0],
                [(1 - p_depolar_error_cnot) / 2, 0, 0, (2 - p_depolar_error_cnot) / 4],
            ],
            dtype=complex,
        )
        desired_state = ft.reduce(
            np.kron, [desired_state4comm_qubits] + [ns.qubits.ketutil.ket2dm(ks.s0)] * 5
        )
        fidelity = qapi.fidelity(qubits, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)

    def test_can_do_10percent_cnot_depol_on_proc_qubits(self):
        p_depolar_error_cnot = 0.1
        comm_qubit_depolar_rate = 0.0
        proc_qubit_depolar_rate = 0.0
        processor = (
            create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(
                p_depolar_error_cnot=p_depolar_error_cnot,
                comm_qubit_depolar_rate=comm_qubit_depolar_rate,
                proc_qubit_depolar_rate=proc_qubit_depolar_rate,
            )
        )
        prog = QuantumProgram()
        prog.apply(instr.INSTR_INIT, [ii for ii in range(7)])
        prog.apply(instr.INSTR_H, [2])
        prog.apply(instr.INSTR_CNOT, [2, 3])
        processor.execute_program(prog)
        ns.sim_run(10**10 + 3)  # running for 10s + 3ns (the 3ns is the
        # initialisation time and may need updated later)
        qubits = processor.peek([ii for ii in range(7)])
        desired_state4first2data_qubits = np.array(
            [
                [(2 - p_depolar_error_cnot) / 4, 0, 0, (1 - p_depolar_error_cnot) / 2],
                [0, p_depolar_error_cnot / 4, 0, 0],
                [0, 0, p_depolar_error_cnot / 4, 0],
                [(1 - p_depolar_error_cnot) / 2, 0, 0, (2 - p_depolar_error_cnot) / 4],
            ],
            dtype=complex,
        )
        desired_state = ft.reduce(
            np.kron,
            [ns.qubits.ketutil.ket2dm(ks.s0)] * 2
            + [desired_state4first2data_qubits]
            + [ns.qubits.ketutil.ket2dm(ks.s0)] * 3,
        )
        fidelity = qapi.fidelity(qubits, desired_state)
        self.assertAlmostEqual(fidelity, 1.00000, 5)


if __name__ == "__main__":
    unittest.main()
