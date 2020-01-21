from neuromllite import Network, Cell, InputSource, Population, Synapse, RectangularRegion, RandomLayout 
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example11_Synapses')
net.notes = 'Example 11: synaptic properties'
net.parameters = { 'input_amp':   0.99,
                   'weight':      1,
                   'tau_syn':     2} 

cell = Cell(id='testcell', pynn_cell='IF_cond_alpha')
cell.parameters = { "tau_refrac":5, "i_offset":0 }
net.cells.append(cell)


input_source = InputSource(id='i_clamp', 
                           pynn_input='DCSource', 
                           parameters={'amplitude':'input_amp', 'start':200., 'stop':800.})
net.input_sources.append(input_source)

r1 = RectangularRegion(id='region1', x=0,y=0,z=0,width=1000,height=100,depth=1000)
net.regions.append(r1)

p0 = Population(id='pop0', size=1, component=cell.id, properties={'color':'1 0 0'},random_layout = RandomLayout(region=r1.id))
p1 = Population(id='pop1', size=1, component=cell.id, properties={'color':'0 1 0'},random_layout = RandomLayout(region=r1.id))

net.populations.append(p0)
net.populations.append(p1)

net.synapses.append(Synapse(id='ampaSyn', 
                            pynn_receptor_type='excitatory', 
                            pynn_synapse_type='cond_alpha', 
                            parameters={'e_rev':-10, 'tau_syn':'tau_syn'}))

net.projections.append(Projection(id='proj0',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse='ampaSyn',
                                  delay=2,
                                  weight='weight'))
net.projections[0].random_connectivity=RandomConnectivity(probability=1)


net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=p0.id,
                        percentage=50))

print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample11',
                 network=new_file,
                 duration='1000',
                 dt='0.01',
                 recordTraces={'all':'*'},
                 recordVariables={'synapses:ampaSyn:0/g':{'pop1':'*'}},
                 recordSpikes={'pop0':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)

