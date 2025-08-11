# -*- coding: utf-8 -*-
"""
Functions and classes for creating specific QPUs.
"""

import numpy as np

from netsquid.components import instructions as instr
from netsquid.components.qprocessor import QuantumProcessor, PhysicalInstruction
from netsquid.components.models.qerrormodels import (DepolarNoiseModel, 
                                                     DephaseNoiseModel)

from dqc_simulator.hardware.noise_models import (AnalyticalDepolarisationModel,
                                                 MeasurementNoiseModel,
                                                 NDimDepolarNoiseModel)
from dqc_simulator.qlib.gates import (INSTR_ARB_GEN, INSTR_CH, INSTR_CT,
                                      INSTR_T_DAGGER,
                                      INSTR_S_DAGGER,
                                      INSTR_SINGLE_QUBIT_UNITARY, 
                                      INSTR_TWO_QUBIT_UNITARY,
                                      INSTR_SINGLE_QUBIT_NEGLIGIBLE_TIME,
                                      INSTR_TWO_QUBIT_NEGLIGIBLE_TIME)


class QPU(QuantumProcessor):
    """
    

    Parameters
    ----------
    name : TYPE
        DESCRIPTION.
    num_positions : int, optional
        The number of qubits on the memory. The default is 20. Note that 
        additional fictitious qubits will also be placed on the memory to 
        allow modelling of emitted photons. Therefore, the num_positions 
        property will differ from the value specified here.
    mem_noise_models : TYPE, optional
        DESCRIPTION. The default is None. This will be overriden if 
        comm_qubit_mem_noise_model or 
    phys_instructions : TYPE, optional
        DESCRIPTION. The default is None.
    fallback_to_nonphysical : TYPE, optional
        DESCRIPTION. The default is False.
    properties : TYPE, optional
        DESCRIPTION. The default is None.
    num_comm_qubits : TYPE, optional
        DESCRIPTION. The default is 0.
    comm_qubit_mem_noise_model : :class:`~netsquid.components.models.qerrormodels.QuantumErrorModel`
        The memory noise model for all comm qubits. If this is not None, 
        mem_noise_models will be overridden.
    processing_qubit_mem_noise_model : :class:`~netsquid.components.models.qerrormodels.QuantumErrorModel`
        The memory noise model for all processing qubits. If this is not None, 
        mem_noise_models will be overridden.
        
    Attributes
    ----------
    mem_pos_types : list of str
        The type of each memory position. Can be 'comm', 'processing' or 
        'photon', reflecting the types of qubits that can occupy the position.
    comm_qubit_positions : list of int
        The memory positions of the communication qubits
    processing_qubit_positions : list of int
        The memory positions of the processing qubits
    photon_positions :list of int
        The fictitious memory positions reserved for facilitating photon 
        emission.
    num_real_positions : list of int
        The number of real memory positions (which exludes those reserved for 
        modelling photon emission).
    comm_qubits_free : list of int
        The positions of communication qubits which are free to use. Here, 
        'free to use' means that they are not hosting quantum information which
        should not be overwritten.
    ebit_ready : bool
        Whether there is an ebit (entangled bit) ready or not. This defaults to
        False and will become True when entanglement is successfully 
        distributed between this `QPU` and another.
    """
    def __init__(self, name, num_positions=20, mem_noise_models=None, 
                 phys_instructions=None, 
                 fallback_to_nonphysical=False, properties=None,
                 num_comm_qubits=0,
                 comm_qubit_mem_noise_model=None, 
                 processing_qubit_mem_noise_model=None):
        mem_pos_types, num_photon_spaces = self._get_mem_pos_types_N_num_photons(
                                                 num_positions, 
                                                 num_comm_qubits)
        self.mem_pos_types = mem_pos_types
        if (comm_qubit_mem_noise_model or processing_qubit_mem_noise_model 
            is not None):
            mem_noise_models = self._get_mem_noise_models(
                                            mem_pos_types, 
                                            comm_qubit_mem_noise_model,
                                            processing_qubit_mem_noise_model)
        super().__init__(name, num_positions=num_positions + num_photon_spaces,
                         mem_noise_models=mem_noise_models, 
                         phys_instructions=phys_instructions, 
                         mem_pos_types=mem_pos_types, 
                         fallback_to_nonphysical=fallback_to_nonphysical,
                         properties=properties)
        self.comm_qubit_positions = self.get_positions_matching_type('comm')
        self.processing_qubit_positions = self.get_positions_matching_type(
                                                                'processing')
        self.photon_positions = self.get_positions_matching_type('photon')
        self.num_real_positions = (self.num_positions 
                                   - len(self.photon_positions))
        #instantiating the comm_qubits_free attribute to be the same as 
        #comm_qubit_positions (initially). The list constructor is important 
        #here to make sure that comm-qubits free is a copy of 
        #comm_qubit_positions rather than an alias for it.
        self.comm_qubits_free = list(self.comm_qubit_positions)
        self.ebit_ready = False
            
    def get_positions_matching_type(self, pos_type):
        """
        Gets indices of memory positions matching the given type.
        
        Parameters
        ----------
        pos_type : str
            The type of memory position. Allowed values are 'comm', 
            'processing', and 'photon'.

        Returns
        -------
        positions_matching_pos_type : list of int
            The memory positions with the specified `pos_type`.
        """
        #I could also have used boolean masking with numpy for the following 
        #but that method is slower for the number of memory positions that 
        #would be feasibly simulable (according to ipython's %timeit)
        positions_matching_pos_type = []
        for ii, mem_pos_type in enumerate(self.mem_pos_types):
            if mem_pos_type == pos_type:
                positions_matching_pos_type.append(ii)
        return positions_matching_pos_type
    
    def _get_mem_pos_types_N_num_photons(self, num_positions, num_comm_qubits):
        """
        Create a list of memory position types.
        
        The output of this should be of a form useable as the value for the
        `mem_pos_types` parameter for a 
        `~netsquid.components.qprocessor.QuantumProcessor`.

        Parameters
        ----------
        num_positions : int
            The total number of memory positions.
        num_comm_qubits : int
            The number of comm_qubits.

        Returns
        -------
        mem_pos_types : list of str
            The types of memory position. There should be one string for each 
            memory position.

        """
        #determining number of fictitious memory positions needed to model photon 
        #emission
        num_photon_spaces = num_comm_qubits
        #photons are not included in the next line because num_positions
        num_processing_qubits = num_positions - num_comm_qubits
        mem_pos_types = (["comm"] * num_comm_qubits
                         + ["processing"] * num_processing_qubits
                         + ["photon"] * num_photon_spaces)
        return mem_pos_types, num_photon_spaces
    
    def _get_mem_noise_models(self, mem_pos_types, comm_qubit_mem_noise_model,
                              processing_qubit_mem_noise_model):
        """
        Gets an ordered list of memory noise models

        Parameters
        ----------
        mem_pos_types : list of str
            The types of memory position. There should be one string for each 
            memory position.

        Returns
        -------
        mem_noise_models: list of :class:`~netsquid.components.models.qerrormodels.QuantumErrorModel`
            The noise models to apply to the corresponding memory positions.
        """
        mem_noise_models = []
        for mem_pos_type in mem_pos_types:
            if mem_pos_type == 'comm':
                mem_noise_models.append(comm_qubit_mem_noise_model)
            elif mem_pos_type == 'processing':
                mem_noise_models.append(processing_qubit_mem_noise_model)
            elif mem_pos_type == 'photon':
                mem_noise_models.append(None) #None because photons are not sitting 
                                              #within the memory. Any noise they 
                                              #have should be modelled using an 
                                              #emission noise model.
            else:
                raise ValueError(f'"{mem_pos_type}" is not of one of the allowed '
                                 'values for mem_pos_type for this processor.' 
                                 'The allowed values are: "comm", "data", and '
                                 '"photon".')
        return mem_noise_models


