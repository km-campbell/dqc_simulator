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

from netsquid.components import instructions as instr
from netsquid.components import QuantumProgram
from netsquid.protocols import NodeProtocol
# =============================================================================
# from netsquid_trappedions import EmitProg #EmitProg not actually specific 
#                                           #to trapped ions.
# =============================================================================
from netsquid.qubits import ketstates as ks


#TO DO: think about enforcing some expected inheritance behaviour, eg with 
#properties

class Base4PhysicalLayerProtocol(NodeProtocol):
    """
    An abstract base class for physical layer protocols.
    
    This contains everything that all physical layer protocols should use, 
    including the link layer itself, which is implemented as the 
    `run_link_layer` subgenerator method. This method should be called in the 
    run method of all physical layer protocols, typically prior to anything 
    else other than the beginning of the while loop needed for all of the 
    :class: `~pydynaa.core.EventExpression` subgenerators.
    
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
        self._deterministic = None #made into read-only property below
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
        #The value of the next four attributes will be overwritten in the 
        #run method, which is the first point at which the node attribute must
        #have a value other than None
        self.classical_connection_port_name = None
        self.classical_conn_port = None
        self.entangling_connection_port_name = None
        self.ent_conn_port = None
        #TO DO: think about if you should declare these in QpuOSProtocol, which
        #you will need to do anyway, and then send them here with the other 
        #attributes
        
    @property
    def deterministic(self):
        """
        Read-only bool property indicating whether the entanglement is 
        deterministic or not
        
        Must be overwritten when subclassing by setting the value of 
        self._deterministic in the __init__ method
        """
        if self._deterministic is None:
            raise NotImplementedError('Must set value of read-only '
                                      'deterministic property by setting a '
                                      'value for self._deterministic in the'
                                      '__init__ method')
        if not isinstance(self._deterministic, bool):
            raise TypeError('The deterministic property must have type bool. '
                            f'The currently set value ({self._deterministic})'
                            'is not of type bool.')
        return self._deterministic
    
    @deterministic.setter
    def deterministic(self, value):
        raise TypeError('deterministic is a read-only property - its value'
                        'cannot be set by the user')
        
    def run_link_layer(self):
        """
        Handles entanglement requests from higher-level protocols.
        
        This is a subgenerator, allowing the run method to call it and wait on
        :class: `~pydynaa.core.EventExpression`s that this subgenerator waits 
        on. It waits on a signal from higher-level protocols and changes this 
        protocol's instance attributes to reflect information in that signal. 
        It must be prepended by `yield from` when calling.
        
        Yields
        ------
        :class: `~pydynaa.core.EventExpression`
            Sends :class: `~pydynaa.core.EventExpression`s to the run method, 
            causing it to wait on signals.
        """
        yield self.await_signal(self.superprotocol, 
                                signal_label=self.ent_request_label)
        #the following could be replaced with any desired specs (including 
        #a tuple of them). TO DO: think about whether you want to have more
        #specs (eg, entanglement fidelity like in Wehner stack papers).
        #For now, I'll keep it simple
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
        self.entangling_connection_port_name = self.node.connection_port_name(
                                                        self.other_node_name,
                                                        label="entangling")
        self.ent_conn_port = self.node.ports[
                                self.entangling_connection_port_name]
    
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
            wait_time = 100 #ns
            self.classical_conn_port.tx_output(self.handshake_ready_label)
            #await response from server or timeout
            evexpr = yield (self.await_port_input(self.classical_conn_port) | 
                            self.await_timer(wait_time))
            #note: timeout may occur if physical layers signalled at different 
            #times by their QpuOSProtocol
            if evexpr.second_term.value:
            #if timeout occurred:
                #resend handshake message
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
        #defining value of read-only deterministic property (see base class)
        self._deterministic = True 
        
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
        msg = self.ent_conn_port.rx_input() #Message containing qubits
        #adding information on the quantum memory positions to add qubits to
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
            yield from super().run_link_layer()
# =============================================================================
#             yield from self.one_way_handshake()
# =============================================================================
            yield from self.handshake()
            if self.role == 'client' and self.ready4ent:
                #sending entanglement request to quantum source
                self.ent_conn_port.tx_output(self.ent_request_msg)
                #the sending of the request must be done by the client because
                #the client receiving a message back from the server is the 
                #last part of the handshake
            yield from self.handle_quantum_input()
            


class ProbabilisticEntanglingProtocol(Base4PhysicalLayerProtocol):
    """
    An abstract base class for probabilistic physical layer protocols.
    
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
    max_num_ent_attempts = bool or none, optional
        The number of entanglement attempts to make before giving up and 
        handing back control to higher layers.

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
                 ready4ent=True, max_num_ent_attempts=None):
        super().__init__(node=node, name=name, role=role, 
                         other_node_name=other_node_name,
                         comm_qubit_indices=comm_qubit_indices,
                         ready4ent=ready4ent)
        #defining value of read-only deterministic property (see base class)
        self._deterministic = False 
        self.max_num_ent_attempts = max_num_ent_attempts


