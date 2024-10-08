# -*- coding: utf-8 -*-
# =============================================================================
# 
# Created on Fri Sep 13 09:29:30 2024
# 
# @author: kenny
# =============================================================================
"""
Protocols for the physical layer similar to that defined in the Wehner network 
stack.

Notes
-----
The original [1]_ and revised [2]_ papers on the Wehner network stack give 
further details.

References
----------
.. [1] A. Dahlberg, et al., A link layer protocol for quantum networks, in: 
       Proceedings of the ACM Special Interest Group on Data Communication,
       ACM (2019)

.. [2] M. Pompili, et al., Experimental demonstration of entanglement delivery 
       using a quantum network stack, npj Quantum Information, 8 (2022)
       
       
.. todo::
    
    Decide if this module should be called link_and_physical_layer to 
    reflect the fact that the functionality of the physical layer is 
    encapsulated in a method of the base class for the physical layer. Also, 
    need to condiser using ABC things because you want to make sure that 
    subclasses have certain behaviour.

"""
#TO DO: think about if this module should be called link_and_physical_layer to 
#reflect the fact that the functionality of the physical layer is encapsulated
#in the base class for the physical layer.

from netsquid.protocols import NodeProtocol





class Base4PhysicalLayerProtocol(NodeProtocol):
    """
    An abstract base class for physical layer protocols.
    
    Parameters
    ----------
    node : :class: `~netsquid.nodes.node.Node` or None, optional
        Node this protocol runs on. If None, a node should be set later before 
        starting this protocol. [1]_
    name : str or None, optional
        Name of protocol. If None, the name of the class is used.
    role : str or None, optional
        Whether the QPU is a 'client' (initiating the handshake) or a 
        'server' (responding to the handshake). If None, must be overwritten
        prior to the start of the protocol, eg in the link layer protocol.
    other_node_name : str or None, optional. [1]_
        The name of the other QPU node involved in the entangled link. If 
        None, must be overwritten prior to the start of the protocol, eg in the 
        link_layer_protocol.
    comm_qubit_indices = list of int or None, optional
        The index of the memory position in which the comm-qubit that should 
        host the entanglement is being held.
    ready4ent = bool, optional
        Whether the QPU is ready or not for entanglement

    Attributes
    ----------
    superprotocol : :class: `netsquid.protocols.nodeprotocols.NodeProtocol`
        The superprotocol for this protocol. This protocol will be 
        executed as a subprotocol of the superprotocol. The value of this 
        attribute should be overwritten by the superprotocol.
    num_entanglements2generate : int 
        The number of instances of the requested entanglement to be specified.
        For many subclasses this will be fixed but in others it will be 
        variable and will be overwritten by the link layer.
    entanglement_type2generate : str
        The type of entanglement to be used. For many subclasses this will be
        fixed but in others it will be variable and will be overwritten by the 
        link layer.
    ent_ready_label : str
        The label to use to signal the successful distribution of 
        entanglement.
    ent_failed_label : str
        The label to use to signal that entanglement distribution has
        failed
        
    Notes
    -----
    Although num_entanglements2generate and entanglement_type2generate to 
    generate will not be used in many subclasses of this protocol, they are 
    useful for the user to be able to find.
        
    References
    ----------
    The parameters in which Ref. [1]_ was cited were inherited from 
    :class: `~netsquid.protocols.nodeprotocols.NodeProtocol` and the description
    used for those parameters was taken from the NetSquid documentation [1]_
    
    .. [1] https://netsquid.org/
    
    .. todo::
        
        Think about whether to set role, other_node_name, comm_qubit_indices,
        and read4ent as attributes or properties only, not parameters, as they 
        should be set by protocols at higher layers. The advantage of this is
        to avoid confusion when a user sets values for these parameters
        and they are then overwritten. However, the parameter formulation does
        make instantiating the physical layer within higher layers easier.
    """
    def __init__(self, node=None, name=None, role=None,
                 other_node_name=None, comm_qubit_indices=None,
                 ready4ent=True):
        super().__init__(node=node, name=name)
        self.superprotocol = None #should be overwritten by higher-layer
                                  #protocols
        self.other_node_name = other_node_name
        self.comm_qubit_indices = comm_qubit_indices
        self.ready4ent = ready4ent
        #The following attributes will need to be overwritten in some
        #subclasses
        self.num_entanglements2generate = 1
        self.entanglement_type2generate = None
        #the following two handshake labels are not strictly necessary because
        #any input message to the port would do the same thing. However, they 
        #make what is going on clearer and facilitate debugging.
        self.handshake_ready_label = "READY4ENT"
        self.handshake_not_ready_label = "NOT_READY4ENT"
        self.ent_ready_label = "ENT_READY"
        self.ent_failed_label = "ENT_FAILED"
        self.ent_request_label = "ENT_REQUEST"
        self.add_signal(self.ent_ready_label)
        self.add_signal(self.ent_failed_label)
        self.add_signal(self.ent_request_label)
        #The value of the next two attributes will be overwritten in the 
        #run method, which is the first point at which the node attribute must
        #have a value other than None
        self.classical_connection_port_name = None
        self.classical_conn_port = None
        #TO DO: think about if you should declare these in QpuOSProtocol, which
        #you will need to do anyway, and then send them here with the other 
        #attributes
        
    def handle_ent_request(self):
        """
        Handles entanglement requests from higher-level protocols.
        
        This is a subgenerator, allowing the run method to call it and wait on
        :class: `~pydynaa.core.EventExpression`s that this subgenerator waits 
        on. It waits on a signal from higher-level protocols and changes this 
        protocol's instance attributes to reflect information in that signal.
        
        Yields
        ------
        :class: `~pydynaa.core.EventExpression`
            Sends :class: `~pydynaa.core.EventExpression`s to the run method, 
            causing it to wait on signals.
        """
        print("entered physical layer base protocol's handle_ent_request method"
              f" on {self.node.name}")
        yield self.await_signal(self.superprotocol, 
                                signal_label=self.ent_request_label)
        #the following could be replaced with any desired specs (including 
        #a tuple of them). TO DO: think about whether you want to have more
        #specs (eg, entanglement fidelity like in Wehner stack papers).
        #For now, I'll keep it simple
        print("passed await_signal method within handle_ent_request on "
              f"{self.node.name}")
        signal_results = self.superprotocol.get_signal_result(
                                                self.ent_request_label)
        #updating relevant attributes
        self.role = signal_results[0]
        self.other_node_name = signal_results[1] 
        self.comm_qubit_indices = signal_results[2]
        self.num_entanglements2generate = signal_results[3]
        self.entanglement_type2generate = signal_results[4]
        self.classical_connection_port_name = self.node.connection_port_name(
                                                        self.other_node_name,
                                                        label="classical")
        self.classical_conn_port = self.node.ports[
                                       self.classical_connection_port_name]
    
    def signal_outcome(self, ent_successful):
        """
        Signals entanglement generation outcome to 
        QpuManagementProtocol/HandleCommBlockForOneNodeProtocol.

        Parameters
        ----------
        ent_successful : bool
            True if entanglement has been successfully distributed.
            False otherwise.
            
        .. todo::
            
            Choose between which of QpuManagementProtocol and 
            HandleCommBlockForOneNodeProtocol to use and update the first line of 
            this docstring and all relevant calls to the protocol in this function.
            When you have made this choice format the name 
            correctly with backticks and the full import name, etc.
        """
        if self.ent_successful:
            self.send_signal(self.ent_ready_label)
        elif not self.ent_successful:
            self.send_signal(self.ent_failed_label)
            
    def handshake(self):
        """
        Implements a handshake protocol to facilitate synchronisation between
        QPUs prior to generating entanglement

        Returns
        -------
        None.

        """
        if self.role == 'client':
            self.classical_conn_port.tx_output(self.handshake_ready_label)
