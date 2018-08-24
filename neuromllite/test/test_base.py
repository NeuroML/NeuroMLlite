from neuromllite import *
from neuromllite.utils import *

import pickle

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestBaseSaveLoad(unittest.TestCase):
    
    def get_example_network(self):
        net = Network(id='net0')
        net.notes = "...."

        p0 = Population(id='pop0', size=5, component='iaf', properties={'color':'0 .8 0'})
        p1 = Population(id='pop1', size=10, component='iaf', properties={'color':'0 0 .8'})
        net.populations.append(p0)
        net.populations.append(p1)

        net.projections.append(Projection(id='proj0',
                                          presynaptic=p0.id, 
                                          postsynaptic=p1.id,
                                          synapse='ampa'))

        net.projections[0].random_connectivity=RandomConnectivity(probability=0.5)
        
        return net
    
    def get_example_simulation(self):

        id = 'Sim0'
        sim = Simulation(id=id,
                         network='%s.json'%'net0',
                         duration='1000',
                         dt='0.01',
                         recordTraces={'all':'*'})
        return sim

    def test_save_load_json(self):
        
        
        for o in [self.get_example_simulation(), self.get_example_network()]:
        
            str0 = str(o)
            json0 = o.to_json()

            print(str0)

            new_file = o.to_json_file('temp/%s.json'%o.id)
            
            if 'net' in o.id:
                o1 = load_network_json(new_file)
            else:
                o1 = load_simulation_json(new_file)
                

            str1 = str(o1)
            json1 = o1.to_json()

            print(str1)

            self.assertEqual(str0, str1)
            self.assertEqual(json0, json1)

    def test_save_load_pickle(self):
        
        for o in [self.get_example_simulation(), self.get_example_network()]:
            
            str0 = str(o)
            json0 = o.to_json()

            print(str0)

            pstr0 = pickle.dumps(o)

            o1 = pickle.loads(pstr0)

            str1 = str(o1)
            json1 = o1.to_json()

            print(str1)

            self.assertEqual(str0, str1)
            self.assertEqual(json0, json1)
        