class MidpointHeraldingProtocol(ProbabilisticEntanglingProtocol):
    """
    Physical layer protocol for generating entanglement between QPUs.
    
    This protocol assumes that each QPU produces a photon entangled with one 
    of its comm qubits and these photons are measured with a BSM between the 
    two QPUs to leave the static comm qubits entangled with each other.
    
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
    max_num_ent_attempts = bool or none, optional
        The number of entanglement attempts to make before giving up and 
        handing back control to higher layers.

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
    Similar idea to the Wehner stack [1]_, [2]_.
    
    References
    ----------
    .. [1] A. Dahlberg, et al., A link layer protocol for quantum networks, in: 
           Proceedings of the ACM Special Interest Group on Data Communication,
           ACM (2019)

    .. [2] M. Pompili, et al., Experimental demonstration of entanglement 
           delivery using a quantum network stack, npj Quantum Information, 8 
           (2022)
    """
    def __init__(self, node=None, name=None, role=None,
                 other_node_name=None, comm_qubit_indices=None, 
                 ready4ent=True, max_num_ent_attempts=100):
        super().__init__(node=node, name=name, role=role, 
                         other_node_name=other_node_name,
                         comm_qubit_indices=comm_qubit_indices,
                         ready4ent=ready4ent, 
                         max_num_ent_attempts=max_num_ent_attempts)
        self.entanglement_type2generate = 'bell_pair'
        self.ent_request_msg = "ENT_REQUEST"
        #The next two instance attributes will be overwritten in the run 
        #method because this is the first time that self.node must have a value
        #other than None and it is convenient to use self.node to instantiate
        #the next two attributes.
        self.entangling_connection_port_name = None
        self.ent_conn_port = None
        #initialising internal counter to count the number of times 
        #entanglement has been attempted
        self._ent_attempt_counter = 0
        
    def entangle_comm_qubits(self):
        while True: #will be broken with break command on successful 
                    #entanglement or when max number of entanglement attempts
                    #is exceeded:
            emit_program = QuantumProgram()
            #By construction, self.comm_qubit_indices are the relevant comm-qubit 
            #positional indices to act on rather than the positions of ALL 
            #comm-qubits
            emit_program.apply(instr.INSTR_INIT, 
                               qubit_indices=self.comm_qubit_indices)
            #TO DO: decide if photon_positions should be an attribute of the 
            #qmemory or the node and add the attribute to whichever you decide on
            photon_index = self.node.qmemory.photon_positions[0]
            if len(self.comm_qubit_indices) == 1:
                comm_qubit_index = self.comm_qubit_indices[0]
            else:
                raise ValueError('There are too many comm-qubit indices. '
                                 'Currently, only one comm-qubit can be used here.'
                                 'It is assumed that there is one photon emission'
                                 ' at a time.')
            emit_program.apply(instr.INSTR_EMIT, 
                               qubit_indices=[comm_qubit_index, photon_index])
    # =============================================================================
    #         #initialising a COPY of comm_qubit indices
    #         unused_comm_qubit_indices = list(self.comm_qubit_indices)
    #         #TO DO: decide if the following should be an attribute of the qmemory 
    #         #or the node and add the attributed to whichever you decide on
    #         photon_indices = self.node.qmemory.photon_positions
    #         for ii in range(self.num_entanglements2generate):
    #             comm_qubit_index = unused_comm_qubit_indices[ii]
    #             photon_index = photon_indices[ii]
    #             emit_program.apply(instr.INSTR_EMIT, 
    #                           qubit_indices=[comm_qubit_index, photon_index])
    # =============================================================================
            yield self.node.qmemory.excute_program(emit_program)
            yield self.await_port_input(self.ent_conn_port)
            bsm_outcome, = self.ent_conn_port.rx_input().items
            program = QuantumProgram()
            if bsm_outcome.success:
                #converting to PHI_PLUS state
                #applying corrective gates to only one of the qubits involved in 
                #the bell pair (which one does not matter up to a global phase)
                if self.role == 'server':
                    #x gate needed for both PSI_PLUS and PSI_MINUS
                    program.apply(instr.INSTR_X, 
                                  qubit_indices=comm_qubit_index)
                    if bsm_outcome.bell_index == ks.BellIndex.PSI_MINUS:
                        program.apply(instr.INSTR_Z, 
                                      qubit_indices=comm_qubit_index)
                    elif bsm_outcome.bell_index != ks.BellIndex.PSI_PLUS:
                        raise ValueError(
                            'the BSMOutcome must have bell_index attr'
                            'with value netsquid.qubits.ketstates.'
                            'BellIndex.PSI_PLUS or PSI_MINUS. Instead, '
                            f'it has value {bsm_outcome.bell_index} here.')
                    yield self.node.qmemory.execute_program(program)
                    self.classical_conn_port.tx_output(self.ent_ready_label)
                    self.send_signal(self.ent_ready_label)
                elif self.role == 'client':
                    yield self.await_port_input(self.ent_conn_port)
                    self.sent_signal(self.ent_ready_label)
                    break #breaking the while loop at the start of this method
            else: #if bsm_outcome.success == False:
                if self._ent_attempt_counter > (self.max_num_ent_attempts- 1):
                    self.send_signal(self.ent_failed_label)
                    break #breaking the while loop at the start of this method
                else:
                    self._ent_attempt_counter = self._ent_attempt_counter + 1
        
    def run(self):
        while True:
            #deferring handling of signalling to the base class as this will be
            #identical for all subclasses. This will override the role, 
            #other_node_name, comm_qubit_indices, num_entanglements2generate, 
            #and entanglement_type2generate attributes with useful values (in 
            #place of the default None).
            yield from super().run_link_layer()
            yield from self.handshake() #TO DO: improve handshake 
            #At the moment, the following will only be able to emit one photon
            #at a time. INSTR_EMIT can only emit one photon at a time but one 
            #could use many such instructions in a program to emit more than 
            #one.
            yield from self.entangle_comm_qubits()

            
            
        
        
        
        
