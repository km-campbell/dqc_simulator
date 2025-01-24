# =============================================================================
# # -*- coding: utf-8 -*-
# 
# Created on Tue Sep 10 14:06:26 2024
# 
# @author: kenny
# 
# =============================================================================
"""
An extensible library of `netsquid.nodes.connections.Connection <connections>`
 useful for a DQC and wrappers for creating instances of them.
"""

from netsquid.components import (ClassicalChannel, FibreDelayModel,
                                 QuantumChannel, QSource, SourceStatus)
from netsquid.nodes.connections import Connection, DirectConnection
from netsquid.qubits import StateSampler
from netsquid_physlayer.heralded_connection import MiddleHeraldedConnection


#DELETE COMMENTS BELOW ONCE FINISHED REFACTORING

#Changelog relative to original entangling connection (things likely to 
#impact pre-existing code only):
#   1) removed keywork argument called `other_node_initial` (check this is)
#      not specified in any instances of the function
#   2) added state4distribution parameter
#   3) changed name of class itself

#Notes:
#   1) Be careful of syncronisation when using the
#      BlackBoxEntanglingQsourceConnection. This used to be handled via a 
#      protocol on a central node containing a QSource but will now need to be
#      handled by ensuring that only one of the QPUs sends a trigger request 
#      once they have both ensured they are ready to receive an entangled qubit
#      via appropriate handshake protocols
    
#TO DO:
#   Think about how to model delay. You may wish to allow user to specify
#   noise parameters to allow them to use the connection as abstract or
#   real as they wish


def create_classical_fibre_link(network, node_a, node_b, length, 
                                label='classical'):
    """
    Setus up a classical fibre connection between two QPUs.

    Parameters
    ----------
    network : :class: `~netsquid.nodes.network.Network`
        The entire network.
    node_a, node_b : :class: `~netsquid.nodes.Node`
        The QPUs to be linked.
    length : float
        the length of the connection.
    """
    connection = DirectConnection(
                                'DirectConnection',
                               channel_AtoB=ClassicalChannel(
                                   "Channel_A2B", length=length,
                                    models={"delay_model": FibreDelayModel()}),
                               channel_BtoA=ClassicalChannel(
                                   "Channel_B2A", length=length,
                                    models={"delay_model": FibreDelayModel()}))
    #generating names obeying netsquid naming conventions for port on QPUs that 
    #connect a Node to a connection but using the (unique) node name as the ID
    node_a_port_name = node_a.connection_port_name(node_b.name, 
                                                   label=label)
    node_b_port_name = node_b.connection_port_name(node_a.name,
                                                   label=label)
    network.add_connection(node_a, node_b, connection=connection,
                           port_name_node1=node_a_port_name,
                           port_name_node2=node_b_port_name,
                           label=label)



class BlackBoxEntanglingQsourceConnection(Connection):
    """
    Intended to connnect source of entangled photons and 2 QPUs.
    
    Generates a pair of entangled qubits sharing a particular state without 
    regard for how that state was generated. The state is intended to be 
    specified analytically and the state definition can be used to specify the
    noise on the entangled photons if desired. In this way, the need for 
    multiple simulation runs (which would be required by a probabilistic noise
    model) is circumvented. Therefore distribution with this connection is 
    deterministic and any probablistic effects are incorporated into the 
    chosen entanglement distribution rate (ie, the average entanglement 
    distribution rate should be used).
    
    The black box :class: `~netsquid.components.qsource.QSource` is triggered
    via the sending of a classical trigger message from either QPU. It is 
    assumed that both QPUs are ready to receive an entangled qubit when the 
    trigger message is sent, which will need to be enforced using the 
    :class: `~netsquid.protocols.nodeprotocols.NodeProtocol`(s) used to send 
    the trigger message. Only one trigger message should be sent per 
    entanglement distribution desired to avoid unintended behaviour (ie, a 
    trigger message should not be sent by both QPUs requesting the same 
    entangled pair).

    Parameters
    ----------
    delay : float
        The time for entanglement distribution to occur
        [ns].
    state4distribution : array
        The density matrix of the state that the entangled qubits should 
        possess.
    name : str, optional
        Name of this connection. Default is
        "BlackBoxEntanglingQsourceConnection".
    """

    def __init__(self, delay,
                 state4distribution,
                 name="BlackBoxEntanglingQsourceConnection"):
        super().__init__(name=name)
        qchannel_qsource2A = QuantumChannel("qchannel_qsource2A",
                                            delay=delay)
        qchannel_qsource2B = QuantumChannel("qchannel_qsource2B", 
                                            delay=delay)
        cchannelA2qsource_trigger = ClassicalChannel("cchannel_A2qsource_trigger",
                                                     delay=0) 
                                                     #the classical delay is
                                                     #implicitly included in
                                                     #delay of quantum 
                                                     #channels here to model
                                                     #the total entanglment
                                                     #distribution time.
                                                     #TO DO: revisit this
        cchannelB2qsource_trigger = ClassicalChannel("cchannel_B2qsource_trigger",
                                                     delay=0)
                                                    #TO DO: revisit delay
                                                    #as commented above
        qsource = QSource("qsource", 
                          StateSampler([state4distribution], [1.0]),
                          num_ports=2,
                          status=SourceStatus.EXTERNAL) 
        #adding extra trigger port and then forwareding that to the trigger so
        #that two classical connections can be connected to the trigger.
        qsource.add_ports(["extra_trigger"])
        qsource.ports["extra_trigger"].forward_input(qsource.ports["trigger"])
        #TO DO: tinker with qsource to see if it can be made to emit 
        #multiple pairs of entangled photons
        #Adding channels and forwarding to and from the connection's 
        #"A" and "B" ports to the input ("send") and ouput ("recv")
        #ports of the channel. An input to the channel's "send" port then 
        #forwards to the 
        #"recv" port in the channel behind the scenes, after some delay 
        self.add_subcomponent(qchannel_qsource2A,
                              forward_output=[("A", "recv")])
        self.add_subcomponent(qchannel_qsource2B, 
                              forward_output=[("B", "recv")])
        self.add_subcomponent(cchannelA2qsource_trigger,
                              forward_input=[("A", "send")])
        self.add_subcomponent(cchannelB2qsource_trigger,
                              forward_input=[("B", "send")])
        self.add_subcomponent(qsource)
        #adding the remaining connections between components within the 
        #overall Connection
        qsource.ports["qout0"].connect(qchannel_qsource2A.ports["send"])
        qsource.ports["qout1"].connect(qchannel_qsource2B.ports["send"])
        qsource.ports["trigger"].connect(
                                    cchannelA2qsource_trigger.ports["recv"])
        qsource.ports["extra_trigger"].connect(
                                    cchannelB2qsource_trigger.ports["recv"])
        
