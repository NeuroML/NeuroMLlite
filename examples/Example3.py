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
net.to_json_file()

################################################################################
###   Build Simulation object & save as JSON


sim = Simulation(id='SimExample3',
                 duration='1000',
                 dt='0.025',
                 recordTraces='all')
                 
sim.to_json_file()


################################################################################
###   Run in some simulators

if '-netpyne' in sys.argv:
    generate_and_run(sim, net, simulator='NetPyNE')
    
elif '-jnmlnrn' in sys.argv:
    generate_and_run(sim, net, simulator='jNeuroML_NEURON')
    
elif '-jnmlnetpyne' in sys.argv:
    generate_and_run(sim, net, simulator='jNeuroML_NetPyNE')
    
elif '-sonata' in sys.argv:
    generate_and_run(sim, net, simulator='Sonata') # Will not "run" obviously...
    
elif '-graph' in sys.argv:
    generate_and_run(sim, net, simulator='Graph') # Will not "run" obviously...
    
else:
    
    generate_and_run(sim, net, simulator='jNeuroML')


#generate_and_run(sim, net, simulator='NEURON')







