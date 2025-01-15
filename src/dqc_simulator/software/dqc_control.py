# -*- coding: utf-8 -*-
"""
Software for controlling the simulated DQC hardware.

Designed to act on hardware created using 
:mod: `~dqc_simulator.hardware.dqc_creation`
"""

import pydynaa
from netsquid.components import instructions as instr
from netsquid.components.qprogram import QuantumProgram
from netsquid.nodes.node import Node
from netsquid.protocols.protocol import Signals, Protocol
from netsquid.protocols.nodeprotocols import NodeProtocol

from dqc_simulator.hardware.quantum_processors import QPU
from dqc_simulator.software.compilers import sort_greedily_by_node_and_time
from dqc_simulator.software.physical_layer import (
                                    Base4PhysicalLayerProtocol, 
                                    AbstractCentralSourceEntangleProtocol)
from dqc_simulator.util.helper import QDCSignals


class UnfinishedQuantumCircuitError(Exception):
    """
    Error to be raised when a quantum circuit has not run all the way through.
    """
    pass


class QpuOSProtocol(NodeProtocol):
    """
    Runs all operations for a given QPU.
    
    This protocol serves as the operating system for our QPU. It will be used
    as a subprotocol of another protocol (the `superprotocol`).
    
    Parameters
    ----------
    superprotocol : :class: `~netsquid.protocols.protocol.Protocol`
        The protocol that this will be a subprotocol of.
    gate_tuples : list of lists of tuples 
        The gates and primitives (blocks of gates and operations that are part 
        of remote gates or other DQC-specific operations) to be conducted. Each 
        sublist corresponds to the gates to be
        conducted on a time slice. The tuples represent the gates or primitives.
        Remote gates may have a list of 
        tuples as the first entry of a gate tuple if in the recv role to
        allow several local
        gates to be applied as part of the remote gate.
        Each gate_tuple in gate_tuples4this_node_and_time must have
        form:
        1) for single-qubit gate: (gate_type, qubit_index)
        2) for two-qubit gate: (gate_type, qubit_index1, qubit_index2)
        3) for remote gate primitive:
                either : i) (data_qubit_index or sometimes
                             index of qubit to be
                             teleported/distributed, 
                             other_node_name, scheme, role).
                                     OR
                         ii) (other_node_name, scheme, role)
                        
                              
            where othernode_name is the name attribute of a
            netsquid.nodes.Node object, and gate_type is an
            instruction from netsquid.components.instructions
    node : :class: `netsquid.nodes.node.Node`, subclass thereof or None, optional
        The QPU node that this protocol will act on. If None, a node should be
        set later before starting this protocol.
    name : str or None, optional
        Name of protocol. If None, the name of the class is used.
        
    Notes
    -----
    The logic used in the _run_time_slice and, by extension, run methods of 
    this protocol is a generalisation of the use of subprotocols in NetSquid
    `~netsquid.protocols.protocol.Protocol`s. Subprotocols are 
    `~netsquid.protocols.protocol.Protocol`s and so their run method can only 
    yield `~pydynaa.core.EventExpression`s. This is clean because it is easy to 
    understand what is being yielded. However, here it was convenient to 
    make use of the fact that `Protocol` run methods are merely a specific 
    type of the more general python generator object. Generators can yield 
    anything and so rather than using `Protocol`s, whose run methods can yield
    only `EventExpressions`, I instead use generators that yield 
    `EventExpression`s, to indicate that something has happened in the sim, 
    AND variables that can be used by subsequent generators. 
    
    If subprotocols had been used it would have been necessary to send 
    variables, such as recently allocated comm-qubit indices and the 
    `QuantumProgram` being modified, as signals between the different 
    subprotocols. It becomes very complicated to make sure that subprotocols 
    which implement later instructions are actually started before the 
    subprotocols implementing earlier instructions so that the latter 
    subprotocols can wait on signals from the former. Ie, things like the 
    last used comm-qubit index become very hard to track. This is particularly 
    challenging to implement inside a simple if elif control flow. By contrast,
    with subgenerators, the relevant variables are returned after all 
    `EventExpression`s have been yielded, making the logic simpler.
    """
    #The core idea of what follows is to add instructions to a QuantumProgram
    #until remote gates occur, at which point the program will be run to that 
    #point, re-initialised and then added to with instructions needed for the
    #part of the remote gate done on this node. The classical port names have
    #been chosen so that the sending and receiving port have the same f-string
    #but will have different names when this protocol is acted on the 
    #appropriate nodes

    def __init__(self, superprotocol, gate_tuples, 
                 node=None, name=None):
        super().__init__(node, name)
        self.single_qubit_subroutines = ('logged',)
        self.superprotocol = superprotocol
        self.gate_tuples = gate_tuples
        #adding attributes for tracking what gates have evaluated
        self._gate_tuples_evaluated = [[]]
        #the next attribute is for storing gate tuples for local gates added to
        #a QuantumProgram but not yet evaluated
        self._local_gate_tuples_pending = [] 
        self._max_num_time_slices = len(self.gate_tuples)
        #The following subgenerators are similar to subprotocols implemented
        #in functional form rather than as classes. Unlike subprotocols (as far
        #as I can tell), the protocol_subgenerators can yield variables
        #needed for subsequent processes as well as event expressions used to 
        #evolve the simulation in time (the latter part the subprotocols can
        #do).
        self.protocol_subgenerators = {"cat" : self._cat_subgenerator,
                                       "tp" : self._tp_subgenerator}
        self.ent_request_label = "ENT_REQUEST"
        self.ent_ready_label = "ENT_READY"
        self.ent_failed_label = "ENT_FAILED"
        self.start_time_slice_label = "START_TIME_SLICE"
        self.finished_time_slice_label = "FINISHED_TIME_SLICE"
        self.add_signal(self.ent_request_label)
        self.add_signal(self.ent_ready_label)
        self.add_signal(self.ent_failed_label)
        self.add_signal(self.start_time_slice_label)
        self.add_signal(self.finished_time_slice_label)
        self.add_signal(QDCSignals.RESULT_PRODUCED)
        
    def add_phys_layer(self, physical_layer_protocol):
        """
        Convenience method for adding physical layer.
        
        Parameters
        ----------
        physical_layer_protocol : :class: `~dqc_simulator.software.physical_layer.Base4PhysicalLayerProtocol`
            A physical layer protocol.
        """
        physical_layer_protocol.superprotocol = self
        self.add_subprotocol(physical_layer_protocol, 
                             name='physical_layer_protocol')

    def _flexi_program_apply(self, qprogram, gate_instr, qubit_indices, 
                             gate_op, output_key='last'):
        """
        Handles the possibility gate_op is not defined in the gate instruction.

        Such a scenario can be useful because it 
        allows one to define one PhysicalInstruction for a variety of gates,
        making it possible to implement gates of the form 
        gate_name(list_of_parameters) without having to define a 
        PhysicalInstruction for infinitely many possible parameter values.

        Parameters
        ----------
        qprogram : an instance of 
                   netsquid.netsquid.components.qprogram.QuantumProgram
            A quantum program.
        gate_instr : instance of netsquid.components.instructions.Instruction
            A quantum instruction describing a gate. Note, this may not 
            have the operator used to carry out the gate predefined. If the 
            operator is not incorporated in the instruction definition it is
            included in gate_op (see below).
        qubit_indices : int or list of int
            The indices of the qubits to act the instruction on.
        gate_op : instance of netsquid.qubits.operators.Operator
            The operator used to apply the quantum gate.
        output_key : str, optional
            Dictionary key to store instruction output with. Default
            is to store all output using the key last.
            
        .. todo::
            
            Handle situations where entanglement is successful or not 
            successful in _request_entanglement method (see comment there)
        """
        if gate_op is None:
            qprogram.apply(gate_instr, qubit_indices, output_key=output_key)
        else:
            qprogram.apply(gate_instr, qubit_indices, operator=gate_op,
                           output_key=output_key)
            
    def _request_entanglement(self, role, other_node_name, comm_qubit_indices,
                              num_entanglements2generate=1,
                              entanglement_type2generate='bell_pair'):
        """
        Requests entanglement.
        
        Passes entanglement request to link layer.

        Parameters
        ----------
        role : str
            Whether the QPU is a 'client' (initiating the handshake) or a 
            'server' (responding to the handshake.)
        other_node_name : str
            The name of the other QPU node between which entanglement should 
            be distributed.
        comm_qubit_indices : list of int
            The indices of the comm-qubits that should be used.
        num_entanglements2generate : int, optional
            The number of entanglements that should be distributed. Eg, for 
            bipartite entanglement this would be the number of entangled pairs.
            The default is 1.
        entanglement_type2generate : str, optional
            The type of entanglement to distribute. The default is 'bell_pair'.

        Yields
        ------
        None.

        """
        
        #send entanglement request to link layer specifying the other node
        #involved in the connection and the comm-qubit to be used:
        self.send_signal(self.ent_request_label, 
                         result=(role, other_node_name, comm_qubit_indices,
                                 num_entanglements2generate,
                                 entanglement_type2generate))
        #wait for entangled qubit to arrive in requested comm-qubit slot:
        wait4succsessful_ent = self.await_signal(
                                   self.subprotocols['physical_layer_protocol'],
                                   signal_label=self.ent_ready_label)
        wait4failed_ent = self.await_signal(
                              self.subprotocols['physical_layer_protocol'],
                              signal_label=self.ent_failed_label)
        evexpr = yield wait4succsessful_ent | wait4failed_ent
        #TO DO: handle the case where entanglement fails properly rather than 
        #raising an error.
        if evexpr.second_term.value: #if entanglement failed signal received
            raise NotImplementedError(
                     'Entanglement distribution has failed. If a using a '
                     'non-deterministic physical layer, this is most likely '
                     'because the max_num_ent_attempts has been '
                     'exceeded. At the moment, there is no handler in place '
                     'to deal with this scenario.')
            
    def _cat_entangle(self, program, other_node_name,
                      data_or_tele_qubit_index, classical_comm_port):
        yield self.node.qmemory.execute_program(program)
        self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
        #re-initialising self._local_gate_tuples_pending
        self._local_gate_tuples_pending = []

        program=QuantumProgram()
        if len(self.node.qmemory.comm_qubits_free) == 0: 
            #if there are NO comm_qubits free:
            #using first comm-qubit that's free with a
            #name unique to this role so that it can
            #be reused in the "disentangle_end" role
            raise Exception(f"Scheduling error: No"
                            f"comm-qubits free. There"
                            f" are too many remote" 
                            f"gates on {self.node.name}"
                            f"in this time slice")
        else:
            comm_qubit_index = self.node.qmemory.comm_qubits_free[0]
            #removing comm qubit being used from list
            #of available comm-qubits:
            if not self.node.qmemory.ebit_ready: #if there is no ebit ready:
                yield from self._request_entanglement('client', 
                                                      other_node_name, 
                                                      [comm_qubit_index])
            program.apply(instr.INSTR_CNOT,
                          [data_or_tele_qubit_index,
                          comm_qubit_index])
            program.apply(instr.INSTR_MEASURE, 
                          [comm_qubit_index],
                          output_key="ma")
            #run program to this point
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            #comm-qubit is immediately freed by
            #measurement so is not deleted from
            #comm_qubits_free here
            ma, = program.output["ma"]
            classical_comm_port.tx_output(ma)
            program = QuantumProgram() #resetting
            return program #note that this will only be 
                                               #be returned after all the 
                                               #EventExpressions from the prev.
                                               #yield statements have been 
                                               #outputed 
        
    def _cat_correct(self, program, other_node_name, classical_comm_port):
        yield self.node.qmemory.execute_program(program)
        self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
        #re-initialising self._local_gate_tuples_pending
        self._local_gate_tuples_pending = []
        program=QuantumProgram()
        if len(self.node.qmemory.comm_qubits_free) == 0: 
            #if there are NO comm_qubits free:
            raise Exception(f"Scheduling error: No"
                            f" comm-qubits free. There"
                            f" are too many remote"
                            f" gates on"
                            f" {self.node.name} in "
                            f"this time slice")
        else: #if there are comm-qubits free
            #using first comm_qubit that's free with
            #name specific to role (so that it can be
            #found by "disentangle_start")
            comm_qubit_index = self.node.qmemory.comm_qubits_free[0]
            #removing comm qubit being used from list
            #of available comm-qubits:
            if not self.node.qmemory.ebit_ready: #if there is no ebit ready:
                yield from self._request_entanglement('server', 
                                                      other_node_name, 
                                                      [comm_qubit_index])
            del self.node.qmemory.comm_qubits_free[0]
            #wait for measurement result from _cat_entangle on the other node
            yield self.await_port_input(classical_comm_port)
            meas_result, = classical_comm_port.rx_input().items
            if meas_result == 1:
                program.apply(instr.INSTR_X, comm_qubit_index)
            elif meas_result != 0:
                raise ValueError('Measurement result must be an integer with '
                                 f'value 0 or 1. The current value, '
                                 f'{meas_result}, does not meet this criteria.'
                                 )
        return (comm_qubit_index, program) #note that this will only be 
                                           #be returned after all the 
                                           #EventExpressions from the prev.
                                           #yield statements have been 
                                           #outputed 
                                           
    def _cat_disentangle_start(self, program, comm_qubit_index, 
                           classical_comm_port):
        #don't need comm-qubit free to do this. It
        #will use the comm-qubit index defined in the 
        #last operation (ie, correct)
        program.apply(instr.INSTR_H, comm_qubit_index)
        program.apply(instr.INSTR_MEASURE, comm_qubit_index, output_key="mb")
        yield self.node.qmemory.execute_program(program)
        self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
        #re-initialising self._local_gate_tuples_pending
        self._local_gate_tuples_pending = []
        meas_result, = program.output["mb"]  
        program = QuantumProgram() #re-initialising
        classical_comm_port.tx_output(meas_result)
        #freeing comm-qubit now that it is not needed
        self.node.qmemory.comm_qubits_free = (self.node.qmemory.comm_qubits_free +
                                      [comm_qubit_index])
        #re-odering from smallest number to largest
        self.node.qmemory.comm_qubits_free.sort()
        return program
    
    def _cat_disentangle_end(self, program, classical_comm_port,
                             data_or_tele_qubit_index):
        yield self.await_port_input(classical_comm_port)
        meas_result, = (
            classical_comm_port.rx_input().items)
        if meas_result == 1:
            #correcting some qubit entangled in the
            #cat-entanglement step
            program.apply(instr.INSTR_Z, [data_or_tele_qubit_index])
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            program = QuantumProgram()
        elif meas_result != 0:
            raise ValueError('Measurement result must be an integer with value'
                             f' 0 or 1. The current value, {meas_result}, does '
                             'not meet this criteria.')
        #if meas_result == 0, we do nothing. No gates are required.
        return program
    
    def _bsm(self, program, data_or_tele_qubit_index, other_node_name,
             classical_comm_port):
        yield self.node.qmemory.execute_program(program)
        self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
        #re-initialising self._local_gate_tuples_pending
        self._local_gate_tuples_pending = []
        program=QuantumProgram()
        if len(self.node.qmemory.comm_qubits_free) == 0 :
            #if there are no comm-qubits free:
            raise Exception(f"Scheduling error:"
                            f"No comm-qubits free."
                            f" There are too many "
                            f"remote gates on "
                            f" {self.node.name} in"
                            f" this time slice")
        else: #if there are comm-qubits free
            comm_qubit_index = self.node.qmemory.comm_qubits_free[0]
            #there is no need to delete a comm-qubit 
            #it will be restored at the end of this 
            #block
            if (data_or_tele_qubit_index == -1 and
                len(self.node.qmemory.comm_qubits_free) <
                len(self.node.qmemory.comm_qubit_positions)):
                #letting qubit to be teleported be the 
                #last used communication qubit from the 
                #prev time-slice
                data_or_tele_qubit_index = comm_qubit_index - 1
            if not self.node.qmemory.ebit_ready: 
                yield from self._request_entanglement('client', 
                                                      other_node_name, 
                                                      [comm_qubit_index])
            program.apply(instr.INSTR_CNOT, [data_or_tele_qubit_index, 
                          comm_qubit_index])
            program.apply(instr.INSTR_H, [data_or_tele_qubit_index])
            program.apply(instr.INSTR_MEASURE, [comm_qubit_index],
                          output_key="m1")
