from neuromllite import (
    RelativeLayout,
    Cell,
    Synapse,
    InputSource,
    Input,
    RectangularRegion,
)
from neuromllite.NetworkGenerator import generate_network
from neuromllite.utils import load_network_json
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

################################################################################
###   Reuse network from Example1

net = load_network_json("../../../examples/Example1_TestNetwork.json")
net.id = "Example_Layout"

net.notes = "...."


################################################################################
###   Add some elements to the network & save new JSON

r1 = RectangularRegion(id="region1", x=0, y=0, z=0, width=1000, height=100, depth=1000)
r2 = RectangularRegion(
    id="region2", x=1000, y=1000, z=1000, width=1000, height=100, depth=1000
)
net.regions.append(r1)
net.regions.append(r2)

net.populations[0].size = 1
net.populations[0].relative_layout = RelativeLayout(x=0, y=50, z=0, region=r1.id)
net.populations[1].size = 1
net.populations[1].relative_layout = RelativeLayout(x=50, y=0, z=50, region=r2.id)

net.populations[0].component = "hhcell"
net.populations[1].component = "hhcell"

net.cells.append(
    Cell(
        id="hhcell", neuroml2_source_file="../../../examples/test_files/hhcell.cell.nml"
    )
)
net.synapses.append(
    Synapse(
        id="ampa", neuroml2_source_file="../../../examples/test_files/ampa.synapse.nml"
    )
)


print(net.to_json())
new_file = net.to_json_file("%s.json" % net.id)


################################################################################
###   Use a handler which just prints info on positions, etc.

def_handler = DefaultNetworkHandler()

generate_network(net, def_handler)


################################################################################
###   Export to some formats, e.g. try:
###        python Example2.py -graph2

from neuromllite.NetworkGenerator import check_to_generate_or_run
from neuromllite import Simulation
import sys

check_to_generate_or_run(sys.argv, Simulation(id="Sim%s" % net.id, network=new_file))
