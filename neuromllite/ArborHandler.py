#
#
#   A class to handle events by Arbor (work in progress)...
#
#

from neuromllite.utils import print_v
from neuromllite.utils import evaluate
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from pyneuroml.pynml import convert_to_units

import numpy as np


import arbor

class ArborHandler(DefaultNetworkHandler):

    pops_vs_components = {}

    proj_weights = {}
    proj_delays = {}

    input_info = {}

    '''
    populations = {}
    projections = {}
    input_sources = {}

    inputs = []
    cells = {}'''

    pop_indices_vs_gids = {}

    def __init__(self, nl_network):
        print_v("Initiating Arbor...")
        self.nl_network = nl_network
        self.curr_gid = 0


    def handle_document_start(self, id, notes):
        print_v("Document: %s"%id)


    def handle_network(self, network_id, notes, temperature=None):

        print_v("Network: %s"%network_id)
        if temperature:
            print_v("  Temperature: "+temperature)
        if notes:
            print_v("  Notes: "+notes)


    def handle_population(self,
                          population_id,
                          component, size=-1,
                          component_obj=None,
                          properties={}):

        sizeInfo = " as yet unspecified size"
        if size>=0:
            sizeInfo = ", size: "+ str(size)+ " cells"
        if component_obj:
            compInfo = " (%s)"%component_obj.__class__.__name__
        else:
            compInfo=""

        print_v("Population: "+population_id+", component: "+component+compInfo+sizeInfo)

        self.pops_vs_components[population_id] = component
        self.pop_indices_vs_gids[population_id]={}

        '''
        self.model = arbor.single_cell_model(self.cells[component])
        self.model.probe('voltage', '"center"', frequency=10000)

        exec('self.POP_%s = self.sim.Population(%s, self.cells["%s"], label="%s")'%(population_id,size,component,population_id))
        #exec('print_v(self.POP_%s)'%(population_id))
        exec('self.populations["%s"] = self.POP_%s'%(population_id,population_id))'''


    #
    #  Should be overridden to create specific cell instance
    #
    def handle_location(self, id, population_id, component, x, y, z):
        #self.printLocationInformation(id, population_id, component, x, y, z)

        self.pop_indices_vs_gids[population_id][id] = self.curr_gid
        self.curr_gid+=1

        '''
        exec('self.POP_%s.positions[0][%s] = %s'%(population_id,id,x))
        exec('self.POP_%s.positions[1][%s] = %s'%(population_id,id,y))
        exec('self.POP_%s.positions[2][%s] = %s'%(population_id,id,z))'''


    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):

        synInfo=""
        if synapse_obj:
            synInfo += " (syn: %s)"%synapse_obj.__class__.__name__

        if pre_synapse_obj:
            synInfo += " (pre comp: %s)"%pre_synapse_obj.__class__.__name__

        print_v("Projection: "+projName+" ("+type+") from "+prePop+" to "+postPop+" with syn: "+synapse+synInfo)

        self.proj_weights[projName] = np.zeros((len(self.pop_indices_vs_gids[prePop]),len(self.pop_indices_vs_gids[postPop])))
        self.proj_delays[projName] = np.zeros((len(self.pop_indices_vs_gids[prePop]),len(self.pop_indices_vs_gids[postPop])))

        '''
        exec('self.projection__%s_conns = []'%(projName))'''


    #
    #  Should be overridden to handle network connection
    #
    def handle_connection(self, projName, id, prePop, postPop, synapseType, \
                                                    preCellId, \
                                                    postCellId, \
                                                    preSegId = 0, \
                                                    preFract = 0.5, \
                                                    postSegId = 0, \
                                                    postFract = 0.5, \
                                                    delay = 0, \
                                                    weight = 1):

        self.print_connection_information(projName, id, prePop, postPop, synapseType, preCellId, postCellId, weight)
        print_v("Src cell: %d, seg: %f, fract: %f -> Tgt cell %d, seg: %f, fract: %f; weight %s, delay: %s ms" % (preCellId,preSegId,preFract,postCellId,postSegId,postFract, weight, delay))

        self.proj_weights[projName][preCellId][postCellId] = weight
        self.proj_delays[projName][preCellId][postCellId] = delay



    #
    #  Should be overridden to handle end of network connection
    #
    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):

        print_v("Projection finalising: "+projName+" from "+prePop+" to "+postPop+" completed")
        '''
        #exec('print(self.projection__%s_conns)'%projName)
        exec('self.projection__%s_connector = self.sim.FromListConnector(self.projection__%s_conns, column_names=["weight", "delay"])'%(projName,projName))

        exec('self.projections["%s"] = self.sim.Projection(self.populations["%s"],self.populations["%s"], ' % (projName,prePop,postPop) + \
                                                          'connector=self.projection__%s_connector, ' % projName + \
                                                          'synapse_type=self.sim.StaticSynapse(weight=%s, delay=%s), ' % (1,5) + \
                                                          'receptor_type="%s", ' % (self.receptor_types[synapse]) + \
                                                          'label="%s")'%projName)

        #exec('print(self.projections["%s"].describe())'%projName)'''



    #
    #  Should be overridden to create input source array
    #
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):

        self.print_input_information(inputListId, population_id, component, size)
        if input_comp_obj:
            print('Input comp: %s'%input_comp_obj)

        if size<0:
            self.log.error("Error! Need a size attribute in sites element to create spike source!")
            return

        self.input_info[inputListId] = (population_id, component)

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(self, inputListId, id, cellId, segId = 0, fract = 0.5, weight=1):

        population_id, component = self.input_info[inputListId]

        print_v("Input: %s[%s] (%s), pop: %s, cellId: %i, seg: %i, fract: %f, weight: %f" % (inputListId,id,component,population_id,cellId,segId,fract,weight))
        '''
        #Bad in many ways...
        for cell in self.cells:
            stim = self.inputs[0]
            print(dir(stim))
            print_v('Added: %s to %s'%(stim, cell))



        #exec('print  self.POP_%s'%(population_id))
        #exec('print  self.POP_%s[%s]'%(population_id,cellId))

        exec('self.POP_%s[%s].inject(self.input_sources[component]) '%(population_id,cellId))
        #exec('self.input_sources[component].inject_into(self.populations["%s"])'%(population_id))

        #exec('pulse = self.sim.DCSource(amplitude=0.9, start=19, stop=89)')
        #pulse.inject_into(pop_pre)
        #exec('self.populations["pop0"][0].inject(pulse)')'''


    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input: %s completed" % inputName)


    def finalise_document(self):
        print_v("Building recipe with: %s" % self.pop_indices_vs_gids)
        print_v("Weights: %s" % self.proj_weights)
        print_v("Delays: %s" % self.proj_delays)


        self.neuroML_arbor_recipe = NeuroML_Arbor_Recipe(self.nl_network,
                                                         self.pop_indices_vs_gids,
                                                         self.pops_vs_components,
                                                         self.proj_weights,
                                                         self.proj_delays)

