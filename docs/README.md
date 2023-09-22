# Specification of NeuroMLlite v0.5.8
**Note: the NeuroMLlite specification is still in development! Subject to change...**

## Network
A Network containing multiple Population's, connected by Projection's and receiving Input's

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for the Network</i></td>
 </tr>


  <tr>
    <td><b>parameters</b></td>
    <td>Any</td>
    <td><i>Dictionary of global parameters for the network</i></td>
 </tr>


  <tr>
    <td><b>version</b></td>
    <td>str</td>
    <td><i>Information on verson of NeuroMLlite</i></td>
 </tr>


  <tr>
    <td><b>seed</b></td>
    <td>int</td>
    <td><i>Seed for random number generator used when building network</i></td>
 </tr>


  <tr>
    <td><b>temperature</b></td>
    <td>float</td>
    <td><i>Temperature at which to run network (float in deg C)</i></td>
 </tr>


  <tr>
    <td><b>network_reader</b></td>
    <td><a href="#networkreader">NetworkReader</a></td>
    <td><i>A class which can read in a network (e.g. from a structured format)</i></td>
 </tr>


</table>

### Allowed children
<table>
  <tr>
    <td><b>cells</b></td>
    <td><a href="#cell">Cell</a></td>
    <td><i>The Cells which can be present in Populations</i></td>
  </tr>


  <tr>
    <td><b>synapses</b></td>
    <td><a href="#synapse">Synapse</a></td>
    <td><i>The Synapse definitions which are used in Projections</i></td>
  </tr>


  <tr>
    <td><b>input_sources</b></td>
    <td><a href="#inputsource">InputSource</a></td>
    <td><i>The InputSource definitions which define the types of stimulus which can be applied in Inputs</i></td>
  </tr>


  <tr>
    <td><b>regions</b></td>
    <td><a href="#rectangularregion">RectangularRegion</a></td>
    <td><i>The Regions in which Populations get placed.</i></td>
  </tr>


  <tr>
    <td><b>populations</b></td>
    <td><a href="#population">Population</a></td>
    <td><i>The Populations of Cells making up this network ...</i></td>
  </tr>


  <tr>
    <td><b>projections</b></td>
    <td><a href="#projection">Projection</a></td>
    <td><i>The Projections between Populations</i></td>
  </tr>


  <tr>
    <td><b>inputs</b></td>
    <td><a href="#input">Input</a></td>
    <td><i>The inputs to apply to the elements of Populations</i></td>
  </tr>


</table>

## NetworkReader
A NetworkReader definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>type</b></td>
    <td>str</td>
    <td><i>The type of NetworkReader</i></td>
 </tr>


  <tr>
    <td><b>parameters</b></td>
    <td>Any</td>
    <td><i>Dictionary of parameters for the NetworkReader</i></td>
 </tr>


</table>

## Cell
A Cell definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this Cell</i></td>
 </tr>


  <tr>
    <td><b>parameters</b></td>
    <td>Any</td>
    <td><i>Dictionary of parameters for the cell</i></td>
 </tr>


  <tr>
    <td><b>neuroml2_source_file</b></td>
    <td>str</td>
    <td><i>File name of NeuroML2 file defining the cell</i></td>
 </tr>


  <tr>
    <td><b>lems_source_file</b></td>
    <td>str</td>
    <td><i>File name of LEMS file defining the cell</i></td>
 </tr>


  <tr>
    <td><b>neuroml2_cell</b></td>
    <td>str</td>
    <td><i>Name of standard NeuroML2 cell type</i></td>
 </tr>


  <tr>
    <td><b>pynn_cell</b></td>
    <td>str</td>
    <td><i>Name of standard PyNN cell type</i></td>
 </tr>


  <tr>
    <td><b>arbor_cell</b></td>
    <td>str</td>
    <td><i>Name of standard Arbor cell type</i></td>
 </tr>


  <tr>
    <td><b>bindsnet_node</b></td>
    <td>str</td>
    <td><i>Name of standard BindsNET node</i></td>
 </tr>


</table>

