***************
Getting started
***************

Welcome to the getting started guide for absolute beginners to using
dqc_simulator! This guide assumes that you have already installed 
dqc_simulator and its prerequisites on your system. If this is not 
the case, please follow the 
:doc:`installation instructions <installation>`. This guide also assumes  
a working knowledge of quantum computing and quantum information. 
If this is not the case, I recommend Nielsen and Chuang's excellent
introductory text [1]_. Finally, we do make occasional, very basic, use of the 
`NumPy <https://numpy.org/>`_ and `pandas <https://pandas.pydata.org/>` libraries,
although, what is done should be fairly easy to understand without knowledge of 
these libraries.

dqc_simulator is a python package for the simple simulation of 
distributed quantum computers (DQCs). It is built on top of the
`NetSquid <https://netsquid.org/>`_ library but does not require 
a detailed understanding of NetSquid to use. The only required 
NetSquid commands can be found in this tutorial. That said, users that 
are more familiar with NetSquid can easily integrate the package 
into their existing workflow if they wish to consider more complicated
scenarios, such as error detection, or specify their own hardware in 
more detail. 

In keeping with this philosophy, the core content of this guide is 
intended to be self contained, but I frequently signpost where users
already familiar with NetSquid can further extend the functionality
discussed.

The guide will take you through the main ideas of `dqc_simulator` and 
give step-by-step instructions to building your first DQC simulation experiment.

Why use dqc_simulator?
======================

Classically simulating a DQC is challenging. It involves all of the challenges of simulating 
a quantum computer and all of the challenges of simulating a quantum network. There are many
possible aspects to such a simulation, from the minutia of hardware control to the choice 
of how to represent the quantum formalism and the way in which you should specify higher 
level algorithmic considerations.

`NetSquid <https://netsquid.org/>`_ is probably the most comprehensive attempt to account 
for all of these considerations and features the capacity for full-stack simulation of a 
DQC with the ability to specify arbitrary hardware and software in a formalism-agnostic 
fashion (quantum states can be simulated using a variety of formalisms with different pros
and cons). However, it was developed 
for the simulation of quantum networks more generally and, due to its generality, simulating
DQCs can be quite labour intensive and requires a significant amount of manual specification.

The aim of dqc_simulator is to retain the generality and flexibility of 
`NetSquid <https://netsquid.org/>`_ while automating typical DQC tasks. This allows 
users unfamiliar with NetSquid to easily simulate DQCs while allowing more advanced users,
with some knowledge of NetSquid, to integrate dqc_simulator into their workflow for 
especially complicated use cases, such as a full-stack simulation of quantum error correction
or the use of DQCs within larger networks. 

The key features of dqc_simulator are:

*  **Easy-to-use interface for specifying distributed quantum circuits.**
*  **Interpreter for running communication primitives.**
*  **Automatic partitioning of monolithic (single-processor)**
   **quantum circuits between quantum processing units (QPUs).** Arbitrary
   algorithms for doing this can be specified by the user
   if desired, using the DQC circuit interface. Circuits
   can be specified as a list of tuples or as a .qasm
   file.
*  **Automatic management of remote gates and communication qubits.**
*  **Automatic compilation using pre-made compilers.** The user
   can also easily specify their own.

Importing dqc_simulator
=======================

dqc_simulator can be imported into python code with the line: ::

       import dqc_simulator

Creating the hardware
=====================

Hardware specification can be done in three easy stages:

1. Specify a QPU
2. Specify a quantum connection
3. Create the network

Step 1: specifying a QPU
------------------------

For step 1, a handy class is provided. Lets use it to create a 
QPU: ::

      from dqc_simulator.hardware.quantum_processors import NoisyQPU
      qpu = NoisyQPU()

This QPU has two types of qubit: communication qubits, which 
are used to host ebits, and processing qubits, which are used in 
the same way as qubits on a monolithic quantum computer. We can specify
the maximum number of communication qubits that our QPU can hold
with the `num_comm_qubits` keyword argument and the total number 
of qubits (including communication and processing qubits) using
`num_positions`. Ie, ::

   qpu = NoisyQPU(num_comm_qubits=2,
                  num_positions=10)

Creates a processor with space for 2 comm-qubits and 8 processing 
qubits, making 10 total qubits. This allows us to constrain what 
it is possible for our hardware to handle. The positions of the 
communication and processing qubits can be accessed later
using the `QPU.comm_qubit_positions` and 
`QPU.processing_qubit_positions` attributes, respectively.

