# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 12:40:42 2023

@author: kenny
"""

import pydynaa
from netsquid.protocols.protocol import Signals, Protocol
from netsquid.protocols.nodeprotocols import NodeProtocol
from netsquid.components import instructions as instr
from netsquid.components.qprogram import QuantumProgram


from dqc_simulator.software.compilers import sort_greedily_by_node_and_time

#The following will act on the qsource node, Charlie, when one of the nodes 
#either side of Charlie a message to Charlie asking for an entangled pair.
#This message should have the form of a pair of indices in a tuple with the 
#first index being the comm qubit of the node requesting entanglement and the 
#second index being the comm qubit of the node it is requesting entanlgement 
#with
class EntangleLinkedNodesProtocol(NodeProtocol):
    """ Designed to act on the quantum source node
    Charlie_{node_a.name}<->{node_b.name}, so as to distribute an entangled 
    pair to node_a and node_b from a quantum source between them. This protocol
    will do something when Charlie_{node_a.name}<->{node_b.name} receives a 
    message consisting of a tuple with 2 indices. The first index is the index
    of node_a's comm qubit and the second that of node_b. The protocol can only
    connect linked nodes and will not work over a virtual quantum connection.
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

class HandleCommBlockForOneNodeProtocol(NodeProtocol):
    """Carries out the parts of the protocol on one node. This is designed 
    such that it can carry out all parts of a circuit on one node which will be 
    compiled using the greedy algorithm but is also 
    capable of doing a single communication block if used as a subprotocol
    and fed only the gate tuples for that block.
    
        INPUT:
            gate_tuples: list or list-like iterable of tuples 
                        (first entry may be list of tuples if there are
                         remote gates)
                The gates to be conducted. Remote gates may have a list of 
                tuples as the first entry of this list if in the recv role to
                allow several local
                gates to be applied as part of the remote gate.
                Each gate_tuple in gate_tuples4this_node_and_time must have
                form:
                1) for single-qubit gate: (gate_type, qubit_index)
                2) for two-qubit gate: (gate_type, qubit_index1, qubit_index2)
                3) for remote gate primitive: (data_qubit_index or sometimes
                                               index of qubit to be
                                               teleported/distributed, 
                                               other_node_name, scheme, role).
                    where othernode_name is the name attribute of a
                    netsquid.nodes.Node object, and gate_type is an
                    instruction from netsquid.components.instructions
                    
            comm_qubits_free: list of indices, optional
            Should be in order from lowest to highest
            comm_qubit_positions: list of indices, optional
            The memory positions allocated to comm-qubits. This enforces
            the topology. It is distinct from comm-qubits free which
            #initialises the comm-qubits free on a node at the point in time
            #the first gate tuple inputted occurs
            ebits_ready : bool, optional
            Initialises whether the node has any comm-qubits entangled with 
            those on another node
    """
    #The core idea of what follows is to add instructions to a QuantumProgram
    #until remote gates occur, at which point the program will be run to that 
    #point, re-initialised and then added to with instructions needed for the
    #part of the remote gate done on this node. The classical port names have
    #been chosen so that the sending and receiving port have the same f-string
    #but will have different names when this protocol is acted on the 
    #appropriate nodes

    def __init__(self, gate_tuples, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gate_tuples = gate_tuples

    def _flexi_program_apply(self, qprogram, gate_instr, qubit_indices, 
                             gate_op):
        """
        A subroutine to handle the possibility that the gate_op is not defined
        in the gate instruction. Such a scenario can be useful because it 
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
        """
        if gate_op is None:
            qprogram.apply(gate_instr, qubit_indices)
        else:
            qprogram.apply(gate_instr, qubit_indices, operator=gate_op)

    def run(self):
        program=QuantumProgram()
        while True:
         #TO DO: could potentially put another for loop here which cycles over
         #each row of gate_tuples outputted for this node by the scheduler
         #with some yield statement after each row of gate_tuples have been
         #evaluated to make it wait for next time slice. This would save
         #having to make many protocols
         
            for gate_tuple in self.gate_tuples:
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
                            other_node_name = gate_tuple[0]
                            scheme = gate_tuple[1]
                            role = gate_tuple[2]
                        node_names = [self.node.name, other_node_name]
                        node_names.sort()
                        classical_comm_port = self.node.ports[
                            f"classical_connection_{self.node.name}->"
                            f"{other_node_name}"]
                        ent_request_port = self.node.ports[
                            f"request_entanglement_{node_names[0]}<->"
                            f"{node_names[1]}"]
                        if scheme == "cat":
                            if role == "entangle":
                                yield self.node.qmemory.execute_program(
                                    program)
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
                                    cat_ent_comm_qubit_index = (
                                        self.node.comm_qubits_free[0]) 
                                    #removing comm qubit being used from list
                                    #of available comm-qubits:
                                    if not self.node.ebit_ready:
                                        #if there is no ebit ready:
                                        node_names = [self.node.name,
                                                      other_node_name]
                                        node_names.sort()
                                        ent_recv_port = self.node.ports[
                                            f"quantum_input_from_charlie"
                                            f"{cat_ent_comm_qubit_index}_"
                                            f"{node_names[0]}<->{node_names[1]}"]
                                        #send entanglement request specifying
                                        #the comm-qubit to be used:
                                        ent_request_port.tx_output(
                                            cat_ent_comm_qubit_index)
                                        #wait for entangled qubit to arrive in
                                        #requested comm-qubit slot:
                                        yield self.await_port_input(
                                            ent_recv_port)
                                    program.apply(instr.INSTR_CNOT,
                                                  [data_or_tele_qubit_index,
                                                  cat_ent_comm_qubit_index])
                                    program.apply(instr.INSTR_MEASURE, 
                                                  [cat_ent_comm_qubit_index],
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
                                    
                            elif role == "correct":
                                yield self.node.qmemory.execute_program(
                                    program)
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
                                    cat_corr_comm_qubit_index = (
                                        self.node.comm_qubits_free[0])
                                    #removing comm qubit being used from list
                                    #of available comm-qubits:
                                    if not self.node.ebit_ready:
                                        #if there is no ebit ready
                                        ent_recv_port = self.node.ports[
                                            f"quantum_input_from_charlie"
                                            f"{cat_corr_comm_qubit_index}_"
                                            f"{node_names[0]}<->{node_names[1]}"]
                                        #send entanglement request specifying 
                                        #the comm-qubit to be used:
                                        ent_request_port.tx_output(
                                            cat_corr_comm_qubit_index)
                                        #wait for entangled qubit to arrive in
                                        #requested comm-qubit slot:
                                        yield self.await_port_input(
                                            ent_recv_port)
                                    del self.node.comm_qubits_free[0]
                                    #wait for measurement result
                                    yield self.await_port_input(
                                        classical_comm_port)
                                    meas_result, = (
                                        classical_comm_port.rx_input().items)
                                    if meas_result == 1:
                                        program.apply(instr.INSTR_X,
                                                      cat_corr_comm_qubit_index)
                                    #renaming cat-comm index so that it is 
                                    #accessible from either tp or cat-comm
                                    #for the local two-qubit gates
                                    comm_qubit_index = cat_corr_comm_qubit_index
    
                            elif role == "disentangle_start":
                                #don't need comm-qubit free to do this. It
                                #will use the comm-qubit index defined in the 
                                #last operation (ie,
                                #correct)
                                program.apply(instr.INSTR_H,
                                              cat_corr_comm_qubit_index)
                                program.apply(instr.INSTR_MEASURE,
                                              cat_corr_comm_qubit_index,
                                              output_key="mb")
                                yield self.node.qmemory.execute_program(program)
                                meas_result, = program.output["mb"]  
                                program = QuantumProgram() #re-initialising
                                classical_comm_port.tx_output(meas_result)
                                #freeing comm-qubit now that it is not needed
                                self.node.comm_qubits_free = (
                                    self.node.comm_qubits_free +
                                    [cat_corr_comm_qubit_index])
                                #re-odering form smallest number to largest
                                self.node.comm_qubits_free.sort()
            
                            elif role == "disentangle_end":
                                yield self.await_port_input(
                                    classical_comm_port)
                                meas_result, = (
                                    classical_comm_port.rx_input().items)
                                if meas_result == 1:
                                    #correcting some qubit entangled in the
                                    #cat-entanglement step
                                    program.apply(instr.INSTR_Z,
                                                  [data_or_tele_qubit_index])
                                    yield self.node.qmemory.execute_program(
                                        program)
                                    program = QuantumProgram()
                            else:
                                raise ValueError(
                                    "final element of gate_tuple is not valid"
                                    " role")
                            
                        elif scheme == "tp":
                            if role == "bsm":
                                yield self.node.qmemory.execute_program(
                                    program)
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
                                    comm_qubit_index = (
                                        self.node.comm_qubits_free[0])
                                    #there is no need to delete a comm-qubit 
                                    #it will be restored at the end of this 
                                    #block
                                    if (data_or_tele_qubit_index == -1 and
                                        len(self.node.comm_qubits_free) <
                                        len(self.node.comm_qubit_positions)):
                                        #letting qubit to be teleported be the 
                                        #last used communication qubit from the 
                                        #prev time-slice
                                        data_or_tele_qubit_index = (
                                            comm_qubit_index - 1)
                                    if not self.node.ebit_ready: 
                                        #if there is no ebit ready:
                                        ent_recv_port = self.node.ports[
                                            f"quantum_input_from_charlie"
                                            f"{comm_qubit_index}_"
                                            f"{node_names[0]}<->{node_names[1]}"]
                                        #send entanglement request specifying
                                        #the comm-qubit to be used:
                                        ent_request_port.tx_output(
                                            comm_qubit_index)
                                        #wait for entangled qubit to arrive in
                                        #requested comm-qubit slot:
                                        yield self.await_port_input(
                                            ent_recv_port)
                                    program.apply(instr.INSTR_CNOT, 
                                                  [data_or_tele_qubit_index, 
                                                   comm_qubit_index])
                                    program.apply(instr.INSTR_H,
                                                  [data_or_tele_qubit_index])
                                    program.apply(instr.INSTR_MEASURE,
                                                  [comm_qubit_index],
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
                                    program.apply(instr.INSTR_MEASURE, 
                                                  [data_or_tele_qubit_index],
                                                  output_key = "m2")
                                    yield self.node.qmemory.execute_program(
                                        program)
                                    m1, = program.output["m1"]
                                    m2, = program.output["m2"]
                                    program = QuantumProgram()
                                    #re-setting data-qubit to zero after
                                    #measurement (comm-qubit already reset
                                    #when entanglement re-distributed)
                                    #TO DO: GET THIS TO TAKE SAME TIME AS 
                                    #APPLYING AN X-GATE controlled by the 
                                    #measurement result.
                                    program.apply(instr.INSTR_INIT,
                                                  data_or_tele_qubit_index)
                                    yield self.node.qmemory.execute_program(
                                        program)
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
                                    program = QuantumProgram() #re-initialising
                                    if (data_or_tele_qubit_index in 
                                        self.node.comm_qubit_positions):
                                        #freeing comm_qubit now that it has been
                                        #measured
                                        self.node.comm_qubits_free = (
                                            self.node.comm_qubits_free + 
                                            [data_or_tele_qubit_index])
                                        #re-ordering from smallest number to
                                        #largest
                                        self.node.comm_qubits_free.sort()

                            elif role == "correct":
                                yield self.node.qmemory.execute_program(
                                    program)
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
                                    comm_qubit_index = (
                                        self.node.comm_qubits_free[0]) 
                                    del self.node.comm_qubits_free[0]
                                    #removing comm qubit being used from list of 
                                    #available comm-qubits:
                                    if not self.node.ebit_ready:
                                        #if there is no ebit ready:
                                        ent_recv_port = self.node.ports[
                                            f"quantum_input_from_charlie"
                                            f"{comm_qubit_index}_"
                                            f"{node_names[0]}<->{node_names[1]}"]
                                        #send entanglement request specifying
                                        #the comm-qubit to be used:
                                        ent_request_port.tx_output(
                                            comm_qubit_index)
                                        #wait for entangled qubit to arrive in
                                        #requested comm-qubit slot:
                                        yield self.await_port_input(
                                            ent_recv_port)
                                    yield self.await_port_input(
                                        classical_comm_port)
                                    meas_results, = (
                                        classical_comm_port.rx_input().items)
                                    if meas_results[0] == 1:
                                        program.apply(instr.INSTR_X, 
                                                      comm_qubit_index)
                                    if meas_results[1] == 1:
                                        program.apply(instr.INSTR_Z, 
                                                      comm_qubit_index)
                                    yield self.node.qmemory.execute_program(
                                        program)
                                    program = QuantumProgram()
                                    
                            elif role == "correct4tele_only":
                                #TO DO: implement more effiently. Currently,
                                #this is just a copy and past of the above role
                                #with one line (deleting the comm-qubit free)
                                #removed
                                yield self.node.qmemory.execute_program(
                                    program)
                                program=QuantumProgram()
                                if len(self.node.comm_qubits_free) == 0 : 
                                    #if there are no comm-qubits free:
                                    raise Exception(f"Scheduling error: No"
                                                    f" comm-qubits free. "
                                                    f"There are too many"
                                                    f" remote gates on "
                                                    f" {self.node.name} in"
                                                    f" this time slice")
                                else: #if there are comm-qubits free
                                    #establishing new comm-qubit for the
                                    #current teleportation
                                    comm_qubit_index = (
                                        self.node.comm_qubits_free[0]) 
                                    #removing comm qubit being used from list 
                                    #of available comm-qubits:
                                    if not self.node.ebit_ready: 
                                        #if there is no ebit ready:
                                        ent_recv_port = self.node.ports[
                                            f"quantum_input_from_charlie"
                                            f"{comm_qubit_index}_"
                                            f"{node_names[0]}<->{node_names[1]}"]
                                        #send entanglement request specifying 
                                        #the comm-qubit to be used:
                                        ent_request_port.tx_output(
                                            comm_qubit_index)
                                        #wait for entangled qubit to arrive in
                                        #requested comm-qubit slot:
                                        yield self.await_port_input(
                                            ent_recv_port)
                                    yield self.await_port_input(
                                        classical_comm_port)
                                    meas_results, = (
                                        classical_comm_port.rx_input().items)
                                    if meas_results[0] == 1:
                                        program.apply(instr.INSTR_X, 
                                                      comm_qubit_index)
                                    if meas_results[1] == 1:
                                        program.apply(instr.INSTR_Z, 
                                                      comm_qubit_index)
                                    yield self.node.qmemory.execute_program(
                                        program)
                                    program = QuantumProgram()
                                    
                            else:
                                raise ValueError(
                                    "final element of gate_tuple is not valid"
                                    " role")
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

class dqcMasterProtocol(Protocol):
    """ Protocol which executes a distributed quantum circuit 
    INPUT: 
        gate_tuples:  list of tuples.
            The gates implemented in the entire circuit. The tuples should be
            of the form:
            1) single-qubit gate: (gate_instr, qubit, node_name)
            2) two-qubit gate: (list of instructions or gate_instruction if
                                local,qubit0, node0_name, qubit1, node1_name,
                                scheme) 
                                #can later extend this to multi-qubit gates
                                #keeping scheme as last element
                                list of instructions: list
                                    list of same form as gate_tuples
                                    containing the local gates to be conducted
                                    as part of the remote gate. Ie, for
                                    remote-cnot this would contain the cnot 
                                    (but not the gates used for bsm or
                                     correction).
                                    Note if this is given as empty list and 
                                    scheme = "tp" then it will just do a
                                    teleportation
        compiler_func: function, optional
            The compiler function to be used to split gate_tuples into
            protocols by node and time-slice
    """
    def __init__(self, gate_tuples, network, *args, 
                 compiler_func=sort_greedily_by_node_and_time, **kwargs):
        super().__init__(*args, **kwargs)
        self.gate_tuples = gate_tuples
        self.network = network
        self.compiler_func = compiler_func
        #TO DO: initialise values that used to be initialised in 
        #HandleCommBlockForOneNodeProtocol as attributes for node (MAYBE DO IN
        #NETWORK CREATION FUNCTION INSTEAD)
        
    def run(self):
        node_op_dict = self.compiler_func(self.gate_tuples)
        node_dict = {}
        for node_key in node_op_dict:
            node_dict[node_key] = self.network.get_node(node_key)
        for node_name in dict(self.network.nodes):
            if node_name.startswith("Charlie"):
                charlie = self.network.get_node(node_name)
                entangling_protocol = EntangleLinkedNodesProtocol(
                    node=charlie, name=f"{node_name}_protocol")
                entangling_protocol.start()
        #initialising dummy event expression 
        dummy_entity = pydynaa.Entity()
        evtype_dummy = pydynaa.EventType("dummy_event", "dummy event")
        evexpr_dummy = pydynaa.EventExpression(
            source=dummy_entity, event_type=evtype_dummy)
        expr = evexpr_dummy
        dummy_entity._schedule_now(evtype_dummy)
        
        #finding max length of dictionary entry
        longest_list_in_node_op_dict = max(node_op_dict.values(), key=len)
        max_num_time_slices = len(longest_list_in_node_op_dict)
        while True:
            for time_slice in range(max_num_time_slices):
                for node_key in node_op_dict:
                    #if node does anything on this time slice
                    if time_slice < len(node_op_dict[node_key]): 
                        #strictly less than because python indexes from 0
                        gate_tuples4node_and_time = (
                            node_op_dict[node_key][time_slice])
                        protocol4node_and_time = (
                            HandleCommBlockForOneNodeProtocol(
                                gate_tuples4node_and_time,
                                node=node_dict[node_key]))
                        expr = expr & self.await_signal(
                            protocol4node_and_time, Signals.SUCCESS)
                        protocol4node_and_time.start()
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