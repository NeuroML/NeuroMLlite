from neuromllite import *
from neuromllite.utils import *

import modelspec
from modelspec import field
from modelspec import optional, instance_of

import pickle

try:
    import unittest2 as unittest
except ImportError:
    import unittest


def get_example_network():
    net = Network(id="net0", parameters={})
    net.notes = "...."

    net.parameters = {
        "int": 3,
        "float": 3.3,
        "str": "str",
        "bool": True,
        "list": [1, 2, 3],
        "dict": {"a": 1, "f": False, "d": {"a": 2}},
        "dict2": {"a": 1, "l": [33, 22]},
    }

    p0 = Population(id="pop0", size=5, component="iaf", properties={"color": "0 .8 0"})
    p1 = Population(id="pop1", size=10, component="iaf", properties={"color": "0 0 .8"})
    net.populations.append(p0)
    net.populations.append(p1)

    net.projections.append(
        Projection(id="proj0", presynaptic=p0.id, postsynaptic=p1.id, synapse="ampa")
    )

    net.projections[0].random_connectivity = RandomConnectivity(probability=0.5)

    return net


def get_example_simulation():
    id = "Sim0"
    sim = Simulation(
        id=id,
        network="%s.json" % "net0",
        duration="1000",
        dt="0.01",
        record_traces={"all": "*"},
    )
    return sim


class TestCustomSaveLoad(unittest.TestCase):
    def test_save_load_json(self):
        @modelspec.define
        class NewCell(Base):
            """
            A new cell definition

            Args:
                id: the cell id
                neuroml2_source_file: The path to the source file
            """

            id: str = field(validator=instance_of(str))
            neuroml2_source_file: str = field(
                default=None, validator=optional(instance_of(str))
            )

        @modelspec.define
        class NewSynapse(Base):
            """
            A new synapse definition

            Args:
                id: the synapse id
                neuroml2_source_file: The path to the source file
                tested: A boolean attribute
            """

            id: str = field(validator=instance_of(str))
            neuroml2_source_file: str = field(
                default=None, validator=optional(instance_of(str))
            )
            tested: bool = field(default=None, validator=optional(instance_of(bool)))

        @modelspec.define
        class NewRandomConnectivity(Base):
            """
            A new random connectivity definition

            Args:
                probability: Random probability of connection

            """

            probability: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )

        @modelspec.define
        class NewNetwork(Base):
            """
            A new network definition

            Args:
                id: a unique identifier for the network
                cells: a list of cells
                synapses: a list of synapses
                version: Information on verson of NeuroMLlite
                seed: Seed for random number generator used when building network
                stable: Testing...
                parameters: Dictionary of global parameters for the network
                random_connectivity: Use random connectivity
            """

            id: str = field(validator=instance_of(str))
            cells: List[NewCell] = field(factory=list)
            synapses: List[NewSynapse] = field(factory=list)
            version: str = field(default="NeuroMLlite 0.0", validator=instance_of(str))
            seed: int = field(default=None, validator=optional(instance_of(int)))
            stable: bool = field(default=None, validator=optional(instance_of(bool)))
            parameters: Dict[str, Any] = field(
                default=None, validator=optional(instance_of(dict))
            )
            random_connectivity: NewRandomConnectivity = field(
                default=None, validator=optional(instance_of(NewRandomConnectivity))
            )
            ee0: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee1: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee2: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee3: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee4: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee5: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )
            ee6: ValueExprType = field(
                default=None, validator=optional(instance_of(value_expr_types))
            )

        net = NewNetwork(id="netid", parameters={"size": 3, "name": None})

        # Some tests on what's allowed
        net.ee0 = "str"
        net.ee1 = {"a": 2}
        net.ee2 = 1
        net.ee3 = 1.1
        net.ee4 = True
        net.ee5 = [1, 2]
        net.ee6 = None

        cell = NewCell(id="cellid1")
        cell.neuroml2_source_file = "nnn"
        cell2 = NewCell(id="cellid2")
        cell2.neuroml2_source_file = "nnn2"
        # net.cells.append(cell)

        print(net)
        print(net.cells)
        print(net)
        """  """
        net.cells.append(cell)
        net.cells.append(cell2)

        syn0 = NewSynapse(id="syn0", neuroml2_source_file=None, tested=True)
        net.synapses.append(syn0)
        syn1 = NewSynapse(id="syn1", neuroml2_source_file="xx", tested=None)
        net.synapses.append(syn1)

        rc = NewRandomConnectivity(probability=0.01)
        net.random_connectivity = rc
        net.stable = False
        print(rc)
        print(net)

        try:
            print(net.notcells)
        except Exception as e:
            print("  As expected, an exception: [%s]..." % e)

        str_orig = str(net)

        filenamej = "%s.json" % net.id
        net.to_json_file(filenamej)

        filenamey = "%s.yaml" % net.id
        # net.id = net.id+'_yaml'
        net.to_yaml_file(filenamey)
        from modelspec.utils import load_json, load_yaml

        dataj = load_json(filenamej)
        print_v("Loaded network specification from %s" % filenamej)
        netj = NewNetwork.from_dict(dataj)
        str_netj = str(netj)

        datay = load_yaml(filenamey)
        print_v("Loaded network specification from %s" % filenamey)

        nety = NewNetwork.from_dict(datay)
        str_nety = str(nety)

        verbose = False
        print("----- Before -----")
        print(str_orig)
        print("----- After via %s -----" % filenamej)
        print(str_netj)
        print("----- After via %s -----" % filenamey)
        print(str_nety)

        print("Test JSON..")
        if sys.version_info[0] == 2:
            assert len(str_orig) == len(
                str_netj
            )  # Order not preserved in py2, just test len
        else:
            assert str_orig == str_netj

        print("Test YAML..")
        if sys.version_info[0] == 2:
            assert len(str_orig) == len(
                str_nety
            )  # Order not preserved in py2, just test len
        else:
            assert str_orig == str_nety

        print("Test EvaluableExpressions")
        for i in range(7):
            assert eval("net.ee%i" % i) == eval("netj.ee%i" % i)
            assert eval("net.ee%i" % i) == eval("nety.ee%i" % i)


class TestBaseSaveLoad(unittest.TestCase):
    def test_save_load_json(self):
        for o in [get_example_simulation(), get_example_network()]:
            str0 = str(o)
            json0 = o.to_json()

            print(str0)

            new_file = o.to_json_file("temp/%s.json" % o.id)

            if "net" in o.id:
                o1 = load_network_json(new_file)
            else:
                o1 = load_simulation_json(new_file)

            str1 = str(o1)
            json1 = o1.to_json()

            print(str1)

            print("Loaded from %s" % new_file)

            if sys.version_info[0] == 2:  # Order not preserved in py2, just test len
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


if __name__ == "__main__":
    # Some tests
    tc = TestCustomSaveLoad()
    tc.test_save_load_json()

    tb = TestBaseSaveLoad()
    tb.test_save_load_pickle()
    tb.test_save_load_json()
