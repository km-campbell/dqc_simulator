dqc\_simulator.software
=======================

Everything needed to define, compile, and interpret quantum circuits
on a distributed quantum computer. 

This includes the capacity to parse openQASM 2.0 files for arbitrary 
monolithic quantum circuits, partition them then interpret them in a 
form the underlying NetSquid backend can understand or define 
pre-partitioned distributed quantum circuits and interpret those.

.. todo::

   Could potentially change way control qubits are managed using
   :attr: `~netsquid.components.qmemory.MemoryPosition.in_use`
   flag and corresponding `pydynaa` events. Could also 
   make use of `~netsquid-qrepchain.processing_nodes.CommunicationMemoryManager`.
   Finally, the modules related to parsing should potentially be moved.


.. toctree::
   :caption: Modules
   :maxdepth: 2

   software/dqc_simulator.software.ast2dqc_circuit
   software/dqc_simulator.software.compiler_preprocessing
   software/dqc_simulator.software.compilers
   software/dqc_simulator.software.dqc_circuit
   software/dqc_simulator.software.dqc_control
   software/dqc_simulator.software.link_layer
   software/dqc_simulator.software.partitioner
   software/dqc_simulator.software.physical_layer
   software/dqc_simulator.software.qasm2ast
   software/dqc_simulator.software.transpiler