By default all noise is turned off and the QPU is ideal. However,
adding noise is as simple as choosing keyword arguments in the 
above function. For example: ::

   qpu = NoisyQPU(
                  p_depolar_error_cnot=1e-03,
                  single_qubit_gate_error_prob=2e-05,
                  meas_error_prob=3e-03,
                  comm_qubit_depolar_rate=0.06,
                  proc_qubit_depolar_rate=0.05,
                  single_qubit_gate_time=135 * 10**3,
                  two_qubit_gate_time=600 * 10**3,
                  measurement_time=600 * 10**4, 
                  num_positions=10,
                  num_comm_qubits=2)

We have now added depolarising noise to all cnot gates with 
probability :math:`1 \times 10^{-03}` and to all single-qubit 
gates with probability :math:`2 \times 10^{-05}`. The probability
of getting a bit flip during measurement has been set to 
:math:`3 \times 10^{-03}` and we have imposed time dependent 
memory depolarisation at a rate of memory depolarisation at a 
rate of :math:`0.06` Hz on the communication qubits and 
:math:`0.05Hz` on the processing qubits. You will also
notice that we have defined times for various operations (in 
units of ns). These define the duration of that operation and
influence any time dependent memory depolarisation or anything 
else that depends on time.
   
.. note::
   Advanced users, with a background in
   `NetSquid <https://netsquid.org/>`_ may wish to define their
   own QPUs. This can be done by subclassing from the
   `dqc_simulator.hardware.quantum_processors.QPU`. This is itself
   a subclass to the `QuantumProcessor` class defined in 
   `NetSquid <https://netsquid.org/>`_ and is very similar but 
   it adds the `comm_qubit_positions` and 
   `processing_qubit_positions` attributes, which are made use 
   of a great deal by the interpreter and so it is recommended 
   to use the `QPU` as your base class. See the API reference for
   more details.

We actually don't need to create a `QPU` object at this point. 
It's going to be done for us behind the scenes in step 3.
However, we will need to provide the subclass of 
 `QPU` that we wish to use and the parameters we want. This 
will look something like: ::

      qpu_class = NoisyQPU
      kwargs4qpu = {'p_depolar_error_cnot' : 1e-03,
                     'single_qubit_gate_error_prob' : 2e-05,
                     'meas_error_prob' : 3e-03,
                     'comm_qubit_depolar_rate' : 0.06,
                     'proc_qubit_depolar_rate' : 0.05,
                     'single_qubit_gate_time' : 135 * 10**3,
                     'two_qubit_gate_time' : 600 * 10**3,
                     'measurement_time' : 600 * 10**4, 
                     'num_positions' : 10,
                     'num_comm_qubits' : 2}

Step 2: specifying a quantum connection
---------------------------------------

Step 2 is very similar. This time there are a few classes to choose from,
which are all subclasses of `netsquid.nodes.connections.Connection`.
We will focus here on `BlackBoxEntanglingQsourceConnection`, which is 
recommended for those new to `dqc_simulator`, who wish to work in 
the densitry matrix formalism. This creates a black box source of 
ebits between QPUs, where the ebits can be in any two-qubit state
specified in the density matrix formalism. For typical and simple  
modelling of noisy ebits, I recommend the `werner_state` function. 
Lets see what this will look like: ::

      from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
      from dqc_simulator.qlib.states import werner_state
      entangling_connection_class = BlackBoxEntanglingQsourceConnection
      F_werner = 0.9
      kwargs4conn = {'delay' : 1e9/182, # in ns. Corresponds to rate of 182Hz
                     'state4distribution' : werner_state(F_werner)}

Step 3: creating a DQC network
------------------------------

