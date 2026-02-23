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
* pydynaa>=1.0.2

### Installation instructions for users

First, create a NetSquid account using the instructions on 
[NetSquid](https://netsquid.org/). Much of the package's functionality 
relies on NetSquid and so this is important to make full use of the package.

To make your NetSquid account credentials available during package installation, use the commands 

```
export UV_INDEX_NETSQUID_USERNAME=<USERNAME>
export UV_INDEX_NETSQUID_PASSWORD=<PASSWORD>
```
where `<USERNAME>` and `<PASSWORD>` are the username and password for your NetSquid account. You can also store your
NetSquid authentication details using any other method of choice 
compatible with the [uv package manager](https://docs.astral.sh/uv/).

Once your NetSquid authentication credentials are made available, install `dqc_simulator` using the command

```
pip install dqc_simulator
```

### Installation instructions for developers

To install the package from source use the command

```
git clone https://github.com/km-campbell/dqc_simulator.git
```

### Documentation

The documentation is available via readthedocs [here](https://km-campbell-dqc-simulator.readthedocs.io/en/latest/).

Alternatively, the project documentation can be built locally by cloning the repository, 
as detailed above, and then using the commands 

```
cd docs
make html
```

A version of the documentation will then be available in the docs/build directory.
Within that directory open index.html to access the documentation.


## Acknowledgements

I acknowledge the use of modified code from nuqasm2 in the qasm2ast module 
subject to the Apache 2.0 license included above under the name
LICENSE4qasm2ast_base_code. It is explicitly stated in any modules where modified nuqasm2 code is used.