# =============================================================================
#                                     #discarding the comm qubit to allow
#                                     #another one to be retrieved.
#                                     #Physically, this can be thought of as
#                                     #reinitialising
#                                     #the comm-qubit prior to entangling it
#                                     #with another photon
#                                     program.apply(instr.INSTR_DISCARD,
#                                                   comm_qubit_index)
# =============================================================================
            program.apply(instr.INSTR_MEASURE, [data_or_tele_qubit_index],
                          output_key = "m2")
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            m1, = program.output["m1"]
            m2, = program.output["m2"]
            program = QuantumProgram()
            #re-setting data-qubit to zero after
            #measurement (comm-qubit already reset
            #when entanglement re-distributed)
            #TO DO: GET THIS TO TAKE SAME TIME AS 
            #APPLYING AN X-GATE controlled by the 
            #measurement result.
            program.apply(instr.INSTR_INIT, data_or_tele_qubit_index)
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            program = QuantumProgram()
            classical_comm_port.tx_output((m1, m2))
            if data_or_tele_qubit_index in self.node.qmemory.comm_qubit_positions:
                #freeing comm_qubit now that it has been
                #measured
                self.node.qmemory.comm_qubits_free = (self.node.qmemory.comm_qubits_free + 
                                              [data_or_tele_qubit_index])
                #re-ordering from smallest number to
                #largest
                self.node.qmemory.comm_qubits_free.sort()
        return program
    
    def _handle_meas_results4tp_correct(self, meas_results, index, program):
        error_msg = ('All elements of meas_results must be integers with value'
                     ' 0 or 1. The current meas_results, which have the value,'
                     f' {meas_results} do not meet this criteria')
        if meas_results[0] == 1:
            program.apply(instr.INSTR_X, index)
        elif meas_results[0] != 0:
            raise ValueError(error_msg)
        #elif meas_results[0] == 0, do nothing
        if meas_results[1] == 1:
            program.apply(instr.INSTR_Z, index)
        elif meas_results[1] != 0:
            raise ValueError(error_msg)
        #elif meas_results[1] == 0, do nothing
    
    def _tp_correct(self, program, other_node_name,
                    classical_comm_port, reserve_comm_qubit, swap_commNdata,
                    data_qubit_index=None):
        """
        

        Parameters
        ----------
        program : TYPE
            DESCRIPTION.
        other_node_name : TYPE
            DESCRIPTION.
        classical_comm_port : TYPE
            DESCRIPTION.
        reserve_comm_qubit : bool
            Whether or not to reserve the comm-qubit being used, so that the
            state teleported there cannot be overwritten. Will reserve if True.
        swap_commNdata : bool
            Whether to swap the data qubit and comm qubit prior to applying
            measurement dependent gates.
        data_qubit_index : int
            The index of the data qubit index to SWAP the comm qubit index with
            if swap_commNdata == True

        Raises
        ------
        Exception
            DESCRIPTION.

        Yields
        ------
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.

        """
        yield self.node.qmemory.execute_program(program)
        self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
        #re-initialising self._local_gate_tuples_pending
        self._local_gate_tuples_pending = []
        program=QuantumProgram()
        if len(self.node.qmemory.comm_qubits_free) == 0 :
            #if there are no comm-qubits free:
            raise Exception(f"Scheduling error: No "
                            f" comm-qubits free. "
                            f"There are too many"
                            f" remote gates on "
                            f"{self.node.name} in "
                            f"this time slice")
        else: #if there are comm-qubits free
            #establishing new comm-qubit for the current
            #teleportation
            comm_qubit_index = self.node.qmemory.comm_qubits_free[0]
            if reserve_comm_qubit:
                del self.node.qmemory.comm_qubits_free[0]
            #removing comm qubit being used from list of 
            #available comm-qubits:
            if not self.node.qmemory.ebit_ready:#if there is no ebit ready:
                yield from self._request_entanglement('server', 
                                                      other_node_name, 
                                                      [comm_qubit_index])
            yield self.await_port_input(classical_comm_port)
            meas_results, = classical_comm_port.rx_input().items
            if swap_commNdata:
