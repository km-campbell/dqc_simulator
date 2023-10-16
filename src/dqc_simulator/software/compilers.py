# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 15:01:31 2023

@author: kenny
"""

#Note: some compilation is also done in dqc_control.py. There common 
#subroutines used by Cat-comm and TP-comm are broken down into individual gates
#and run on individual nodes. The role of these compilers is to break a 
#monolithic quantum circuit into the lower level commands used in dqc_control.py.
#That said, very general compilers can be defined here. The only limitation is
#that they use only intraprocessor quantum gates and the interprocessor 
#subroutines involved in Cat and TP-comm


import netsquid as ns
from netsquid.components import instructions as instr


def sort_greedily_by_node_and_time(gate_tuples):
    """
    Distributes the circuit between nodes and splits into explicit time-slices
    (rows in output array).
    
    INPUT: 
        gate_tuples:  list of tuples
        The gates in the entire circuit. The tuples should be of the form:
        1) single-qubit gate: (gate_instr, qubit, node_name)
        2) two-qubit gate: (list of instructions or gate_instruction if local,
                            qubit0, node0_name, qubit1, node1_name, scheme)
                            #can later extend this to multi-qubit gates
                            #keeping scheme as last element
                            list of instructions: list
                                list of same form as gate_tuples containing
                                the local gates to be conducted as part of the
                                remote gate. Ie, for remote-cnot this would
                                contain the cnot (but not the gates used for
                                 bsm or correction).Note if this is given as
                                empty list and scheme = "tp" then it will
                                just do a teleportation
                                
                            qubitii: int
                                The qubit index
                            node_name: str
                            The name of the relevant node
                            scheme: str, optional 
                                Only needed for remote gates

                            

    OUTPUT: 
        node_op_dict: dict 
            Dictionary with term for each node which is an list of different 
            time slices (each time slice is a list within the list)
    """
    node_op_dict = {}

    for gate_tuple in gate_tuples:
        if len(gate_tuple) == 3: #if single-qubit gate
            gate_instr = gate_tuple[0]
            qubit_index = gate_tuple[1]
            node_name = gate_tuple[2]

            if node_name in node_op_dict: #if node in node_op_dict already
                #adding to last row of node_op_dict entry for this node
                node_op_dict[node_name][-1] = (node_op_dict[node_name][-1] +
                                            [(gate_instr, qubit_index)])

            else:
                node_op_dict[node_name] = [[(gate_instr, qubit_index)]] 

        elif len(gate_tuple) > 3: #if multi-qubit gate
            qubit_index0 = gate_tuple[1]
            node0_name = gate_tuple[2]
            qubit_index1 = gate_tuple[3]
            node1_name = gate_tuple[4]
            if node0_name == node1_name: #if local
                gate_instr = gate_tuple[0]
                node_name = node0_name
                if node_name in node_op_dict: #if node in node_op_dict already
                    node_op_dict[node_name][-1] = (node_op_dict[node_name][-1]
                                                   + 
                                                   [(gate_instr, qubit_index0, 
                                                  qubit_index1)]) 
                                                  #adding to last row
                                                  #of node_op_dict entry 
                                                  #for this node 
                    
                else: #if dictionary entry does not exist
                    node_op_dict[node_name] = [[(gate_instr, qubit_index0, 
                                             qubit_index1)]] #list of lists
            else: #if remote gate
                scheme = gate_tuple[-1]
                more2do4tp_safe = False 
                gate_instructions = gate_tuple[0]
                #if only one instruction given, with no qubit index specified
                #eg, just instr.INSTR_CNOT given:
                if type(gate_instructions) is ns.components.instructions.IGate:
                    #putting into correct form to use the comm-qubit index
                    #as the control. Which comm-qubit index to use will be 
                    #defined by the correction block in
                    #HandleCommBlockForOneNodeProtocol in dqc_control.py
                    gate_instructions = [(gate_instructions, -1, 
                                          qubit_index1)]
                if node0_name not in node_op_dict: #if node0 does not yet have
                                                   #entry in node_op_dict
                    node_op_dict[node0_name] = [[]]
                if node1_name not in node_op_dict: #if node1 does not yet have
                                                   #entry in node_op_dict
                    node_op_dict[node1_name] =[[]]
                if (len(node_op_dict[node0_name])
                    > len(node_op_dict[node1_name])):
                    length_diff = (len(node_op_dict[node0_name]) - 
                                   len(node_op_dict[node1_name]))
                    #adding dummy rows to make lengths match (enforcing
                    #scheduling)
                    start = len(node_op_dict[node1_name])
                    end = start + length_diff
                    for ii in range(start, end):
                        node_op_dict[node1_name].append([])
                elif (len(node_op_dict[node0_name])
                      < len(node_op_dict[node1_name])): 
                    length_diff = (len(node_op_dict[node1_name]) - 
                                   len(node_op_dict[node0_name]))
                    #adding dummy rows to make lengths match (enforcing
                    #scheduling)
                    start = len(node_op_dict[node0_name])
                    end = start + length_diff
                    for ii in range(start, end):
                        node_op_dict[node0_name].append([])
                if scheme == "cat":
                    node0_list = (
                        [(qubit_index0, node1_name, "cat", "entangle")] + 
                        [(qubit_index0, node1_name, "cat", "disentangle_end")])
                    node1_list = (
                        [(node0_name, "cat", "correct")]
                        + gate_instructions + 
                        [(qubit_index1, node0_name,
                          "cat", "disentangle_start")])
                elif scheme == "tp_risky":
                    #does not teleport back to original node to free up 
                    #comm-qubit
                    node0_list = [(qubit_index0, node1_name, "tp", "bsm")] 
                    node1_list = ([(node0_name, "tp", "correct")]
                                      + gate_instructions)
                elif scheme == "free_comm_qubit_with_tele":
                    node0_list = [(qubit_index0, node1_name, "tp", "bsm")]
                    node1_list = [(node0_name, "tp", "correct4tele_only"),
                                   (instr.INSTR_SWAP, -1, qubit_index1)] 
                elif scheme == "tp_safe":
                    #does tp remote gate then teleports back to original node 
                    #to free up comm-qubit.
                    #for remote gate:
                    node0_list = [(qubit_index0, node1_name, "tp", "bsm")]
                    node1_list = ([(qubit_index1, node0_name, "tp", "correct")]
                                  + gate_instructions)
                    more2do4tp_safe = True
                    #for teleportation back
                    node1_list_nxt_ts = [(-1, node0_name, "tp", "bsm")]
                    node0_list_nxt_ts = [(node1_name, "tp",
                                          "correct4tele_only"), 
                                  (instr.INSTR_SWAP, -1, qubit_index0)]
                    
                else:
                    raise Exception(f"Scheme not specified for remote gate"
                                    f"{gate_tuple} or is not of form 'cat',"
                                    f" 'tp_safe' or 'tp_risky'")
                #adding the lists to the last row of the relevant dictionary
                #entry for each node
                node_op_dict[node0_name][-1] = (node_op_dict[node0_name][-1] + 
                                             node0_list)
                node_op_dict[node1_name][-1] = (node_op_dict[node1_name][-1] + 
                                             node1_list)
                if more2do4tp_safe:
                    node_op_dict[node0_name].append(node0_list_nxt_ts)
                    node_op_dict[node0_name].append([])
                    node_op_dict[node1_name].append(node1_list_nxt_ts)
                    node_op_dict[node1_name].append([])
                else:
                    #adding extra row to the ammended dictionary entries to 
                    #indicate start of new time slice
                    node_op_dict[node0_name].append([])
                    node_op_dict[node1_name].append([])
                    
    for node_key in node_op_dict:
        if node_op_dict[node_key][-1] == []:
            del node_op_dict[node_key][-1]
            
    return node_op_dict