Step 3 brings everything together using one more Class,
`DQC`, which links together copies of the specified
`QPU` using copies of the specified `Connection`. Lets bring everything 
together and see `DQC` in action: ::

      import itertools as it

      from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
      from dqc_simulator.hardware.dqc_creation import DQC
      from dqc_simulator.hardware.quantum_processors import NoisyQPU
      from dqc_simulator.qlib.states import werner_state

      # Defining QPU
      qpu_class = NoisyQPU
      kwargs4qpu = {'p_depolar_error_cnot' : 1e-03,
                     'single_qubit_gate_error_prob' : 2e-05,
                     'meas_error_prob' : 3e-03,
                     'comm_qubit_depolar_rate' : 0.06,
                     'proc_qubit_depolar_rate' : 0.05,
                     'single_qubit_gate_time' : 135 * 10**3,
                     'two_qubit_gate_time' : 600 * 10**3,
                     'measurement_time' : 600 * 10**4, 
                     'num_positions' : 10,
                     'num_comm_qubits' : 2}

      # Defining connection
      entangling_connection_class = BlackBoxEntanglingQsourceConnection
      F_werner = 0.9
      kwargs4conn = {'delay' : 1e9/182, #in ns
                     'state4distribution' : werner_state(F_werner)}

      num_qpus = 3
      quantum_topology = [(0, 1)]
      classical_topology = list(it.combinations(range(3), 2))
      dqc = DQC(entangling_connection_class, num_qpus,
                  quantum_topology, classical_topology,
                  qpu_class=qpu_class,
                  **kwargs4qpu, **kwargs4conn)

This creates a distributed quantum computer (`DQC`) with three 
QPUs, two of which are connected by an entangling connection 
over which ebits can be distributed. All of the qubits are 
connected classically. Alternative network topologies can 
be specified by changing the `quantum_topology` and 
`classical_topology` arguments.

Behind the scenes, QPUs have been assigned to network nodes
which conventionally have the names 'node_ii' for where `ii`
is an integer between 0 and `num_qpus` - 1. These nodes 
can be accessed using the `DQC.nodes` attribute.

Creating the software
=====================

Now we have the hardware made, we want to make some software 
to run on it. `dqc_simulator` facilitates two ways of specifying
distributed quantum circuits: either a pre-partioned circuit can be specified
or a monolithic quantum circuit can be specified, which will be 
partitioned for you. We will start with the former option.

Partitioned circuit
-------------------

Specifying a partitioned circuit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Partitioned quantum circuits are specified as lists of gate
tuples. The following types of tuples are allowed:

1. **For single-qubit gate**: (`gate_instr`, `qubit_index`, `node_name`)
2. **For local two-qubit gate**: (`gate_instr`, `qubit_index0`, `node_name0`, `qubit_index1`,
                                  `node_name1`)
3. **For remote two-qubit gate**: (`gate_instr` or `gate_instrs`, `qubit_index0`, 
                                   `node_name0`, `qubit_index1`, `node_name1`, `scheme`)

where

* `gate_instr` : `netsquid.components.instructions.Instruction`
   The quantum gate to use. For the `NoisyQPU` defined earlier, 
   the allowed instructions are:

   * `netsquid.components.instructions.INSTR_INIT` which initialises a qubit or qubits,
     each in the state :math:`|0\rangle`. 
   * `netsquid.components.instructions.INSTR_H` : the Hadamard gate.
   * `netsquid.components.instructions.INSTR_X` : the Pauli X gate.
   * `netsquid.components.instructions.INSTR_Z` : the Pauli Z gate.
   * `netsquid.components.instructions.INSTR_S` : the S, or phase, gate.
   * `dqc_simulator.qlib.gates.INSTR_S_DAGGER` : the hermitian conjugate of the S gate.
   * `netsquid.components.instructions.INSTR_T` : the T gate, or :math:`\frac{\pi}{8}`, gate.
   * `dqc_simulator.qlib.gates.INSTR_T_DAGGER` : the hermitian conjugate of the T gate.
   * `netsquid.components.instructions.INSTR_CNOT` : the CNOT gate.
   * `netsquid.components.instructions.INSTR_CZ` : the CZ gate.
   * `netsquid.components.instructions.INSTR_MEASURE` : a computational basis measurement
   * `dqc_simulator.qlib.gates.INSTR_SINGLE_QUBIT_UNITARY` : which allows advanced users 
      to specify an arbitary single remote gate by specifying an 
      operation. See `netsquid.components.qprogram.QuantumProgram.apply`.   
   * `netsquid.components.instructions.INSTR_SWAP`. The SWAP gate. This is implemented 
      using three CNOT gates. See Fig. 1.7 of Ref. [1]_.
   * `dqc_simulator.qlib.gates.INSTR_TWO_QUBIT_UNITARY` : similar to
     `INSTR_SINGLE_QUBIT_UNITARY` but for two qubit gates.
   * `dqc_simulator.qlib.gates.INSTR_SINGLE_QUBIT_NEGLIBIBLE_TIME` : similar to 
     `INSTR_SINGLE_QUBIT_UNITARY` but for ideal and almost instantaneous single-qubit gates.
   * `dqc_simulator.qlib.gates.INSTR_TWO_QUBIT_NEGLIGIBLE_TIME` : similar to 
     `INSTR_SINGLE_QUBIT_NEGLIBIBLE_TIME` but for two qubit gates.

