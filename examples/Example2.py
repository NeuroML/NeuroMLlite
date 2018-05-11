from neuromllite import RandomLayout, Cell, Synapse, InputSource, Input, RectangularRegion
from neuromllite.NetworkGenerator import generate_network
from neuromllite.NetworkGenerator import generate_neuroml2_from_network
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

################################################################################
###   Reuse network from Example1

from Example1 import net

net.notes = "A simple network with 2 populations & projection between them. "+ \
            "Cells are specified to be NeuroML 2 HH cell models & pre population " \
            "is given a spiking input."


################################################################################
###   Add some elements to the network & save new JSON

r1 = RectangularRegion(id='region1', x=0,y=0,z=0,width=1000,height=100,depth=1000)
r2 = RectangularRegion(id='region2', x=0,y=200,z=0,width=1000,height=100,depth=1000)
net.regions.append(r1)
net.regions.append(r2)

net.populations[0].random_layout = RandomLayout(region=r1.id)
net.populations[1].random_layout = RandomLayout(region=r2.id)

net.populations[0].component = 'hhcell'
net.populations[1].component = 'hhcell'

net.cells.append(Cell(id='hhcell', neuroml2_source_file='test_files/hhcell.cell.nml'))
net.synapses.append(Synapse(id='ampa', neuroml2_source_file='test_files/ampa.synapse.nml'))

input_source = InputSource(id='poissonFiringSyn', neuroml2_source_file='test_files/inputs.nml')
net.input_sources.append(input_source)

net.inputs.append(Input(id='stim_%s'%net.populations[0].id,
                            input_source=input_source.id,
                            population=net.populations[0].id,
                            percentage=80))

print(net.to_json())
net.to_json_file('Example2_%s.json'%net.id)


################################################################################
###   Use a handler which just prints info on positions, etc.

def_handler = DefaultNetworkHandler()

generate_network(net, def_handler)


################################################################################
###   Builds a NeuroML 2 representation, save as XML

generate_neuroml2_from_network(net, 
                               nml_file_name='Example2_%s.net.nml'%net.id)

################################################################################
###   Builds a NeuroML 2 representation, save as HDF5

generate_neuroml2_from_network(net, 
                               nml_file_name='Example2_%s.net.nml.h5'%net.id,
                               format='hdf5')
                               