# =============================================================================
#             #await response from server
#             yield self.await_port_input(self.classical_conn_port)
# =============================================================================
        elif self.role == 'server':
            yield self.await_port_input(self.classical_conn_port)
            #TO DO: get signal results here to bring in time?
            if self.ready4ent:
                self.classical_conn_port.tx_output(self.handshake_ready_label)
            elif not self.ready4ent:
                self.classical_con_port.tx_output(self.handshake_not_ready_label)
        #TO DO: add timed release functionality for synchronisation (which
        #is to be used if timed_release parameter is set to True). The time
        #should relate to the expected latency of the classical message. This 
        #could be achieved by having the client node include the time it sends
        #the meeting and have the server infer the 
        #channel latency from the time the message
        #is received.
        #TO DO: facilitate having multiple entanglements on the same time slice,
        #which may require having some sort of job ID.
        
    def run(self):
        print(f'entered base physical layer run method for {self.node.name}')
        yield from self.handle_ent_request()
        
        
    #TO DO:
    #1) Add transduction methods where appropriate. Emission can be done
    #with the emit instruction. 

        

#Following decorator explicitly labels the next class as a subprotocol of 
#Base4PhysicalLayerProtocol
@Base4PhysicalLayerProtocol.register
class AbstractCentralSourceEntangleProtocol(Base4PhysicalLayerProtocol):
    """ Abstract protocol for generating entanglement.
    
    An abstract way of generating ebits designed to act on QPUs connected by
    a :class: `~dqc_simulator.hardware.connections.BlackBoxEntanglingQsourceConnection`.
    Details of the ebit generation are ignored, with the state specified 
    analytically. The state definition can be used to specify the
    noise on the entangled photons if desired. In this way, the need for 
    multiple simulation runs (which would be required by a probabilistic noise
    model) is circumvented.
    
    Parameters
    ----------
    node : :class: `~netsquid.nodes.node.Node` or None, optional
        Node this protocol runs on. If None, a node should be set later before 
        starting this protocol. [1]_
    name : str or None, optional
        Name of protocol. If None, the name of the class is used. [1]_
    role : str
        Whether the QPU is a 'client' (initiating the handshake) or a 
        'server' (responding to the handshake.)
        The name of the other QPU node involved in the entangled link. If 
        None, must be overwritten prior to the start of the protocol, eg in the 
        link layer_protocol.
    other_node_name : str or None, optional
        The name of the other QPU node involved in the entanglment distribution.
        If None, must be overwritten prior to the the start of the protocol,
        eg in the link layer protocol
    comm_qubit_indices = list of int or None, optional
        The index of the memory position in which the comm-qubit that should 
        host the entanglement is being held.
    ready4ent = bool por None , optional
        Whether the QPU is ready or not for entanglement. If None, must be 
        overwritten prior to the the start of the protocol, eg in the 
        link layer protocol.

    Attributes
    ----------
    superprotocol : :class: `netsquid.protocols.nodeprotocols.NodeProtocol`
        The superprotocol for this protocol. This protocol will be 
        executed as a subprotocol of the superprotocol. The value of this 
        attribute should be overwritten by the superprotocol.
    num_entanglements2generate : int 
        The number of instances of the requested entanglement to be specified.
    entanglement_type2generate : str
        The type of entanglement to be used.
    ent_ready_label : str
        The label to use to signal the successful distribution of 
        entanglement.
    ent_failed_label : str
        The label to use to signal that entanglement distribution has
        failed
    
    Notes
    -----
    This abstracts from the details of photon generation by treating flying
    and communication qubits as the same thing. Restraints on the number of 
    communication qubits can be enforced at the QPU nodes but entangled 
    communication qubits are generated at a central quantum source and sent
    to the QPUs. In this way, we can model error and loss but needn't simulate
    the details of entanglement between static communication qubits and photons.
    
    References
    ----------
    The parameters in which Ref. [1]_ was cited were inherited from 
    :class: `~netsquid.protocols.nodeprotocols.NodeProtocol` and the description
    used for those parameters was taken from the NetSquid documentation [1]_
    
    .. [1] https://netsquid.org/
    """
    
    def __init__(self, node=None, name=None, role=None,
                 other_node_name=None, comm_qubit_indices=None, 
                 ready4ent=True):
        super().__init__(node=node, name=name, role=role, 
                         other_node_name=other_node_name,
                         comm_qubit_indices=comm_qubit_indices,
                         ready4ent=ready4ent)
        self.entanglement_type2generate = 'bell_pair'
        self.ent_request_msg = "ENT_REQUEST"
        #The next two instance attributes will be overwritten in the run 
        #method because this is the first time that self.node must have a value
        #other than None and it is convenient to use self.node to instantiate
        #the next two attributes.
        self.entangling_connection_port_name = None
        self.ent_conn_port = None
        
    def one_way_handshake(self):
        """
        Implements a one-way version of the handshake protocol.
        
        This subgenerator assumes that entanglement is possible and time 
        synchronisation is not necessary, which is useful for the 
        detereministic entanglement distribution scheme here.
        """
        if self.role == 'client':
            self.classical_conn_port.tx_output(self.handshake_ready_label)
