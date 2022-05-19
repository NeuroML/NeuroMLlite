import collections

__version__ = "0.5.2"

# import pyNN
# import nest

from typing import List, Dict, Any, Optional, Union, Tuple, Callable, TypeVar, Type

import modelspec
from modelspec import optional, instance_of, in_, has, field, fields
from modelspec.base_types import Base, ValueExprType, value_expr_types


def convert2float(x: Any) -> float:
    """Convert to float if not None"""
    if x is not None:
        return float(x)
    else:
        return None


def convert2int(x: Any) -> float:
    """Convert to int if not None"""
    if x is not None:
        return int(x)
    else:
        return None


class NetworkReaderX:
    pop_locations = {}

    def parse(self, handler):
        raise Exception("This needs to be implemented...")

    def get_locations(self):
        return self.pop_locations


@modelspec.define
class NMLBase(Base):
    """Base class for NeuroML objects."""
    notes: str = field(kw_only=True, default=None, validator=optional(instance_of(str)))


@modelspec.define
class Cell(NMLBase):
    """
    A Cell definition.

    Args:
        id: Unique identifier for this Cell
        parameters: Dictionary of parameters for the cell
        neuroml2_source_file: File name of NeuroML2 file defining the cell
        lems_source_file: File name of LEMS file defining the cell
        neuroml2_cell: Name of standard NeuroML2 cell type
        pynn_cell: Name of standard PyNN cell type
        arbor_cell: Name of standard Arbor cell type
        bindsnet_node: Name of standard BindsNET node
    """
    id: str = field(validator=instance_of(str))
    parameters: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    neuroml2_source_file: str = field(default=None, validator=optional(instance_of(str)))
    lems_source_file: str = field(default=None, validator=optional(instance_of(str)))
    neuroml2_cell: str = field(default=None, validator=optional(instance_of(str)))
    pynn_cell: str = field(default=None, validator=optional(instance_of(str)))
    arbor_cell: str = field(default=None, validator=optional(instance_of(str)))
    bindsnet_node: str = field(default=None, validator=optional(instance_of(str)))


@modelspec.define
class Synapse(NMLBase):
    """
    A Synapse definition.

    Args:
        id: Unique identifier for this Synapse
        parameters: Dictionary of parameters for the synapse
        neuroml2_source_file: File name of NeuroML2 file defining the synapse
        lems_source_file: File name of LEMS file defining the synapse
        pynn_synapse_type: The pynn synapse type. Valid values are: "curr_exp", "curr_alpha", "cond_exp", "cond_alpha".
        pynn_receptor_type: The pynn receptor type. Valid values are: "excitatory", "inhibitory".
    """
    id: str = field(validator=instance_of(str))
    parameters: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    neuroml2_source_file: str = field(default=None, validator=optional(instance_of(str)))
    lems_source_file: str = field(default=None, validator=optional(instance_of(str)))
    pynn_synapse_type: str = field(default=None, validator=optional(in_(["curr_exp", "curr_alpha", "cond_exp", "cond_alpha"])))
    pynn_receptor_type: str = field(default=None, validator=optional(in_(["excitatory", "inhibitory"])))


@modelspec.define
class InputSource(NMLBase):
    """
    An InputSource definition.

    Args:
        id: Unique identifier for this InputSource
        parameters: Dictionary of parameters for the InputSource
        neuroml2_source_file: File name of NeuroML2 file defining the input source
        neuroml2_input: Name of standard NeuroML2 input
        lems_source_file: File name of LEMS file defining the input source
        pynn_input: Name of PyNN input
    """
    id: str = field(validator=instance_of(str))
    parameters: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    neuroml2_source_file: str = field(default=None, validator=optional(instance_of(str)))
    neuroml2_input: str = field(default=None, validator=optional(instance_of(str)))
    lems_source_file: str = field(default=None, validator=optional(instance_of(str)))
    pynn_input: str = field(default=None, validator=optional(instance_of(str)))


@modelspec.define
class RectangularRegion(NMLBase):
    """
    A RectangularRegion definition.

    Args:
        id: Unique identifier for this rectangular region.
        x: x coordinate of corner of region
        y: y coordinate of corner of region
        z: z coordinate of corner of region
        width: width of the rectangular region
        height: height of the rectangular region
        depth: depth of the rectangular region
    """
    id: str = field(validator=instance_of(str))
    x: float = field(validator=instance_of(float), converter=convert2float)
    y: float = field(validator=instance_of(float), converter=convert2float)
    z: float = field(validator=instance_of(float), converter=convert2float)
    width: float = field(validator=instance_of(float), converter=convert2float)
    height: float = field(validator=instance_of(float), converter=convert2float)
    depth: float = field(validator=instance_of(float), converter=convert2float)


@modelspec.define
class RandomLayout(NMLBase):
    """
    A RandomLayout definition.

    Args:
        region: Region in which to place population
    """
    region: str = field(validator=instance_of(str))