def create_arbor_cell(cell, nl_network, gid):

    if cell.arbor_cell=='cable_cell':

        default_tree = arbor.segment_tree()
        radius = evaluate(cell.parameters['radius'], nl_network.parameters) if 'radius' in cell.parameters else 3

        default_tree.append(arbor.mnpos, arbor.mpoint(-1*radius, 0, 0, radius), arbor.mpoint(radius, 0, 0, radius), tag=1)

        labels = arbor.label_dict({'soma':   '(tag 1)',
                                   'center': '(location 0 0.5)'})

        labels['root'] = '(root)'

        decor = arbor.decor()

        v_init = evaluate(cell.parameters['v_init'], nl_network.parameters) if 'v_init' in cell.parameters else -70
        decor.set_property(Vm=v_init)

        decor.paint('"soma"', cell.parameters['mechanism'])

        if gid==0:
            ic = arbor.iclamp( nl_network.parameters['input_del'], nl_network.parameters['input_dur'], nl_network.parameters['input_amp'])
            print_v("Stim: %s"%ic)
            decor.place('"center"', ic)

        decor.place('"center"', arbor.spike_detector(-10))


        # (2) Mark location for synapse at the midpoint of branch 1 (the first dendrite).
        labels['synapse_site'] = '(location 0 0.5)'
        # (4) Attach a single synapse.
        decor.place('"synapse_site"', 'expsyn')

        default_cell = arbor.cable_cell(default_tree, labels, decor)

        print_v("Created a new cell for gid %i: %s"%(gid,cell))
        print_v("%s"%(default_cell))

        return default_cell


