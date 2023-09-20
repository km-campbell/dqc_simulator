# -*- coding: utf-8 -*-
"""
Created on Thu May 18 10:13:44 2023

@author: kenny
"""

#custom noise models

#bit flip noise

import numpy as np

from netsquid.components.models.qerrormodels import QuantumErrorModel
from netsquid.qubits import qubitapi as qapi
from netsquid.util.constrainedmap import ValueConstraint
from netsquid.qubits.dmutil import partialtrace, reorder_dm

#To take analytical approach of applying a channel rather than an operator,
#you will need to specify that the density matrix formalism is used
#and also work within that formalism specifically. This means you need 
#to access the dm itself.

#for implementing dms analytically, the following may be useful:
import netsquid as ns
from netsquid.qubits import qubitapi as qapi
from netsquid.components.qprogram import QuantumProgram
from netsquid.qubits.qformalism import QFormalism, set_qstate_formalism
from netsquid.components import instructions as instr
from netsquid.qubits import ketstates as ks



#TO DO: figure our how to formulate maths as latex in docstring


def apply_analytical_depolarisation2dm(qubits, p_error):
    r"""
    Applies a depolarisation channel of the form 
    :math: `\rho_out = (1 - p_error) rho_in 
           + p_error/dim{i, j} Tr_{i,j} (rho_in) o_times I_{i, j}'.
    This circumvents the need for repeated runs, as it is not probabilistic.
    It is equivalent to equations (2) and (3) in
    QuantumRepeaters:The Role of Imperfect Local Operations in Quantum 
    Communication
    by Briegel, Dur, Cirac and Zoller but I split it into two parts.
    I assume the ideal operation is first done and then act a channel which 
    either does nothing with some probability or decoheres the ideal output
    with some probability.
    
    This noise model is designed to be used after a gate or only on one qubit
    at a time because it assumes all qubits share a qstate. This assumption 
    is good if the qubits have been acted on by a multi-qubit gate
    INPUT: 
        qubit: :class: netsquid.qubits.Qubit obj or list
            The qubit upon which the depolarisation channel should act
        p_error
    """ 
    if type(qubits) == ns.qubits.qubit.Qubit:
        qubits = [qubits]
    elif len(qubits) > 1:
        ii = 0
        while ii < (len(qubits) - 1):
            qubit = qubits[ii]
            nxt_qubit = qubits[ii + 1]
            if qubit.qstate != nxt_qubit.qstate:
                raise Exception(f"Qubits {qubit.name} and {nxt_qubit.name} do"
                                f" not share a quantum state")
            else:
                ii = ii + 1
    else:
        raise TypeError(f"qubits must be type {ns.qubits.qubit.Qubit} or list")
    qubit = qubits[0]
    indices4entire_state = qubit.qstate.indices #dictionary
    indices4subspace = [] #subspace containing qubits involved in ideal gate
    for qubit in qubits:
        index4qubit = indices4entire_state[qubit.name]
        indices4subspace = indices4subspace + [index4qubit]
    ideal_dm = qubit.qstate.dm #does not matter which qubit as all share same
                               #qstate after gate which acts on all of them
    subspace_dim = 2 ** len(indices4subspace)
    noise_mat = np.kron(partialtrace(ideal_dm, indices4subspace),
                      np.eye(subspace_dim))
    #re-ordering so that the noise matrix applies noise to the correct places:
    #list of form [complement_indices, subspace_indices] needed for noise_mat
    #to apply to the right places
    indices4entire_state_list = list(indices4entire_state.values())
    indices4complement_space = list(set(indices4entire_state_list) -
                                    set(indices4subspace))
    desired_ordering = [*indices4complement_space, *indices4subspace]
    noise_mat = reorder_dm(noise_mat, desired_ordering)
    partially_depolarised_dm = ((1 - p_error) * ideal_dm + 
                                (p_error/subspace_dim) * noise_mat)
    qubit_list = qubit.qstate.qubits
    qapi.assign_qstate(qubit_list, partially_depolarised_dm,
                       formalism=QFormalism.DM)
    #TO DO: add error if dm is not a valid dm
    #TO DO: Neaten and optimise this function
    