@modelspec.define
class RelativeLayout(NMLBase):
    """
    A RelativeLayout definition.

    Args:
        region: The Region relative to which population should be positioned.
        x: x position relative to x coordinate of Region
        y: y position relative to y coordinate of Region
        z: z position relative to z coordinate of Region
    """
    region: str = field(validator=instance_of(str))
    x: float = field(validator=instance_of(float), converter=convert2float)
    y: float = field(validator=instance_of(float), converter=convert2float)
    z: float = field(validator=instance_of(float), converter=convert2float)


@modelspec.define
class Location(NMLBase):
    """
    A Location definition.

    Args:
        x: x coordinate of location
        y: y coordinate of location
        z: z coordinate of location
    """
    x: float = field(validator=instance_of(float), converter=convert2float)
    y: float = field(validator=instance_of(float), converter=convert2float)
    z: float = field(validator=instance_of(float), converter=convert2float)


@modelspec.define
class SingleLocation(NMLBase):
    """
    A SingleLocation definition.

    Args:
        location: Location of the single Cell.
    """
    location: Location = field(validator=instance_of(Location))


@modelspec.define
class Population(NMLBase):
    """
    A Population definition.

    Args:
        id: Unique identifier for this Population
        size: The size of the population.
        component: The type of Cell to use in this population.
        properties: A dictionary of properties (metadata) for this population.
        random_layout: Layout in the random RectangularRegion.
        relative_layout: Position relative to RectangularRegion.
        single_location: Explicit location of the one Cell in the population
    """
    id: str = field(validator=instance_of(str))
    size: ValueExprType = field(validator=instance_of(value_expr_types))
    component: str = field(validator=instance_of(str))
    properties: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    random_layout: RandomLayout = field(default=None, validator=optional(instance_of(RandomLayout)))
    relative_layout: RelativeLayout = field(default=None, validator=optional(instance_of(RelativeLayout)))
    single_location: SingleLocation = field(default=None, validator=optional(instance_of(SingleLocation)))

    def has_positions(self):
        """
        Returns True if the population has a position.

        Returns:
            True if the population has a position.
        """
        if self.random_layout is not None:
            return True
        elif self.relative_layout is not None:
            return True
        elif self.single_location is not None:
            return True
        else:
            return False


@modelspec.define
class RandomConnectivity(NMLBase):
    """
    A RandomConnectivity definition.

    Args:
        probability: Random probability of connection.
    """
    probability: ValueExprType = field(validator=instance_of(value_expr_types))


@modelspec.define
class OneToOneConnector(NMLBase):
    """
    A OneToOneConnector definition.
    """
    pass


# Temp! to redefine more generally!
@modelspec.define
class ConvergentConnectivity(NMLBase):
    """
    A ConvergentConnectivity definition.

    Args:
        num_per_post: Number per post-synaptic neuron.
    """
    num_per_post: float = field(validator=instance_of(float), converter=convert2float)


@modelspec.define
class Projection(NMLBase):
    """
    A Projection definition.

    Args:
        id: Unique identifier for this Projection
        presynaptic: Presynaptic Population
        postsynaptic: Postsynaptic Population
        synapse: Which Synapse to use
        pre_synapse: For continuous connections, what presynaptic component to use (default: silent analog synapse)
        type: type of projection: projection (default; standard chemical, event triggered), electricalProjection
            (for gap junctions) or continuousProjection (for analogue/graded synapses)
        delay: Delay to use (default: 0)
        weight: Weight to use (default: 1)
        random_connectivity: Use random connectivity
        convergent_connectivity: Use convergent connectivity
        one_to_one_connector: Connect cell index i in pre pop to cell index i in post pop for all i

    """
    id: str = field(validator=instance_of(str))
    presynaptic: str = field(validator=optional(instance_of(str)))
    postsynaptic: str = field(validator=optional(instance_of(str)))
    synapse: str = field(validator=optional(instance_of(str)))
    pre_synapse: str = field(default=None, validator=optional(instance_of(str)))
    type: str = field(default="projection", validator=optional(instance_of(str)))
    delay: ValueExprType = field(default=None, validator=optional(instance_of(value_expr_types)))
    weight: ValueExprType = field(default=None, validator=optional(instance_of(value_expr_types)))
    random_connectivity: RandomConnectivity = field(default=None, validator=optional(instance_of(RandomConnectivity)))
    convergent_connectivity: ConvergentConnectivity = field(default=None, validator=optional(instance_of(ConvergentConnectivity)))
    one_to_one_connector: OneToOneConnector = field(default=None, validator=optional(instance_of(OneToOneConnector)))


