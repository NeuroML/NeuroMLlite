from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation, RectangularRegion, RandomLayout
import sys

################################################################################
###   Build new network

net = Network(id="Example12_MultiComp")
net.notes = "Example 12: Multicompartmental cells..."

net.seed = 7890
net.temperature = 32.0

net.parameters = {"N": 10, "fractionE": 0.8, "weightInput": 1}

r1 = RectangularRegion(
    id="region1", x=0, y=0, z=0, width=1000, height=100, depth=1000
)
net.regions.append(r1)

pyr_cell = Cell(id="pyr_4_sym", neuroml2_source_file="test_files/acnet2/pyr_4_sym.cell.nml")
net.cells.append(pyr_cell)
bask_cell = Cell(id="bask", neuroml2_source_file="test_files/acnet2/bask.cell.nml")
net.cells.append(bask_cell)


input_source = InputSource(
    id="poissonFiringSyn", neuroml2_source_file="test_files/inputs.nml"
)
net.input_sources.append(input_source)
"""
input_source = InputSource(id='iclamp0',
                           pynn_input='DCSource',
                           parameters={'amplitude':0.2, 'start':100., 'stop':900.})"""

net.input_sources.append(input_source)


pE = Population(
    id="popE",
    size="int(N*fractionE)",
    component=pyr_cell.id,
    properties={"color": ".7 0 0"},
    random_layout=RandomLayout(region=r1.id),
)
pI = Population(
    id="popI",
    size="N - int(N*fractionE)",
    component=bask_cell.id,
    properties={"color": "0 0 .7"},
    random_layout=RandomLayout(region=r1.id),
)

net.populations.append(pE)
net.populations.append(pI)

net.synapses.append(
    Synapse(id="ampa", neuroml2_source_file="test_files/ampa.synapse.nml")
)
net.synapses.append(
    Synapse(id="gaba", neuroml2_source_file="test_files/gaba.synapse.nml")
)


net.projections.append(
    Projection(
        id="projEI",
        presynaptic=pE.id,
        postsynaptic=pI.id,
        synapse="ampa",
        delay=2,
        weight=0.2,
        random_connectivity=RandomConnectivity(probability=0.8),
    )
)


net.inputs.append(
    Input(
        id="stim",
        input_source=input_source.id,
        population=pE.id,
        percentage=100,
        weight="weightInput",
    )
)

print(net)
print(net.to_json())
new_file = net.to_json_file("%s.json" % net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(
    id="Sim%s"%net.id,
    network=new_file,
    duration="1000",
    seed="1111",
    dt="0.025",
    record_traces={"all": "*"},
    record_spikes={
        pE.id: "*",
        pI.id: "*",
    }
)

sim.to_json_file()


################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
