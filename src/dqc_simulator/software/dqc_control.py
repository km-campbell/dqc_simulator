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

from dqc_simulator.software.compilers import sort_greedily_by_node_and_time
from dqc_simulator.hardware.dqc_creation import QpuNode

#The following will act on the qsource node, Charlie, when one of the nodes 
#either side of Charlie a message to Charlie asking for an entangled pair.
#This message should have the form of a pair of indices in a tuple with the 
#first index being the comm qubit of the node requesting entanglement and the 
#second index being the comm qubit of the node it is requesting entanlgement 
#with
class AbstractFromPhotonsEntangleProtocol(NodeProtocol):
    """ Abstract protocol for generating entanglement.
    
    An abstract way of generating photons designed to act on a specific 
    instance of :class: `~netsquid.nodes.node.Node` created within 
    :func: `~dqc_simulator.hardware.dqc_creation.create_abstract_entangling_link`.
    
    Notes
    -----
    This abstracts from the details of photon generation by treating flying
    and communication qubits as the same thing. Restraints on the number of 
    communication qubits can be enforced at the QPU nodes but entangled 
    communication qubits are generated at a central quantum source and sent
    to the QPUs. In this way, we can model error and loss but needn't simulate
    the details of entanglement between static communication qubits and photons.
    The protocol assumes a certain network structure and is designed to act on
    a quantum source node Charlie_{node_a.name}<->{node_b.name}, so as to 
    distribute an entangled 
    pair to node_a and node_b from a quantum source between them. This protocol
    will do something when Charlie_{node_a.name}<->{node_b.name} receives a 
    message consisting of a tuple with 2 indices. The first index is the index
    of node_a's comm qubit and the second that of node_b. The protocol can only
    connect linked nodes and will not work over a virtual quantum connection.
    
    .. todo::
        
        Deprecate this once refactoring is finished.
    """
        
    def run(self):
        def route_based_on_m1_m2(m1, m2):
            qsource_output_port0 = self.node.subcomponents[
                f"qsource_{self.node.name}"].ports["qout0"]
            qsource_output_port1 = self.node.subcomponents[
                f"qsource_{self.node.name}"].ports["qout1"]
            #removing any pre-existing connections to allow for new routing
            if qsource_output_port0.is_connected:
                qsource_output_port0.disconnect()
            if qsource_output_port1.is_connected:
                qsource_output_port1.disconnect()
            #routing quantum source output based on message content:
            if m1 == 0: #if node_a's first comm qubit is selected
                qsource_output_port0.forward_output(self.node.ports["qout0"])
            elif m1 == 1: #if node_a's second comm qubit is selected
                qsource_output_port0.forward_output(self.node.ports["qout2"])
            else:
                raise ValueError("comm qubit indices must be 0 or 1 in "
                                 " current topology")
            if m2 == 0:
                qsource_output_port1.forward_output(self.node.ports["qout1"])
            elif m2 == 1:
                qsource_output_port1.forward_output(self.node.ports["qout3"])
            else:
                raise ValueError("comm qubit indices must be 0 or 1 in "
                                 " current topology")
                #TO DO: allow number of comm-qubits to be specified in network
                #def and then allow any number of comm_qubits here
                #variable here (you can use a pattern on the names
                #of the qout{ii} ports)
            #trigger generation of entangled state
            self.node.subcomponents[f"qsource_{self.node.name}"].trigger()
            
        #initialising variables which will be overwritten when received
        #(this allows whether or not they are defined to be used in if loop)
        m1_defined = False
        m2_defined = False
        while True:
            #wait for entanglement request from node_a or node_b
            expr = yield (self.await_port_input(self.node.ports[
                                "entanglement_request_inputA2C"])
                           | self.await_port_input(self.node.ports[
                                "entanglement_request_inputB2C"]))
            if expr.first_term.value:
                msg, = self.node.ports[
                    "entanglement_request_inputA2C"].rx_input().items
                if type(msg) == int:
                    m1 = msg
                    m1_defined = True
            else:
                msg, = self.node.ports[
                    "entanglement_request_inputB2C"].rx_input().items
                if type(msg) == int:
                    m2 = msg
                    m2_defined = True
            
            if type(msg) == tuple:
                m1 = msg[0]
                m2 = msg[1]
                route_based_on_m1_m2(m1, m2)

            if m1_defined and m2_defined:
                route_based_on_m1_m2(m1, m2)
                #re-initialising
                m1_defined = False
                m2_defined = False
                
            #TO DO: raise error if Alice sends tuple and 
            #Bob sends int or vice versa


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
    """
    #The core idea of what follows is to add instructions to a QuantumProgram
    #until remote gates occur, at which point the program will be run to that 
    #point, re-initialised and then added to with instructions needed for the
    #part of the remote gate done on this node. The classical port names have
    #been chosen so that the sending and receiving port have the same f-string
    #but will have different names when this protocol is acted on the 
    #appropriate nodes

    def __init__(self, superprotocol, gate_tuples, node=None, name=None):
        super().__init__(node, name)
        self.superprotocol = superprotocol
        self.gate_tuples = gate_tuples
        #The following subgenerators are similar to subprotocols implemented
        #in functional form rather than as classes. Unlike subprotocols (as far
        #as I can tell), the protocol_subgenerators can yield variables
        #needed for subsequent processes as well as event expressions used to 
        #evolve the simulation in time.
        self.protocol_subgenerators = {"cat" : self._cat_subgenerator,
                                       "tp" : self._tp_subgenerator}
        self.ent_request_label = "ENT_REQUEST"
        self.ent_ready_label = "ENT_READY"
        self.ent_failed_label = "ENT_FAILED"
        self.start_time_slice_label = "START_TIME_SLICE"
        #TO DO: add link layer as a subprotocol.

    def _flexi_program_apply(self, qprogram, gate_instr, qubit_indices, 
                             gate_op):
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
            
        .. todo::
            
            Handle situations where entanglement is successful or not 
            successful in _request_entanglement method (see comment there)
        """
        if gate_op is None:
            qprogram.apply(gate_instr, qubit_indices)
        else:
            qprogram.apply(gate_instr, qubit_indices, operator=gate_op)
            
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
        #TO DO: change comm_qubit_index to comm_qubit_indices here and in calls
        #and ensure that wherever it is called a list or tuple is being 
        #inputted
        
        #send entanglement request to link layer specifying the other node
        #involved in the connection and the comm-qubit to be used:
        self.send_signal(self.ent_request_label, 
                         result=(role, other_node_name, comm_qubit_indices,
                                 num_entanglements2generate,
                                 entanglement_type2generate))        
        #TO DO: correct the following. Instances of the class must be provided
        #to await_signal not the class itself. Moreover, 
        #EntanglementGenerationProtocol has been deprecated and instead an 
        #instance of the physical layer protocol will be needed.
        #wait for entangled qubit to arrive in requested comm-qubit slot:
        wait4succsessful_ent = self.await_signal(
                                   EntanglementGenerationProtocol,
                                   signal_label=self.ent_ready_label)
        wait4failed_ent = self.await_signal(
                              EntanglementGenerationProtocol,
                              signal_label= self.ent_failed_label)
        evexpr = yield wait4succsessful_ent | wait4failed_ent
        #TO DO: implement block commented out below. It may be enough to only
        #handle the case where entanglement failed as previously you just 
        #waited for entanglement to be ready
