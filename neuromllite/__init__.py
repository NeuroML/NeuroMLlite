import collections

__version__ = '0.3.4'

#import pyNN
#import nest

from neuromllite.BaseTypes import Base
from neuromllite.BaseTypes import BaseWithId
from neuromllite.BaseTypes import NetworkReader


class EvaluableExpression(str):

    def __init__(self, expr):
        self.expr = expr



class Network(BaseWithId):

    _definition = 'A Network containing multiple _Population_s, connected by _Projection_s and receiving _Input_s'

    def __init__(self, **kwargs):

        self.allowed_children = collections.OrderedDict([('cells',('The _Cell_s which can be present in _Population_s',Cell)),
                                 ('synapses',('The _Synapse_ definitions which are used in _Projection_s',Synapse)),
                                 ('input_sources',('The _InputSource_ definitions which define the types of stimulus which can be applied in _Input_s',InputSource)),
                                 ('regions',('The _Regions_ in which _Population_s get placed',RectangularRegion)),
                                 ('populations',('The _Population_s of _Cell_s making up this network...',Population)),
                                 ('projections',('The _Projection_s between _Population_s',Projection)),
                                 ('inputs',('The inputs to apply to the elements of _Population_s',Input))])

        self.allowed_fields = collections.OrderedDict([('version',('Information on verson of NeuroMLlite',str)),
                                                       ('seed',('Seed for random number generator used when building network',int)),
                                                       ('temperature',('Temperature at which to run network (float in deg C)',float)),
                                                       ('parameters',('Dictionary of global parameters for the network',dict)),
                                                       ('network_reader',('A class which can read in a network (e.g. from a structured format)',NetworkReader))])

        super(Network, self).__init__(**kwargs)

        self.version = 'NeuroMLlite v%s'%__version__


class Cell(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file defining the cell',str)),
                               ('lems_source_file',('File name of LEMS file defining the cell',str)),
                               ('neuroml2_cell',('Name of standard NeuroML2 cell type',str)),
                               ('pynn_cell',('Name of standard PyNN cell type',str)),
                               ('arbor_cell',('Name of standard Arbor cell type',str)),
                               ('parameters',('Dictionary of parameters for the cell',dict))])

        super(Cell, self).__init__(**kwargs)


class Synapse(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file defining the synapse',str)),
                                        ('lems_source_file',('File name of LEMS file defining the synapse',str)),
                                        ('pynn_synapse_type',('Options: "curr_exp", "curr_alpha", "cond_exp", "cond_alpha".',str)),
                                        ('pynn_receptor_type',('Either "excitatory" or "inhibitory".',str)),
                                        ('parameters',('Dictionary of parameters for the synapse',dict))])

        super(Synapse, self).__init__(**kwargs)


class InputSource(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                               ('lems_source_file',('File name of LEMS file',str)),
                               ('neuroml2_input',('Name of standard NeuroML2 input',str)),
                               ('pynn_input',('Name of standard PyNN input',str)),
                               ('parameters',('Dictionary of parameters for the InputSource',dict))])

        super(InputSource, self).__init__(**kwargs)

'''
class Region(BaseWithId):

    def __init__(self, **kwargs):

        super(Region, self).__init__(**kwargs)'''


class RectangularRegion(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('x',('x coordinate of corner',float)),
                               ('y',('y coordinate of corner',float)),
                               ('z',('z coordinate of corner',float)),
                               ('width',('Width of rectangular region',float)),
                               ('height',('Height of rectangular region',float)),
                               ('depth',('Depth of rectangular region',float))])

        super(RectangularRegion, self).__init__(**kwargs)


class Population(BaseWithId):

    def __init__(self, **kwargs):

        #self.allowed_children = collections.OrderedDict([('positions',('List of explicit positions...',str))])

        self.allowed_fields = collections.OrderedDict([('size',('Size of population',EvaluableExpression)),
                               ('component',('Type of _Cell_ to use in population',str)),
                               ('properties',('Dictionary of properties (metadata) for the population',dict)),
                               ('random_layout',('Layout in random _Region_',RandomLayout)),
                               ('relative_layout',('Position relative to _Region_.',RelativeLayout)),
                               ('single_location',('Explicit location of the one _Cell_ in the population',SingleLocation))])


        super(Population, self).__init__(**kwargs)

    def has_positions(self):
        if self.random_layout: return True
        elif self.relative_layout: return True
        elif self.single_location: return True
        else: return False


class RandomLayout(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('region',('Region in which to place population',str))])

        super(RandomLayout, self).__init__(**kwargs)



