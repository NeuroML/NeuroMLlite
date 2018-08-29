from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
from neuromllite.NetworkGenerator import generate_and_run
from neuromllite.NetworkGenerator import generate_neuroml2_from_network
import sys

################################################################################
###   Build new network

net = Network(id='Example7_Brunel2000')
net.notes = 'Example 7: based on network of Brunel 2000'

net.parameters = { 'g':4, 'eta':'1', 'order':5}

cell = Cell(id='ifcell', pynn_cell='IF_cond_alpha')

                   
cell.parameters = { 'tau_m':       20, 
                    'tau_refrac':  2,
                    'v_rest':      0,
                    'v_reset':     0,
                    'v_thresh':    20,
                    'cm':          0.001,
                    "i_offset":    0}

#cell = Cell(id='hhcell', neuroml2_source_file='test_files/hhcell.cell.nml')
net.cells.append(cell)

expoisson = Cell(id='expoisson', pynn_cell='SpikeSourcePoisson')
expoisson.parameters = { 'rate':       200 }
net.cells.append(expoisson)


'''
input_source = InputSource(id='iclamp0', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':0.002, 'start':100., 'stop':900.})

input_source = InputSource(id='poissonFiringSyn', 
                           neuroml2_input='poissonFiringSynapse',
                           parameters={'average_rate':"eta", 'synapse':"ampa", 'spike_target':"./ampa"})

                           

net.input_sources.append(input_source)'''

pE = Population(id='Epop', size='4*order', component=cell.id, properties={'color':'1 0 0'})
pEpoisson = Population(id='Einput', size='4*order', component=expoisson.id, properties={'color':'.5 0 0'})
pI = Population(id='Ipop', size='1*order', component=cell.id, properties={'color':'0 0 1'})

net.populations.append(pE)
net.populations.append(pEpoisson)
net.populations.append(pI)


net.synapses.append(Synapse(id='ampa', 
                            pynn_receptor_type='excitatory', 
                            pynn_synapse_type='curr_alpha', 
                            parameters={'tau_syn':0.1}))
net.synapses.append(Synapse(id='gaba', 
                            pynn_receptor_type='inhibitory', 
                            pynn_synapse_type='curr_alpha', 
                            parameters={'tau_syn':0.1}))
                            

net.projections.append(Projection(id='projEinput',
                                  presynaptic=pEpoisson.id, 
                                  postsynaptic=pE.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.002,
                                  random_connectivity=RandomConnectivity(probability=.5)))
'''           
net.projections.append(Projection(id='projEE',
                                  presynaptic=pE.id, 
                                  postsynaptic=pE.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.002,
                                  random_connectivity=RandomConnectivity(probability=.5)))'''
                                  
net.projections.append(Projection(id='projEI',
                                  presynaptic=pE.id, 
                                  postsynaptic=pI.id,
                                  synapse='ampa',
                                  delay=2,
                                  weight=0.002,
                                  random_connectivity=RandomConnectivity(probability=.5)))
'''
net.projections.append(Projection(id='projIE',
                                  presynaptic=pI.id, 
                                  postsynaptic=pE.id,
                                  synapse='gaba',
                                  delay=2,
                                  weight=0.02,
                                  random_connectivity=RandomConnectivity(probability=.5)))

net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=pE.id,
                        percentage=50))'''

print(net)
print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample7',
                 network=new_file,
                 duration='1000',
                 dt='0.025',
                 recordTraces={pE.id:'*',pI.id:'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)

