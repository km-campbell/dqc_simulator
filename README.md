# dqc_simulator

## An easy-to-use distributed quantum computing simulator

With many simulators, specifying a quantum algorithm is
as easy as specifying a quantum circuit. Why can't
things be as simple for distributed quantum computers (DQCs)?
With dqc_simulator they can! A python package built on top of the more
general quantum network simulation library
[NetSquid](https://netsquid.org/), dqc_simulator allows
users to simply simulate quantum circuits on
near-arbitrary, user-specifiable DQC hardware. The package aims to retain the
flexibility and power of [NetSquid](https://netsquid.org/)
while automatically handling some of the messier details of applying
[NetSquid](https://netsquid.org/) to the DQC setting.

Key features:

1. Easy-to-use interface for specifying distributed
   quantum circuits.
2. Automatic partitioning of monolithic (single-processor)
   quantum circuits
   between quantum processing units (QPUs). Arbitrary
   algorithms for doing this can be specified by the user
   if desired, using the DQC circuit interface. Circuits
   can be specified as a list of tuples or as a .qasm
   file.
3. Automatic management of remote gates and communication
   qubits.
4. Automatic compilation using pre-made compilers. The user
   can also easily specify their own.

### Requirements

* python 3.9
* NetSquid 1.1.7. See [NetSquid](https://netsquid.org/).
* NetSquid-PhysLayer 4.3.0. See [link](https://docs.netsquid.org/snippets/netsquid-physlayer/).

The remaining requirements can be found on pypi and are in the requirements.txt file.

### Installation instructions for users

First, install NetSquid version 1.1.7 using the instructions on 
[NetSquid](https://netsquid.org/). This will require creating a NetSquid 
account.

Then install the requirements using the command 

```
pip install -r requirements.txt
```

Finally, the package itself can be installed.
It is intended to make this package available on PyPi in the near future. 
For now, please access directly from this repository using the command

```
pip install git+https://github.com/km-campbell/dqc_simulator.git
```

To edit the package or have access to the documentation use 

```
git clone https://github.com/km-campbell/dqc_simulator.git
```

### Documentation

The documentation is available via readthedocs [here]<https://km-campbell-dqc-simulator.readthedocs.io/en/latest/>

Alternatively, the project documentation can be built locally by cloning the repository, 
as detailed above, and then using the commands 

```
cd docs
make html
```

A version of the documentation will then be available in the docs/build directory.
Within that directory open index.html to access the documentation.

### Known issues

In addition, to anything listed in the issues section of the repo, the following issues exist.

* Some tests are implemented within a separate private repository as they pertain to
  specific experiments. Equivalent tests need to be added here.
* The documentation is incomplete and some docstrings require updating.


## Acknowledgements

I acknowledge the use of modified code from nuqasm2 in the qasm2ast module 
subject to the Apache 2.0 license included above under the name
LICENSE4qasm2ast_base_code. It is explicitly stated in any modules where modified nuqasm2 code is used.

