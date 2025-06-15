Getting started
===============

Welcome to the getting started guide for absolute beginners to using
dqc_simulator! This guide assumes that you have already installed 
dqc_simulator and its prerequisites on your system. If this is not 
the case, please follow the 
:doc:`installation instructions <installation>`. This guide also assumes  
a working knowledge of quantum computing and quantum information. 
If this is not the case, I recommend Nielsen and Chuang's excellent
introductory text [1]_.

dqc_simulator is a python package for the simple simulation of 
distributed quantum computers (DQCs). It is built on top of the
`NetSquid <https://netsquid.org/>`_ library but does not require 
a detailed understanding of NetSquid to use. That said, users that 
are more familiar with NetSquid can easily integrate the package 
into their existing workflow if they wish to consider more complicated
scenarios, such as error detection, or specify their own hardware in 
more detail. 

This guide will take you through the main ideas of dqc_simulator and 
take you through building your first DQC simulation experiment.

Why use dqc_simulator?
----------------------

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
-----------------------

dqc_simulator can be imported into python code with the line: ::

       import dqc_simulator

Creating the hardware
---------------------

Hardware specification can be done in three easy stages:

1. Specify a QPU
2. Specify a quantum connection
3. Create the network

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
it is possible for our hardware to handle. 

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
rate of :math:`0.06`Hz on the communication qubits and 
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

Creating the software
---------------------


References
----------

.. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
       Information, 10th ed. (Cambridge University Press, 2010).

.. todo::
    
    Finish.