class ProbabilisticQSourceConnection(Connection):
    """
    Intended to connnect source of entangled photons and 2 QPUs.
    
    Generates a pair of entangled qubits sharing a particular state without 
    regard for how that state was generated. 
    
    The black box :class: `~netsquid.components.qsource.QSource` is triggered
    via the sending of a classical trigger message from either QPU. It is 
    assumed that both QPUs are ready to receive an entangled qubit when the 
    trigger message is sent, which will need to be enforced using the 
    :class: `~netsquid.protocols.nodeprotocols.NodeProtocol`(s) used to send 
    the trigger message. Only one trigger message should be sent per 
    entanglement distribution desired to avoid unintended behaviour (ie, a 
    trigger message should not be sent by both QPUs requesting the same 
    entangled pair).

    Parameters
    ----------
    delay : float
        The time for entanglement distribution to occur
        [ns].
    states4distribution : list of tuples (state, float)
        Where state is `~netsquid.qubits.qrepr.QRepr` or `numpy.ndarray`.
        Quantum state representations to distribute. Quantum state
        representations and the
        probability of being in that state
    name : str, optional
        Name of this connection. Default is
        "BlackBoxEntanglingQsourceConnection".
    """
    def __init__(self, delay,
                 states4distribution,
                 name="ProbabilisticQsourceConnection"):
        super().__init__(name=name)
        qchannel_qsource2A = QuantumChannel("qchannel_qsource2A",
                                            delay=delay)
        qchannel_qsource2B = QuantumChannel("qchannel_qsource2B", 
                                            delay=delay)
        cchannelA2qsource_trigger = ClassicalChannel("cchannel_A2qsource_trigger",
                                                     delay=0) 
                                                     #the classical delay is
                                                     #implicitly included in
                                                     #delay of quantum 
                                                     #channels here to model
                                                     #the total entanglment
                                                     #distribution time.
                                                     #TO DO: revisit this
        cchannelB2qsource_trigger = ClassicalChannel("cchannel_B2qsource_trigger",
                                                     delay=0)
                                                    #TO DO: revisit delay
                                                    #as commented above
        qsource = QSource("qsource", 
                          StateSampler([state[0] for state in states4distribution], 
                                       [state[1] for state in states4distribution]),
                          num_ports=2,
                          status=SourceStatus.EXTERNAL) 
        #adding extra trigger port and then forwareding that to the trigger so
        #that two classical connections can be connected to the trigger.
        qsource.add_ports(["extra_trigger"])
        qsource.ports["extra_trigger"].forward_input(qsource.ports["trigger"])
        #TO DO: tinker with qsource to see if it can be made to emit 
        #multiple pairs of entangled photons
        #Adding channels and forwarding to and from the connection's 
        #"A" and "B" ports to the input ("send") and ouput ("recv")
        #ports of the channel. An input to the channel's "send" port then 
        #forwards to the 
        #"recv" port in the channel behind the scenes, after some delay 
        self.add_subcomponent(qchannel_qsource2A,
                              forward_output=[("A", "recv")])
        self.add_subcomponent(qchannel_qsource2B, 
                              forward_output=[("B", "recv")])
        self.add_subcomponent(cchannelA2qsource_trigger,
                              forward_input=[("A", "send")])
        self.add_subcomponent(cchannelB2qsource_trigger,
                              forward_input=[("B", "send")])
        self.add_subcomponent(qsource)
        #adding the remaining connections between components within the 
        #overall Connection
        qsource.ports["qout0"].connect(qchannel_qsource2A.ports["send"])
        qsource.ports["qout1"].connect(qchannel_qsource2B.ports["send"])
        qsource.ports["trigger"].connect(
                                    cchannelA2qsource_trigger.ports["recv"])
        qsource.ports["extra_trigger"].connect(
                                    cchannelB2qsource_trigger.ports["recv"])