# =============================================================================
#         if evexpr.first_term.value: #if entanglement success signal recieved:
#             #do something
#         elif evexpr.second_term.value: #if entanglement failed signal received:
#             #do something else
# =============================================================================
            
        #TO DO: delete commented out block below once it has been reimplemented 
        #as its own protocol in the physical layer if refactoring is successful
# =============================================================================
#         node_names = [self.node.name, other_node_name]
#         node_names.sort()
#         ent_recv_port = self.node.ports[
#             f"quantum_input_from_charlie"
#             f"{comm_qubit_index}_"
#             f"{node_names[0]}<->{node_names[1]}"]
#         #send entanglement request specifying
#         #the comm-qubit to be used:
#         ent_request_port.tx_output(comm_qubit_index)
#         #wait for entangled qubit to arrive in
#         #requested comm-qubit slot:
#         yield self.await_port_input(ent_recv_port)
# =============================================================================
            
    def _cat_entangle(self, program, other_node_name,
                      data_or_tele_qubit_index, classical_comm_port):
        yield self.node.qmemory.execute_program(program)
        program=QuantumProgram()
        if len(self.node.comm_qubits_free) == 0: 
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
            comm_qubit_index = self.node.comm_qubits_free[0]
            #removing comm qubit being used from list
            #of available comm-qubits:
            if not self.node.ebit_ready: #if there is no ebit ready:
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
            yield self.node.qmemory.execute_program(
                program) 
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
        program=QuantumProgram()
        if len(self.node.comm_qubits_free) == 0: 
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
            comm_qubit_index = self.node.comm_qubits_free[0]
            #removing comm qubit being used from list
            #of available comm-qubits:
            if not self.node.ebit_ready: #if there is no ebit ready:
                yield from self._request_entanglement('server', 
                                                      other_node_name, 
                                                      [comm_qubit_index])
            del self.node.comm_qubits_free[0]
            #wait for measurement result
            yield self.await_port_input(classical_comm_port)
            meas_result, = classical_comm_port.rx_input().items
            if meas_result == 1:
                program.apply(instr.INSTR_X, comm_qubit_index)
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
        meas_result, = program.output["mb"]  
        program = QuantumProgram() #re-initialising
        classical_comm_port.tx_output(meas_result)
        #freeing comm-qubit now that it is not needed
        self.node.comm_qubits_free = (self.node.comm_qubits_free +
                                      [comm_qubit_index])
        #re-odering form smallest number to largest
        self.node.comm_qubits_free.sort()
        return program
    
    def _cat_disentangle_end(self, program, classical_comm_port,
                             data_or_tele_qubit_index):
        yield self.await_port_input(
            classical_comm_port)
        meas_result, = (
            classical_comm_port.rx_input().items)
        if meas_result == 1:
            #correcting some qubit entangled in the
            #cat-entanglement step
            program.apply(instr.INSTR_Z, [data_or_tele_qubit_index])
            yield self.node.qmemory.execute_program(program)
            program = QuantumProgram()
        return program
    
    def _bsm(self, program, data_or_tele_qubit_index, other_node_name,
             classical_comm_port):
        yield self.node.qmemory.execute_program(program)
        program=QuantumProgram()
        if len(self.node.comm_qubits_free) == 0 :
            #if there are no comm-qubits free:
            raise Exception(f"Scheduling error:"
                            f"No comm-qubits free."
                            f" There are too many "
                            f"remote gates on "
                            f" {self.node.name} in"
                            f" this time slice")
        else: #if there are comm-qubits free
            comm_qubit_index = self.node.comm_qubits_free[0]
            #there is no need to delete a comm-qubit 
            #it will be restored at the end of this 
            #block
            if (data_or_tele_qubit_index == -1 and
                len(self.node.comm_qubits_free) <
                len(self.node.comm_qubit_positions)):
                #letting qubit to be teleported be the 
                #last used communication qubit from the 
                #prev time-slice
                data_or_tele_qubit_index = comm_qubit_index - 1
            #TO DO: implement the following if block as a subgenerator because 
            #it appears many times in your different subgenerators
            if not self.node.ebit_ready: 
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
            program = QuantumProgram()
