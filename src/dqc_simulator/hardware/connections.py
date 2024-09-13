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
 useful for a DQC.
"""

from netsquid.components import (ClassicalChannel, QuantumChannel, QSource,
                                 SourceStatus)
from netsquid.nodes.connections import Connection
from netsquid.qubits import StateSampler


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


class BlackBoxEntanglingQsourceConnection(Connection):
    """
    Intended to connnect source of entangled photons and 2 QPUs.
    
    Generates a pair of entangled qubits sharing a particular state without 
    regard for how that state was generated. The state is intended to be 
    specified analytically and the state definition can be used to specify the
    noise on the entangled photons if desired. In this way, the need for 
    multiple simulation runs (which would be required by a probabilistic noise
    model) is circumvented.
    
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
    port_number : str, optional
        Number to go in port names so as to distinguish different entangling 
        connections created from this class.
    name : str, optional
        Name of this connection. Default is
        "BlackBoxEntanglingQsourceConnection".
    """

    def __init__(self, delay,
                 state4distribution,
                 port_number=1, 
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


#TO DO:
#   Figure out whether by using a product state you can have 
#   multiple entangled pairs distributed. You have already
#   established that you can use a product state to emit multiple
#   qubits from each port and now need to check that the qubits
#   emitted from the same port are not the ones entangled with 
#   each other (which would be no good to you). It is probably easiest
#   to do this once you have made the Connection above (by tweaking it 
#   slightly).