# =============================================================================
#                 program.apply(instr.INSTR_CNOT, [comm_qubit_index,
#                                                  data_qubit_index])
#                 program.apply(instr.INSTR_CNOT, [data_qubit_index,
#                                                  comm_qubit_index])
#                 program.apply(instr.INSTR_CNOT, [comm_qubit_index,
#                                                  data_qubit_index])
# =============================================================================
                program.apply(instr.INSTR_SWAP, [comm_qubit_index,
                                                 data_qubit_index])
                self._handle_meas_results4tp_correct(meas_results, 
                                                     data_qubit_index, 
                                                     program)
            else:
                self._handle_meas_results4tp_correct(meas_results, 
                                                     comm_qubit_index, 
                                                     program)
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            program = QuantumProgram()
        return (comm_qubit_index, program)
    
    def _cat_subgenerator(self, role, program, other_node_name,
                          data_or_tele_qubit_index,
                          classical_comm_port,
                          comm_qubit_index):
# =============================================================================
#         #commented out block is alternative implementation. It is more easily
#         #extensible but I think maybe a little harder to understand, in the 
#         #sense that it hides which subgenerators change what variables:
#         cat_subgenerator_funcs = {
#                              "entangle" : self._cat_entangle(other_node_name,
#                                                              comm_qubit_index,
#                                                              ent_request_port),
#                              "correct" : self._cat_correct(program, 
#                                                            other_node_name,
#                                                            classical_comm_port,
#                                                            ent_request_port),
#                              "disentangle_start" : self._cat_disentangle_start(
#                                                         program,
#                                                         comm_qubit_index, 
#                                                         classical_comm_port),
#                              "disentangle_end" : self._cat_disentangle_end(
#                                                     program, 
#                                                     classical_comm_port,
#                                                     data_or_tele_qubit_index)}
#         evexpr_or_vars = yield from self.cat_subgenerator_funcs[role]
# =============================================================================

        if role == "entangle":
            evexpr_or_program = yield from self._cat_entangle(
                                    program, 
                                    other_node_name,
                                    data_or_tele_qubit_index,
                                    classical_comm_port)
            #output will be EventExpression until end of 
            #generator is reached when it will instead 
            #be tuple of useful variables to pass on to 
            #subsequent code. The following works on the 
            #tuple:
            program = evexpr_or_program
                
        elif role == "correct":
            evexpr_or_tuple = yield from self._cat_correct(
                                    program, 
                                    other_node_name,
                                    classical_comm_port)
            #output will be EventExpression until end of 
            #generator is reached when it will instead 
            #be tuple of useful variables to pass on to 
            #subsequent code. The following works on the 
            #tuple:
            comm_qubit_index = evexpr_or_tuple[0]
            program = evexpr_or_tuple[1]

        elif role == "disentangle_start":
            evexpr_or_program = ( 
                yield from self._cat_disentangle_start(
                                    program,
                                    comm_qubit_index, 
                                    classical_comm_port))
            program = evexpr_or_program
            
        elif role == "disentangle_end":
            evexpr_or_program = ( 
                yield from self._cat_disentangle_end(
                                program, 
                                classical_comm_port,
                                data_or_tele_qubit_index))
            program = evexpr_or_program
            
        else:
            raise ValueError(
                "final element of gate_tuple is not valid"
                " role")
        return (comm_qubit_index, program)
            
    def _tp_subgenerator(self, role, program, other_node_name,
                         data_or_tele_qubit_index,
                         classical_comm_port,
                         comm_qubit_index):
        
        if role == "bsm":
            evexpr_or_program = (
                yield from self._bsm(
                    program, 
                    data_or_tele_qubit_index,
                    other_node_name,
                    classical_comm_port))
            program = evexpr_or_program

        elif role == "correct":
            reserve_comm_qubit = True
            swap_commNdata = False
            evexpr_or_tuple = (
                yield from self._tp_correct(
                    program,
                    other_node_name,
                    classical_comm_port,
                    reserve_comm_qubit,
                    swap_commNdata))
            comm_qubit_index = evexpr_or_tuple[0]
            program = evexpr_or_tuple[1]
                
        elif role == "correct4tele_only":
            reserve_comm_qubit = False
            swap_commNdata = False
            evexpr_or_tuple = (
                yield from self._tp_correct(
                    program,
                    other_node_name,
                    classical_comm_port,
                    reserve_comm_qubit,
                    swap_commNdata))
            comm_qubit_index = evexpr_or_tuple[0]
            program = evexpr_or_tuple[1]
            
        elif role == "swap_then_correct":
            reserve_comm_qubit = False
            swap_commNdata = True
            evexpr_or_tuple = (
                yield from self._tp_correct(
                    program,
                    other_node_name,
                    classical_comm_port,
                    reserve_comm_qubit,
                    swap_commNdata,
                    data_qubit_index=data_or_tele_qubit_index))
            comm_qubit_index = evexpr_or_tuple[0]
            program = evexpr_or_tuple[1]
                
        else:
            raise ValueError(
                "final element of gate_tuple is not valid"
                " role")
        return (comm_qubit_index, program)
    
    #SHOULD the following be implemented as a protocol in its own right along 
    #with all primitives?
    def _logged_instr(self, program, gate_tuple):
        """
        Subgenerator that carries out a single-qubit subroutine in which a 
        single-qubit gate is conducted and the result logged.
        
        This is most likely to be used for a measurements of some type (ie, the
        single-qubit gate is a measurement in some basis).

        Parameters
        ----------
        gate_instr : `~netsquid.components.instructions.Instruction`
            The single-qubit gate to carry out a logged version of. In most 
            cases this will be measurement in some basis.
        qubit_index : int
            The qubit to act on.
        
        Yields
        -------
        `~pydynaa.core.EventExpression`
            These allow the sim to wait on Events to happen.
        
        """
        while True:
            gate_instr, gate_op = self._get_gate_instruction_and_op(gate_tuple)
            ancilla_qubit_index = gate_tuple[1]
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            program=QuantumProgram()
            self._flexi_program_apply(program, gate_instr, ancilla_qubit_index, 
                                      gate_op,
                                      output_key='result')
            yield self.node.qmemory.execute_program(program)
            result, = program.output['result']
            self.send_signal(QDCSignals.RESULT_PRODUCED, 
                             result=(result, ancilla_qubit_index))
            self._gate_tuples_evaluated[-1].append(gate_tuple)
            break
        
    def _get_gate_instruction_and_op(self, gate_tuple):
        gate_instr = gate_tuple[0] 
        #handling gate types with associated parameters:
        try: #if gate_instr is iterable:
            gate_op = gate_instr[1]
            gate_instr = gate_instr[0]
        except TypeError: #elif gate_instr is not iterable
            gate_op = None
        return gate_instr, gate_op
        
    def _handle_single_qubit_gate(self, program, gate_tuple):
        gate_instr, gate_op = self._get_gate_instruction_and_op(gate_tuple)
        qubit_index = gate_tuple[1]
        self._flexi_program_apply(program, gate_instr, qubit_index,
                                  gate_op)
        self._local_gate_tuples_pending.append(gate_tuple)
        #self._local_gate_tuples_pending will be added to 
        #self._gate_tuples_evaluated whenever a program is run,
        #allowing us to raise error if not all gate tuples are 
        #evaluated at the end of the sim run.
        
    #TO DO: remove the following if you can't get it to work.
    def _handle_remote_gate_primitive(self, program, gate_tuple, 
                                      comm_qubit_index):
        #The remote gates in this block will use different
        #comm-qubits because logical gates using the same 
        #comm-qubit will occur in different time slices or will
        #have been converted to local gates once teleportation
        #or cat-entanglement has already been done
        while True:
            if len(gate_tuple) == 4:
                data_or_tele_qubit_index = gate_tuple[0]
                other_node_name = gate_tuple[1]
                scheme = gate_tuple[2]
                role = gate_tuple[3]
            elif len(gate_tuple) == 3:
                data_or_tele_qubit_index = None
                other_node_name = gate_tuple[0]
                scheme = gate_tuple[1]
                role = gate_tuple[2]
            node_names = [self.node.name, other_node_name]
            node_names.sort()
            classical_connection_port_name = ( 
                self.node.connection_port_name(
                                                other_node_name,
                                                label="classical"))
            classical_conn_port = self.node.ports[
                                     classical_connection_port_name]
            evexpr_or_variables = ( 
                yield from self.protocol_subgenerators[scheme](
                                        role,
                                        program,
                                        other_node_name,
                                        data_or_tele_qubit_index,
                                        classical_conn_port,
                                        comm_qubit_index))
            #past this point evexpr_or_variables will be the
            #variables
            variables4subsequent_local_gates = evexpr_or_variables
            #keeping track of what gate tuples have been evaluated 
            #to raise error if not all evaluated at end of sim
            self._gate_tuples_evaluated[-1].append(gate_tuple)
            break #breaking inner while loop to allow next 
                  #gate_tuple to be evaluated.
        return variables4subsequent_local_gates
    
    def _handle_local_two_qubit_gate(self, program, gate_tuple, 
                                     comm_qubit_index):
        gate_instr, gate_op = self._get_gate_instruction_and_op(gate_tuple)
        qubit_index0 = gate_tuple[1]
        qubit_index1 = gate_tuple[2]
        if qubit_index0 == -1:
            qubit_index0 = comm_qubit_index #defined in remote gate
                                            #section above
        self._flexi_program_apply(program, gate_instr,
                                  [qubit_index0, qubit_index1],
                                  gate_op)
        self._local_gate_tuples_pending.append(gate_tuple)
        #self._local_gate_tuples_pending will be added to 
        #self._gate_tuples_evaluated whenever a program is run,
        #allowing an error to be raised if not all gate tuples are 
        #evaluated at the end of the sim run.
        
    def _run_time_slice(self, gate_tuples4time_slice):
        #intialising variables that should be overwritten later but are needed
        #as function arguments:
        program=QuantumProgram()
        comm_qubit_index = float("nan")
        #TO DO: think about whether this while loop is needed because there is 
        #a while loop in the enclosing scope. One reason to keep it would be
        #to avoid overwriting the program and comm_qubit_index
        while True:
            for gate_tuple in gate_tuples4time_slice:
                if len(gate_tuple) == 2: #if single-qubit gate:
                    self._handle_single_qubit_gate(program, gate_tuple)
                elif gate_tuple[-1] in self.single_qubit_subroutines: 
                    yield from self._logged_instr(program, gate_tuple)
                elif (isinstance(gate_tuple[-1], str) and gate_tuple[-2] in 
                      self.protocol_subgenerators): #if primitive for remote
                                                    #gate:
                    #The remote gates in this block will use different
                    #comm-qubits because logical gates using the same 
                    #comm-qubit will occur in different time slices or will
                    #have been converted to local gates once teleportation
                    #or cat-entanglement has already been done
                    evexpr_or_variables = yield from self._handle_remote_gate_primitive(
                                                        program, gate_tuple, 
                                                        comm_qubit_index)
                    #past this point evexpr_or_variables will be the
                    #variables for use in subsequent remote gates. The program
                    #needs spelled out here and not in other subgenerators 
                    #because of the additional nesting of 
                    #self._flexi_program_apply inside _cat_subgenerators or 
                    #_tp_subgenerators which are in turn inside of 
                    #_handle_remote_gate_primitive
                    comm_qubit_index = evexpr_or_variables[0]
                    program = evexpr_or_variables[1]
                #strictly speaking the following will allow any local 
                #multi-qubit gate. You need to decide whether you want to allow
                #for this or not (if you want arbitrary multi-qubit then need
                #to change compiler)
                elif isinstance(gate_tuple[-1], int): #if local 2-qubit gate
                    self._handle_local_two_qubit_gate(program, gate_tuple,
                                                      comm_qubit_index)
            #executing any instructions that have not yet been executed. It is 
            #important that the quantum program is always reset after each node
            #is finished to avoid waiting infinitely long if there is nothing 
            #left to execute
            yield self.node.qmemory.execute_program(program)
            self._gate_tuples_evaluated[-1].extend(
                                               self._local_gate_tuples_pending)
            #re-initialising self._local_gate_tuples_pending
            self._local_gate_tuples_pending = []
            self.send_signal(self.finished_time_slice_label)
            break #breaking outermost while loop
            #TO DO: add entanglement swapping
            
    def raise_error_if_not_all_gates_executed(self):
        """
        To be run after the end of a sim run.
        """
        if self._gate_tuples_evaluated != self.gate_tuples:
            index_of_last_time_slice_evaluated = ( 
                                        len(self._gate_tuples_evaluated) - 1)
            index_of_final_time_slice = len(self.gate_tuples) - 1
            try:
                last_gate_tuple_evaluated = self._gate_tuples_evaluated[-1][-1]
            except IndexError:
                last_gate_tuple_evaluated = self._gate_tuples_evaluated[-1]
            raise UnfinishedQuantumCircuitError(
                        "Not all operations in the quantum circuit have run. "
                        "Evaluation stopped in time slice "
                        f"{index_of_last_time_slice_evaluated} out of "
                        f"{index_of_final_time_slice}. The last gate_tuple to "
                        f"be evaluated was {last_gate_tuple_evaluated}. "
                        "Overall, the gates evaluated were "
                        f"{self._gate_tuples_evaluated} and the gate tuples "
                        f"that SHOULD have been evaluated were "
                        f"{self.gate_tuples}")

    def run(self):
        if 'physical_layer_protocol' not in self.subprotocols or not \
            isinstance(self.subprotocols['physical_layer_protocol'], 
                       Base4PhysicalLayerProtocol):
            raise ValueError(f'{self.name} requires a physical layer protocol, '
                             'which is a subclass of Base4PhysicalLayerProtocol,'
                             'to be added. This can be done with the '
                             'add_phys_layer method')
        
        self.subprotocols['physical_layer_protocol'].start()
        #this protocol will be made a subprotocol of another and so will 
        #automatically stop when the parent protocol does. This avoids the 
        #infinite loop that would otherwise occur from the following.
        time_slice=0
        while True:
            yield self.await_signal(self.superprotocol, 
                                    signal_label=self.start_time_slice_label)
            gate_tuples4time_slice = self.gate_tuples[time_slice]
            yield from self._run_time_slice(gate_tuples4time_slice)
            if time_slice < (self._max_num_time_slices - 1):
                #synchronise number of time slices in 
                #self._gate_tuples_evaluated with the number of time slices in 
                #self._gate_tuples
                self._gate_tuples_evaluated.append([])
            time_slice = time_slice + 1

