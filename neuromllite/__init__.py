import collections

__version__ = '0.1.7'

from neuromllite.BaseTypes import Base
from neuromllite.BaseTypes import BaseWithId
from neuromllite.BaseTypes import NetworkReader


class EvaluableExpression(str):
    
    def __init__(self,expr):
        self.expr = expr
        
    
      
class Network(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_children = collections.OrderedDict([('cells',('The cell definitions...',Cell)),
                                 ('synapses',('The synapse definitions...',Synapse)),
                                 ('input_sources',('The input definitions...',InputSource)),
                                 ('regions',('The regions...',RectangularRegion)),
                                 ('populations',('The populations...',Population)),
                                 ('projections',('The projections...',Projection)),
                                 ('inputs',('The inputs to apply...',Input))])
                                 
        self.allowed_fields = collections.OrderedDict([('version',('Information on verson of NeuroMLlite',str)),
                                                       ('temperature',('Temperature at which to run network (float in deg C)',float)),
                                                       ('parameters',('Dict of global parameters for the network',dict)),
                                                       ('network_reader',('Can read in network',NetworkReader))])
                        
        super(Network, self).__init__(**kwargs)
        
        self.version = 'NeuroMLlite v%s'%__version__
          
  
class Cell(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                               ('lems_source_file',('File name of LEMS file',str)),
                               ('neuroml2_cell',('Name of standard NeuroML2 cell type',str)),
                               ('pynn_cell',('Name of standard PyNN cell type',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(Cell, self).__init__(**kwargs)
  
  
class Synapse(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                                        ('lems_source_file',('File name of LEMS file',str)),
                                        ('pynn_synapse_type',("Options: 'curr_exp', 'curr_alpha', 'cond_exp', 'cond_alpha'.",str)),
                                        ('pynn_receptor_type',("Either 'excitatory' or 'inhibitory'.",str)),
                                        ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(Synapse, self).__init__(**kwargs)
  
  
class InputSource(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                               ('neuroml2_input',('Name of standard NeuroML2 input',str)),
                               ('pynn_input',('Name of standard PyNN input',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
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
                               ('component',('Type of cell to use in population',str)),
                               ('properties',('Dict of properties (metadata) for the population',dict)),
                               ('random_layout',('Layout in random region',RandomLayout)),
                               ('single_location',('Explicit location',SingleLocation))])
                               
                      
        super(Population, self).__init__(**kwargs)
 
 
class RandomLayout(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('region',('Region in which to place population',str))])
                               
        super(RandomLayout, self).__init__(**kwargs)
 
 
class SingleLocation(Base):

    def __init__(self, **kwargs):
        
        #self.allowed_children = collections.OrderedDict([('locations',('The locations...',Location))])
        self.allowed_fields = collections.OrderedDict([('location',('The location...',Location))])
                               
        super(SingleLocation, self).__init__(**kwargs)


class Location(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('x',('x coordinate',float)),
                               ('y',('y coordinate',float)),
                               ('z',('z coordinate',float))])
                               
        super(Location, self).__init__(**kwargs)
        
        
class Projection(BaseWithId):

    def __init__(self, **kwargs):
        self.allowed_fields = collections.OrderedDict([('presynaptic',('Presynaptic population',str)),
                               ('postsynaptic',('Postsynaptic population',str)),
                               ('synapse',('Synapse to use',str)),
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
                               ('percentage',('Percentage of cells to apply this input to',float)),
                               ('number_per_cell',('Number of individual inputs per selected cell',EvaluableExpression)),
                               ('weight',('Weight to use (default: 1)',EvaluableExpression))])
                               
                      
        super(Input, self).__init__(**kwargs)


class RandomConnectivity(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('probability',('Random probability of connection',float))])
                               
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
        
        self.allowed_fields = collections.OrderedDict([('type',('Type of NetworkReader',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
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
                               ('recordVariables',('Record named variables?',dict))])
                        
        super(Simulation, self).__init__(**kwargs)
     
        self.version = 'NeuroMLlite v%s'%__version__       
            
        
