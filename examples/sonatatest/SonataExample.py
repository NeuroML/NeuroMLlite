from neuromllite import Network, Cell, InputSource, Population, Synapse, RectangularRegion, RandomLayout 
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='SonataExample')
net.notes = 'Example for testing Sonata'
net.parameters = { 'input_amp':       0.190,
                   'input_del':       100,
                   'input_dur':       800} 

cell = Cell(id='testcell', pynn_cell='IF_cond_alpha')
cell.parameters = { "i_offset":   0, 
                    "cm":         0.117,
                    "tau_m":      22.1,
                    "tau_refrac": 3,
                    "v_reset":    -50,
                    "v_rest":     -78,
                    "v_thresh":   -47 }
                     
                    
net.cells.append(cell)
'''
cell2 = Cell(id='testcell2', pynn_cell='IF_cond_alpha')
cell2.parameters = { "tau_refrac":5, "i_offset":-.1 }
net.cells.append(cell2)'''

input_source = InputSource(id='i_clamp', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':'input_amp', 'start':'input_del', 'stop':'input_del+input_dur'})
net.input_sources.append(input_source)

r1 = RectangularRegion(id='region1', x=0,y=0,z=0,width=1000,height=100,depth=1000)
net.regions.append(r1)

p0 = Population(id='pop0', size=2, component=cell.id, properties={'color':'1 0 0'},random_layout = RandomLayout(region=r1.id))
net.populations.append(p0)
'''
p1 = Population(id='pop1', size=2, component=cell2.id, properties={'color':'0 1 0'},random_layout = RandomLayout(region=r1.id))
p2 = Population(id='pop2', size=1, component=cell2.id, properties={'color':'0 0 1'},random_layout = RandomLayout(region=r1.id))

net.populations.append(p1)
net.populations.append(p2)'''

'''
net.synapses.append(Synapse(id='ampaSyn', 
                            pynn_receptor_type='excitatory', 
                            pynn_synapse_type='cond_alpha', 
                            parameters={'e_rev':-10, 'tau_syn':2}))
net.synapses.append(Synapse(id='gabaSyn', 
                            pynn_receptor_type='inhibitory', 
                            pynn_synapse_type='cond_alpha', 
                            parameters={'e_rev':-80, 'tau_syn':10}))

net.projections.append(Projection(id='proj0',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse='ampaSyn',
                                  delay=2,
                                  weight=0.02))
net.projections[0].random_connectivity=RandomConnectivity(probability=1)

net.projections.append(Projection(id='proj1',
                                  presynaptic=p0.id, 
                                  postsynaptic=p2.id,
                                  synapse='gabaSyn',
                                  delay=2,
                                  weight=0.01))
net.projections[1].random_connectivity=RandomConnectivity(probability=1)'''

net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=p0.id,
                        percentage=50))

print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimSonataExample',
                 network=new_file,
                 duration='1000',
                 dt='0.01',
                 recordTraces={'all':'*'},
                 recordSpikes={'pop0':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)

