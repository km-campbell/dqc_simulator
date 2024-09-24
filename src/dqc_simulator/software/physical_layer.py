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

class SignalOutcome2Qpu(NodeProtocol):
    """
    Signals to QpuManagementProtocol/HandleCommBlockForOneNodeProtocol
    
    Intended to be used as a subprotocol for signalling 
    
    .. todo::
        
        Choose between which of QpuManagementProtocol and 
        HandleCommBlockForOneNodeProtocol and update the first line of this 
        docstring
    """
    def run(self):
        pass
        #FINISH (replacing pass above)

# =============================================================================
# class HandshakeProtocol(NodeProtocol):
#     """
#     Handshake protocol between QPUs, letting both QPUs know that the other
#     is ready to start entanglement distribution.
#     
#     Intended to be used as a subprotocol of other physical layer protocols
#     
#     
#     """
#     def run(self):
#         
# 
# class MidpointHeraldingProtocol(EntanglementGenerationProtocol):
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
#     def __init__(self):
#         #initiate HandshakeProtocol as subprotocol
#         
#     def run(self):
#         #wait on trigger
#         #start handshake
#         
#         
#         
#         
# =============================================================================