@modelspec.define
class Input(NMLBase):
    """
    An Input definition.

    Args:
        id: Unique identifier for this Input
        input_source: Type of input to use in population
        population: Population to target
        percentage: Percentage of Cells to apply input to
        cell_ids: Specific ids of _Cell_s to apply this input to (cannot be used with percentage
        number_per_cell: Number of individual inputs per selected Cell (default: 1)
        segment_ids: Which segments to target (default: [0])
        weight: Weight to use (default: 1)
    """

    id: str = field(validator=instance_of(str))
    input_source: str = field(default=None, validator=optional(instance_of(str)))
    population: str = field(default=None, validator=optional(instance_of(str)))
    cell_ids: ValueExprType = field(default="", validator=optional(instance_of(value_expr_types)))
    percentage: float = field(default=None, validator=optional(instance_of(float)), converter=convert2float)
    number_per_cell: ValueExprType = field(default="", validator=optional(instance_of(value_expr_types)))
    segment_ids: ValueExprType = field(default="", validator=optional(instance_of(value_expr_types)))
    weight: ValueExprType = field(default=None, validator=optional(instance_of(value_expr_types)))


@modelspec.define
class NetworkReader(NMLBase):
    """
    A NetworkReader definition.

    Args:
        type: The type of NetworkReader
        parameters: Dictionary of parameters for the NetworkReader
    """
    type: str = field(default=None, validator=optional(instance_of(str)))
    parameters: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))


@modelspec.define
class Simulation(NMLBase):
    """
    A Simulation definition.

    Args:
        id: Unique identifier for this Simulation
        version: Information on verson of NeuroMLlite
        network: File name of network to simulate
        duration: Duration of simulation (ms)
        dt: Timestep of simulation (ms)
        seed: Seed for stochastic elements os the simulation
        record_traces: Record traces?
        record_spikes: Record spikes?
        record_rates: Record rates?
        record_variables: Record named variables?
        plots2D: Work in progress...
        plots3D: Work in progress...
    """
    id: str = field(validator=instance_of(str))
    version: str = field(default=f"NeuroMLlite v{__version__}", validator=optional(instance_of(str)), metadata={"omit_if_default": False})
    network: str = field(default=None, validator=optional(instance_of(str)))
    duration: float = field(default=None, validator=optional(instance_of(float)), converter=convert2float)
    dt: float = field(default=None, validator=optional(instance_of(float)), converter=convert2float)
    seed: int = field(default=None, validator=optional(instance_of(int)), converter=convert2int)
    record_traces: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    record_spikes: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    record_rates: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    record_variables: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    plots2D: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    plots3D: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))


@modelspec.define
class Network(NMLBase):
    """
    A Network containing multiple Population's, connected by Projection's and receiving Input's

    Args:
        id: Unique identifier for the Network
        parameters: Dictionary of global parameters for the network
        cells: The Cells which can be present in Populations
        synapses: The Synapse definitions which are used in Projections
        input_sources: The InputSource definitions which define the types of stimulus which can be applied in Inputs
        regions: The Regions in which Populations get placed.
        populations: The Populations of Cells making up this network ...
        projections: The Projections between Populations
        inputs: The inputs to apply to the elements of Populations
        version: Information on verson of NeuroMLlite
        seed: Seed for random number generator used when building network
        temperature: Temperature at which to run network (float in deg C)
        network_reader: A class which can read in a network (e.g. from a structured format)
        notes: Human readable notes about the network
    """

    id: str = field(validator=instance_of(str))
    parameters: Dict[str, Any] = field(default=None, validator=optional(instance_of(dict)))
    cells: List[Cell] = field(factory=list, validator=instance_of(list))
    synapses: List[Synapse] = field(factory=list, validator=instance_of(list))
    input_sources: List[InputSource] = field(factory=list, validator=instance_of(list))
    regions: List[RectangularRegion] = field(factory=list, validator=instance_of(list))
    populations: List[Population] = field(factory=list, validator=instance_of(list))
    projections: List[Projection] = field(factory=list, validator=instance_of(list))
    inputs: List[Input] = field(factory=list, validator=instance_of(list))
    version: str = field(default=f"NeuroMLlite v{__version__}", validator=instance_of(str), metadata={"omit_if_default": False})
    seed: int = field(default=None, validator=optional(instance_of(int)))
    temperature: float = field(default=None, validator=optional(instance_of(float)), converter=convert2float)
    network_reader: NetworkReader = field(default=None)


if __name__ == "__main__":

    net = Network(id="net")
    doc = net.generate_documentation(format="markdown")
    print(doc)
    with open("../docs/README.md", "w") as d:
        d.write(doc)

    import json
    import yaml

    doc = net.generate_documentation(format="dict")
    doc = {"version": "NeuroMLlite v%s" % __version__, "specification": doc}
    with open("../docs/NeuroMLlite_specification.json", "w") as d:
        d.write(json.dumps(doc, indent=4))
    with open("../docs/NeuroMLlite_specification.yaml", "w") as d:
        d.write(yaml.dump(doc, indent=4, sort_keys=False))
