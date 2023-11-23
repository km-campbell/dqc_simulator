from qiskit import qasm2
from qiskit.compiler import transpile


#NOT YET WORKING PROPERLY

def convert2different_native_gates(source_filepath,
                                   output_filepath,
                                   basis_gates,
                                   include_paths):
    """
    

    Parameters
    ----------
    source_filepath : str
        The path to the source code (including the filename).
    output_filepath : str
        The desired path to save the transpiled circuit to (should be 
        .qasm file.
    basis_gates : list of str
        The list of basis gates. The names should be as seen in the 
        documentation for qiskit.circuit.library.standard_gates.
        (https://qiskit.org/documentation/apidoc/circuit_library.html)
    include_paths : list of str
        The path(s) any files referenced by include statements in the source 
        code (eg, qelib1.inc) in the order in which they should be searched.
        

    Returns
    -------
    None.

    """
    original_qc = qasm2.load(source_filepath, 
               include_path=include_paths)
    transpiled_qc = transpile(original_qc, basis_gates=basis_gates,
                              translation_method='translator')
    qasm2.dump(transpiled_qc, output_filepath)