* `qubit_index` or `qubit_index_ii` for :math:`ii \in \{0, 1\}` : int or list of int
      The index of qubit to act the gate instruction on. If the `gate_instr` is 
      `instr.INSTR_INIT` a list of qubits can be used. Communication qubits are 
      specified with the index -1. The interpreter discussed in the next section 
      will automatically handle which communication qubits are used.
* `node_name` or `node_name_ii` : str
   The QPU node to act on. This is the QPU node where the qubit specified by the 
   preceding `qubit_index` resides.
* `scheme` : str
   The type of remote gate to use. The options are: 'cat', '1tp', '2tp', 'tp_safe'. See Fig. 
   2 of Ref. [2]_ for more details. 'cat' and 'TP-safe' are often alternatively referred to as 
   'telegate' and 'teledata', respectively in the literature. Be aware that '1tp' and '2tp'
   do not leave qubits where they started off.
* 'gate_instrs' : list of tuples
   Local gates that should applied during a remote gate prior to disentangling for 
   'cat' or teleporting back for 'tp_safe'. This allows compound remote gates to be 
   defined. The tuples should have the form specified for type 1 or type 2 gate tuples 
   defined above (ie, for local single or two-qubit gates).

Running a partitioned circuit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the partitioned circuit has been specified, it is easy to run. `dqc_simulator` 
defines an interpreter for pre-partitioned circuits called `DQCMasterProtocol`.

If we create the hardware as above, we can run a quantum circuit on it as follows: ::

      import netsquid as ns
      from netsquid.components import instructions as instr

      from dqc_simulator.software.dqc_control import DQCMasterProtocol

      # Defining the gates 
      gate_tuples = [(instr.INSTR_INIT, range(2, 5), 'node_0'),
                     (instr.INSTR_INIT, range(2, 5), 'node_1'),
                     (instr.INSTR_INIT, range(2, 5), 'node_2'),
                     (instr.INSTR_H, 2, 'node_0'),
                     (instr.INSTR_CNOT, 2, 'node_0', 2, 'node_1', 'cat')]

      # Running the circuit
      protocol = DQCMasterProtocol(gate_tuples, nodes=dqc.nodes)
      protocol.start()
      ns.sim_run()

This has run the simulation but right now we have not taken any results. Users 
familiar with NetSquid will know that we can see the changes we have made 
by inspecting the hardware. See the NetSquid 
`tutorial <https://docs.netsquid.org/latest-release/tutorial.intro.html>`_. However,
as NetSquid users will also know, this is not necessary. We will explore how to 
take simulation results in a :ref:`later section <taking_simulation_results>`.

Starting with a monolithic circuit
----------------------------------

.. todo::

   Write this section. Only the first step of the above will change (ie, how the 
   gate_tuples are arrived at behind the scenes.)

.. _taking_simulation_results:

Taking simulation results 
=========================

For simple experiments, in which we only want to know the output fidelity of a 
quantum circuit relative to the ideal case, we can use the 
`dqc_simulator.util.helper.get_data_collector` function. This creates a 
`netsquid.util.datacollector.DataCollector` object already set-up to take fidelity 
results at the end of the experiment. Using the interpreter protocol and hardware we 
defined previously,  it is set up as follows :: 

      import numpy as np

      from dqc_simulator.util.helper import get_data_collector

      # Retrieving QPU nodes from DQC
      node_0 = dqc.get_node('node_0')
      node_1 = dqc.get_node('node_1')

      qubit_indices_2b_checked = [(2, node_0), (2, node_1)]
      desired_state = np.sqrt(1/2) * np.array([[1],[0], [0], [1]])
      dc = get_data_collector(protocol, qubit_indices_2b_checked,
                              desired_state)