def create_processor(alpha=1, beta=0, depolar_rate=0, dephase_rate=0, 
                     num_positions=7, mem_pos_types=None,
                     name="quantum_processor"):
    """Factory to create a quite artificial quantum processor. 

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
        
    Notes
    -----
    The gate durations are too small to be physical. This processor was used
    for cases where gate duration (as long as it was finite to avoid a
    :class:`~netsquid.components.qprocessor.ProcessorBusyError`) did not
    matter.
    """
# =============================================================================
#     measure_noise_model = DephaseNoiseModel(dephase_rate=dephase_rate,
#                                             time_independent=True)
# =============================================================================
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
                                 phys_instructions=physical_instructions,
                                 mem_pos_types=mem_pos_types)
    return processor 


def _phys_instructions_4_standard_lib_gates_and_convenience_ops(
                                        cnot_depolar_model,
                                        single_qubit_gate_noise_model,
                                        meas_noise_model,
                                        num_comm_qubits,
                                        single_qubit_gate_time,
                                        two_qubit_gate_time,
                                        measurement_time,
                                        alpha, beta):
    """
    Physical instructions for the standard lib gates and some additional 
    convenience operators (eg, gates to make an arbitrary state for the start 
    of an experiment).

    Parameters
    ----------
    cnot_depolar_model : TYPE
        DESCRIPTION.
    num_comm_qubits : TYPE
        DESCRIPTION.
    single_qubit_gate_time : TYPE
        DESCRIPTION.
    two_qubit_gate_time : TYPE
        DESCRIPTION.
    measurement_time : TYPE
        DESCRIPTION.
    alpha : TYPE
        DESCRIPTION.
    beta : TYPE
        DESCRIPTION.

    Returns
    -------
    physical_instructions : list of :class:`~netsquid.components.qprocessor.PhysicalInstruction`s
    """
    #creating processor for all Nodes
    physical_instructions = [
            PhysicalInstruction(instr.INSTR_INIT, duration=3, parallel=False,
                                toplogy=None),
            PhysicalInstruction(instr.INSTR_H, duration=single_qubit_gate_time, 
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(instr.INSTR_X, duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(instr.INSTR_Z, duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(instr.INSTR_S, duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(INSTR_S_DAGGER, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(instr.INSTR_T, duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(INSTR_T_DAGGER, duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(instr.INSTR_CNOT, duration=two_qubit_gate_time,
                                parallel=True, topology=None, 
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(instr.INSTR_CZ, duration=two_qubit_gate_time,
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
                                quantum_noise_model=meas_noise_model, 
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
            PhysicalInstruction(INSTR_SINGLE_QUBIT_UNITARY, 
                                duration=single_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=single_qubit_gate_noise_model),
            PhysicalInstruction(INSTR_TWO_QUBIT_UNITARY, 
                                duration=two_qubit_gate_time,
                                parallel=True, topology=None,
                                quantum_noise_model=cnot_depolar_model),
            PhysicalInstruction(INSTR_SINGLE_QUBIT_NEGLIGIBLE_TIME,
                                duration=3, parallel=True, topology=None),
            PhysicalInstruction(INSTR_TWO_QUBIT_NEGLIGIBLE_TIME, 
                                duration=3, parallel=True, topology=None)]
    return physical_instructions


def create_qproc_with_analytical_noise_ionQ_aria_durations_N_standard_lib_gates(   
                                         p_depolar_error_cnot=0,
                                         comm_qubit_depolar_rate=0,
                                         proc_qubit_depolar_rate=0,
                                         single_qubit_gate_time=135 * 10**3,
                                         two_qubit_gate_time=600 * 10**3,
                                         measurement_time=600 * 10**4,
                                         alpha=1, beta=0,
                                         num_positions=20,
                                         num_comm_qubits=2):
    """
    Creates quantum processor loosely based on ionQ Aria but with different
    native gates.
    
    .. deprecated::
        This function will be removed in later version as its functionality is
        now provided by the more general NoisyQPU class in a style more
        consistent with object-orientated programming
    
    Parameters
    ----------
    p_depolar_error_cnot : float, optional
        The probability of a depolarisation error after each CNOT gate.
        The default value is 0.
    comm_qubit_depolar_rate : float, optional
        The depolarisation rate for communication qubits. 
        The default value is 0.
    proc_qubit_depolar_rate : float
        The depolarisation rate for processing qubits.
        The default value is 0.
    single_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 135 * 10**3.
    two_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**3.
    measurement_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**4.
    alpha, beta : float, optional
        Settings for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default 
        is 1 for alpha and 0 for beta.
    num_positions : int, optional
        The number of memory positions. Note that this does not include the 
        number of photons (which each occupy a fictitious memory position). The
        default is 20.
    num_comm_qubits : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    qprocessor : :class:`~netsquid.components.qprocessor.QuantumProcessor`
    
    Notes
    -----
    Uses universal gate sets from Ref. [1]_. Analytical noise is used.
    Gate durations are taken from averages for single and two-qubit gates on
    IonQ's Aria machine.
    
    References
    ----------
    .. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
        Information, 10th ed. (Cambridge University Press, 2010).
    """
    cnot_depolar_model = AnalyticalDepolarisationModel(
        p_error=p_depolar_error_cnot, time_independent=True)
    #TO DO: decide whether to replace the following with NetSquid's built-in 
    #DepolarNoiseModel which gives the same results when the DM formalism is 
    #used and allows other formalisms to also be used.
    comm_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        comm_qubit_depolar_rate, time_independent=False)
    processing_qubit_memory_depolar_model = AnalyticalDepolarisationModel(
        proc_qubit_depolar_rate, time_independent=False)
    single_qubit_gate_noise_model = None
    meas_noise_model = None
    #creating processor for all Nodes
    physical_instructions = ( 
        _phys_instructions_4_standard_lib_gates_and_convenience_ops(
                                        cnot_depolar_model,
                                        single_qubit_gate_noise_model,
                                        meas_noise_model,
                                        num_comm_qubits,
                                        single_qubit_gate_time,
                                        two_qubit_gate_time,
                                        measurement_time,
                                        alpha, beta))
    qprocessor = QPU("custom_noisy_qprocessor",
                     phys_instructions=physical_instructions, 
                     num_positions=num_positions,
                     num_comm_qubits=num_comm_qubits,
                     comm_qubit_mem_noise_model=comm_qubit_memory_depolar_model, 
                     processing_qubit_mem_noise_model=processing_qubit_memory_depolar_model)
    
    qprocessor.add_composite_instruction(instr.INSTR_SWAP, 
                                         [(instr.INSTR_CNOT, (0, 1)),
                                          (instr.INSTR_CNOT, (1, 0)),
                                          (instr.INSTR_CNOT, (0, 1))],
                                          topology=None)
    return qprocessor

def create_noisy_qpu( p_depolar_error_cnot=0,
                      single_qubit_gate_error_prob=0,
                      meas_error_prob=0,
                      comm_qubit_depolar_rate=0,
                      proc_qubit_depolar_rate=0,
                      single_qubit_gate_time=135 * 10**3,
                      two_qubit_gate_time=600 * 10**3,
                      measurement_time=600 * 10**4, 
                      alpha=1, beta=0,
                      num_positions=20,
                      num_comm_qubits=2):
    """
    Creates quantum processor loosely based on ionQ Aria but with different
    native gates.
    
    .. deprecated::
        Use NoisyQPU instead.
    
    Parameters
    ----------
    p_depolar_error_cnot : float, optional
        The probability of a depolarisation error after each CNOT gate.
        The default value is 0.
    single_qubit_gate_error_prob : float
        The probability of a depolarisation error occuring during a single 
        qubit gate.
    meas_error_prob : float
        The probability of a bit flip error occuring during measurement, giving
        the opposite result from an ideal measurement.
    comm_qubit_depolar_rate : float, optional
        The depolarisation rate for communication qubits. 
        The default value is 0.
    proc_qubit_depolar_rate : float
        The depolarisation rate for processing qubits.
        The default value is 0.
    single_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 135 * 10**3.
    two_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**3.
    measurement_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**4.
    alpha, beta : float, optional
        Settings for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default 
        is 1 for alpha and 0 for beta.
    num_positions : TYPE, optional
        DESCRIPTION. The default is 20.
    num_comm_qubits : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    qprocessor : :class:`netsquid.components.qprocessor.QuantumProcessor
    
    Notes
    -----
    Uses universal gate sets from Ref. [1]_. Numerical noise is used.
    Gate durations are taken from averages for single and two-qubit gates on
    IonQ's Aria machine.
    
    References
    ----------
    .. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
        Information, 10th ed. (Cambridge University Press, 2010).
    """
    cnot_depolar_model = NDimDepolarNoiseModel(p_depolar_error_cnot, 
                                               time_independent=True)
    comm_qubit_memory_depolar_model = DepolarNoiseModel(comm_qubit_depolar_rate,
                                                        time_independent=False)
    processing_qubit_memory_depolar_model = DepolarNoiseModel(proc_qubit_depolar_rate,
                                                        time_independent=False)
    meas_noise_model = MeasurementNoiseModel(meas_error_prob)
    single_qubit_gate_noise_model = DepolarNoiseModel(single_qubit_gate_error_prob,
                                                      time_independent=True)
    #creating processor for all Nodes
    physical_instructions = ( 
        _phys_instructions_4_standard_lib_gates_and_convenience_ops(
                                            cnot_depolar_model,
                                            single_qubit_gate_noise_model,
                                            meas_noise_model,
                                            num_comm_qubits,
                                            single_qubit_gate_time,
                                            two_qubit_gate_time,
                                            measurement_time,
                                            alpha, beta))
    qprocessor = QPU("custom_noisy_qprocessor",
                     phys_instructions=physical_instructions, 
                     num_positions=num_positions,
                     num_comm_qubits=num_comm_qubits,
                     comm_qubit_mem_noise_model=comm_qubit_memory_depolar_model, 
                     processing_qubit_mem_noise_model=processing_qubit_memory_depolar_model)
    
    qprocessor.add_composite_instruction(instr.INSTR_SWAP, 
                                         [(instr.INSTR_CNOT, (0, 1)),
                                          (instr.INSTR_CNOT, (1, 0)),
                                          (instr.INSTR_CNOT, (0, 1))],
                                          topology=None)
    return qprocessor



def create_qproc_with_numerical_noise_ionQ_aria_durations_N_standard_lib_gates(   
                                         p_depolar_error_cnot=0,
                                         single_qubit_gate_error_prob=0,
                                         meas_error_prob=0,
                                         comm_qubit_depolar_rate=0,
                                         proc_qubit_depolar_rate=0,
                                         single_qubit_gate_time=135 * 10**3,
                                         two_qubit_gate_time=600 * 10**3,
                                         measurement_time=600 * 10**4, 
                                         alpha=1, beta=0,
                                         num_positions=20,
                                         num_comm_qubits=2):
    """
    Creates quantum processor loosely based on ionQ Aria but with different
    native gates.
    
    .. deprecated::
        Use noisy QPU instead.
    
    Parameters
    ----------
    p_depolar_error_cnot : float, optional
        The probability of a depolarisation error after each CNOT gate.
        The default value is 0.
    comm_qubit_depolar_rate : float, optional
        The depolarisation rate for communication qubits. 
        The default value is 0.
    proc_qubit_depolar_rate : float
        The depolarisation rate for processing qubits.
        The default value is 0.
    single_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 135 * 10**3.
    two_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**3.
    measurement_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**4.
    alpha, beta : float, optional
        Settings for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default 
        is 1 for alpha and 0 for beta.
    num_positions : TYPE, optional
        DESCRIPTION. The default is 20.
    num_comm_qubits : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    qprocessor : :class:`netsquid.components.qprocessor.QuantumProcessor
    
    Notes
    -----
    Uses universal gate sets from Ref. [1]_. Numerical noise is used.
    Gate durations are taken from averages for single and two-qubit gates on
    IonQ's Aria machine.
    
    References
    ----------
    .. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
        Information, 10th ed. (Cambridge University Press, 2010).
    """
    return create_noisy_qpu( 
                            p_depolar_error_cnot=p_depolar_error_cnot,
                            single_qubit_gate_error_prob=single_qubit_gate_error_prob,
                            meas_error_prob=meas_error_prob,
                            comm_qubit_depolar_rate=comm_qubit_depolar_rate,
                            proc_qubit_depolar_rate=proc_qubit_depolar_rate,
                            single_qubit_gate_time=single_qubit_gate_time,
                            two_qubit_gate_time=two_qubit_gate_time,
                            measurement_time=measurement_time, 
                            alpha=alpha, beta=beta,
                            num_positions=num_positions,
                            num_comm_qubits=num_comm_qubits)


# =============================================================================
# def create_qproc4oxford_dqc_proof_of_principle(
#                                          p_depolar_error_cnot=0,
#                                          comm_qubit_depolar_rate=0,
#                                          proc_qubit_depolar_rate=0,
#                                          single_qubit_gate_time=135 * 10**3,
#                                          two_qubit_gate_time=600 * 10**3,
#                                          measurement_time=600 * 10**4, 
#                                          alpha=1, beta=0,
#                                          num_positions=20,
#                                          num_comm_qubits=2):
#     """
#     Creates a QPU designed to be compared to those in _[1].
#     
#     References
#     ----------
#     .. [1] D. Main, P. Drmota, D. P. Nadlinger, E. M. Ainley, A. Agrawal, 
#         B. C. Nichol, et al., Distributed Quantum Computing across an Optical 
#         Network Link, arXiv:2407.00835. 
#     """
#     cnot_depolar_model = AnalyticalDepolarisationModel(
#                                 p_error=p_depolar_error_cnot,
#                                 time_independent=True)
#     comm_qubit_memory_depolar_model = DepolarNoiseModel(
#                                          comm_qubit_depolar_rate,
#                                          time_independent=False)
#     processing_qubit_memory_depolar_model = DepolarNoiseModel(
#                                                 proc_qubit_depolar_rate,
#                                                 time_independent=False)
#     physical_instructions = [] #FILL THIS LIST IN
# =============================================================================


class NoisyQPU(QPU):
    """
    Creates quantum processor loosely based on ionQ Aria but with different
    native gates.
    
    Parameters
    ----------
    p_depolar_error_cnot : float, optional
        The probability of a depolarisation error after each CNOT gate.
        The default value is 0.
    single_qubit_gate_error_prob : float
        The probability of a depolarisation error occuring during a single 
        qubit gate.
    meas_error_prob : float
        The probability of a bit flip error occuring during measurement, giving
        the opposite result from an ideal measurement.
    comm_qubit_depolar_rate : float, optional
        The depolarisation rate for communication qubits. 
        The default value is 0.
    proc_qubit_depolar_rate : float
        The depolarisation rate for processing qubits.
        The default value is 0.
    single_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 135 * 10**3.
    two_qubit_gate_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**3.
    measurement_time : TYPE, optional
        DESCRIPTION. The default is 600 * 10**4.
    alpha, beta : float, optional
        Settings for the artificial convenience gate INSTR_ARB_GEN, which 
        initialises the state of a qubit as alpha |0> + beta |1>. The default 
        is 1 for alpha and 0 for beta.
    num_positions : TYPE, optional
        DESCRIPTION. The default is 20.
    num_comm_qubits : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    qprocessor : :class:`netsquid.components.qprocessor.QuantumProcessor
    
    Notes
    -----
    Uses universal gate sets from Ref. [1]_. Numerical noise is used.
    Gate durations are taken from averages for single and two-qubit gates on
    IonQ's Aria machine.
    
    References
    ----------
    .. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
        Information, 10th ed. (Cambridge University Press, 2010).
    """
    def __init__(self, 
                 name="custom_noisy_qprocessor",
                 p_depolar_error_cnot=0,
                 single_qubit_gate_error_prob=0,
                 meas_error_prob=0,
                 comm_qubit_depolar_rate=0,
                 proc_qubit_depolar_rate=0,
                 single_qubit_gate_time=135 * 10**3,
                 two_qubit_gate_time=600 * 10**3,
                 measurement_time=600 * 10**4, 
                 alpha=1, beta=0,
                 num_positions=20,
                 num_comm_qubits=2):
        
        cnot_depolar_model = NDimDepolarNoiseModel(p_depolar_error_cnot, 
                                                   time_independent=True)
        comm_qubit_memory_depolar_model = DepolarNoiseModel(comm_qubit_depolar_rate,
                                                            time_independent=False)
        processing_qubit_memory_depolar_model = DepolarNoiseModel(proc_qubit_depolar_rate,
                                                            time_independent=False)
        meas_noise_model = MeasurementNoiseModel(meas_error_prob)
        single_qubit_gate_noise_model = DepolarNoiseModel(single_qubit_gate_error_prob,
                                                          time_independent=True)
        #creating processor for all Nodes
        physical_instructions = ( 
            _phys_instructions_4_standard_lib_gates_and_convenience_ops(
                                                cnot_depolar_model,
                                                single_qubit_gate_noise_model,
                                                meas_noise_model,
                                                num_comm_qubits,
                                                single_qubit_gate_time,
                                                two_qubit_gate_time,
                                                measurement_time,
                                                alpha, beta))
        super().__init__(name,
                         phys_instructions=physical_instructions, 
                         num_positions=num_positions,
                         num_comm_qubits=num_comm_qubits,
                         comm_qubit_mem_noise_model=comm_qubit_memory_depolar_model, 
                         processing_qubit_mem_noise_model=processing_qubit_memory_depolar_model)

        self.add_composite_instruction(instr.INSTR_SWAP, 
                                        [(instr.INSTR_CNOT, (0, 1)),
                                         (instr.INSTR_CNOT, (1, 0)),
                                         (instr.INSTR_CNOT, (0, 1))],
                                         topology=None)