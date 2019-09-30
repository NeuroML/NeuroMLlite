
from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example10_Lorenz')
net.notes = 'Example 10: Lorenz'
net.parameters = { 'N': 1}

cell = Cell(id='lorenzCell', lems_source_file='test_files/Lorenz1963.xml')
net.cells.append(cell)


pop = Population(id='lorenzPop', size='1', component=cell.id, properties={'color':'.7 0 0'})
net.populations.append(pop)

                            
print(net)
print(net.to_json())
new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Build Simulation object & save as JSON

sim = Simulation(id='SimExample10',
                 network=new_file,
                 duration='1e4',
                 dt='1',
                 recordVariables={'x':{'all':'*'},
                                  'y':{'all':'*'},
                                  'z':{'all':'*'}},
                 plots2D={'X-Y':{'x_axis':'lorenzPop[0]/x',
                                 'y_axis':'lorenzPop[0]/y'},
                          'Y-Z':{'x_axis':'lorenzPop[0]/y',
                                 'y_axis':'lorenzPop[0]/z'},
                          'X-Z':{'x_axis':'lorenzPop[0]/x',
                                 'y_axis':'lorenzPop[0]/z'}},
                 plots3D={'X-Y-Z':{'x_axis':'lorenzPop[0]/x',
                                   'y_axis':'lorenzPop[0]/y',
                                   'z_axis':'lorenzPop[0]/z'}})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
