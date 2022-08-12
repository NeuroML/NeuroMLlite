from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation, RectangularRegion, RandomLayout
import sys

################################################################################
###   Build new network

net = Network(id="Example12_MultiComp")
net.notes = "Example 12: Multicompartmental cells..."

net.seed = 1234
net.temperature = 32.0

net.parameters = {"N": 20,
                  "fractionE": 0.7,
                  "weightInput": 0.7,
                  "prob_e_e": 0.1,
                  "prob_e_i": 0.9,
                  "prob_i_e": 0.8,
                  "prob_i_i": 0.3,
                  "global_delay": 2}

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
    id="pop_pyr",
    size="int(N*fractionE)",
    component=pyr_cell.id,
    properties={"color": ".8 0 0"},
    random_layout=RandomLayout(region=r1.id),
)
pI = Population(
    id="pop_bask",
    size="N - int(N*fractionE)",
    component=bask_cell.id,
    properties={"color": "0 0 .8"},
    random_layout=RandomLayout(region=r1.id),
)

net.populations.append(pE)
net.populations.append(pI)

syn_e_e = Synapse(id="AMPA_syn", neuroml2_source_file="test_files/acnet2/AMPA_syn.synapse.nml")
net.synapses.append(syn_e_e)
syn_e_i = Synapse(id="AMPA_syn_inh", neuroml2_source_file="test_files/acnet2/AMPA_syn_inh.synapse.nml")
net.synapses.append(syn_e_i)
syn_i_e = Synapse(id="GABA_syn", neuroml2_source_file="test_files/acnet2/GABA_syn.synapse.nml")
net.synapses.append(syn_i_e)
syn_i_i = Synapse(id="GABA_syn_inh", neuroml2_source_file="test_files/acnet2/GABA_syn_inh.synapse.nml")
net.synapses.append(syn_i_i)



net.projections.append(
    Projection(
        id="projEE",
        presynaptic=pE.id,
        postsynaptic=pE.id,
        synapse=syn_e_e.id,
        delay="global_delay",
        random_connectivity=RandomConnectivity(probability="prob_e_e"),
    )
)
net.projections.append(
    Projection(
        id="projEI",
        presynaptic=pE.id,
        postsynaptic=pI.id,
        synapse=syn_e_i.id,
        delay="global_delay",
        random_connectivity=RandomConnectivity(probability="prob_e_i"),
    )
)



net.projections.append(
    Projection(
        id="projIE",
        presynaptic=pI.id,
        postsynaptic=pE.id,
        synapse=syn_i_e.id,
        delay="global_delay",
        random_connectivity=RandomConnectivity(probability="prob_i_e"),
    )
)
net.projections.append(
    Projection(
        id="projII",
        presynaptic=pI.id,
        postsynaptic=pI.id,
        synapse=syn_i_i.id,
        delay="global_delay",
        random_connectivity=RandomConnectivity(probability="prob_i_i"),
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
