
from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example8_Extension')
net.notes = 'Example 8: general testing...'

net.seed = 7890
net.temperature = 32

net.parameters = { 'N': 10, 'fractionE': 0.8, 'weightInput': 1}

cell = Cell(id='hhcell', neuroml2_source_file='test_files/hhcell.cell.nml')
net.cells.append(cell)


input_source = InputSource(id='poissonFiringSyn', neuroml2_source_file='test_files/inputs.nml')
net.input_sources.append(input_source)
'''
input_source = InputSource(id='iclamp0', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':0.2, 'start':100., 'stop':900.})'''
                           
net.input_sources.append(input_source)


pE = Population(id='Epop', size='int(N*fractionE)', component=cell.id, properties={'color':'.7 0 0'})
pRS = Population(id='RSpop', size='N - int(N*fractionE)', component=cell.id, properties={'color':'0 0 .7'})

net.populations.append(pE)
net.populations.append(pRS)

net.synapses.append(Synapse(id='ampa', neuroml2_source_file='test_files/ampa.synapse.nml'))
net.synapses.append(Synapse(id='gaba', neuroml2_source_file='test_files/gaba.synapse.nml'))
                            
                            
net.projections.append(Projection(id='projEI',
                                  presynaptic=pE.id, 
                                  postsynaptic=pRS.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.2,
                                  random_connectivity=RandomConnectivity(probability=.8)))
                            
                            
net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=pE.id,
                        percentage=50,
                        weight='weightInput'))

print(net)
print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample8',
                 network=new_file,
                 duration='1000',
                 seed='1111',
                 dt='0.025',
                 recordTraces={'all':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
