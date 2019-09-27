
from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Spikers')
net.notes = 'Example with spiking entities..'
net.parameters = { 'N': 10, 'weightInput': 10, 'input_rate': 40}

cell = Cell(id='iafcell', pynn_cell='IF_cond_alpha')
cell.parameters = { "tau_refrac":10 }
net.cells.append(cell)

input_cell = Cell(id='InputCell', pynn_cell='SpikeSourcePoisson')
input_cell.parameters = {
    'start':    0,
    'duration': 10000000000,
     'rate':    'input_rate'
}
net.cells.append(input_cell)

input_cell_100 = Cell(id='InputCell100', pynn_cell='SpikeSourcePoisson')
input_cell_100.parameters = {
    'start':    0,
    'duration': 10000000000,
     'rate':    100
}
net.cells.append(input_cell_100)


input_source_p0 = InputSource(id='poissonFiringSyn', neuroml2_source_file='../test_files/inputs.nml')
net.input_sources.append(input_source_p0)

input_source1 = InputSource(id='iclamp1', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':0.8, 'start':100., 'stop':900.})
                           
net.input_sources.append(input_source1)


pop0 = Population(id='pop0', size='N', component=cell.id, properties={'color':'.7 0 0'})
net.populations.append(pop0)
pop1 = Population(id='pop1', size='N', component=cell.id, properties={'color':'0 .7 0'})
net.populations.append(pop1)
pop2 = Population(id='pop2', size='N', component=cell.id, properties={'color':'0 .7 0.7'})
net.populations.append(pop2)
#

ipop0 = Population(id='input_pop0', size='N', component=input_cell.id, properties={'color':'.7 .7 .7'})
net.populations.append(ipop0)
ipop1 = Population(id='input_pop1', size='N', component=input_cell_100.id, properties={'color':'.7 .1 .7'})
net.populations.append(ipop1)

#pRS = Population(id='RSpop', size='N - int(N*fractionE)', component=cell.id, properties={'color':'0 0 .7'})

#net.populations.append(pRS)
'''
net.synapses.append(Synapse(id='ampa', neuroml2_source_file='test_files/ampa.synapse.nml'))
#net.synapses.append(Synapse(id='gaba', neuroml2_source_file='test_files/gaba.synapse.nml'))
                            
                            
net.projections.append(Projection(id='projEI',
                                  presynaptic=pE.id, 
                                  postsynaptic=pRS.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.2,
                                  random_connectivity=RandomConnectivity(probability=.8)))
                            
                            '''
net.inputs.append(Input(id='stim0',
                        input_source=input_source_p0.id,
                        population=pop0.id,
                        percentage=50,
                        weight='weightInput'))

net.inputs.append(Input(id='stim1',
                        input_source=input_source1.id,
                        population=pop1.id,
                        percentage=100))

net.inputs.append(Input(id='stim2',
                        input_source=input_source1.id,
                        population=pop2.id,
                        percentage=50))

print(net)
print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimSpikers',
                 network=new_file,
                 duration='10000',
                 dt='0.025',
                 recordTraces={'pop0':'*','pop1':'*','pop2':'*'},
                 recordSpikes={'all':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
