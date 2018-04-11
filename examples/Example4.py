from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
from neuromllite.NetworkGenerator import generate_and_run
import sys

################################################################################
###   Build new network

net = Network(id='Example4_PyNN')
net.notes = 'Example 4: a network with PyNN cells & inputs'

cell = Cell(id='testcell', pynn_cell='IF_cond_alpha')
cell.parameters = { "tau_refrac":5, "i_offset":.1 }
net.cells.append(cell)

cell2 = Cell(id='testcell2', pynn_cell='IF_cond_alpha')
cell2.parameters = { "tau_refrac":5, "i_offset":-.1 }
net.cells.append(cell2)

input_source = InputSource(id='iclamp0', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':0.99, 'start':200., 'stop':800.})
net.input_sources.append(input_source)


p0 = Population(id='pop0', size=2, component=cell.id)
p1 = Population(id='pop1', size=2, component=cell2.id)
p2 = Population(id='pop2', size=1, component=cell2.id)

net.populations.append(p0)
net.populations.append(p1)
net.populations.append(p2)

net.synapses.append(Synapse(id='ampa', 
                            pynn_receptor_type='excitatory', 
                            pynn_synapse_type='cond_alpha', 
                            parameters={'e_rev':-10, 'tau_syn':2}))
net.synapses.append(Synapse(id='gaba', 
                            pynn_receptor_type='inhibitory', 
                            pynn_synapse_type='cond_alpha', 
                            parameters={'e_rev':-80, 'tau_syn':10}))

net.projections.append(Projection(id='proj0',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.02))
net.projections[0].random_connectivity=RandomConnectivity(probability=1)

net.projections.append(Projection(id='proj1',
                                  presynaptic=p0.id, 
                                  postsynaptic=p2.id,
                                  synapse='gaba',
                                  delay=2,
                                  weight=0.02))
net.projections[1].random_connectivity=RandomConnectivity(probability=1)

net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=p0.id,
                        percentage=70))

print(net.to_json())
net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample4',
                 duration='1000',
                 dt='0.025',
                 recordTraces='all')
                 
sim.to_json_file()


################################################################################
###   Run in some simulators

print("**** Generating and running ****")


if '-pynnnest' in sys.argv:
    generate_and_run(sim, net, simulator='PyNN_NEST')
    
elif '-pynnnrn' in sys.argv:
    generate_and_run(sim, net, simulator='PyNN_NEURON')
    
elif '-pynnbrian' in sys.argv:
    generate_and_run(sim, net, simulator='PyNN_Brian')
    
elif '-jnml' in sys.argv:
    generate_and_run(sim, net, simulator='jNeuroML')
    
elif '-jnmlnrn' in sys.argv:
    generate_and_run(sim, net, simulator='jNeuroML_NEURON')
    
elif '-jnmlnetpyne' in sys.argv:
    generate_and_run(sim, net, simulator='jNeuroML_NetPyNE')
    
else:
    generate_and_run(sim, net, simulator='PyNN_NeuroML')