# =============================================================================
#                                     if m2 == 1:
#                                         program.apply(instr.INSTR_X,
#                                                       data_or_tele_qubit_index)
#                                         yield (
#                                           self.node.qmemory.execute_program(
#                                               program))
#                                         program = QuantumProgram()
# =============================================================================
            classical_comm_port.tx_output((m1, m2))
            if data_or_tele_qubit_index in self.node.comm_qubit_positions:
                #freeing comm_qubit now that it has been
                #measured
                self.node.comm_qubits_free = (self.node.comm_qubits_free + 
                                              [data_or_tele_qubit_index])
                #re-ordering from smallest number to
                #largest
                self.node.comm_qubits_free.sort()
        return program
    
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
        program=QuantumProgram()
        if len(self.node.comm_qubits_free) == 0 :
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
            comm_qubit_index = self.node.comm_qubits_free[0]
            if reserve_comm_qubit:
                del self.node.comm_qubits_free[0]
            #removing comm qubit being used from list of 
            #available comm-qubits:
            if not self.node.ebit_ready:#if there is no ebit ready:
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
                if meas_results[0] == 1:
                    program.apply(instr.INSTR_X, data_qubit_index)
                if meas_results[1] == 1:
                    program.apply(instr.INSTR_Z, data_qubit_index)
            else:
                if meas_results[0] == 1:
                    program.apply(instr.INSTR_X, comm_qubit_index)
                if meas_results[1] == 1:
                    program.apply(instr.INSTR_Z, comm_qubit_index)
            yield self.node.qmemory.execute_program(program)
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

    def _run_time_slice(self, gate_tuples4time_slice):
        #intialising variables that should be overwritten later but are needed
        #as function arguments:
        program=QuantumProgram()
        comm_qubit_index = float("nan")
        while True:
            for gate_tuple in gate_tuples4time_slice:
                gate_instr = gate_tuple[0] 
                #handling gate types with associated parameters:
                try: #if gate_instr is iterable:
                    gate_op = gate_instr[1]
                    gate_instr = gate_instr[0]
                except TypeError: #elif gate_instr is not iterable
                    gate_op = None
                    
                if len(gate_tuple) == 2: #if single-qubit gate
                    qubit_index = gate_tuple[1]
                    self._flexi_program_apply(program, gate_instr, qubit_index,
                                              gate_op)
                elif type(gate_tuple[-1]) == str: #if primitive for remote gate
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
                        classical_comm_port = self.node.ports[
                            f"classical_connection_{self.node.name}->"
                            f"{other_node_name}"]
                        evexpr_or_variables = ( 
                            yield from self.protocol_subgenerators[scheme](
                                                    role,
                                                    program,
                                                    other_node_name,
                                                    data_or_tele_qubit_index,
                                                    classical_comm_port,
                                                    comm_qubit_index))
                        #past this point evexpr_or_variables will be the
                        #variables
                        comm_qubit_index = evexpr_or_variables[0]
                        program = evexpr_or_variables[1]
                        break #breaking inner while loop to allow next 
                              #gate_tuple to be evaluated.
                elif type(gate_tuple[-1]) == int: #if local 2-qubit gate
                    qubit_index0 = gate_tuple[1]
                    qubit_index1 = gate_tuple[2]
                    if qubit_index0 == -1:
                        qubit_index0 = comm_qubit_index #defined in remote gate
                                                        #section above
                    self._flexi_program_apply(program, gate_instr,
                                              [qubit_index0, qubit_index1],
                                              gate_op)
            #executing any instructions that have not yet been executed. It is 
            #important that the quantum program is always reset after each node
            #to avoid waiting infinitely long if there is nothing left to
            #execute
            yield self.node.qmemory.execute_program(program) 
            self.send_signal(Signals.SUCCESS)
            break #breaking outermost while loop
            #TO DO: add entanglement swapping

    def run(self):
        #this protocol will be made a subprotocol of another and so will 
        #automatically stop when the parent protocol does. This avoids the 
        #infinite loop that would otherwise occur from the following.
        time_slice=0
        while True:
            yield self.await_signal(self.superprotocol, 
                                    signal_label=self.start_time_slice_label)
            gate_tuples4time_slice = self.gate_tuples[time_slice]
            yield from self._run_time_slice(gate_tuples4time_slice)
            time_slice = time_slice + 1
