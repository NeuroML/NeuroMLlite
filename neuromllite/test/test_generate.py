from neuromllite import *
from neuromllite.utils import *
from neuromllite.NetworkGenerator import *


try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestGenerate(unittest.TestCase):
    
    
    def get_example_simulation(self):

        id = 'Sim3'
        sim = Simulation(id=id,
                         network='../../examples/Example4_PyNN.json',
                         duration='1000',
                         dt='0.01',
                         recordTraces={'all':'*'})
        return sim

    def test_generate_nml(self):
        
        sim = self.get_example_simulation()
        network = load_network_json(sim.network)
        
        gen_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp/nml')
        if not os.path.isdir(gen_dir): os.mkdir(gen_dir)
        
        generate_neuroml2_from_network(network, 
                                       base_dir=os.path.abspath(os.path.dirname(sim.network)),
                                       target_dir=gen_dir)
        
       
    
    def test_generate_jnml(self):
        sim = self.get_example_simulation()
        
        gen_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp/jnml')
        if not os.path.isdir(gen_dir): os.mkdir(gen_dir)
        
        generate_and_run(sim, 
                         simulator='jNeuroML',
                         target_dir=gen_dir)
        
