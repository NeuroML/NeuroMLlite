from neuromllite import *
from neuromllite.NetworkGenerator import *
from neuromllite.utils import load_network_json
import sys

################################################################################
###   Reuse network from Example2

filename = 'Example2_TestNetwork.json'
net = load_network_json(filename)
net.id = 'Example3_Network'
net.notes = 'Example 3: simple network with 2 populations of NeuroML2 cells, a projection between them and spiking input.'
print(net)
new_file = net.to_json_file()

################################################################################
###   Build Simulation object & save as JSON


sim = Simulation(id='SimExample3',
                 network=new_file,
                 duration='1000',
                 dt='0.025',
                 recordTraces={'all':'*'})
                 
sim.to_json_file()



################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)