# =============================================================================
#         #intialising variables that should be overwritten later but are needed
#         #as function arguments:
#         program=QuantumProgram()
#         comm_qubit_index = float("nan")
#         while True:
#          #TO DO: could potentially put another for loop here which cycles over
#          #each row of gate_tuples outputted for this node by the scheduler
#          #with some yield statement after each row of gate_tuples have been
#          #evaluated to make it wait for next time slice. This would save
#          #having to make many protocols
#          
#             for gate_tuple in self.gate_tuples:
#                 gate_instr = gate_tuple[0] 
#                 #handling gate types with associated parameters:
#                 try: #if gate_instr is iterable:
#                     gate_op = gate_instr[1]
#                     gate_instr = gate_instr[0]
#                 except TypeError: #elif gate_instr is not iterable
#                     gate_op = None
#                     
#                 if len(gate_tuple) == 2: #if single-qubit gate
#                     qubit_index = gate_tuple[1]
#                     self._flexi_program_apply(program, gate_instr, qubit_index,
#                                               gate_op)
#                 elif type(gate_tuple[-1]) == str: #if primitive for remote gate
#                     #The remote gates in this block will use different
#                     #comm-qubits because logical gates using the same 
#                     #comm-qubit will occur in different time slices or will
#                     #have been converted to local gates once teleportation
#                     #or cat-entanglement has already been done
#                     while True:
#                         if len(gate_tuple) == 4:
#                             data_or_tele_qubit_index = gate_tuple[0]
#                             other_node_name = gate_tuple[1]
#                             scheme = gate_tuple[2]
#                             role = gate_tuple[3]
#                         elif len(gate_tuple) == 3:
#                             data_or_tele_qubit_index = None
#                             other_node_name = gate_tuple[0]
#                             scheme = gate_tuple[1]
#                             role = gate_tuple[2]
#                         node_names = [self.node.name, other_node_name]
#                         node_names.sort()
#                         classical_comm_port = self.node.ports[
#                             f"classical_connection_{self.node.name}->"
#                             f"{other_node_name}"]
#                         evexpr_or_variables = ( 
#                             yield from self.protocol_subgenerators[scheme](
#                                                     role,
#                                                     program,
#                                                     other_node_name,
#                                                     data_or_tele_qubit_index,
#                                                     classical_comm_port,
#                                                     comm_qubit_index))
#                         #past this point evexpr_or_variables will be the
#                         #variables
#                         comm_qubit_index = evexpr_or_variables[0]
#                         program = evexpr_or_variables[1]
#                         break #breaking inner while loop to allow next 
#                               #gate_tuple to be evaluated.
#                 elif type(gate_tuple[-1]) == int: #if local 2-qubit gate
#                     qubit_index0 = gate_tuple[1]
#                     qubit_index1 = gate_tuple[2]
#                     if qubit_index0 == -1:
#                         qubit_index0 = comm_qubit_index #defined in remote gate
#                                                         #section above
#                     self._flexi_program_apply(program, gate_instr,
#                                               [qubit_index0, qubit_index1],
#                                               gate_op)
#             #executing any instructions that have not yet been executed. It is 
#             #important that the quantum program is always reset after each node
#             #to avoid waiting infinitely long if there is nothing left to
#             #execute
#             yield self.node.qmemory.execute_program(program) 
#             self.send_signal(Signals.SUCCESS)
#             break #breaking outermost while loop
#             #TO DO: add entanglement swapping
# =============================================================================

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
    allowed_qpu_types : tuple or subclass of :class: `~netsquid.nodes.node.Node`
        The class(es) that should be interpretted as QPU nodes. These should be
        distinct from those used for other purposes.
    name : str or None, optional. Name of protocol. If None, the name of the 
        class is used [1]_.
            
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
    """
    def __init__(self, partitioned_gates, network,
                 background_protocol_lookup=None,
                 compiler_func=None,
                 allowed_qpu_types=None,
                 name=None):
        super().__init__(name)
        self.start_time_slice_label = "START_TIME_SLICE"
        self.add_signal(self.start_time_slice_label)
        self.partitioned_gates = partitioned_gates
        self.network = network
        #instantiating default arguments
        if compiler_func is None:
            self.compiler_func = sort_greedily_by_node_and_time
        else:
            self.compiler_func = compiler_func
        if background_protocol_lookup is None:
            #defaulting to starting AbstractFromPhotonsEntangleProtocol on 
            #anything that is not a QpuNode
            self.background_protocol_lookup = ( 
                            {Node : AbstractFromPhotonsEntangleProtocol})
        else:
            self.background_protocol_lookup = background_protocol_lookup
        if allowed_qpu_types is None:
            self.allowed_qpu_types = QpuNode
        else:
            self.allowed_qpu_types = allowed_qpu_types
            
        self.qpu_op_dict = self.compiler_func(self.partitioned_gates)
        self.qpu_dict = {}
        for node_name, node in self.network.nodes.items():
# =============================================================================
#             print(node)
# =============================================================================
            if isinstance(node, self.allowed_qpu_types): #isinstance also 
                                                         #looks for subclasses
                self.qpu_dict[node_name] = node
                qpu_protocol = QpuOSProtocol(
                                    superprotocol=self, 
                                    gate_tuples=self.qpu_op_dict[node_name],
                                    node=node)
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
        
    def run(self):
        for qpu_name in self.qpu_op_dict:
            self.subprotocols[f'{qpu_name}_OS'].start()
# =============================================================================
#         qpu_op_dict = self.compiler_func(self.partitioned_gates)
#         qpu_dict = {}
#         for node_name, node in self.network.nodes.items():
# # =============================================================================
# #             print(node)
# # =============================================================================
#             if isinstance(node, self.allowed_qpu_types): #isinstance also 
#                                                          #looks for subclasses
#                 qpu_dict[node_name] = node
#             else:
#                 node_type = type(node)
#                 background_protocol = self.background_protocol_lookup[node_type](
#                                          node=node,
#                                          name=f"{node_name}_protocol")
#                 background_protocol.start()
# =============================================================================

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
# =============================================================================
#                         gate_tuples4node_and_time = (
#                             qpu_op_dict[qpu_name][time_slice])
#                         protocol4node_and_time = (
#                             QpuOSProtocol(
#                                 gate_tuples4node_and_time,
#                                 node=qpu_dict[qpu_name]))
#                         expr = expr & self.await_signal(protocol4node_and_time, 
#                                                         Signals.SUCCESS)
# =============================================================================
                        #signalling subprotocols to start the next time slice
                        self.send_signal(self.start_time_slice_label)
                        #waiting on subprotocols to complete time slice
                        expr = expr & self.await_signal(
                                        self.subprotocols[f'{qpu_name}_OS'], 
                                        Signals.SUCCESS)
# =============================================================================
#                         protocol4node_and_time.start()
# =============================================================================
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