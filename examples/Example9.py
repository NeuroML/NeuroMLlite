
from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example9_HindmarshRose')
net.notes = 'Example 9: HindmarshRose'
net.parameters = { 'N': 10}

cell = Cell(id='hrCell', lems_source_file='test_files/HindmarshRose3d.xml')
net.cells.append(cell)




pop = Population(id='hrPop', size='1', component=cell.id, properties={'color':'.7 0 0'})


net.populations.append(pop)

                            
                            

print(net)
print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample9',
                 network=new_file,
                 duration='1000000',
                 dt='25',
                 recordVariables={'x':{'all':'*'},
                                  'y':{'all':'*'},
                                  'z':{'all':'*'}})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