.. note::

   Users familiar with NetSquid can take more abitrary results by defining their 
   own `netsquid.util.datacollector.DataCollector`. As the name suggests, 
   the interpreter, `DQCMasterProtocol` is simply a subclass of 
   `netsquid.protocols.protocol.Protocol` (or more precisely 
   `netsquid.protocols.nodeprotocols.LocalProtocol`) and so it will send a 
   `netsquid.protocols.protocol.Signals.FINISHED` signal when the distributed 
   quantum circuit has finished running, which can be used to trigger the 
   collection of data.

This would check that the experiment that we defined earlier does produce the 
desired Bell state between qubit 2 on node_0 and node_1. It's worth knowing that 
NetSquid does provide a variety of predefined states in their 
`netsquid.qubits.ketstates` module, which can save time when defining the 
`desired_state` variable.

To access the collected results we can simply use the 
`DataCollector.dataframe` attribute to retrieve a `pandas.DataFrame`, ie: ::

      results = dc.dataframe

If you do not know how to use pandas and do not wish to learn then I suggest 
simply specifying a `filename` (including the path to reach that file) as as a string and
exporting to an Excel file or csv as follows: ::

      # For exporting to Excel
      filename = '<path>/results.xlsx' # replace <path> with desired path to file
      results.to_excel(filename)

      # For exporting to csv
      filename = '<path>/results.csv'
      results.to_csv(filename)

Running a full experiment
=========================

We now have all the tools needed to simulate an arbitary distributed quantum 
circuit on emulated DQC hardware. Lets bring everything that we have learned 
together to run a quantum experiment and take results for it: ::

   import itertools as it

   import netsquid as ns
   from netsquid.components import instructions as instr
   from netsquid.qubits.qformalism import QFormalism
   import numpy as np

   from dqc_simulator.hardware.connections import BlackBoxEntanglingQsourceConnection
   from dqc_simulator.hardware.dqc_creation import DQC
   from dqc_simulator.hardware.quantum_processors import NoisyQPU
   from dqc_simulator.qlib.states import werner_state
   from dqc_simulator.software.dqc_control import DQCMasterProtocol
   from dqc_simulator.util.helper import get_data_collector

   # Setting the formalism used to the density matrix formalism
   ns.set_qstate_formalism(QFormalism.DM)

   # Restting the state of the simulation (this is good practice)
   ns.sim_reset()

   # Defining QPU
   qpu_class = NoisyQPU
   kwargs4qpu = {'p_depolar_error_cnot' : 1e-03,
                  'single_qubit_gate_error_prob' : 2e-05,
                  'meas_error_prob' : 3e-03,
                  'comm_qubit_depolar_rate' : 0.06,
                  'proc_qubit_depolar_rate' : 0.05,
                  'single_qubit_gate_time' : 135 * 10**3,
                  'two_qubit_gate_time' : 600 * 10**3,
                  'measurement_time' : 600 * 10**4,
                  'num_positions' : 10,
                  'num_comm_qubits' : 2}

   # Defining connection
   entangling_connection_class = BlackBoxEntanglingQsourceConnection
   F_werner = 0.9
   kwargs4conn = {'delay' : 1e9/182, #in ns
                  'state4distribution' : werner_state(F_werner)}

   # Setting up the hardware
   num_qpus = 3
   quantum_topology = [(0, 1)]
   classical_topology = list(it.combinations(range(3), 2))
   dqc = DQC(entangling_connection_class, num_qpus,
               quantum_topology, classical_topology,
               qpu_class=qpu_class,
               **kwargs4qpu, **kwargs4conn)

   # Retrieving QPU nodes from DQC
   node_0 = dqc.get_node('node_0')
   node_1 = dqc.get_node('node_1')
   node_2 = dqc.get_node('node_2')

   # Identifying the processing qubits that we wish to initialise
   qubits0 = node_0.qmemory.processing_qubit_positions[0:3]
   qubits1 = node_1.qmemory.processing_qubit_positions[0:3]
   qubits2 = node_2.qmemory.processing_qubit_positions[0:3]

   # Defining the gates
   gate_tuples = [(instr.INSTR_INIT, qubits0, node_0.name),
                  (instr.INSTR_INIT, qubits1, node_1.name),
                  (instr.INSTR_INIT, qubits2, node_2.name),
                  (instr.INSTR_H, qubits0[0], node_0.name),
                  (instr.INSTR_CNOT, qubits0[0], node_0.name, qubits1[0], node_1.name, 'cat')]

   # Setting up the software
   protocol = DQCMasterProtocol(gate_tuples, nodes=dqc.nodes)

   # Preparing data collection
   qubit_indices_2b_checked = [(qubits0[0], node_0), (qubits1[0], node_1)]
   desired_state = np.sqrt(1/2) * np.array([[1],[0], [0], [1]])
   dc = get_data_collector(protocol, qubit_indices_2b_checked,
                           desired_state)

   # Running the circuit
   protocol.start()
   ns.sim_run()

   results = dc.dataframe
   print(results)
   # Expected output: 0.8922410631572217

