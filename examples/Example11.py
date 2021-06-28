from neuromllite import Network, Cell, InputSource, Population, Synapse, RectangularRegion, RandomLayout 
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example11_Synapses')
net.notes = 'Example 11: synaptic properties'
net.parameters = { 'input_amp':   0.23,
                   'weight':      1.01}
                   #'tau_syn':     2} 

cell = Cell(id='iafCell0', neuroml2_source_file='test_files/iaf.cell.nml')
#cell.parameters = { "tau_refrac":5, "i_offset":0 }
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

ampaSyn = Synapse(id='ampa', neuroml2_source_file='test_files/ampa.synapse.nml')
net.synapses.append(ampaSyn)
                      
nmdaSyn = Synapse(id='nmdaSyn', neuroml2_source_file='test_files/NMDA.synapse.nml')      
net.synapses.append(nmdaSyn)

net.projections.append(Projection(id='proj0',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse=ampaSyn.id,
                                  delay=0,
                                  weight='weight'))
net.projections[0].random_connectivity=RandomConnectivity(probability=1)

net.projections.append(Projection(id='proj1',
                                  presynaptic=p0.id, 
                                  postsynaptic=p1.id,
                                  synapse=nmdaSyn.id,
                                  delay=0,
                                  weight='weight'))
net.projections[1].random_connectivity=RandomConnectivity(probability=1)


net.inputs.append(Input(id='stim',
                        input_source=input_source.id,
                        population=p0.id,
                        percentage=100))

print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample11',
                 network=new_file,
                 duration='1000',
                 dt='0.01',
                 recordTraces={'all':'*'},
                 recordVariables={'synapses:%s:0/g'%ampaSyn.id:{'pop1':'*'},
                                  'synapses:%s:0/g'%nmdaSyn.id:{'pop1':'*'}},
                 recordSpikes={'pop0':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)