class RelativeLayout(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('region',('The _Region_ relative to which population should be positioned',str)),
                               ('x',('x position relative to x coordinate of _Region_',float)),
                               ('y',('y position relative to y coordinate of _Region_',float)),
                               ('z',('z position relative to z coordinate of _Region_',float))])

        super(RelativeLayout, self).__init__(**kwargs)


class SingleLocation(Base):

    def __init__(self, **kwargs):

        #self.allowed_children = collections.OrderedDict([('locations',('The locations...',Location))])
        self.allowed_fields = collections.OrderedDict([('location',('The location of the single _Cell_',Location))])

        super(SingleLocation, self).__init__(**kwargs)


class Location(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('x',('x coordinate',float)),
                               ('y',('y coordinate',float)),
                               ('z',('z coordinate',float))])

        super(Location, self).__init__(**kwargs)


class Projection(BaseWithId):

    def __init__(self, **kwargs):
        self.allowed_fields = collections.OrderedDict([('presynaptic',('Presynaptic _Population_',str)),
                               ('postsynaptic',('Postsynaptic _Population_',str)),
                               ('synapse',('Which _Synapse_ to use',str)),
                               ('pre_synapse',('For continuous connections, what presynaptic component to use (default: silent analog synapse)',str)),
                               ('type',('type of projection: projection (default; standard chemical, event triggered), electricalProjection (for gap junctions) or continuousProjection (for analogue/graded synapses)',str)),
                               ('delay',('Delay to use (default: 0)',EvaluableExpression)),
                               ('weight',('Weight to use (default: 1)',EvaluableExpression)),
                               ('random_connectivity',('Use random connectivity',RandomConnectivity)),
                               ('convergent_connectivity',('Use ConvergentConnectivity',ConvergentConnectivity)),
                               ('one_to_one_connector',('Connect cell index i in pre pop to cell index i in post pop for all i',OneToOneConnector))])

        super(Projection, self).__init__(**kwargs)


class Input(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('input_source',('Type of input to use in population',str)),
                               ('population',('Population to target',str)),
                               ('percentage',('Percentage of _Cell_s to apply this input to',float)),
                               ('number_per_cell',('Number of individual inputs per selected _Cell_ (default: 1)',EvaluableExpression)),
                               ('segment_ids',('Which segments to target (default: [0])',EvaluableExpression)),
                               ('weight',('Weight to use (default: 1)',EvaluableExpression))])


        super(Input, self).__init__(**kwargs)


class RandomConnectivity(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('probability',('Random probability of connection',EvaluableExpression))])

        super(RandomConnectivity, self).__init__(**kwargs)


class OneToOneConnector(Base):

    def __init__(self, **kwargs):

        super(OneToOneConnector, self).__init__(**kwargs)

# Temp! to redefine more generally!
class ConvergentConnectivity(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('num_per_post',('Number per post synaptic neuron',float))])

        super(ConvergentConnectivity, self).__init__(**kwargs)



class NetworkReader(Base):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('type',('The type of NetworkReader',str)),
                               ('parameters',('Dictionary of parameters for the NetworkReader',dict))])

        super(NetworkReader, self).__init__(**kwargs)


class Simulation(BaseWithId):

    def __init__(self, **kwargs):

        self.allowed_fields = collections.OrderedDict([('version',('Information on verson of NeuroMLlite',str)),
                               ('network',('File name of network to simulate',str)),
                               ('duration',('Duration of simulation (ms)',float)),
                               ('dt',('Timestep of simulation (ms)',float)),
                               ('seed',('Seed for stochastic elements os the simulation (integer)',int)),
                               ('recordTraces',('Record traces?',dict)),
                               ('recordSpikes',('Record spikes?',dict)),
                               ('recordRates',('Record rates?',dict)),
                               ('recordVariables',('Record named variables?',dict)),
                               ('plots2D',('Work in progress...',dict)),
                               ('plots3D',('Work in progress...',dict))])

        super(Simulation, self).__init__(**kwargs)

        self.version = 'NeuroMLlite v%s'%__version__



if __name__ == '__main__':

    net = Network(id='net')
    doc = net.generate_documentation(format='markdown')
    print(doc)
    with open('../docs/README.md','w') as d:
        d.write(doc)

    import json
    import yaml
    doc = net.generate_documentation(format='dict')
    doc = {'version':'NeuroMLlite v%s'%__version__, 'specification':doc}
    with open('../docs/NeuroMLlite_specification.json','w') as d:
        d.write(json.dumps(doc,indent=4))
    with open('../docs/NeuroMLlite_specification.yaml','w') as d:
        d.write(yaml.dump(doc,indent=4,sort_keys=False))
