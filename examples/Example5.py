from neuromllite import Network, Cell, Synapse, NetworkReader, InputSource, Input
from neuromllite.NetworkGenerator import generate_neuroml2_from_network
import sys


################################################################################
###   Build new network

percent = 5
net = Network(id='BBP_%spercent'%percent, notes = 'A network with the Blue Brain Project connectivity data (%s% of total cells)')

default_cell = Cell(id='hhcell', neuroml2_source_file='test_files/hhcell.cell.nml')

net.network_reader = NetworkReader(type='BBPConnectomeReader',
                                   parameters={'id':net.id,
                                               'filename':'test_files/cons_locs_pathways_mc0_Column.h5',
                                               'percentage_cells_per_pop':percent,
                                               'DEFAULT_CELL_ID':default_cell.id,
                                               'cell_info':{default_cell.id:default_cell}})
                            
net.cells.append(default_cell)
net.synapses.append(Synapse(id='ampa', neuroml2_source_file='test_files/ampa.synapse.nml'))
net.synapses.append(Synapse(id='gaba', neuroml2_source_file='test_files/gaba.synapse.nml'))

                            
input_source = InputSource(id='poissonFiringSyn', neuroml2_source_file='test_files/inputs.nml')
net.input_sources.append(input_source)

for pop in ['L4_PC']:
    net.inputs.append(Input(id='stim_%s'%pop,
                            input_source=input_source.id,
                            population=pop,
                            percentage=80))

new_file = net.to_json_file('%s.json'%net.id)


################################################################################
###   Builds a NeuroML 2 representation, save as XML

format_='xml'
nml_file_name, nml_doc = generate_neuroml2_from_network(net, 
                               nml_file_name='%s.net.nml%s'%(net.id, '.h5' if format_=='hdf5' else ''), 
                               format=format_)


from neuromllite import Simulation

recordTraces={'all':'*'}
recordSpikes={'all':'*'}


sim = Simulation(id='SimExample5',
                 network=new_file,
                 duration=500,
                 dt=0.025,
                 recordTraces=recordTraces,
                 recordSpikes=recordSpikes)
           
sim.to_json_file()           
                               

################################################################################
###   Run in some simulators

from neuromllite.NetworkGenerator import check_to_generate_or_run
import sys

check_to_generate_or_run(sys.argv, sim)