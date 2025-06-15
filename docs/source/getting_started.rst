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
3. Specify the network

For step 1, a handy pre-built function is provided. Lets use it to create a 
processor: ::

      from dqc_simulator.hardware.quantum_processors import create_noisy_qpu
      qpu = create_noisy_qpu()

This QPU has two types of qubit: communication qubits, which 
are used to host ebits, and processing qubits, which are used in 
the same way as qubits on a monolithic processor. We can specify
the maximum number of communication qubits that our QPU can hold
with the `num_comm_qubits` keyword argument and the total number 
of qubits (including communication and processing qubits) using
`num_positions`. Ie, ::

   qpu = create_noisy_qpu(num_comm_qubits=2,
                          num_positions=10)

Creates a processor with space for 2 comm-qubits and 8 processing 
qubits, making 10 total qubits. This allows us to constrain what 
it is possible for our hardware to handle. 

By default all noise is turned off and the QPU is ideal. However,
adding noise is as simple as choosing keyword arguments in the 
above function. For example: ::

   qpu = create_noisy_qpu(
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
However, we will need to provide the function we wish to 
use to create a `QPU` and the parameters we want. This 
will look something like: ::

      qpu_func = create_noisy_qpu
      params4qpu_func = {'p_depolar_error_cnot' : 1e-03,
                        'single_qubit_gate_error_prob' : 2e-05,
                        'meas_error_prob' : 3e-03,
                        'comm_qubit_depolar_rate' : 0.06,
                        'proc_qubit_depolar_rate' : 0.05,
                        'single_qubit_gate_time' : 135 * 10**3,
                        'two_qubit_gate_time' : 600 * 10**3,
                        'measurement_time' : 600 * 10**4, 
                        'num_positions' : 10,
                        'num_comm_qubits' : 2}

Step 2 is very similar. This time there are a few functions to 
choose from. We will focus here on
 `create_bb_elink`, which is 
 recommended for those new to the package, who wish to work in 
 the densitry matrix formalism. This creates a connection 
 object, which is essentially a black box source of entangled 
 ebits between QPUs, where the ebits can be in any two-qubit state
 specified in the density matrix formalism. For typical and simple modelling 
 of noisy ebits, I recommend the `werner_state` function. 
 Lets see what this will look like: ::

      from dqc_simulator.hardware.connections import create_bb_elink
      from dqc_simulator.qlib.states import werner_state
      F_werner = 0.9 # The Werner state fidelity
      ent_dist_rate = 182 # Hz
      elink_func = create_bb_elink
      params4elink_func = { 
         'state4distribution': werner_state(F_werner), 
         'ent_dist_rate': ent_dist_rate}
      
Step 3 brings everything together using one more function,
`create_dqc_network`, which links together copies of the specified
QPU using copies of the specified connection. Lets bring everything 
together and see `create_dqc_network` in action: ::

      import itertools as it

      dqc = create_dqc_network(create_entangling_link=elink_func,
                               custom_qpu_func=qpu_func,
                               **params4qpu_func,
                               **params4_elink_func,
                               num_qpus=3
                               classical_topology=[list(it.combinations(range(3), 2))],
                               quantum_topology=[(0, 1)])




.. todo::

   Make things work more using instantiated QPU objects and 
   connection objects. This is more pythonic and readable. For backwards 
   commpatability, what is already there can be retained too.







References
----------

.. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
       Information, 10th ed. (Cambridge University Press, 2010).

.. todo::
    
    Finish.

