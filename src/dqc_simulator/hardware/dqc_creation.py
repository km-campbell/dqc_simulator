# -*- coding: utf-8 -*-
"""
Created on Fri Mar 31 12:37:47 2023

@author: kenny
"""

import warnings

import netsquid as ns
from netsquid.nodes import Node, Connection, Network
from netsquid.components.qchannel import QuantumChannel
from netsquid.components.cchannel import ClassicalChannel
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.qubits.state_sampler import StateSampler
from netsquid.qubits import ketstates as ks
from netsquid.components.models.delaymodels import FibreDelayModel

from dqc_simulator.hardware.quantum_processors import create_processor



class EntanglingConnection(Connection):
    """Designed to connect a node containing a source of entangled qubits to a 
    QPU node

    Parameters
    ----------
    delay : float
        The time taken for an entangled qubit to travel between source and node
        [ns].
    port_number : str, optional
        Number to go in port names so as to distinguish different entangling 
        connections created from this class.
    other_node_initial : str, optional
        Letter to go in port names, to indicate which node is being connected
        to the source node
    name : str, optional
        Name of this connection.

    """

    def __init__(self, delay,
                 port_number=1, other_node_initial="A",
                 name="EntanglingConnection"):
        super().__init__(name=name)
        self.add_ports(
            [f"{other_node_initial}_quantum0", 
             f"{other_node_initial}_quantum1", 
             f"{other_node_initial}_classical",
             "C_quantum0", "C_quantum1", "C_classical"])
        qchannel_c2other0 = QuantumChannel(f"qchannel_C2{other_node_initial}0",
                                           delay=delay)
        qchannel_c2other1 = QuantumChannel("qchannel_C2{other_node_initial}1", 
                                           delay=delay)
        cchannel_other2c = ClassicalChannel(f"cchannel_{other_node_initial}2C",
                                               delay=0) #the classical delay is
                                                        #implicitly included in
                                                        #delay of quantum 
                                                        #channels here to model
                                                        #the total entanglment
                                                        #distribution time.
        #Adding channels and forwarding from connection's port to the input
        #port of the channel ("send"). The "send" port then forwards to the 
        #"recv" port in the channel behind the scenes, after some delay 
        self.add_subcomponent(qchannel_c2other0, 
                              forward_output=[(f"{other_node_initial}_quantum0", 
                                               "recv")],
                              forward_input=[("C_quantum0", "send")])
        self.add_subcomponent(qchannel_c2other1,
                              forward_output=[(f"{other_node_initial}_quantum1", 
                                               "recv")],
                              forward_input=[("C_quantum1", "send")])
        self.add_subcomponent(cchannel_other2c, 
                              forward_output=[("C_classical", "recv")],
                              forward_input=[(f"{other_node_initial}_classical",
                                              "send")])

