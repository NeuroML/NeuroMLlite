
from neuromllite import Network, Cell, InputSource, Population, Synapse
from neuromllite import Projection, RandomConnectivity, Input, Simulation
import sys

################################################################################
###   Build new network

net = Network(id='Example9_HindmarshRose')
net.notes = 'Example 9: HindmarshRose'
net.parameters = { 'N': 1}

cell = Cell(id='hrCell', 
            lems_source_file='test_files/HindmarshRose3d.xml')
cell.parameters = {}

params = {'a':1, 'b':3, 'c':-3.0, 'd':5.0, 's':4.0, 'I':5.0, 'x1':-1.3, 'r':0.002, 'x0':-1.3, 'y0':-1.0, 'z0':1.0}

for p in params:
    cell.parameters[p]=p
    net.parameters[p]=params[p]
    
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
                                  'z':{'all':'*'}},
                 plots2D={'X-Y':{'x_axis':'hrPop[0]/x',
                                 'y_axis':'hrPop[0]/y'},
                          'Y-Z':{'x_axis':'hrPop[0]/y',
                                 'y_axis':'hrPop[0]/z'},
                          'X-Z':{'x_axis':'hrPop[0]/x',
                                 'y_axis':'hrPop[0]/z'}},
                 plots3D={'X-Y-Z':{'x_axis':'hrPop[0]/x',
                                   'y_axis':'hrPop[0]/y',
                                   'z_axis':'hrPop[0]/z'}})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)
