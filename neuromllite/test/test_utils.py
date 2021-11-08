from neuromllite import *
from neuromllite.utils import *
import numpy as np

from test_base import get_example_network, get_example_simulation

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestUtils(unittest.TestCase):
    def test_evaluate(self):

        assert evaluate("33") == 33.0
        assert evaluate("33") == 33
        assert evaluate(33) == 33
        params = {"p": 33}
        assert evaluate("p+p", params, verbose=True) == 66

        assert type(evaluate("33")) == int
        assert type(evaluate("33.0")) == int
        assert type(evaluate("33.1")) == float
        assert type(evaluate("33.1a")) == str

        assert type(evaluate("33.1a")) == str

        import random

        rng = random.Random(1234)

        # print('random: %s'%evaluate('1*random()',rng=rng))
        assert evaluate("1*random()", rng=rng) == 0.9664535356921388

        assert evaluate("math.sin(math.pi/2)", verbose=True) == 1

        assert evaluate([1, 2, 3], verbose=True)[2] == 3

        params = {"a": np.array([0, 1, 0]), "b": np.array([1, 1, 3])}

        assert evaluate("a+b", params, verbose=True)[2] == 3

    def test_pops_vs_cell_indices(self):

        from neuromllite.utils import get_pops_vs_cell_indices_seg_ids

        network = get_example_network()
        sim = get_example_simulation()
        sim.recordTraces = {}
        sim.recordSpikes = {}
        sim.recordRates = {}

        for recordSpec in [sim.recordTraces, sim.recordSpikes, sim.recordRates]:

            print("Testing...")
            recordSpec["all"] = "*"
            pvi = get_pops_vs_cell_indices_seg_ids(recordSpec, network)
            print("Record spec: %s evaluates as %s" % (recordSpec, pvi))

            for pop in network.populations:
                assert pop.size == len(pvi[pop.id])

            recordSpec = {"pop1": "*"}
            pvi = get_pops_vs_cell_indices_seg_ids(recordSpec, network)
            print("Record spec: %s evaluates as %s" % (recordSpec, pvi))

            for pop in network.populations:
                if pop.id in pvi:
                    assert len(pvi[pop.id]) == (pop.size if pop.id == "pop1" else 0)

            recordSpec = {"pop1": 0, "pop0": 3}
            pvi = get_pops_vs_cell_indices_seg_ids(recordSpec, network)
            print("Record spec: %s evaluates as %s" % (recordSpec, pvi))

            for pop in network.populations:
                if pop.id in pvi:
                    assert (
                        len(pvi[pop.id]) == 1
                        and recordSpec[pop.id] == list(pvi[pop.id].keys())[0]
                    )

            recordSpec = {"pop1": "0:3", "pop0": "0:[3]"}
            pvi = get_pops_vs_cell_indices_seg_ids(recordSpec, network)
            print("Record spec: %s evaluates as %s" % (recordSpec, pvi))

            for pop in network.populations:
                if pop.id in pvi:
                    print(pvi[pop.id].values())
                    assert (
                        len(pvi[pop.id]) == 1
                        and list(pvi[pop.id].keys())[0] == 0
                        and list(pvi[pop.id].values())[0][0] == 3
                    )

            recordSpec = {"pop1": [0, 2], "pop0": list(range(4))}
            pvi = get_pops_vs_cell_indices_seg_ids(recordSpec, network)

            print("Record spec: %s evaluates as %s" % (recordSpec, pvi))
            for pop in network.populations:
                if pop.id in pvi:
                    assert len(pvi[pop.id]) == len(recordSpec[pop.id])

        return True


if __name__ == "__main__":
    tu = TestUtils()
    tu.test_evaluate()