class dqcMasterProtocol(Protocol):
    """ Protocol which executes a distributed quantum circuit. 
    
    Parameters
    ----------
    partitioned_gates:  list of tuples.
        The gates implemented in the entire circuit. The tuples should be
        of the form:
        1) single-qubit gate: (gate_instr, qubit, node_name)
        2) two-qubit gate: (list of instructions or gate_instruction if
                            local,qubit0, node0_name, qubit1, node1_name,
                            scheme) 
                            #can later extend this to multi-qubit gates
                            #keeping scheme as last element
                            list of instructions: list
                                list of same form as partitioned_gates
                                containing the local gates to be conducted
                                as part of the remote gate. Ie, for
                                remote-cnot this would contain the cnot 
                                (but not the gates used for bsm or
                                 correction).
                                Note if this is given as empty list and 
                                scheme = "tp" then it will just do a
                                teleportation
    network : :class: `~netsquid.nodes.network.Network`
        Wraps all simulated hardware.
    physical_layer_protocol_class: class or None
        The class of the physical layer protocol. The choice must be callable
        with no explicit arguments. If None, 
        :class: `~dqc_simulator.software.physical_layer.AbstractCentralSourceEntangleProtocol`
        is used.
    background_protocol_lookup : dict
        Lookup table with keys being subclasses of netsquid.nodes.node.Node
        and protocols being non-QPU subclasses of 
        netsquid.protocols.protocol.Protocol. This is used to start all 
        protocols that exist outside of time slice structure and must be 
        initialised to make the network function.
    compiler_func: function, optional
        The compiler function to be used to split partitioned_gates into
        protocols by node and time-slice. If None (default), then 
        :func: `~dqc_simulator.software.compilers.sort_greedily_by_node_and_time`
        is used.
    num_entanglement_attempts : int or None, optional
        The number of entanglement attempts for the physical layer to use 
        before returning control to higher layers. This must be specified if 
        the physical layer entanglement protocol used is not deterministic. The
        default is None (which assumes the physical layer is deterministic by
        default).
    name : str or None, optional. Name of protocol. If None, the name of the 
        class is used [1]_.
            
    Attributes
    ----------
    physical_layer_protocol : :class: `~dqc_simulator.software.physical_layer.Base4PhysicalLayer
        The physical layer protocol used.
        
    Notes
    -----
    This protocol violates locality by splitting everything into time slices. 
    Each time slice
    obeys locality but the entire network is instantaneously made aware when a 
    time slice ends. This is intended to be an easier-to-implement abstraction
    of each node knowing the entire circuit and having a time slice 
    counter of things it is allowed to do on that time slice before waiting a 
    certain amount of time (the max time for operations on any QPU in the 
    entire circuit) prior to evaluating the operations it has for that time slice.
    This construction is a compromise between retaining the 
    user's ability to easily use and test their own almost arbitrary compilation 
    schemes (global sequencing can be enforced using the time slices,
    simplifying the coding of compilers to the production of nested lists of 
    gate tuples) and an easier to use framework that waits for resources to 
    become available
    and greedily conducts operations as soon as possible, which can be achieved
    by putting everything in one time slice. A limitation of the framework is
    that a given QPU may not be able to do subprotocols for more than one remote
    gate at once even if there are enough resources to do so (I am essentially
    assuming that each QPU can be involved in only one remote gate per time 
    slice).
    
    References
    ----------
    The parameters in which Ref. [1]_ was cited were inherited from 
    :class: `~netsquid.protocols.protocol.Protocol` and the description
    used for those parameters was taken from the NetSquid documentation [1]_
    
    .. [1] https://netsquid.org/
    
    .. todo::
        
        Decide whether to use *args4physical_layer, **kwargs for physical layer
        to allow the physical layer protocol to be called with arguments
    """
    def __init__(self, partitioned_gates, network,
                 physical_layer_protocol_class=None,
                 background_protocol_lookup=None,
                 compiler_func=None,
                 num_entanglement_attempts=None,
                 name=None):
        super().__init__(name)
        self.start_time_slice_label = "START_TIME_SLICE"
        self.finished_time_slice_label = "FINISHED_TIME_SLICE"
        self.add_signal(self.start_time_slice_label)
        self.add_signal(self.finished_time_slice_label)
        self.partitioned_gates = partitioned_gates
        self.network = network
        #TO DO: think about whether it would be better to instantiate default
        #arguments using the setter of a property
        
        #instantiating default arguments
        if physical_layer_protocol_class is None:
            physical_layer_protocol_class = ( 
                AbstractCentralSourceEntangleProtocol)
        else:
            #TO DO: raise error if calling this without arguments raises error
            physical_layer_protocol_class = physical_layer_protocol_class
        if compiler_func is None:
            self.compiler_func = sort_greedily_by_node_and_time
        else:
            self.compiler_func = compiler_func
            
        self.background_protocol_lookup = background_protocol_lookup
            
        self.qpu_op_dict = self.compiler_func(self.partitioned_gates)
        all_nodes = self.network.nodes
        for node_name in self.qpu_op_dict:
        #I use qpu_op_dict rather than network.nodes here to avoid any
        #situations in which a QPU node has not been added to the network but 
        #has instructions specified for it without an error being raised 
            node = all_nodes[node_name]
            if isinstance(node.qmemory, QPU): 
            #if the node has a QPU and that QPU has instructions to run at any
            #point
                qpu_protocol = QpuOSProtocol(
                                    superprotocol=self, 
                                    gate_tuples=self.qpu_op_dict[node_name],
                                    node=node,
                                    name=f'QpuOSProtocol_{node.name}')
                self.physical_layer_protocol = ( 
                    physical_layer_protocol_class(node=node))
                if not self.physical_layer_protocol.deterministic:
                    self.physical_layer_protocol.num_entanglement_attempts = (
                        num_entanglement_attempts)
                        
                qpu_protocol.add_phys_layer(self.physical_layer_protocol)
                self.add_subprotocol(qpu_protocol, 
                                     name=f'{node_name}_OS')
