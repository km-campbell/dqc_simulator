# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 14:13:35 2023

@author: kenny
"""

class DqcCircuit():
    def __init__(self, qregs, cregs, native_gates, ops,
                 qreg2node_lookup=None, circuit_type=None):
        """ 
        Parameters
            ----------
            qregs : dict of dicts
                The quantum registers and their associated info. Subdicts
                should have the keys 'size', and 'starting_index', and integer
                values for each.
            cregs : dict
                The classical registers and their associated sizes.
            native_gates : dict
                The gates native to the processor upon which the DQC circuit
                will be enacted.
            ops : list of lists
                The operations (such as gates, initialisations or measurements)
                in the quantum circuit written in a way dqc_simulator can 
                understand.
            qreg2node_lookup : dict or None, optional
                A mapping from qreg names to node names. This can be used to 
                specify the partitioning of the circuit manually by associating
                each qreg with an appropriate node name
            circuit_type : str or None, optional
                Meta info indicating what is left to do to the circuit
                 Can be 'monolithic', 'unpartitioned' 'prepped4partitioning',
                 or 'partitioned'. TO DO: add more options like 'optimised'.
        """
        self.qregs = qregs 
        self.cregs = cregs
        self.native_gates = native_gates
        self.ops = ops
        self.qreg2node_lookup = qreg2node_lookup
        self.circuit_type = circuit_type
        self.qubit_count = 0 
        self.scheme = None #if this is a str, then it is the scheme all 
                           #two-qubit gates will be conducted using
        self.node_sizes = dict() #when processed should be dict with entries of 
                                 #form node_name : integer value 
        self.gate_macros = dict() 

    def replace_qreg_names(self, node_0_name='placeholder',
                            node_1_name='placeholder'):
        """Replaces node names in each gate_spec in ops with a placeholder 
        indicating that partitioning should be done
        
        Parameters
            ----------
            node_1_name : str, optional
                The word to use for the first node in each gate_spec or 
                an appropriate_placeholder"""
        for gate_spec in self.ops:
            gate_spec[2] = node_0_name
            if len(gate_spec) >= 5:
                gate_spec[4] = node_1_name
                
    def _replace_qreg_names_with_placeholder(self):
        self.replace_qreg_names(node_0_name='placeholder',
                                 node_1_name='placeholder')
        self.circuit_type = 'prepped4partitioning'
            
    def _convert2monolithic(self):
        """Replaces node names in each gate_spec in ops the name monolithic
           processor"""
        self.replace_qreg_names(node_0_name='monolithic_processor',
                                 node_1_name='monolithic_processor')
        self.circuit_type = 'monolithic'
        
    def _specify_partition_manually(self):
        for gate_spec in self.ops:
            gate_spec[2] = self.qreg2node_lookup[gate_spec[2]]
            if len(gate_spec) >= 5:
                gate_spec[4] = self.qreg2node_lookup[gate_spec[4]]
        self.circuit_type = 'partitioned'

        
    def qregs2nodes(self, conversion_strategy):
        """
        Converts qreg names to node names for all gate_spec elements of 
        self.ops.

        Parameters
        ----------
        conversion_strategy : str or None, optional
            How to partition the circuit. This is used by the to ascertain how 
            to convert the qreg names to node names. Can be 'monolithic', 
            'manual', or 'auto'. 
                'monolithic' : all gate_spec elements in self.ops have 
                               all node names set to "monolithic_processor"
                'manual' : the node names in all gate_spec elements will be 
                           specified by the qreg2node_lookup. This 
                           corresponds to a user-specified partitioning of 
                           the circuit
                'auto' : all node names are replaced with 'placeholder', 
                        awaiting automated partitioning. MAY BE SUPERFLUOUS
        """
        circuit_type_converters = {
                   'auto' : self._replace_qreg_names_with_placeholder, #MAY BE SUPERFLUOUS
                   'monolithic' : self._convert2monolithic,
                   'manual' : self._specify_partition_manually
                   }
        converter_subroutine = circuit_type_converters[conversion_strategy]
        converter_subroutine()
        
    def add_scheme_to_2_qubit_gates(self, scheme):
        """
        Specifies the scheme to be used for all two qubit gates.
        
        Parameters
        ----------
        scheme : str
            The scheme to be used for all two_qubit_gates
        """
        self.scheme = scheme
        for gate_spec in self.ops:
            if len(gate_spec) >= 5:
                gate_spec.append(scheme)
            
    def lock_in_gate_specs(self):
        """Renders all elements of self.ops immutable. This is useful for 
           protecting against accidental alteration of elements in self.ops.
        """
        for gate_spec in self.ops:
            gate_spec = tuple(gate_spec)
            
# =============================================================================
#     def partition(self, partitioner):
#         self = partitioner(self)
#         
# =============================================================================