# =============================================================================
#             #await response from server
#             yield self.await_port_input(self.classical_conn_port)
# =============================================================================
        elif self.role == 'server':
            yield self.await_port_input(self.classical_conn_port)

    def handle_quantum_input(self):
        """
        Routes qubits on a QPU node to the correct memory position upon 
        receiving input to the port this method is bound to.
        
        Modifies a quantum message inputted to a port, with metadata that puts 
        qubits in the correct memory positions and forwards the altered message
        to the qin port of a 
        :class: `~netsquid.components.qmemory.QuantumMemory` or 
        :class: `~netsquid.components.qprocessor.QuantumProcessor`
        """
        #TO THINK about whether to move this to an abstract base class
        #for protocols expecting a quantum input or the more general 
        #physical layer base class (probably the former)
        yield self.await_port_input(self.ent_conn_port)
        print(f"qubits have arrived at {self.ent_conn_port}")
        msg = self.ent_conn_port.rx_input() #Message containing qubits
        #adding information on the quantum memory positions to add qubits to
        print(f'the qubits at {self.ent_conn_port} are {msg}')
        msg.meta['qm_positions'] = self.comm_qubit_indices
        self.ent_conn_port.forward_input(self.node.qmemory.ports['qin'])
        self.ent_conn_port.tx_input(msg)
        #signalling QpuOSProtocol that entanglement is ready.
        self.send_signal(self.ent_ready_label)
        #undoing the forward input setup above so that, the next time
        #entanglement is distributed, the message is again amended with 
        #metadata before forwarding it on