There we have it! We have simulated a distributed quantum circuit on noisy hardware 
and ascertained the output fidelity of the result.

You may have noticed that a few tweaks and additions have been made relative to the 
previous sections. The first of these is that we have set the quantum formalism used, 
with the code: ::

   import netsquid as ns
   from netsquid.qubits.qformalism import QFormalism

   ns.set_qstate_formalism(QFormalism.DM)

One of the advantages of NetSquid is that it is 
formalism agnostic and so in general, the same hardware and software can be evaluated
using very different representations of the quantum state behind the scenes. Here,
we have chosen to use the density matrix formalsim instead of the default ket vector 
representation. Also available are the stabiliser formalism and graph states with 
local cliffords, as well as a different implemention of the density matrix formalism 
using sparse clifford gates. See the NetSquid `documentation <https://docs.netsquid.org/latest-release/api_qubits/netsquid.qubits.qformalism.html#netsquid.qubits.qformalism.QFormalism>`_
for more details.  

dqc_simulator aims to retain this formalism agnostic approach where possible however, 
sometimes it is convenient to specialise to a specific formalism, so that the interface
is simpler. This was done implicitly when specifying the hardware above as 
`BlackBoxEntanglingQsourceConnection` is intended to distribute ebits whose 
state is specified in the density matrix formalism without worrying about the 
physical details of how this state would be produced. Alternative options can be 
found in the `dqc_simulator.hardware.connections` module.

.. todo::

   Refactor things in the connections module that appear only as functions to classes.
   Will need to retain the unpythonic functions for backwards compatability although maybe
   not for a public facing fork of the simulator.

The other big change relative to previous code is that we have used more attributes of the 
hardware to make keeping track of which qubits are processing qubits much easier. 
Specifically, we used the code: ::

   # Retrieving QPU nodes from DQC
   node_0 = dqc.get_node('node_0')
   node_1 = dqc.get_node('node_1')
   node_2 = dqc.get_node('node_2')

   # Identifying the processing qubits that we wish to initialise
   qubits0 = node_0.qmemory.processing_qubit_positions[0:3]
   qubits1 = node_1.qmemory.processing_qubit_positions[0:3]
   qubits2 = node_2.qmemory.processing_qubit_positions[0:3]

The first code block retrieves the network nodes containing the QPUs while 
the second block accesses the QPUs directly using the `netsquid.nodes.node.Node.qmemory`
attribute to retrieve the QPU and then retrieves the positions of the processing 
qubits for each QPU, as discussed in the hardware section above. Notice that at no 
points was it necessary to worry about what the communication qubits are doing. This 
is a general feature of the 'cat' and 'tp_safe' schemes and greatly simplifies many
simulations. Achieving this functionality was one of the motivations for creating
the dqc_simulator package.




.. warning::

   Due to a `bug <https://forum.netsquid.org/viewtopic.php?t=1185>`_ in NetSquid itself, 
   which causes certain NetSquid objects to not be correctly garbage collected, 
   repeated simulations within the same call to the Python interpreter can eat up more and
   more RAM. This typically is not noticeable but can cause larger simulations to crash
   and you may also notice that the time taken to repeat the same experiment does not
   always scale linearly. The developers of NetSquid have been informed of the bug, but, 
   for until the bug is fixed, I go through a workaround in the next section.

Repeated simulation runs
========================




References
----------

.. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
       Information, 10th ed. (Cambridge University Press, 2010).
.. [2] K Campbell, A Lawey and M Razavi, Quantum data centres: a simulation-based 
       comparative noise analysis, Quantum Science and Technology, 10, 015052,
       DOI: 10.1088/2058-9565/ad9cb8

.. todo::
    
    Finish.

