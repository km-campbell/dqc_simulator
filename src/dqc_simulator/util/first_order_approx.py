# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 12:16:39 2023

@author: kenny
"""

def f_out_with_ent_error_first_order(num_epr_pairs, F_werner):
    """
    The first-order approximation to the error caused by the distribution of 
    entangled pairs.

    Parameters
    ----------
    num_epr_pairs : int
        The number of entangled pairs in the circuit. They would be EPR pairs
        ideally but in reality the Werner state is distributed
    F_werner : float
        The Werner state fidelity of the distributed imperfect entangled pairs 
        (assumed to be in the Werner state).

    Returns
    -------
    f_out : float
        The fidelity at the output of the circuit.
        
    """
    error = 1 - F_werner
    f_out = 1 - num_epr_pairs * error
    return f_out

def f_out_with_cnot_depol_first_order(num_cnots, p_error):
    """
    The first-order approximation to the error caused by depolarisation due to
    imperfect local gates.

    Parameters
    ----------
    num_cnots : int
        The number of local CNOT gates in the circuit.
    p_error : float
        The probability of depolarisation taking place after each 
        local CNOT gate.

    Returns
    -------
    f_out : float
        The fidelity at the output of the circuit.
        
    """
    f_out = 1 - num_cnots * p_error
    return f_out

def f_out_with_mem_depol_first_order(depolar_rate, num_single_qubit_gates, 
                                     num_cnots, num_measurements,
                                     num_epr_pairs, num_classical_comms,
                                     single_qubit_gate_time=135e3,
                                     cnot_gate_time=600e3, 
                                     measurement_time=300e3, 
                                     ent_distr_time=1/182,
                                     node_distance=2):
    """
    The first-order approximation to the error caused by time-dependent memory
    depolarisation.
    
    Parameters
    ----------
    depolar_rate : float
        Memory depolarisation rate in Hz.
    num_single_qubit_gates : int
        The number of single-qubit gates in the circuit.
    num_cnots : int
        The number of local CNOT gates in the circuit.
    num_epr_pairs : int
        The number of EPR pairs distributed between nodes.
    num_measurements : int
        The number of measurements conducted in the circuit.
    num_classical_comms : int
        The number of classical messages sent between nodes
    single_qubit_gate_time : float
        Time taken to complete single-qubit gate in s. I assume here that 
        all single-qubit gates take the same amount of time.
    cnot_gate_time : float
        Time taken to complete CNOT gate in s.
    measurement_time : float
        Time taken to measure the state of a single qubit in the z-basis.
    ent_distr_time : float
        The time taken to distribute entanglement (EPR pairs) between two
        nodes. I assume this is the same between all nodes.
    node_distance : float, optional
        The distance between nodes in m. I assume this is the same between all
        nodes. The default is 2m.

    Returns
    -------
    f_out : float
        The fidelity at the output of the circuit.

    """
    #NOTE: for the following runtime calculation I make the simplifying
    #assumption that the measurement dependent gates all occur (the worst case
    #scenario for latency) and that the only delay in classical communication 
    #is the time taken to travel through the fibre (there is no processing time
    #to recognise that a measurement has occurred and should be sent). I think
    #that both of these assumptions should have a relatively negligible effect
    #relative to the entanglement distillation time and two-qubit gate time,
    #which dominate. All times are in s and speeds in m/s
    c_optical_fibre = 200e6 #light propatation speed through optical fibre in
                            #m/s
    circuit_runtime = (num_single_qubit_gates * single_qubit_gate_time + 
                       num_cnots * cnot_gate_time +
                       num_measurements * measurement_time + 
                       num_epr_pairs * ent_distr_time + 
                       num_classical_comms * node_distance/(200e6))
    f_out = 1 - depolar_rate * circuit_runtime
    return f_out
