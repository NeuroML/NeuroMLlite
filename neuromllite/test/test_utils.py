from neuromllite import *
from neuromllite.utils import *

from test_base import get_example_network, get_example_simulation

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestUtils(unittest.TestCase):
    
    def test_pops_vs_cell_indices(self):
        
        from neuromllite.utils import get_pops_vs_cell_indices
        
        network = get_example_network()
        sim = get_example_simulation()
        sim.recordTraces = {}
        sim.recordSpikes = {}
        sim.recordRates = {}
        
        
        for recordSpec in [sim.recordTraces, sim.recordSpikes, sim.recordRates]:

            recordSpec['all'] = '*'
            pvi = get_pops_vs_cell_indices(recordSpec, network)
            print("Record spec: %s evaluates as %s"%(recordSpec,pvi))

            for pop in network.populations:
                assert(pop.size==len(pvi[pop.id]))

            recordSpec = {'pop1':'*'}
            pvi = get_pops_vs_cell_indices(recordSpec, network)

            for pop in network.populations:
                if pop.id in pvi:
                    assert(len(pvi[pop.id])== (pop.size if pop.id=='pop1' else 0))


            recordSpec = {'pop1':0, 'pop0':3}
            pvi = get_pops_vs_cell_indices(recordSpec, network)
            print("Record spec: %s evaluates as %s"%(recordSpec,pvi))

            for pop in network.populations:
                if pop.id in pvi:
                    assert(len(pvi[pop.id])==1 and recordSpec[pop.id]==pvi[pop.id][0])

            recordSpec = {'pop1':[0,2], 'pop0':range(4)}
            pvi = get_pops_vs_cell_indices(recordSpec, network)

            print("Record spec: %s evaluates as %s"%(recordSpec,pvi))
            for pop in network.populations:
                if pop.id in pvi:
                    assert(len(pvi[pop.id])==len(recordSpec[pop.id]))

        
        return True