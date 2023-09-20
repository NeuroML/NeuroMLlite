from neuromllite import *
from neuromllite.utils import *

from modelspec.utils import _val_info
from modelspec.utils import evaluate

import numpy as np

from test_base import get_example_network, get_example_simulation

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestUtils(unittest.TestCase):
    def test_pops_vs_cell_indices(self):
        from neuromllite.utils import get_pops_vs_cell_indices_seg_ids

        network = get_example_network()
        sim = get_example_simulation()
        sim.record_traces = {}
        sim.record_spikes = {}
        sim.record_rates = {}

        for recordSpec in [sim.record_traces, sim.record_spikes, sim.record_rates]:
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
