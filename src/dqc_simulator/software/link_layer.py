# -*- coding: utf-8 -*-
# =============================================================================
# Created on Fri Sep 13 09:28:30 2024
# 
# @author: kenny
# =============================================================================

"""
Protocols for the link layer similar to that defined in the Wehner network stack.

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

#TO DO: get rid of following import if you swap HandleCommBlockForOneNodeProtocol
#for a new QpuManagementProtocol (keep if you do not)
from dqc_simulator.software.dqc_control import HandleCommBlockForOneNodeProtocol

class EntanglementGenerationProtocol(NodeProtocol):
    """
    A basic link layer implementation with no signalling needed to the physical 
    layer.
    
    The physical layer protocols that deal with entanglement are implemented
    as subprotocols of this protocol.
    
    Parameters
    ----------
    physical_layer_protocol : :class: `netsquid.protocols.nodeprotocols.NodeProtocol`
        Instance of the physical layer protocol to use to handle entanglement 
        generation.
    node : :class: `netsquid.nodes.node.Node`, subclass thereof or None, optional
        The QPU node that this protocol will act on. If None, a node should be
        set later before starting this protocol. [1]_
    name : str or None, optional
        Name of protocol. If None, the name of the class is used. [1]_
        
    References
    ----------
    References
    ----------
    The parameters in which Ref. [1]_ was cited were inherited from 
    :class: `~netsquid.protocols.nodeprotocols.NodeProtocol` and the description
    used for those parameters was taken from the NetSquid documentation with 
    very minor modification [1]_.
    
    .. [1] https://netsquid.org/
        
    .. todo::
        
        Decide whether to replace HandleCommBlockForOneNodeProtocol with 
        a new protocol called QpuManagementProtocol.
    """
    def __init__(self, physical_layer_protocol, node=None, name=None):
        super().__init__(node, name)
        self.add_subprotocol(physical_layer_protocol,
                             name='physical_layer_protocol')
        self.ent_request_label = "ENT_REQUEST"
# =============================================================================
#         self.ent_ready_label = "ENT_READY"
#         self.ent_failed_label = "ENT_FAILED"
# =============================================================================

    
        
    def run(self):
        #TO DO: determine if this run method should be changed to not be a run
        #method because this should be an abstract base class. This is just to
        #help me think things through more abstractly. This class may also be 
        #used as a subprotocol.
        while True:
            #TO DO: decide what protocol will be sending this signal. 
            #HandleCommBlockForOneNodeProtocol may be replaced by 
            #QpuManagementProtocol. ALSO need to replace the class name with
            #an instance of the class in the following line. Need to think 
            #about how to achieve this.
            yield self.await_signal(HandleCommBlockForOneNodeProtocol, 
                                    signal_label=self.ent_request_label)
            #the following could be replaced with any desired specs (including 
            #a tuple of them). TO DO: think about whether you want to have more
            #specs (eg, entanglement fidelity like in Wehner stack papers).
            #For now, I'll keep it simple
            signal_results = self.get_signal_result(
                                            self.ent_request_label, 
                                            receiver=self)
            role = signal_results[0]
            other_node_name = signal_results[1] 
            comm_qubit_indices = signal_results[2]
            num_entanglements2generate = signal_results[3]
            entanglement_type2generate = signal_results[4]
            #updating relevant attributes
            self.subprotocols['physical_layer_protocol'].role = (
                role)
            self.subprotocols[
                'physical_layer_protocol'].other_node_name = (
                    other_node_name)
            self.subprotocols[
                'physical_layer_protocol'].comm_qubit_indices = (
                    comm_qubit_indices)
            self.subprotocols[
                'physical_layer_protocol'].num_entanglements2generate = ( 
                    num_entanglements2generate)
            self.subprotocols[
                'physical_layer_protocol'].entanglement_type2generate = (
                    entanglement_type2generate)
            self.subprotocols['physical_layer_protocol'].start()
            #TO DO: fix this. Right now, the code will only take in one 
            #physical protocol the whole time rather than starting a new one
            #every time entanglement is requested. Probably need to wait on
            #the protocol finishing too.
            
            
            #TO THINK ABOUT: should the following be done by the physical layer?
            #It seems pointless to have a middle man for this part.
            #Perhaps you could make another protocol to do this and use this
            #as a subprotocol of the physical_layer_protocol, If so, then 
            #you may need to wait on the physical_layer_protocol finishing.
# =============================================================================
#             #TO DO: wait on ENT_READY or ENT_FAILED signals from the physical 
#             #layer
#             wait_on_ent_ready_signal = ( 
#                 self.await_signal(self.subprotocols['physical_layer_protocol'],
#                                   signal_label=self.ent_ready_label))
#             wait_on_ent_failed_signal = (
#                 self.await_signal(self.subprotocols['physical_layer_protocol'],
#                                   signal_label=self.ent_failed_label))
#             evexpr = yield wait_on_ent_ready_signal | wait_on_ent_failed_signal
#             if evexpr.first_term.value: #if ent_ready signal received:
#                 #do one thing
#             elif evexpr.second_term.value: #if ent_failed signal received:
#                 #do something else
# =============================================================================
