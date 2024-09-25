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

# =============================================================================
# class SignalOutcome2Qpu(NodeProtocol):
#     """
#     Signals entanglement generation outcome to 
#     QpuManagementProtocol/HandleCommBlockForOneNodeProtocol.
#     
#     Intended to be used as a subprotocol for other physical layer protocols.
#     
#     Parameters
#     ----------
#     ent_successful : bool or None
#         True if entanglement was successfully generated, False otherwise. If 
#         None, this must be initialised at a later time. For instance, it
#         could be passed to this protocol by the parent protocol
#     node : :class: `~netsquid.nodes.node.Node` or None, optional
#         Node this protocol runs on. If None, a node should be set later before 
#         starting this protocol.
#     name : str or None, optional
#         Name of protocol. If None, the name of the class is used.
#     
#     .. todo::
#         
#         Choose between which of QpuManagementProtocol and 
#         HandleCommBlockForOneNodeProtocol to use and update the first line of 
#         this docstring and all relevant calls to the protocol in this function.
#         When you have made this choice format the name 
#         correctly with backticks and the full import name, etc.
#     """
#     def __init__(self, ent_successful, node=None, name=None):
#         super().__init__(node, name)
#         self.ent_successful = ent_successful
#         self.ent_ready_label = "ENT_READY"
#         self.ent_failed_label = "ENT_FAILED"
#         self.add_signal(self.ent_ready_label)
#         self.add_signal(self.ent_failed_label)
#         
#     def run(self):
#         if self.ent_successful:
#             self.send_signal(self.ent_ready_label)
#         elif not self.ent_successful:
#             self.send_signal(self.ent_failed_label)
# =============================================================================

# =============================================================================
# class HandshakeProtocol(NodeProtocol):
#     """
#     Handshake protocol between QPUs, letting both QPUs know that the other
#     is ready to start entanglement distribution.
#     
#     Intended to be used as a subprotocol of other physical layer protocols 
#     that require synchronisation of different nodes.
#     
#     
#     """
#     def run(self):
# =============================================================================
        
class Base4PhysicalLayerProtocol(NodeProtocol):
    """
    An abstract base class for physical layer protocols.
    
    Parameters
    ----------
    node : :class: `~netsquid.nodes.node.Node` or None, optional
        Node this protocol runs on. If None, a node should be set later before 
        starting this protocol.
    name : str or None, optional
        Name of protocol. If None, the name of the class is used.
    other_node_name : str or None, optional
        The name of the other QPU node involved in the entangled link. If 
        None, must be specified prior to the start of the protocol, eg in the 
        link_layer_protocol.
    comm_qubit_index = int or None, optional
        The index of the memory position in which the comm-qubit that should 
        host the entanglement is being held.

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
        
    .. todo::
        
        Decide if num_entanglements2generate and entanglement_type2generate 
        should be attributes because it is not clear if they will be relevant
        to all of the possible subclasses. However, perhaps setting them as 
        None or a string saying 'N/A' may be appropriate. Also need to think 
        about whether comm_qubit_index should be swapped for comm_qubit_indices
        but need to be careful with this as many of the 
        HandleCommBlockForOneNodeProtocol subgenerators make and use just one
        index. However, this could perhaps be put into a list at some point.
    """
    def __init__(self, node=None, name=None, other_node_name=None,
                 comm_qubit_index=None):
        super().__init__(node, name)
        self.other_node_name = other_node_name
        self.comm_qubit_index = comm_qubit_index
        #The following attributes will need to be overwritten in some
        #subclasses
        self.num_entanglements2generate = 1
        self.entanglement_type2generate = None
        self.ent_ready_label = "ENT_READY"
        self.ent_failed_label = "ENT_FAILED"
        self.add_signal(self.ent_ready_label)
        self.add_signal(self.ent_failed_label)
        
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
        
    #TO DO: add transduction methods where appropriate. Emission can be done
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
        starting this protocol.
    name : str or None, optional
        Name of protocol. If None, the name of the class is used.
    other_node_name : str or None, optional
        The name of the other QPU node involved in the entangled link. If 
        None, must be specified prior to the start of the protocol, eg in the 
        link_layer_protocol.
    comm_qubit_index = int or None, optional
        The index of the memory position in which the comm-qubit that should 
        host the entanglement is being held.

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
    
    .. todo::
        
        Think about whether to change comm_qubit_index for comm_qubit_indices.
        (This should match what is sent by HandleCommBlockForOneNodeProtocol)
    """
    
    def __init__(self, node=None, name=None, other_node_name=None,
                 comm_qubit_index=None):
        super().__init__(node, name, other_node_name, comm_qubit_index)
        self.entanglement_type2generate = 'bell_pair'
        self.ent_request_msg = "ENT_REQUEST"
        self.entangling_connection_port_name = self.node.connection_port_name(
                                                        self.other_node_name,
                                                        label="entangling")
        self.ent_conn_port = self.node.ports[
                                self.entangling_connection_port_name]
        #setting handler function to be called when input message is 
        #received by the relevant port
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
        msg.meta['qm_positions'] = [self.comm_qubit_index]
        self.ent_conn_port.forward_input(self.node.qmemory.ports['qin'])
        self.ent_conn_port.tx_input(msg)
        #TO DO: add forwarding input here instead of when setting up connection 
        #in create_black_box_central_source_entangling_link (will need to update
        #tests of link_2_qpus)
        
    def run(self):
        
        #TO DO: add some sort of handshake here to ensure that only one of the 
        #nodes sends a request to avoid duplication of effort.
            
        #sending entanglement request
        self.ent_conn_port.tx_output(self.ent_request_msg)
        #note that waiting on an input, etc is implicitly handled by 
        #the binding of the input handler earlier. 
            
        
        
        #TO DO: wait for entanglement to be distributed and then signal 
        #HandleCommBlockForOneNodeProtocol using 
        #SignalOutcome2Qpu
        
        
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
#             f"{comm_qubit_index}_"
#             f"{node_names[0]}<->{node_names[1]}"]
#         #send entanglement request specifying
#         #the comm-qubit to be used:
#         ent_request_port.tx_output(comm_qubit_index)
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
        
        
        
        
