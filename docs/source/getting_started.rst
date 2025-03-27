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

Importing dqc_simulator
-----------------------

dqc_simulator can be imported into python code with the line: ::

       import dqc_simulator

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
*  **Automatic partitioning of monolithic (single-processor)**
   **quantum circuits between quantum processing units (QPUs).** Arbitrary
   algorithms for doing this can be specified by the user
   if desired, using the DQC circuit interface. Circuits
   can be specified as a list of tuples or as a .qasm
   file.
*  **Automatic management of remote gates and communication qubits.**
*  **Automatic compilation using pre-made compilers.** The user
   can also easily specify their own.

The DQC circuit interface
-------------------------


   
References
----------

.. [1] M. Nielsen and I. Chuang, Quantum Computation and Quantum 
       Information, 10th ed. (Cambridge University Press, 2010).

.. todo::
    
    Finish.