def create_black_box_central_source_entangling_link(network, node_a, node_b,
                                                    state4distribution,
                                                    ent_dist_rate=0):
    """ 
    Sets up an abstract entangling link between QPUs. 
    
    Adds BlackBoxEntanglingQsourceConnection between two QPUs.
    
    Parameters
    ----------
    network : :class: `~netsquid.nodes.network.Network`
        The entire network.
    node_a, node_b : :class: `~netsquid.nodes.Node`
        A network node.
    state4distribution : numpy.ndarray 
        The entangled state distributed between nodes when
        an EPR pair is requested. Default is |phi^+> Bell state (formalism not
        fixed to ket)
    ent_dist_rate : float, optional
        The rate of entanglement distribution [Hz]. The default is 0
    Notes 
    -----
    This abstracts from the details of photon generation by treating flying
    and communication qubits as the same thing. Restraints on the number of 
    communication qubits can be enforced at the QPU nodes but entangled 
    communication qubits are generated at a central quantum source and sent
    to the QPUs. In this way, we can model error and loss but needn't simulate
    the details of entanglement between static communication qubits and photons.
    """
    if ent_dist_rate > 0 :
        ent_dist_time = 1e9/ent_dist_rate
    elif ent_dist_rate == 0.:
        ent_dist_time = 0
    else:
        raise ValueError(f"{ent_dist_rate} is not a valid entanglement "
                         f"distribution rate. The rate must be >= 0")
    #commented out block below is for after refactor
    connection = BlackBoxEntanglingQsourceConnection(
                    delay=ent_dist_time,
                    state4distribution=state4distribution)
    #generating names obeying netsquid naming conventions for port on QPUs that 
    #connect a Node to a connection but using the (unique) node name as the ID
    node_a_port_name = node_a.connection_port_name(node_b.name, 
                                                   label="entangling")
    node_b_port_name = node_b.connection_port_name(node_a.name,
                                                   label="entangling")
    network.add_connection(node_a, node_b, connection=connection,
                           port_name_node1=node_a_port_name,
                           port_name_node2=node_b_port_name,
                           label='entangling')
    
    
def create_probabilistic_qsource_connection(network, node_a, node_b,
                                            states4distribution,
                                            ent_dist_rate=0):
    """ 
    Sets up an abstract entangling link between QPUs. 
    
    Adds BlackBoxEntanglingQsourceConnection between two QPUs.
    
    Parameters
    ----------
    network : :class: `~netsquid.nodes.network.Network`
        The entire network.
    node_a, node_b : :class: `~netsquid.nodes.Node`
        A network node.
    states4distribution : dict
        Keys are quantum state representations `~netsquid.qubits.qrepr.QRepr`, 
        values are probability of being in that state.
    ent_dist_rate : float
        The rate of entanglement distribution [Hz].
    Notes 
    -----
    This abstracts from the details of photon generation by treating flying
    and communication qubits as the same thing. Restraints on the number of 
    communication qubits can be enforced at the QPU nodes but entangled 
    communication qubits are generated at a central quantum source and sent
    to the QPUs. In this way, we can model error and loss but needn't simulate
    the details of entanglement between static communication qubits and photons.
    """
    if ent_dist_rate > 0 :
        ent_dist_time = 1e9/ent_dist_rate
    elif ent_dist_rate == 0.:
        ent_dist_time = 0
    else:
        raise ValueError(f"{ent_dist_rate} is not a valid entanglement "
                         f"distribution rate. The rate must be >= 0")
    #commented out block below is for after refactor
    connection = ProbabilisticQSourceConnection(
                    delay=ent_dist_time,
                    states4distribution=states4distribution)
    #generating names obeying netsquid naming conventions for port on QPUs that 
    #connect a Node to a connection but using the (unique) node name as the ID
    node_a_port_name = node_a.connection_port_name(node_b.name, 
                                                   label="entangling")
    node_b_port_name = node_b.connection_port_name(node_a.name,
                                                   label="entangling")
    network.add_connection(node_a, node_b, connection=connection,
                           port_name_node1=node_a_port_name,
                           port_name_node2=node_b_port_name,
                           label='entangling')
    
    
