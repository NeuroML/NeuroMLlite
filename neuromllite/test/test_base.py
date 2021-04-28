from neuromllite import *
from neuromllite.utils import *

import pickle

try:
    import unittest2 as unittest
except ImportError:
    import unittest

def get_example_network():

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

def get_example_simulation():

    id = 'Sim0'
    sim = Simulation(id=id,
                     network='%s.json'%'net0',
                     duration='1000',
                     dt='0.01',
                     recordTraces={'all':'*'})
    return sim


class TestCustomSaveLoad(unittest.TestCase):

    def test_save_load_json(self):
        class NewNetwork(BaseWithId):

            _definition = '...'

            def __init__(self, **kwargs):

                self.allowed_children = collections.OrderedDict([('cells',('The cell definitions...',NewCell)),
                                         ('synapses',('The synapse definitions...',NewSynapse))])

                self.allowed_fields = collections.OrderedDict([('version',('Information on verson of NeuroMLlite',str)),
                                                               ('seed',('Seed for random number generator used when building network',int)),
                                                               ('stable',('Testing...',bool)),
                                                               ('random_connectivity',('Use random connectivity',NewRandomConnectivity))])

                super(NewNetwork, self).__init__(**kwargs)

                self.version = 'NeuroMLlite 0.0'

        class NewCell(BaseWithId):

            def __init__(self, **kwargs):

                self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str))])

                super(NewCell, self).__init__(**kwargs)

        class NewSynapse(BaseWithId):

            def __init__(self, **kwargs):

                self.allowed_fields = collections.OrderedDict([('neuroml2_source_file',('File name of NeuroML2 file',str))])

                super(NewSynapse, self).__init__(**kwargs)


        class NewEvaluableExpression(str):

            def __init__(self,expr):
                self.expr = expr

        class NewRandomConnectivity(Base):

            def __init__(self, **kwargs):

                self.allowed_fields = collections.OrderedDict([('probability',('Random probability of connection',NewEvaluableExpression))])

                super(NewRandomConnectivity, self).__init__(**kwargs)



        net = NewNetwork(id='netid')
        cell = NewCell(id='cellid1')
        cell.neuroml2_source_file = 'nnn'
        cell2 = NewCell(id='cellid2')
        cell2.neuroml2_source_file = 'nnn2'
        #net.cells.append(cell)

        print(net)
        print(net.cells)
        print(net)
        '''  '''
        net.cells.append(cell)
        net.cells.append(cell2)

        rc = NewRandomConnectivity(probability=0.01)
        net.random_connectivity = rc
        net.stable = False
        print(rc)
        print(net)

        try:
            print(net.notcells)
        except Exception as e:
            print('  As expected, an exception: [%s]...'%e)

        str_orig = str(net)

        filenamej = '%s.json'%net.id
        net.to_json_file(filenamej)

        filenamey = '%s.yaml'%net.id
        #net.id = net.id+'_yaml'
        net.to_yaml_file(filenamey)
        from neuromllite.utils import load_json, load_yaml, _parse_element

        dataj = load_json(filenamej)
        print_v("Loaded network specification from %s"%filenamej)
        netj = NewNetwork()
        _parse_element(dataj, netj)
        str_netj = str(netj)

        datay = load_yaml(filenamey)
        print_v("Loaded network specification from %s"%filenamey)

        nety = NewNetwork()
        _parse_element(datay, nety)
        str_nety = str(nety)


        verbose = False
        print('----- Before -----')
        print(str_orig)
        print('----- After via %s -----'%filenamej)
        print(str_netj)
        print('----- After via %s -----'%filenamey)
        print(str_nety)

        print('Test JSON..')
        if sys.version_info[0]==2:
            assert(len(str_orig)==len(str_netj)) # Order not preserved in py2, just test len
        else:
            assert(str_orig==str_netj)

        print('Test YAML..')
        if sys.version_info[0]==2:
            assert(len(str_orig)==len(str_nety)) # Order not preserved in py2, just test len
        else:
            assert(str_orig==str_nety)


class TestBaseSaveLoad(unittest.TestCase):

    def test_save_load_json(self):

        for o in [get_example_simulation(), get_example_network()]:

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

            if sys.version_info[0]==2: # Order not preserved in py2, just test len
                self.assertEqual(len(str0), len(str1))
                self.assertEqual(len(json0), len(json1))
            else:
                self.assertEqual(str0, str1)
                self.assertEqual(json0, json1)

    def test_save_load_pickle(self):

        for o in [get_example_simulation(), get_example_network()]:

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
