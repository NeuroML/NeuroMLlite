import collections

__version__ = '0.1.1'

from neuromllite.BaseTypes import Base
from neuromllite.BaseTypes import BaseWithId
from neuromllite.BaseTypes import NetworkReader
      
class Network(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_children = collections.OrderedDict([('cells',('The cell definitions...',Cell)),
                                 ('synapses',('The synapse definitions...',Synapse)),
                                 ('input_sources',('The input definitions...',InputSource)),
                                 ('populations',('The populations...',Population)),
                                 ('projections',('The projections...',Projection)),
                                 ('inputs',('The inputs to apply...',Input))])
                                 
        self.allowed_fields = collections.OrderedDict([('network_reader',('Can read in network',NetworkReader))])
                        
        super(Network, self).__init__(**kwargs)
          
  
class Cell(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                               ('pynn_cell',('Name of standard PyNN cell type',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(Cell, self).__init__(**kwargs)
  
  
class Synapse(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                                        ('pynn_synapse_type',("Options: 'curr_exp', 'curr_alpha', 'cond_exp', 'cond_alpha'.",str)),
                                        ('pynn_receptor_type',("Either 'excitatory' or 'inhibitory'.",str)),
                                        ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(Synapse, self).__init__(**kwargs)
  
  
class InputSource(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str)),
                               ('pynn_input',('Name of standard PyNN input',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(InputSource, self).__init__(**kwargs)
    
    
class Population(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('size',('Size of population',int)),
                               ('component',('Type of cell to use in population',str)),
                               ('color',('Optional color to use for visualizing population',str)),
                               ('random_layout',('Layout in random region',RandomLayout))])
                               
                      
        super(Population, self).__init__(**kwargs)
 
 
class RandomLayout(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('width',('Width of rectangular region',float)),
                               ('height',('Height of rectangular region',float)),
                               ('depth',('Depth of rectangular region',float))])
                               
        super(RandomLayout, self).__init__(**kwargs)

        
class Projection(BaseWithId):

    def __init__(self, **kwargs):
        self.allowed_fields = collections.OrderedDict([('presynaptic',('Presynaptic population',str)),
                               ('postsynaptic',('Postsynaptic population',str)),
                               ('synapse',('Synapse to use',str)),
                               ('delay',('Delay to use',float)),
                               ('weight',('Weight to use',float)),
                               ('random_connectivity',('Use random connectivity',RandomConnectivity)),
                               ('one_to_one_connector',('Connect cell index i in pre pop to cell index i in post pop for all i',OneToOneConnector))])

        super(Projection, self).__init__(**kwargs)
        
        
class Input(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('input_source',('Type of input to use in population',str)),
                               ('population',('Population to target',str)),
                               ('percentage',('Percentage of cells to apply this input to',float))])
                               
                      
        super(Input, self).__init__(**kwargs)


class RandomConnectivity(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('probability',('Random probability of connection',float))])
                               
        super(RandomConnectivity, self).__init__(**kwargs)


class OneToOneConnector(Base):

    def __init__(self, **kwargs):
                               
        super(OneToOneConnector, self).__init__(**kwargs)
        
        
  
class NetworkReader(Base):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('type',('Type of NetworkReader',str)),
                               ('parameters',('Dict of parameters for the cell',dict))])
                      
        super(NetworkReader, self).__init__(**kwargs)
    
    
class Simulation(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('duration',('Duration of simulation (ms)',float)),
                               ('dt',('Timestep of simulation (ms)',float)),
                               ('recordTraces',('Record traces?',str))])
                        
        super(Simulation, self).__init__(**kwargs)
    
                                   
            
        