## Synapse
A Synapse definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this Synapse</i></td>
 </tr>


  <tr>
    <td><b>parameters</b></td>
    <td>Any</td>
    <td><i>Dictionary of parameters for the synapse</i></td>
 </tr>


  <tr>
    <td><b>neuroml2_source_file</b></td>
    <td>str</td>
    <td><i>File name of NeuroML2 file defining the synapse</i></td>
 </tr>


  <tr>
    <td><b>lems_source_file</b></td>
    <td>str</td>
    <td><i>File name of LEMS file defining the synapse</i></td>
 </tr>


  <tr>
    <td><b>pynn_synapse_type</b></td>
    <td>str</td>
    <td><i>The pynn synapse type. Valid values are: "curr_exp", "curr_alpha", "cond_exp", "cond_alpha".</i></td>
 </tr>


  <tr>
    <td><b>pynn_receptor_type</b></td>
    <td>str</td>
    <td><i>The pynn receptor type. Valid values are: "excitatory", "inhibitory".</i></td>
 </tr>


</table>

## InputSource
An InputSource definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this InputSource</i></td>
 </tr>


  <tr>
    <td><b>parameters</b></td>
    <td>Any</td>
    <td><i>Dictionary of parameters for the InputSource</i></td>
 </tr>


  <tr>
    <td><b>neuroml2_source_file</b></td>
    <td>str</td>
    <td><i>File name of NeuroML2 file defining the input source</i></td>
 </tr>


  <tr>
    <td><b>neuroml2_input</b></td>
    <td>str</td>
    <td><i>Name of standard NeuroML2 input</i></td>
 </tr>


  <tr>
    <td><b>lems_source_file</b></td>
    <td>str</td>
    <td><i>File name of LEMS file defining the input source</i></td>
 </tr>


  <tr>
    <td><b>pynn_input</b></td>
    <td>str</td>
    <td><i>Name of PyNN input</i></td>
 </tr>


</table>

## RectangularRegion
A RectangularRegion definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this rectangular region.</i></td>
 </tr>


  <tr>
    <td><b>x</b></td>
    <td>float</td>
    <td><i>x coordinate of corner of region</i></td>
 </tr>


  <tr>
    <td><b>y</b></td>
    <td>float</td>
    <td><i>y coordinate of corner of region</i></td>
 </tr>


  <tr>
    <td><b>z</b></td>
    <td>float</td>
    <td><i>z coordinate of corner of region</i></td>
 </tr>


  <tr>
    <td><b>width</b></td>
    <td>float</td>
    <td><i>width of the rectangular region</i></td>
 </tr>


  <tr>
    <td><b>height</b></td>
    <td>float</td>
    <td><i>height of the rectangular region</i></td>
 </tr>


  <tr>
    <td><b>depth</b></td>
    <td>float</td>
    <td><i>depth of the rectangular region</i></td>
 </tr>


</table>

## Population
A Population definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this Population</i></td>
 </tr>


  <tr>
    <td><b>size</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>The size of the population.</i></td>
 </tr>


  <tr>
    <td><b>component</b></td>
    <td>str</td>
    <td><i>The type of Cell to use in this population.</i></td>
 </tr>


  <tr>
    <td><b>properties</b></td>
    <td>Any</td>
    <td><i>A dictionary of properties (metadata) for this population.</i></td>
 </tr>


  <tr>
    <td><b>random_layout</b></td>
    <td><a href="#randomlayout">RandomLayout</a></td>
    <td><i>Layout in the random RectangularRegion.</i></td>
 </tr>


  <tr>
    <td><b>relative_layout</b></td>
    <td><a href="#relativelayout">RelativeLayout</a></td>
    <td><i>Position relative to RectangularRegion.</i></td>
 </tr>


  <tr>
    <td><b>single_location</b></td>
    <td><a href="#singlelocation">SingleLocation</a></td>
    <td><i>Explicit location of the one Cell in the population</i></td>
 </tr>


</table>

## RandomLayout
A RandomLayout definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>region</b></td>
    <td>str</td>
    <td><i>Region in which to place population</i></td>
 </tr>


</table>

## RelativeLayout
A RelativeLayout definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>region</b></td>
    <td>str</td>
    <td><i>The Region relative to which population should be positioned.</i></td>
 </tr>


  <tr>
    <td><b>x</b></td>
    <td>float</td>
    <td><i>x position relative to x coordinate of Region</i></td>
 </tr>


  <tr>
    <td><b>y</b></td>
    <td>float</td>
    <td><i>y position relative to y coordinate of Region</i></td>
 </tr>


  <tr>
    <td><b>z</b></td>
    <td>float</td>
    <td><i>z position relative to z coordinate of Region</i></td>
 </tr>