def create_abstract_entangling_link(network, node_a, node_b,
                                    state4distribution, 
                                    node_distance, 
                                    ent_dist_rate):
    """ Sets up an abstract entangling link between QPUs. Designed to work with
        AbstractFromPhotonsEntangleProtocol.
    Input:
    network : netsquid.nodes.network.Network
        The entire network.
    node_a :  object created using netsquid.nodes.Node class
        A network node
    node_b : object created using netsquid.nodes.Node class
        A network node
    state4distribution : numpy.ndarray 
        The entangled state distributed between nodes when
        an EPR pair is requested. Default is |phi^+> Bell state (formalism not
        fixed to ket)
    node_distance : float, optional
        Distance between adjacent nodes in km.
    ent_dist_rate : float, optional
        The rate of entanglement distribution [Hz].
        
    Notes: 
        
    This abstracts from the details of photon generation by treating flying
    and communication qubits as the same thing. Restraints on the number of 
    communication qubits can be enforced at the QPU nodes but entangled 
    communication qubits are generated at a central quantum source and sent
    to the QPUs. In this way, we can model error and loss but needn't simulate
    the details of entanglement between static communication qubits and photons.
    """
    #Create an intermediary node to generate entangled pairs and distribute them
    #to certain nodes. This is an abstraction of a repeater chain and control
    charlie = Node(
        f"Charlie_{node_a.name}<->{node_b.name}")
    qsource = QSource(f"qsource_{charlie.name}", 
                      StateSampler([state4distribution], [1.0]), num_ports=2,
                      status=SourceStatus.EXTERNAL) 
    charlie.add_subcomponent(qsource, 
                             name=f"qsource_{charlie.name}")
    charlie.add_ports(["entanglement_request_inputA2C", 
                       "entanglement_request_inputB2C"])
    network.add_nodes([charlie])
    def _add_connection2charlie(node, other_node_initial):
        if ent_dist_rate > 0 :
            ent_dist_time = 1e9/ent_dist_rate
        elif ent_dist_rate == 0.:
            ent_dist_time = 0
        else:
            raise ValueError(f"{ent_dist_rate} is not a valid entanglement "
                             f"distribution rate. The rate must be >= 0")
        q_conn = EntanglingConnection(
                    delay=ent_dist_time, 
                    other_node_initial=other_node_initial,
                    name=(f"EntanglingConnection{other_node_initial}C_"
                          f"{node_a.name}<->{node_b.name}"))
        if node is node_a:
            ii=0
        else:
            ii=1
        network.add_connection(
            node, charlie, connection=q_conn, 
            label=f"quantum{other_node_initial}C",
            port_name_node1=(f"quantum_input_from_charlie0_{node_a.name}<"
                             f"->{node_b.name}"),
            port_name_node2=f"qout{ii}")
        node.add_ports([f"request_entanglement_{node_a.name}<->{node_b.name}",
                        (f"quantum_input_from_charlie1_{node_a.name}<->"
                         f"{node_b.name}")])
        charlie.add_ports(f"qout{ii+2}")
        #disconnecting generically named ports and connecting better named ones
        q_conn.ports["A"].disconnect()
        q_conn.ports["B"].disconnect()
        charlie.ports[f"qout{ii}"].connect(q_conn.ports["C_quantum0"])
        charlie.ports[f"qout{ii+2}"].connect(q_conn.ports["C_quantum1"])
        q_conn.ports[f"{other_node_initial}_quantum0"].connect(
            node.ports[f"quantum_input_from_charlie0_{node_a.name}<->"
                       f"{node_b.name}"])
        q_conn.ports[f"{other_node_initial}_quantum1"].connect(
            node.ports[f"quantum_input_from_charlie1_{node_a.name}<->"
                       f"{node_b.name}"])
        node.ports[f"quantum_input_from_charlie0_{node_a.name}<->"
                   f"{node_b.name}"].forward_input(
                       node.qmemory.ports['qin0'])
        node.ports[f"quantum_input_from_charlie1_{node_a.name}<->"
                   f"{node_b.name}"].forward_input(
                       node.qmemory.ports['qin1'])
        node.ports[f"request_entanglement_{node_a.name}<->"
                   f"{node_b.name}"].connect(
            q_conn.ports[f"{other_node_initial}_classical"])
        
        return q_conn
    
    #add the entangling connections between each node and the qsource
    q_conn_a = _add_connection2charlie(node_a, "A")
    q_conn_b = _add_connection2charlie(node_b, "B")
    q_conn_a.ports["C_classical"].connect(charlie.ports["entanglement_"
                                                        "request_inputA2C"])
    q_conn_b.ports["C_classical"].connect(charlie.ports["entanglement_"
                                                        "request_inputB2C"])


def link_2_qpus(network, node_a, node_b, state4distribution=None, 
                 node_distance=2e-3, ent_dist_rate=0,
                 want_classical_2way_link=True,
                 want_entangling_link=True):
    """ Sets up a link between QPUs.
    Input:
    network : netsquid.nodes.network.Network
        The entire network.
    node_a :  object created using netsquid.nodes.Node class
    A network node
    node_b : object created using netsquid.nodes.Node class
    A network node
    state4distribution : numpy.ndarray 
        The entangled state distributed between nodes when
        an EPR pair is requested. Default is |phi^+> Bell state (formalism not
        fixed to ket)
    node_distance : float, optional
        Distance between adjacent nodes in km.
    ent_dist_rate : float, optional
        The rate of entanglement distribution [Hz].
    want_classical_2way_link : bool, optional
        Whether a two-way classical link should be created between all nodes
        (True) or not (False). 
    want_entangling_link : bool, optional
        Whether a two-way quantum link should be created between all nodes
        (True) or not (False). Nodes can request entangled pairs using this
        link. 
    """
    #instantiating default arguments. Need to do in body of function for mutable
    #objects like a numpy array because default values of functions are defined
    #only when the function is defined (not when it's called) and so mutable 
    #default values can be accidentally changed by code outwith the function.
    #See https://stackoverflow.com/questions/10676729/why-does-using-arg-none-
    #fix-pythons-mutable-default-argument-issue
    if state4distribution is None:
        state4distribution = ks.b00
    
    if want_classical_2way_link is False and want_entangling_link is False:
        raise ValueError("""At least one of want_classical_2way_link and
                         want_entangling_link must be True otherwise
                         the function call would be redundant""")


    # Set up classical connection between nodes:
    if want_classical_2way_link:    #(is True)
        network.add_connection(node_a, node_b,
                               channel_to=ClassicalChannel(
                                   "Channel_A2B", length=node_distance,
                                    models={"delay_model": FibreDelayModel()}),
                               channel_from=ClassicalChannel(
                                   "Channel_B2A", length=node_distance,
                                    models={"delay_model": FibreDelayModel()}), 
                               label="classical", 
                               port_name_node1=(f"classical_connection_"
                               f"{node_a.name}->{node_b.name}"), 
                               port_name_node2=(f"classical_connection_"
                                                f"{node_b.name}->{node_a.name}"))
    if want_entangling_link: #(is True)
        create_abstract_entangling_link(network, node_a, node_b,
                                        state4distribution, 
                                        node_distance, 
                                        ent_dist_rate)

