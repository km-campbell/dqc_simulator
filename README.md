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

Note that the index is needed to install the NetSquid requirement. For uv this it will be necessary to include the index every time that the virtual environment is updated. So, for example when running `uv add` or the first `uv run` after adding a new dependency with `uv add`, even if that dependency is not needed for the package being installed.

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

I acknowledge the use of modified code from nuqasm2 in the qasm2ast module subject to the Apache 2.0 license included above under the name LICENSE4qasm2ast_base_code. It is explicitly stated in any modules where modified nuqasm2 code is used. In my `examples` file, which contains some examples of how dqc_simulator can be used, I acknowledge the use of the .qasm and .inc files from the source code for MQT bench (https://github.com/munich-quantum-toolkit/bench.git). All .qasm and .inc files are sourced from there. More details about MQT bench can be found in the paper: "N Questslich, L Burgholzer and R Wille, MQT Bench: benchmarking software and design automation tools for quantum computing, Quantum, 7, 1062 (2023)".

In my `examples` file, which contains some examples of how dqc_simulator can be used, I acknowledge the use of the `ghz_indep_qiskit_5.qasm` and `qelib1.inc` files from the source code for MQT bench (https://github.com/munich-quantum-toolkit/bench.git). More details about MQT bench can be found in the paper: "N Questslich, L Burgholzer and R Wille, MQT Bench: benchmarking software and design automation tools for quantum computing, Quantum, 7, 1062 (2023)".

I also acknowledge the use of the processify function, which was created by [schlamar](https://gist.github.com/schlamar/2311116) and appears with minor modifications to the error handling in my dqc_simulator.util.helper module. The function is intended to be used as a workaround for a memory leak in NetSquid itself. The leak has been reported to the NetSquid developers but as NetSquid is closed source, I am unable to fix the leak myself. More info on processify is available here [here](https://ys-l.github.io/posts/2015/10/03/processifying-bulky-functions-in-python). The version of processify I used was obtained from the skywalker module by [dgerosa](https://github.com/dgerosa/skywalker.git) with DOI https://zenodo.org/records/15511604. 