def create_midpoint_heralded_entangling_link(
        network, node_a, node_b, 
        length=2e-3, p_loss_init=0,p_loss_length=0, speed_of_light=200000, 
        dark_count_probability=0, detector_efficiency=1.0, visibility=1.0,
        num_resolving=False, coin_prob_ph_ph=1.0, coin_prob_ph_dc=1.0, 
        coin_prob_dc_dc=1.0):
    """
    Sets up an entangling connection with a central BSM between two QPUs.
    
    Adds a 
    :class: `netsquid_physlayer.heralded_connection.MiddleHeraldedConnection` 
    between two nodes.

    Parameters
    ----------
    network : :class: `~netsquid.nodes.network.Network`
        The entire network.
    node_a, node_b : :class: `~netsquid.nodes.Node`
        The QPU nodes to be linked.
    length: float
        Total length [km] of heralded connection (i.e. sum of fibers on both sides on midpoint station).
    p_loss_init: float (optional)
        Probability that photons are lost when entering connection the connection on either side.
    speed_of_light: float (optional)
        Speed of light [km/s] in fiber on either side.
    p_loss_length: float (optional)
        Attenuation coefficient [dB/km] of fiber on either side.
    dark_count_probability: float (optional)
        Dark-count probability per detection
    detector_efficiency: float (optional)
        Probability that the presence of a photon leads to a detection event
    visibility: float (optional)
        Hong-Ou-Mandel visibility of photons that are being interfered (measure of photon indistinguishability)
    num_resolving : bool (optional)
        determines whether photon-number-resolving detectors are used for the Bell-state measurement
    coin_prob_ph_ph : float (optional)
        Coincidence probability for two photons. When using a coincidence time window in the double-click protocol,
        two clicks are only accepted if they occurred within one coincidence time window away from each other.
        This parameter is the probability that if both clicks are photon detections,
        they are within one coincidence window. In general, this depends not only on the size of the coincidence
        time window, but also on the state of emitted photons and the total detection time window. Defaults to 1.
    coin_prob_ph_dc : float (optional)
        Coincidence probability for a photon and a dark count.
        When using a coincidence time window in the double-click protocol,
        two clicks are only accepted if they occurred within one coincidence time window away from each other.
        This parameter is the probability that if one click is a photon detection and the other a dark count,
        they are within one coincidence window. In general, this depends not only on the size of the coincidence
        time window, but also on the state of emitted photons and the total detection time window. Defaults to 1.
    coin_prob_dc_dc : float (optional)
        Coincidence probability for two dark counts. When using a coincidence time window in the double-click protocol,
        two clicks are only accepted if they occurred within one coincidence time window away from each other.
        This parameter is the probability that if both clicks are dark counts,
        they are within one coincidence window. In general, this depends on the size of the coincidence time window
        and the total detection time window. Defaults to 1.

    References
    ----------
    Most of this docstring is taken (with some slight modification in 
    places) from the docstring for 
    `netsquid_physlayer.heralded_connection.MiddleHeraldedConnection`
    in accordance with the apache 2.0 license available at 
    http://www.apache.org/licenses/LICENSE-2.0
    """
    connection = MiddleHeraldedConnection(
                    name='MiddleHeraldedConnection', 
                    length=length, p_loss_init=p_loss_init, 
                    p_loss_length=p_loss_length, 
                    speed_of_light=speed_of_light,
                    dark_count_probability=dark_count_probability, 
                    detector_efficiency=detector_efficiency,
                    visibility=visibility,
                    num_resolving=num_resolving, 
                    coin_prob_ph_ph=coin_prob_ph_ph, 
                    coin_prob_ph_dc=coin_prob_ph_dc, 
                    coin_prob_dc_dc=coin_prob_dc_dc)
    #generating names obeying netsquid naming conventions for port on QPUs that 
    #connect a Node to a connection but using the (unique) node name as the ID
    node_a_port_name = node_a.connection_port_name(node_b.name, 
                                                   label="entangling")
    node_b_port_name = node_b.connection_port_name(node_a.name,
                                                   label="entangling")
    network.add_connection(node_a, node_b, connection=connection,
                           port_name_node1=node_a_port_name,
                           port_name_node2=node_b_port_name,
                           label='entangling')
    node_a.qmemory.ports['qout'].forward_output(node_a.ports[node_a_port_name])
    node_b.qmemory.ports['qout'].forward_output(node_b.ports[node_b_port_name])
    