</table>

## SingleLocation
A SingleLocation definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>location</b></td>
    <td><a href="#location">Location</a></td>
    <td><i>Location of the single Cell.</i></td>
 </tr>


</table>

## Location
A Location definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>x</b></td>
    <td>float</td>
    <td><i>x coordinate of location</i></td>
 </tr>


  <tr>
    <td><b>y</b></td>
    <td>float</td>
    <td><i>y coordinate of location</i></td>
 </tr>


  <tr>
    <td><b>z</b></td>
    <td>float</td>
    <td><i>z coordinate of location</i></td>
 </tr>


</table>

## Projection
A Projection definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this Projection</i></td>
 </tr>


  <tr>
    <td><b>presynaptic</b></td>
    <td>str</td>
    <td><i>Presynaptic Population</i></td>
 </tr>


  <tr>
    <td><b>postsynaptic</b></td>
    <td>str</td>
    <td><i>Postsynaptic Population</i></td>
 </tr>


  <tr>
    <td><b>synapse</b></td>
    <td>str</td>
    <td><i>Which Synapse to use</i></td>
 </tr>


  <tr>
    <td><b>pre_synapse</b></td>
    <td>str</td>
    <td><i>For continuous connections, what presynaptic component to use (default: silent analog synapse)</i></td>
 </tr>


  <tr>
    <td><b>type</b></td>
    <td>str</td>
    <td><i>type of projection: projection (default; standard chemical, event triggered), electricalProjection
(for gap junctions) or continuousProjection (for analogue/graded synapses)</i></td>
 </tr>


  <tr>
    <td><b>delay</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Delay to use (default: 0)</i></td>
 </tr>


  <tr>
    <td><b>weight</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Weight to use (default: 1)</i></td>
 </tr>


  <tr>
    <td><b>random_connectivity</b></td>
    <td><a href="#randomconnectivity">RandomConnectivity</a></td>
    <td><i>Use random connectivity</i></td>
 </tr>


  <tr>
    <td><b>convergent_connectivity</b></td>
    <td><a href="#convergentconnectivity">ConvergentConnectivity</a></td>
    <td><i>Use convergent connectivity</i></td>
 </tr>


  <tr>
    <td><b>one_to_one_connector</b></td>
    <td><a href="#onetooneconnector">OneToOneConnector</a></td>
    <td><i>Connect cell index i in pre pop to cell index i in post pop for all i</i></td>
 </tr>


</table>

## RandomConnectivity
A RandomConnectivity definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>probability</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Random probability of connection.</i></td>
 </tr>


</table>

## ConvergentConnectivity
A ConvergentConnectivity definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>num_per_post</b></td>
    <td>float</td>
    <td><i>Number per post-synaptic neuron.</i></td>
 </tr>


</table>

## OneToOneConnector
A OneToOneConnector definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


</table>

## Input
An Input definition.

### Allowed parameters
<table>
  <tr>
    <td><b>notes</b></td>
    <td>str</td>
    <td><i></i></td>
 </tr>


  <tr>
    <td><b>id</b></td>
    <td>str</td>
    <td><i>Unique identifier for this Input</i></td>
 </tr>


  <tr>
    <td><b>input_source</b></td>
    <td>str</td>
    <td><i>Type of input to use in population</i></td>
 </tr>


  <tr>
    <td><b>population</b></td>
    <td>str</td>
    <td><i>Population to target</i></td>
 </tr>


  <tr>
    <td><b>cell_ids</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Specific ids of <a href="#cell">Cell</a>s to apply this input to (cannot be used with percentage</i></td>
 </tr>


  <tr>
    <td><b>percentage</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Percentage of Cells to apply input to</i></td>
 </tr>


  <tr>
    <td><b>number_per_cell</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Number of individual inputs per selected Cell (default: 1)</i></td>
 </tr>


  <tr>
    <td><b>segment_ids</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Which segments to target (default: [0])</i></td>
 </tr>


  <tr>
    <td><b>weight</b></td>
    <td>Union[EvaluableExpression, List, Dict, ndarray, int, float, str]</td>
    <td><i>Weight to use (default: 1)</i></td>
 </tr>


</table>

