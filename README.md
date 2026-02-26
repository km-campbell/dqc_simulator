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
   between quantum processing units (QPUs). 
   * Arbitrary
   algorithms for doing this can also be specified by the user
   if desired, using the DQC circuit interface.
   * Circuits
   can be specified as a list of tuples or as a .qasm
   file.
3. Automatic management of remote gates and communication
   qubits.
4. Automatic compilation using pre-made compilers. 
   * The user
   can also easily specify their own.

### Requirements

* python 3.9
* NetSquid 1.1.7. See [NetSquid](https://netsquid.org/).
* NetSquid-PhysLayer 4.3.0. See [link](https://docs.netsquid.org/snippets/netsquid-physlayer/).
* pyparsing 3.0.9

### Installation instructions for users

Firstly, if you do not already have one, create a NetSquid account using the instructions [here](https://netsquid.org/). Much of the package's functionality 
relies on NetSquid and so this is important to make full use of the package. However, you do not need to actually install NetSquid at this stage because it will be done automatically in the next step. At the end of the NetSquid account creation process you should have a username and 
password. In what follows replace `<USERNAME>` and `<PASSWORD>` with the username and password for your
Netsquid account.

With a NetSquid account created, `dqc_simulator` and all of its dependencies can be installed with the command:
```
pip install --extra-index-url https://<USERNAME>:<PASSWORD>@pypi.netsquid.org dqc_simulator
```
where `<USERNAME>` and `<PASSWORD>` are the username and password for your NetSquid account.

Alternatively, if using [uv](https://docs.astral.sh/uv/), use the command

```
uv add --index https://<USERNAME>:<PASSWORD>@pypi.netsquid.org dqc_simulator
```

If all of the dependencies have already been installed, then you can instead install `dqc_simulator` using the simpler command

```
pip install dqc_simulator
```
because the `--extra-index-url` was only required by the dependencies. `dqc_simulator` in of itself does not require an account.

For uv, the corresponding simpler command is
```
uv add dqc_simulator
```

### Installation instructions for developers

To install the package from source use the command

```
git clone https://github.com/km-campbell/dqc_simulator.git
```

Then install the [uv package manager](https://docs.astral.sh/uv/) onto your system.

Finally, run 

```
uv sync --index https://<USERNAME>:<PASSWORD>@hw.ac.uk
```
where `<USERNAME>` and `<PASSWORD>` are the username and password for your NetSquid account from the root of the cloned repository. This will allow the build to proceed deterministically and allow you to run all code within the virtual environment included in the `dqc_simulator` repo. For more on this, see the uv [documentation](https://docs.astral.sh/uv/).

Note that syncing is actually done, automatically whenever you run code using `uv run` and so it is possible to skip this step, but `uv sync` is a nice check that everything is working properly.

To test that all is working as it should be, you can run:

```
uv run python -m unittest
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

## Contributing

Contributions to dqc_simulator are very welcome. In particular, I strongly encourage users to add any useful circuit identities or circuits, gates and states to the relevant modules of the qlib subpackage, if you think that things you have made for your own work would be useful to others. In this way, we can make DQC research easier and more accessible for everyone.   

## Feature requests

To request a feature please create an issue with and start the issue title with the words "Feature request". I am very open to adding features that others would find useful, when I get the chance. If you believe that you could add the feature yourself, I strongly encourage you to volunteer to do so in the feature request. I will try to get back to you promptly on if I think that the feature would fit in well with dqc_simulator.

## Acknowledgements

I acknowledge the use of modified code from nuqasm2 in the qasm2ast module 
subject to the Apache 2.0 license included above under the name
LICENSE4qasm2ast_base_code. It is explicitly stated in any modules where modified nuqasm2 code is used.

