"""
The following are arguably integration tests but are sufficiently fast and specific to single functions as
to be included with the unit tests.
"""

from pathlib import Path
import unittest

from dqc_simulator.software.qasm2ast import qasm2ast
from dqc_simulator.software.ast2dqc_circuit import Ast2DqcCircuitTranslator


class Test_ast2dqc_circuit(unittest.TestCase):
    """Testing using circuits from MQTBench. The following aren't currently
    proper tests, they just confirm that no errors are raised"""

    def setUp(self):
        self.directory_path = (
            Path(__file__).parents[2] / "MQT_benchmarking_circuits/"
        ).as_posix() + "/"

    def _get_dqc_circuit(self, filename):
        filepath = self.directory_path + filename
        ast = qasm2ast(filepath, include_path=Path(__file__).parent.as_posix())
        dqc_circuit = Ast2DqcCircuitTranslator(ast).ast2dqc_circuit()
        return dqc_circuit

    def test_with_ae_indep_qiskit_5(self):
        self._get_dqc_circuit("ae_indep_qiskit_5.qasm")

    def test_with_dj_indep_qiskit_5(self):
        self._get_dqc_circuit("dj_indep_qiskit_5.qasm")

    def test_with_ghz_indep_qiskit_5(self):
        self._get_dqc_circuit("ghz_indep_qiskit_5.qasm")

    def test_with_graphstate_indep_qiskit_5(self):
        self._get_dqc_circuit("graphstate_indep_qiskit_5.qasm")

    def test_with_grover_noancilla_indep_qiskit_5(self):
        self._get_dqc_circuit("grover-noancilla_indep_qiskit_5.qasm")

    def test_with_grover_v_chain_indep_qiskit_5(self):
        self._get_dqc_circuit("grover-v-chain_indep_qiskit_5.qasm")

    def test_portfolioqaoa_indep_qiskit_5(self):
        self._get_dqc_circuit("portfolioqaoa_indep_qiskit_5.qasm")

    def test_portfoliovqe_indep_qiskit_5(self):
        self._get_dqc_circuit("portfoliovqe_indep_qiskit_5.qasm")

    def test_qaoa_indep_qiskit_5(self):
        self._get_dqc_circuit("qaoa_indep_qiskit_5.qasm")

    def test_qft_indep_qiskit_5(self):
        self._get_dqc_circuit("qft_indep_qiskit_5.qasm")

    def test_qftentangled_indep_qiskit_5(self):
        self._get_dqc_circuit("qftentangled_indep_qiskit_5.qasm")

    def test_qnn_indep_qiskit_5(self):
        self._get_dqc_circuit("qnn_indep_qiskit_5.qasm")

    def test_qpeexact_indep_qiskit_5(self):
        self._get_dqc_circuit("qpeexact_indep_qiskit_5.qasm")

    def test_qpeinexact_indep_qiskit_5(self):
        self._get_dqc_circuit("qpeinexact_indep_qiskit_5.qasm")

    def test_qwalk_noancilla_indep_qiskit_5(self):
        self._get_dqc_circuit("qwalk-noancilla_indep_qiskit_5.qasm")

    def test_qwalk_v_chain_indep_qiskit_5(self):
        self._get_dqc_circuit("qwalk-v-chain_indep_qiskit_5.qasm")

    def test_random_indep_qiskit_5(self):
        self._get_dqc_circuit("random_indep_qiskit_5.qasm")

    def test_realamprandom_indep_qiskit_5(self):
        self._get_dqc_circuit("realamprandom_indep_qiskit_5.qasm")

    def test_su2random_indep_qiskit_5(self):
        self._get_dqc_circuit("su2random_indep_qiskit_5.qasm")

    def test_twolocalrandom_indep_qiskit_5(self):
        self._get_dqc_circuit("twolocalrandom_indep_qiskit_5.qasm")

    def test_vqe_indep_qiskit_5(self):
        self._get_dqc_circuit("vqe_indep_qiskit_5.qasm")

    def test_wstate_indep_qiskit_5(self):
        self._get_dqc_circuit("wstate_indep_qiskit_5.qasm")


if __name__ == "__main__":
    unittest.main()