# Create a NeuroML recipe
class NeuroML_Arbor_Recipe(arbor.recipe):

    def __init__(self, nl_network, pop_indices_vs_gids, pops_vs_components, proj_weights, proj_delays):
        # The base C++ class constructor must be called first, to ensure that
        # all memory in the C++ class is initialized correctly.
        arbor.recipe.__init__(self)
        self.props = arbor.neuron_cable_properties()
        self.cat = arbor.default_catalogue()
        self.props.register(self.cat)
        self.pop_indices_vs_gids = pop_indices_vs_gids
        self.pops_vs_components = pops_vs_components
        self.nl_network = nl_network
        self.proj_weights = proj_weights
        self.proj_delays = proj_delays

    def get_pop_index(self, gid):
        #Todo: optimise...
        for pop_id in self.pop_indices_vs_gids:
            for index in self.pop_indices_vs_gids[pop_id]:
                if self.pop_indices_vs_gids[pop_id][index]==gid:
                    return pop_id, index

    def get_gid(self, pop_id, index):
        return self.pop_indices_vs_gids[pop_id][index]

    # (6) The num_cells method that returns the total number of cells in the model
    # must be implemented.
    def num_cells(self):
        ncells = sum([len(self.pop_indices_vs_gids[pop_id]) for pop_id in self.pop_indices_vs_gids])
        print_v('Getting num cells: %s'%(ncells))
        return ncells

    # (7) The cell_description method returns a cell
    def cell_description(self, gid):
        pop_id, index = self.get_pop_index(gid)
        comp = self.pops_vs_components[pop_id]

        return create_arbor_cell(self.nl_network.get_child(comp,'cells'),self.nl_network, gid)

    # The kind method returns the type of cell with gid.
    # Note: this must agree with the type returned by cell_description.
    def cell_kind(self, gid):
        cell_kind = arbor.cell_kind.cable
        print_v('Getting cell_kind: %s'%(cell_kind))
        return cell_kind

    # (8) Make a ring network. For each gid, provide a list of incoming connections.
    def connections_on(self, gid):
        # Todo: optimise!!
        pop_id, index = self.get_pop_index(gid)
        conns = []
        for proj in self.nl_network.projections:
            if pop_id==proj.postsynaptic:
                w = self.proj_weights[proj.id]
                in_w = w.T[index]
                d = self.proj_delays[proj.id]
                in_d = d.T[index]
                print_v('Incoming connections for gid %i (%s[%s]), w: %s; d: %s'%(gid,pop_id, index, in_w, in_d))
                for src_index in range(len(in_w)):
                    if in_w[src_index]>0:
                        src_gid = self.get_gid(proj.presynaptic, src_index)
                        conns.append(arbor.connection((src_gid,0), (gid,0), in_w[src_index], in_d[src_index]))

        print_v('Making connections for gid %i (%s[%s]): %s'%(gid,pop_id, index,conns))
        return conns

    def num_targets(self, gid):
        tot_in = len(self.connections_on(gid))
        print_v('num_targets for %i: %s'%(gid,tot_in))

        return 1

    def num_sources(self, gid):
        # Todo: optimise!!
        pop_id, index = self.get_pop_index(gid)
        tot_out = 0
        for proj in self.nl_network.projections:
            if pop_id==proj.presynaptic:
                w = self.proj_weights[proj.id]
                out_w = w[index]
                print_v('Outgoing connections for gid %i (%s[%s]), w: %s'%(gid,pop_id, index, out_w))
                for c in out_w:
                    if c>0: tot_out+=1


        print_v('num_sources for %i: %s'%(gid,tot_out))
        return 1

    # (9) Attach a generator to the first cell in the ring.
    def event_generators(self, gid):
        print_v('Getting event_generators for: %s'%(gid))
        if gid==0:
            sched = arbor.explicit_schedule([1])
            return [arbor.event_generator((0,0), 0.1, sched)]
        return []

    # (10) Place a probe at the root of each cell.
    def probes(self, gid):
        return [arbor.cable_probe_membrane_voltage('"root"')]

    def global_properties(self, kind):
        return self.props
