import collections

__version__ = '0.1.6'

from neuromllite.BaseTypes import Base
from neuromllite.BaseTypes import BaseWithId
from neuromllite.BaseTypes import NetworkReader


class EvaluableExpression(str):
    
    def __init__(self,expr):
        self.expr = expr
        
    
      
class ModelGraph(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_children = collections.OrderedDict([('nodes',('The node definitions...',Node)),
        ('edges',('The edge definitions...',Edge))])
                                 
        self.allowed_fields = collections.OrderedDict([('parameters',('Dict of global parameters for the network',dict))])
                        
        super(ModelGraph, self).__init__(**kwargs)
        
        
class Node(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_children = collections.OrderedDict([('input_ports',('Dict of ...',InputPort)),
             ('functions',('Dict of functions for the node',Function)),
             ('output_ports',('Dict of ...',OutputPort))])
        
        self.allowed_fields = collections.OrderedDict([('type',('Type...',str)),
                               ('parameters',('Dict of parameters for the node',dict))])
                      
        super(Node, self).__init__(**kwargs)
        
        
class Function(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('function',('...',str)),
                               ('args',('Dict of args...',dict))])
                      
        super(Function, self).__init__(**kwargs)
        
        
class InputPort(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('shape',('...',str))])
                      
        super(InputPort, self).__init__(**kwargs)
        
class OutputPort(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('value',('...',str))])
                      
        super(OutputPort, self).__init__(**kwargs)
        
class Edge(BaseWithId):

    def __init__(self, **kwargs):
        
        self.allowed_fields = collections.OrderedDict([('sender',('...',str)),('receiver',('...',str)),('sender_port',('...',str)),('receiver_port',('...',str))])
                      
        super(Edge, self).__init__(**kwargs)
          
  
if __name__ == "__main__":
    
    mod_graph0 = ModelGraph(id='Test', parameters={'speed':4})
    
    node  = Node(id='N0', parameters={'rate':5})
    
    mod_graph0.nodes.append(node)
        
    print(mod_graph0)

    print(mod_graph0.to_json())
    print('==================')
    
    mod_graph = ModelGraph(id='rl_ddm_model')
    
    input_node  = Node(id='input_node', parameters={'input':0.0})
    mod_graph.nodes.append(input_node)
    
    decision_node  = Node(id='decision_node')
    mod_graph.nodes.append(decision_node)
    ddm_analytical = Function(id='ddm_analytical', function='ddm_analytical')
    decision_node.functions.append(ddm_analytical)
    
    processing_node = Node(id='processing_node')
    mod_graph.nodes.append(processing_node)

    processing_node.parameters = {'logistic_gain':3, 'slope':31}
    processing_node.input_ports.append(InputPort(id='input_1', shape='(1,)'))
    processing_node.input_ports.append(InputPort(id='logistic_gain', shape='(1,)'))
    f1 = Function(id='logistic_1', function='logistic', args={'variable1':'input_1','gain':'logistic_gain'})
    processing_node.functions.append(f1)
    f2 = Function(id='linear_1', function='linear', args={'slope':'slope'})
    processing_node.functions.append(f2)
    processing_node.output_ports.append(OutputPort(id='output_1', value='linear_1'))
    
    e1 = Edge(id="inp",sender=input_node.id)
    mod_graph.edges.append(e1)
    
    
    
        
    print(mod_graph)

    print(mod_graph.to_json())
    new_file = mod_graph.to_json_file('ModelGraph.json')