# =============================================================================
#             else:
#                 node_type = type(node)
#                 background_protocol = self.background_protocol_lookup[node_type](
#                                          node=node,
#                                          name=f"{node_name}_protocol")
#                 background_protocol.start()
# =============================================================================

    def check_quantum_circuit_finished(self):
        """
        Should be called after the sim has finished running to check if the 
        intended distributed quantum circuit actually ran all the way through.
        """
        for qpu_name in self.qpu_op_dict:
            self.subprotocols[
                f'{qpu_name}_OS'].raise_error_if_not_all_gates_executed()
        
    def run(self):
        for qpu_name in self.qpu_op_dict:
            self.subprotocols[f'{qpu_name}_OS'].start()
        #initialising dummy event expression 
        dummy_entity = pydynaa.Entity()
        evtype_dummy = pydynaa.EventType("dummy_event", "dummy event")
        evexpr_dummy = pydynaa.EventExpression(
            source=dummy_entity, event_type=evtype_dummy)
        expr = evexpr_dummy
        dummy_entity._schedule_now(evtype_dummy)
        
        #finding max length of dictionary entry
        longest_list_in_qpu_op_dict = max(self.qpu_op_dict.values(), key=len)
        max_num_time_slices = len(longest_list_in_qpu_op_dict)
        while True:
            for time_slice in range(max_num_time_slices):
                for qpu_name in self.qpu_op_dict:
                    #if QPU still has instructions to carry out:
                    if time_slice < len(self.qpu_op_dict[qpu_name]):
                    #strictly less than because python indexes from 0
                        #signalling subprotocols to start the next time slice
                        self.send_signal(self.start_time_slice_label)
                        #waiting on subprotocols to complete time slice
                        expr = expr & self.await_signal(
                                        self.subprotocols[f'{qpu_name}_OS'], 
                                        self.finished_time_slice_label)
                yield expr
                #re-initialising
                expr = evexpr_dummy 
                dummy_entity._schedule_now(evtype_dummy)
            break #exiting outer while loop once for loops are done






#Correcting occupies a qubit because that needs to be used as the control for 
#a cnot etc but the bsm frees one if done to teleport a comm_qubit

#I am assuming:
#1) The input list of gate tuples is loosely ordered like in a circuit diagram
#2) That there is only one remote gate per node on a time slice. This is by 
#construction and so is not really an assumption. All of that said, it is 
#actually possible to have multiple remote gates on a node if the compiler 
#allows it. In that case many of the safeguards here will not work and so you 
#need the compiler to have properly accounted for resources.
#3) For now, gates cannot be done in parallel with receiving entanglement. This
#is probably physically realistic anyway.
#4) At the moment, unlike the CollComm protocol explored by the Santa Barbara
#group, everything is quite coupled to the comm-qubits. This is not completely
#general 