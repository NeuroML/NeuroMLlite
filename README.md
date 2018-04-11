### NeuroMLlite: a common framework for reading/writing/generating network specifications

Work in progress. Moved from https://github.com/NeuroML/NetworkShorthand/tree/master/proposal.

![Architecture](images/NetworkShorthand.png)

The best way to see the currently proposed structure is to look at the examples

#### Ex. 1: Simple network, 2 populations & projection
[JSON](examples/Example1_TestNetwork.json) | [Python script](examples/Example1.py)

Can be exported to:
- **NeuroML 2** (XML or HDF5 format)

#### Ex. 2: Simple network, 2 populations, projection & inputs
[JSON](examples/Example2_TestNetwork.json) | [Python script](examples/Example2.py) | [Generated NeuroML2](examples/Example2_TestNetwork.net.nml)

Can be exported to:
- **NeuroML 2** (XML or HDF5 format)

#### Ex. 3: As above, with simulation specification
[JSON for network](examples/Example3_Network.json) | [JSON for simulation](examples/SimExample3.json) | [Python script](examples/Example3.py) | [Generated NeuroML2](examples/Example3_Network.net.nml) | [Generated LEMS](examples/LEMS_SimExample3.xml)

Can be exported to:
- **NeuroML 2** (XML or HDF5 format)

Can be simulated using:
- **NetPyNE**
- **jNeuroML**
- **NEURON** generated from **jNeuroML**
- **NetPyNE** generated from **jNeuroML**


#### Ex. 4: A network with PyNN cells & inputs
[JSON](examples/Example4_PyNN.json) | [Python script](examples/Example4.py) | [Generated NeuroML2](examples/Example4_PyNN.net.nml) 

Can be exported to:
- **NeuroML 2** (XML or HDF5 format)

Can be simulated using:
- **NEST** via **PyNN**
- **NEURON** via **PyNN**
- **Brian** via **PyNN**
- **jNeuroML**
- **NEURON** generated from **jNeuroML**
- **NetPyNE** generated from **jNeuroML**


#### Ex. 5: A network with the Blue Brain Project connectivity data 
[JSON](examples/BBP_5percent.json) | [Python script](examples/Example5.py) 

Can be exported to:
- **NeuroML 2** (XML or HDF5 format)

Can be simulated using:
- **NetPyNE**

[![Build Status](https://travis-ci.org/NeuroML/NeuroMLlite.svg?branch=master)](https://travis-ci.org/NeuroML/NeuroMLlite)