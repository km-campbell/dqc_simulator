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

"""
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
    """
    def __init__(self, node=None, name=None, role=None, other_node_name=None,
                 comm_qubit_indices=None, ready4ent=True):
        super().__init__(node, name)
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
        self.add_signal(self.ent_ready_label)
        self.add_signal(self.ent_failed_label)
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
        
        
    #TO DO:
    #1) Add transduction methods where appropriate. Emission can be done
    #with the emit instruction. 

        


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
    ready4ent = bool, optional
        Whether the QPU is ready or not for entanglement.

    Attributes
    ----------
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
    
    .. todo::
        
        Think about whether to change comm_qubit_indices for comm_qubit_indices.
        (This should match what is sent by HandleCommBlockForOneNodeProtocol)
    """
    
    def __init__(self, node=None, name=None, role=None, other_node_name=None,
                 comm_qubit_indices=None, ready4ent=True):
        super().__init__(node, name, role, other_node_name, comm_qubit_indices,
                         ready4ent)
        self.entanglement_type2generate = 'bell_pair'
        self.ent_request_msg = "ENT_REQUEST"
        self.entangling_connection_port_name = self.node.connection_port_name(
                                                        self.other_node_name,
                                                        label="entangling")
        self.ent_conn_port = self.node.ports[
                                self.entangling_connection_port_name]
        #setting handler function to be called when input message is 
        #received by the relevant port - essentially configuring the simulated
        #hardware
        self.ent_conn_port.bind_input_handler(self.handle_quantum_input)
        
    def handle_quantum_input(self, msg):
        """
        Routes qubits on a QPU node to the correct memory position.
        
        Modifies a quantum message inputted to a port, with metadata that puts 
        qubits in the correct memory positions and forwards the altered message
        to the qin port of a 
        :class: `~netsquid.components.qmemory.QuantumMemory` or 
        :class: `~netsquid.components.qprocessor.QuantumProcessor`

        Parameters
        ----------
        msg : :class: `~netsquid.components.component.Message`
            A message whose items should be qubits.
        """
        #TO THINK about whether to move this to an abstract base class
        #for protocols expecting a quantum input or the more general 
        #physical layer base class (probably the former)
        msg.meta['qm_positions'] = self.comm_qubit_indices
        self.ent_conn_port.forward_input(self.node.qmemory.ports['qin'])
        self.ent_conn_port.tx_input(msg)
        
    def run(self):
        while True:
            yield from self.handshake()
            if self.role == 'server' and self.ready4ent:
                #sending entanglement request to quantum source
                self.ent_conn_port.tx_output(self.ent_request_msg)
                #TO DO: think about whether to signal that entanglement is 
                #ready. HandleCommBlockForOneNodeProtocol already waits 
                #for the entanglement to arrive. Maybe only need to signal 
                #failure.
            #note that waiting on an input, etc is implicitly handled by 
            #the binding of the input handler in the __init__ method. 
            break
        
        
        #TO DO: wait for entanglement to be distributed and then signal 
        #HandleCommBlockForOneNodeProtocol or change the QPUs ebit_ready 
        #attribute
        
        
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
        
        
        
        