# =============================================================================
#         yield self.await_port_input(self.node.qmemory.ports['qin'])
# =============================================================================
        self.ent_conn_port.forward_input(None)

    def run(self):
        while True:
            #deferring handling of signalling to the base class as this will be
            #identical for all subclasses. This will override the role, 
            #other_node_name, comm_qubit_indices, num_entanglements2generate, 
            #and entanglement_type2generate attributes with useful values (in 
            #place of the default None).
            yield from super().run()
            self.entangling_connection_port_name = self.node.connection_port_name(
                                                            self.other_node_name,
                                                            label="entangling")
            self.ent_conn_port = self.node.ports[
                                    self.entangling_connection_port_name]
            #setting handler function to be called when input message is 
            #received by the relevant port - essentially configuring the simulated
            #hardware
# =============================================================================
#             self.ent_conn_port.bind_input_handler(self.handle_quantum_input)
# =============================================================================
            #Part of the handshake protocol that follows is superfluous for 
            #for this context but may be useful for other entanglement 
            #distribution schemes.
            yield from self.one_way_handshake()
            if self.role == 'server' and self.ready4ent:
                #sending entanglement request to quantum source
                self.ent_conn_port.tx_output(self.ent_request_msg)
            #note that forwarding qubits to the right place and signalling is 
            #handled by the input handler bound to the entangling connection 
            #port in the __init__ method.
            print(f'waiting on qubits on {self.node.name}')
            yield from self.handle_quantum_input()
            print(f'finished waiting on qubits on {self.node.name}')
            
            
        
        #TO DO: wait for entanglement to be distributed and then signal 
        #superprotocol or change the QPU's ebit_ready attribute.
        
        
        #TO DO: ensure both client and server roles are catered for. Above
        #is only for client role. The client and server roles could be
        #different protocols or the role could be an attribute with appropriate
        #handler functions for each role. In this protocol, with the old design
        #the client and server are less distinct and essentially you wait until
        #both parties have sent a request and then proceed. Need to think on
        #whether this is still the approach that you want to take.
# =============================================================================
#         node_names = [self.node.name, other_node_name]
#         node_names.sort()
#         ent_recv_port = self.node.ports[
#             f"quantum_input_from_charlie"
#             f"{comm_qubit_indices}_"
#             f"{node_names[0]}<->{node_names[1]}"]
#         #send entanglement request specifying
#         #the comm-qubit to be used:
#         ent_request_port.tx_output(comm_qubit_indices)
#         #wait for entangled qubit to arrive in
#         #requested comm-qubit slot:
#         yield self.await_port_input(ent_recv_port)
# =============================================================================
# =============================================================================
#         self.send_signal(self.ent_ready_label)
# =============================================================================

# =============================================================================
# class MidpointHeraldingProtocol(Base4PhysicalLayerProtocol):
#     """
#     Physical layer protocol for generating entanglement between QPUs.
#     
#     Intended to be used as a subprotocol of
#     :class: `dqc_simulator.software.link_layer.EntanglementGenerationProtocol`
#     and started in the run method there.
#     
#     Notes 
#     -----
#     Similar idea to the Wehner stack [1]_, [2]_.
#     """
#     def __init__(self):
#         #initiate HandshakeProtocol as subprotocol
#         
#     def run(self):
#         #wait on trigger
#         #start handshake
# =============================================================================
        
        
        
        
