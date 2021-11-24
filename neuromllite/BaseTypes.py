import collections
import json
import sys
from collections import OrderedDict


if __name__ == "__main__":

    # Some tests

    class Network(BaseWithId):

        _definition = "A Network containing multiple _Population_s, connected by _Projection_s and receiving _Input_s"

        def __init__(self, **kwargs):

            self.allowed_children = collections.OrderedDict(
                [
                    ("cells", ("The cell definitions...", Cell)),
                    ("synapses", ("The synapse definitions...", Synapse)),
                ]
            )

            self.allowed_fields = collections.OrderedDict(
                [
                    ("version", ("Information on verson of NeuroMLlite", str)),
                    (
                        "seed",
                        (
                            "Seed for random number generator used when building network",
                            int,
                        ),
                    ),
                    (
                        "random_connectivity",
                        ("Use random connectivity", RandomConnectivity),
                    ),
                ]
            )

            super(Network, self).__init__(**kwargs)

            self.version = "NeuroMLlite 0.0"

    class Cell(BaseWithId):
        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict(
                [("neuroml2_source_file", ("File name of NeuroML2 file", str))]
            )

            super(Cell, self).__init__(**kwargs)

    class Synapse(BaseWithId):
        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict(
                [("neuroml2_source_file", ("File name of NeuroML2 file", str))]
            )

            super(Synapse, self).__init__(**kwargs)

    class EvaluableExpression(str):
        def __init__(self, expr):
            self.expr = expr

    class RandomConnectivity(Base):
        def __init__(self, **kwargs):

            self.allowed_fields = collections.OrderedDict(
                [
                    (
                        "probability",
                        ("Random probability of connection", EvaluableExpression),
                    )
                ]
            )

            super(RandomConnectivity, self).__init__(**kwargs)

    net = Network(id="netid")
    cell = Cell(id="cellid1")
    cell.neuroml2_source_file = "nnn"
    cell2 = Cell(id="cellid2")
    cell2.neuroml2_source_file = "nnn2"
    # net.cells.append(cell)

    print(net)
    print(net.cells)
    print(net)
    """  """
    net.cells.append(cell)
    net.cells.append(cell2)

    rc = RandomConnectivity(probability=0.01)
    net.random_connectivity = rc
    print(rc)
    print(net)

    # print(net['cells'])
    try:
        print(net.notcells)
    except Exception as e:
        print("  As expected, an exception: [%s]..." % e)

    import pprint

    pp = pprint.PrettyPrinter(depth=4)
    # d0 = net.to_simple_dict()
    # print(d0)
    print("--- new format ---")
    d = Base.to_dict_format(net)
    print(d)
    pp.pprint(dict(d))
    print("  To JSON:")
    print(net.to_json())
    print("  To YAML:")
    print(net.to_yaml())

    filenamej = "%s.json" % net.id
    net.to_json_file(filenamej)

    filenamey = "%s.yaml" % net.id
    net.id = net.id + "_yaml"
    net.to_yaml_file(filenamey)
    from neuromllite.utils import load_json, load_yaml, _parse_element

    dataj = load_json(filenamej)
    print_v("Loaded network specification from %s" % filenamej)
    netj = Network()
    _parse_element(dataj, netj)

    datay = load_yaml(filenamey)
    print_v("Loaded network specification from %s" % filenamey)

    nety = Network()
    _parse_element(datay, nety)

    verbose = False
    print("----- Before -----")
    print(net)
    print("----- After via %s -----" % filenamej)
    print(netj)
    print("----- After via %s -----" % filenamey)
    print(nety)

    print("----- Schema -----")
    doc = net.generate_documentation(format=MARKDOWN_FORMAT)
    with open("doc.md", "w") as d:
        d.write(doc)

    doc = net.generate_documentation(format=DICT_FORMAT)
    with open("doc.json", "w") as d:
        d.write(json.dumps(doc, indent=4))