#The following class is based on
#netsquid.components.models.qerrormodels.DepolarNoiseModel and uses some code 
#from there in accordance with the license agreement which allows such actions 
#for non-commercial research use. It follows the standard structure of a 
#QuantumErrorModel
class AnalyticalDepolarisationModel(QuantumErrorModel):
    def __init__(self, p_error, time_independent=True, **kwargs):
        r"""
        Based on netsquid.components.models.DepolarNoiseModel but adjusted to
        be applied analytically and within the DM formalism only. This is 
        intended to avoid the need for multiple runs and thus reduce 
        computation time. However, this model inappropriate for systems with  
        many qubits because of the restriction to the memory-intensive DM 
        formalism.

        Parameters
        ----------
        p_error : float
            Probability that the qubits are depolarised. If``time_independent``
            is True (default), then this a probability as defined in
            :math: `\rho_out = (1 - p_error) rho_in 
                   + p_error/dim{i, j} Tr_{i,j} (rho_in) o_times I_{i, j}'.
            If ``time_independent`` is False,
            then p_{error} is the exponential depolarizing rate per unit time
            [Hz], such that 
            :math: `\rho_{out} = (1 - p_{error}) rho_{in} 
                   + prob_{error}/dim{i, j} Tr_{i,j} (rho_{in})
                   o_times I_{i, j}'
            with :math: `prob_{error} = 1 - e^{\delta t p_{error} * e^{-9}}',
            where :math: `\delta t' is the time qubits spend on a component
            (eg, a quantum memory).
        time_independent : bool, optional
            Whether or not the probability of a depolarisation error occurring
            depends on time. The default is True.
        """
        super().__init__(**kwargs)
        # NOTE time independence should be set *before* the rate
        self.add_property('time_independent', time_independent,
                          value_type=bool)
        def prob_constraint(value):
            if self.time_independent and not 0 <= value <= 1:
                return False
            elif value <0:
                return False
            else:
                return True
        self.add_property('p_error', value=p_error, 
                          value_type=(int, float),
                          value_constraints=ValueConstraint(prob_constraint))
    
    @property
    def p_error(self):
        return self.properties['p_error']
    
    @p_error.setter
    def p_error(self, value):
        self.properties['p_error'] = value
        
    @property
    def time_independent(self):
        """bool: Whether the probability of depolarising is time independent.
        """
        return self.properties['time_independent']

    @time_independent.setter
    def time_independent(self, value):
        self.properties['time_independent'] = value
    
    def error_operation(self, qubits, delta_time=0, **kwargs):
        """
        Error to apply to qubits
        
        INPUT: 
            qubits : tuple of :obj:`~netsquid.qubits.qubit.Qubit`
                Qubits to apply noise to.
            delta_time : float optional
                Time qubits have spent on a component in ns (ns used to
                maintain consistency with QuantumErrorModel parent class).

        """
        if self.time_independent: #for adding errors to quantum
                                  #gates or other events which can be thought 
                                  #of as discrete. Thus, this models things 
                                  #like imperfectly applied gates.
                                  #I assume here that the qubits all share a 
                                  #qstate attribute 
                                  #(netsquid.qubits.Qubit.qstate), which is the 
                                  #case after they are acted on by a shared
                                  #gate. p_error is a probability here
            apply_analytical_depolarisation2dm(qubits, self.p_error)
        else: #for memory decoherence. p_error is now a rate in Hz
            for qubit in qubits:
                prob_error = 1. - np.exp(- delta_time * 1e-9 * self.p_error)
                #factor of 1e-9 in exponent is to convert delta_time from ns to
                #s, so that the units cancel with p_error (which is in Hz)
                apply_analytical_depolarisation2dm(qubit, prob_error)
# =============================================================================
#                 # for DEBUGGING only. REMOVE once finished:
#                 print(f"qubit {qubit} has state{ns.qubits.reduced_dm(qubit)}") 
#                     
# =============================================================================
                    