class QpuNode(Node):
    """Class for creating QPU nodes (QPU including the classical control for 
        that QPU)
    """
    def __init__(self, name, comm_qubit_positions=(0, 1),
                 comm_qubits_free=None,
                 ebit_ready=False, ID=None, qmemory=None, port_names=None):
        super().__init__(name, ID=ID, qmemory=qmemory, port_names=port_names)
        self.comm_qubit_positions = comm_qubit_positions
        self.ebit_ready = ebit_ready
        self.comm_qubits_free = comm_qubits_free
        if comm_qubits_free == None:
            self.comm_qubits_free = [0, 1]
        else:
            self.comm_qubits_free = comm_qubits_free


def create_dqc_network(
                *args4qproc,
                state4distribution=None, #ks.b00 defined in function body
                node_list=None,
                num_qpus=2,
                node_distance=2e-3, ent_dist_rate=0,
                quantum_topology = None, 
                classical_topology = None,
                want_classical_2way_link=True,
                want_entangling_link=True,
                nodes_have_ebit_ready=False,
                node_comm_qubits_free=None, #[0, 1] defined in function body
                node_comm_qubit_positions=None, #(0, 1) defined in function body
                custom_qprocessor_func=create_processor,
                name="linear network",
                **kwargs4qproc):
    """A Network with nodes "Alice" and "Bob",
    connected by an entangling connection and a classical connection.
    
    This class sets up the physical components of the quantum network. The default
    topology of the network is a linear topology of the form
    node_1 <--> node_2 <--> node_3 <--> ...
    If not manually specified with the optional node_list argument, all nodes
    will be identical.

    Input
    ----------
    *args4qproc : 
        The arguments for the custom_qprocessor_func specified. By default,
        there are none of these.
    state4distribution : numpy.ndarray 
        The entangled state distributed between nodes when
        an EPR pair is requested. Default is |phi^+> Bell state (formalism not
        fixed to ket)
    node_list :  list of netsquid.components.nodes.Node objects, optional
        List of nodes to be included in network. Overrides num_qpus if
        specified.
    num_qpus : int (>=2), optional
        The number of identical nodes to be included in the network. Each node 
        has 5 data qubits and two communication qubits. Must be at least 2 to 
        avoid trivial scenario (if you have no connections there is no need)
        for this function, just create a node.
    Is overridden if a node_list is specified.
    node_distance : float, optional
        Distance between adjacent nodes.
    quantum_toplogy : list of tuple pairs of integers, optional
        The quantum network topology. Default is linear. The indices refer to 
        the nodes.to be connected should be connected in the tuple.
    classical_topology: list of tuple pairs of integers, optional
            The classical network topology. Default is linear. The indices 
            refer to the nodes.to be connected should be connected in the tuple.
    want_classical_2way_link : bool, optional
        Whether a two-way classical link should be created between all nodes
        (True) or not (False). Unused if classical_topology or 
        quantum_topology is not None.
    want_entangling_link : bool, optional
        Whether a two-way quantum link should be created between all nodes 
        (True) or not (False). Nodes can request entangled pairs using this
        link. Unused if classical_topology or quantum_topology is not None.
    custom_qprocessor_func: function or None, optional
        Creates the quantum processor object to use on each node. It must
        be able to run with no arguments. If unspecified then
        a default noiseless processor will be used
    name : str, optional
        Name of the network
    **kwargs4qproc : 
        The name-value arguments for the custom_qprocessor_func specified.
        By default (ie, when custom_qprocessor_func has the default value of
        create_processor), these are:    
                depolar_rate : float, optional
                    Depolarization rate of qubits in memory.
                dephase_rate : float, optional
                    Dephasing rate of physical measurement instruction.


    """
    
    #initialising default arguments
    if state4distribution is None:
        state4distribution=ks.b00
    if node_comm_qubit_positions is None:
        node_comm_qubit_positions = (0, 1)
    if node_comm_qubits_free is None:
        node_comm_qubits_free = [0, 1]
        
    if num_qpus < 2:
        raise ValueError("num_qpus must be at least 2")
    if type(num_qpus) is not int:
        raise TypeError("num_qpus must be an integer")

    # Create a network
    network = Network(name)
    def _create_qpus(num_qpus2create=num_qpus, starting_index=0):
        qpu_list = []
        for ii in range(num_qpus2create):
            #need to instantiate a new processor object each time with a 
            #new function call. Otherwise, the code is trying to add the 
            #same processor object to different nodes, as opposed to a copy
            #of it. Maybe look into taking processor creation function into
            #the entire create_dqc_network function rather than doing if 
            #statement. The difficulty is in ensuring that I can still
            #change the values if needed.
            qproc = custom_qprocessor_func(*args4qproc, **kwargs4qproc)
            qproc.name = f"qproc4node_{ii+starting_index}"
            qpu = QpuNode(
                        f"node_{ii+starting_index}", 
                        comm_qubit_positions=node_comm_qubit_positions,
                        comm_qubits_free=node_comm_qubits_free,
                        ebit_ready=nodes_have_ebit_ready, qmemory=qproc)
            qpu_list = qpu_list + [qpu] #appending node to node_list
        return qpu_list
    if node_list is None:
        node_list = _create_qpus(num_qpus2create=num_qpus)
        
    network.add_nodes(node_list)
    if quantum_topology is None and classical_topology is None:
        #create network with linear topology
        def _handle_even_num_qpus(num_qpus_considered):
            for ii in range(num_qpus_considered-1):
                node_1 = network.get_node(f"node_{ii}")
                node_2 = network.get_node(f"node_{ii+1}")
                link_2_qpus(network, node_1, node_2, 
                             state4distribution=state4distribution,
                             node_distance=node_distance, 
                             ent_dist_rate=ent_dist_rate,
                             want_classical_2way_link=want_classical_2way_link, 
                             want_entangling_link=want_entangling_link)
                
        if (num_qpus % 2) == 0:  #if num_qpus is even
            _handle_even_num_qpus(num_qpus)
        else: #if num_qpus is odd
            #handle first num_qpus-1 nodes
            num_qpus_considered = num_qpus - 1
            _handle_even_num_qpus(num_qpus_considered)
            #handle the rest
            node_1 = network.get_node(f"node_{num_qpus-2}") 
            node_2 = network.get_node(f"node_{num_qpus-1}") #num_qpus-1 is 
                                                             #max index
            link_2_qpus(network, node_1, node_2, 
                         state4distribution=state4distribution,
                         want_classical_2way_link=want_classical_2way_link, 
                         want_entangling_link=want_entangling_link)
    else:
        if quantum_topology is not None:
            if (quantum_topology[-1])[1] > (len(network.nodes)-1): 
            #if index is to large for number of nodes in network
                nodes_needed = ((quantum_topology[-1])[1] - 
                                (len(network.nodes) - 1))
                extra_nodes = _create_qpus(num_qpus2create=nodes_needed,
                                           starting_index=num_qpus)
                network.add_nodes(extra_nodes)
                warnings.warn("WARNING: num_qpus was overwritten because there"
                              " were not enough nodes to realise the requested"
                              " topology")
                
            for ii in range(len(quantum_topology)):
                indices = quantum_topology[ii]
                node_a = network.get_node(f"node_{indices[0]}")
                node_b = network.get_node(f"node_{indices[1]}")
                link_2_qpus(network, node_a, node_b,
                             state4distribution=state4distribution, 
                             node_distance=node_distance,  
                             want_classical_2way_link=False,
                             want_entangling_link=True)
        if classical_topology is not None: #if classical_topology is not None
            if (classical_topology[-1])[1] > (len(network.nodes)-1): 
            #if index is to large for number of nodes in network
                nodes_needed = ((classical_topology[-1])[1] - 
                                (len(network.nodes) - 1))
                extra_nodes = _create_qpus(num_qpus2create=nodes_needed,
                                           starting_index=num_qpus)
                network.add_nodes(extra_nodes)
                warnings.warn("WARNING: num_qpus was overwritten because there"
                              " were not enough nodes to realise the requested"
                              " topology")
                
            for ii in range(len(classical_topology)):
                indices = classical_topology[ii]
                node_a = network.get_node(f"node_{indices[0]}")
                node_b = network.get_node(f"node_{indices[1]}")
                link_2_qpus(network, node_a, node_b,
                             state4distribution=state4distribution, 
                             node_distance=node_distance,
                             want_classical_2way_link=True,
                             want_entangling_link=False)
    return network




#CHANGELOG:
#create_processor changed to have only optional arguments. 
