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
    input_lists = {}

    """
    populations = {}
    projections = {}
    input_sources = {}

    inputs = []
    cells = {}"""

    pop_indices_vs_gids = {}

    def __init__(self, nl_network):
        print_v("Initiating Arbor...")
        self.nl_network = nl_network
        self.curr_gid = 0

    def handle_document_start(self, id, notes):
        print_v("Document: %s" % id)

    def handle_network(self, network_id, notes, temperature=None):

        print_v("Network: %s" % network_id)
        if temperature:
            print_v("  Temperature: " + temperature)
        if notes:
            print_v("  Notes: " + notes)

    def handle_population(
        self, population_id, component, size=-1, component_obj=None, properties={}
    ):

        sizeInfo = " as yet unspecified size"
        if size >= 0:
            sizeInfo = ", size: " + str(size) + " cells"
        if component_obj:
            compInfo = " (%s)" % component_obj.__class__.__name__
        else:
            compInfo = ""

        print_v(
            "Population: "
            + population_id
            + ", component: "
            + component
            + compInfo
            + sizeInfo
        )

        self.pops_vs_components[population_id] = component
        self.pop_indices_vs_gids[population_id] = {}

        """
        self.model = arbor.single_cell_model(self.cells[component])
        self.model.probe('voltage', '"center"', frequency=10000)

        exec('self.POP_%s = self.sim.Population(%s, self.cells["%s"], label="%s")'%(population_id,size,component,population_id))
        #exec('print_v(self.POP_%s)'%(population_id))
        exec('self.populations["%s"] = self.POP_%s'%(population_id,population_id))"""

    #
    #  Should be overridden to create specific cell instance
    #
    def handle_location(self, id, population_id, component, x, y, z):
        # self.printLocationInformation(id, population_id, component, x, y, z)

        self.pop_indices_vs_gids[population_id][id] = self.curr_gid
        self.curr_gid += 1

        """
        exec('self.POP_%s.positions[0][%s] = %s'%(population_id,id,x))
        exec('self.POP_%s.positions[1][%s] = %s'%(population_id,id,y))
        exec('self.POP_%s.positions[2][%s] = %s'%(population_id,id,z))"""

    def handle_projection(
        self,
        projName,
        prePop,
        postPop,
        synapse,
        hasWeights=False,
        hasDelays=False,
        type="projection",
        synapse_obj=None,
        pre_synapse_obj=None,
    ):

        synInfo = ""
        if synapse_obj:
            synInfo += " (syn: %s)" % synapse_obj.__class__.__name__

        if pre_synapse_obj:
            synInfo += " (pre comp: %s)" % pre_synapse_obj.__class__.__name__

        print_v(
            "Projection: "
            + projName
            + " ("
            + type
            + ") from "
            + prePop
            + " to "
            + postPop
            + " with syn: "
            + synapse
            + synInfo
        )

        self.proj_weights[projName] = np.zeros(
            (
                len(self.pop_indices_vs_gids[prePop]),
                len(self.pop_indices_vs_gids[postPop]),
            )
        )
        self.proj_delays[projName] = np.zeros(
            (
                len(self.pop_indices_vs_gids[prePop]),
                len(self.pop_indices_vs_gids[postPop]),
            )
        )

        """
        exec('self.projection__%s_conns = []'%(projName))"""

    #
    #  Should be overridden to handle network connection
    #
    def handle_connection(
        self,
        projName,
        id,
        prePop,
        postPop,
        synapseType,
        preCellId,
        postCellId,
        preSegId=0,
        preFract=0.5,
        postSegId=0,
        postFract=0.5,
        delay=0,
        weight=1,
    ):

        self.print_connection_information(
            projName, id, prePop, postPop, synapseType, preCellId, postCellId, weight
        )
        print_v(
            "Src cell: %d, seg: %f, fract: %f -> Tgt cell %d, seg: %f, fract: %f; weight %s, delay: %s ms"
            % (
                preCellId,
                preSegId,
                preFract,
                postCellId,
                postSegId,
                postFract,
                weight,
                delay,
            )
        )

        self.proj_weights[projName][preCellId][postCellId] = weight
        self.proj_delays[projName][preCellId][postCellId] = delay

    #
    #  Should be overridden to handle end of network connection
    #
    def finalise_projection(
        self, projName, prePop, postPop, synapse=None, type="projection"
    ):

        print_v(
            "Projection finalising: "
            + projName
            + " from "
            + prePop
            + " to "
            + postPop
            + " completed"
        )

    #
    #  Should be overridden to create input source array
    #
    def handle_input_list(
        self, inputListId, population_id, component, size, input_comp_obj=None
    ):

        self.print_input_information(inputListId, population_id, component, size)
        if input_comp_obj:
            print("Input comp: %s" % input_comp_obj)

        if size < 0:
            self.log.error(
                "Error! Need a size attribute in sites element to create spike source!"
            )
            return

        self.input_info[inputListId] = (population_id, component, input_comp_obj)
        self.input_lists[inputListId] = []

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(
        self, inputListId, id, cellId, segId=0, fract=0.5, weight=1
    ):

        population_id, component, input_comp_obj = self.input_info[inputListId]

        print_v(
            "Input: %s[%s] (%s), pop: %s, cellId: %i, seg: %i, fract: %f, weight: %f"
            % (inputListId, id, component, population_id, cellId, segId, fract, weight)
        )
        self.input_lists[inputListId].append((cellId, segId, fract, weight))

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input: %s completed" % inputName)

    def finalise_document(self):
        print_v("Building recipe with: %s" % self.pop_indices_vs_gids)
        print_v("Weights: %s" % self.proj_weights)
        print_v("Delays: %s" % self.proj_delays)
        print_v("Inputs: %s" % self.input_info)
        print_v("Input lists: %s" % self.input_lists)

        self.neuroML_arbor_recipe = NeuroML_Arbor_Recipe(
            self.nl_network,
            self.pop_indices_vs_gids,
            self.pops_vs_components,
            self.proj_weights,
            self.proj_delays,
            self.input_info,
            self.input_lists,
        )




# Create a NeuroML recipe
class NeuroML_Arbor_Recipe(arbor.recipe):
    def __init__(
        self,
        nl_network,
        pop_indices_vs_gids,
        pops_vs_components,
        proj_weights,
        proj_delays,
        input_info,
        input_lists,
    ):
        # The base C++ class constructor must be called first, to ensure that
        # all memory in the C++ class is initialized correctly.
        arbor.recipe.__init__(self)
        self.props = arbor.neuron_cable_properties()
        # self.cat = arbor.default_catalogue()
        # self.props.register(self.cat)
        self.pop_indices_vs_gids = pop_indices_vs_gids
        self.pops_vs_components = pops_vs_components
        self.nl_network = nl_network
        self.proj_weights = proj_weights
        self.proj_delays = proj_delays
        self.input_info = input_info
        self.input_lists = input_lists


    def create_arbor_cell(self, cell, gid, pop_id, index):

        if cell.arbor_cell == "cable_cell":

            default_tree = arbor.segment_tree()
            radius = (
                evaluate(cell.parameters["radius"], self.nl_network.parameters)
                if "radius" in cell.parameters
                else 3
            )

            default_tree.append(
                arbor.mnpos,
                arbor.mpoint(-1 * radius, 0, 0, radius),
                arbor.mpoint(radius, 0, 0, radius),
                tag=1,
            )

            labels = arbor.label_dict({"soma": "(tag 1)", "center": "(location 0 0.5)"})

            labels["root"] = "(root)"

            decor = arbor.decor()

            v_init = (
                evaluate(cell.parameters["v_init"], self.nl_network.parameters)
                if "v_init" in cell.parameters
                else -70
            )
            decor.set_property(Vm=v_init)

            decor.paint('"soma"', arbor.density(cell.parameters["mechanism"]))

            decor.place('"center"', arbor.spike_detector(0), "detector")

            for ip in self.input_info:
                if self.input_info[ip][0] == pop_id:
                    print_v("Stim: %s (%s) being placed on %s" % (ip,self.input_info[ip],pop_id))
                    for il in self.input_lists[ip]:
                        cellId, segId, fract, weight = il
                        if cellId == index:
                            if self.input_info[ip][1] == 'i_clamp': # TODO: remove hardcoding of this...
                                ic = arbor.iclamp(
                                    self.nl_network.parameters["input_del"],
                                    self.nl_network.parameters["input_dur"],
                                    self.nl_network.parameters["input_amp"],
                                )
                                print_v("Stim: %s on %s" % (ic,gid))
                                decor.place('"center"', ic, "iclamp")

            # (2) Mark location for synapse at the midpoint of branch 1 (the first dendrite).
            labels["synapse_site"] = "(location 0 0.5)"
            # (4) Attach a single synapse.
            decor.place('"synapse_site"', arbor.synapse("expsyn"), "syn")

            default_cell = arbor.cable_cell(default_tree, labels, decor)

            print_v("Created a new cell for gid %i: %s" % (gid, cell))
            print_v("%s" % (default_cell))

            return default_cell

    def get_pop_index(self, gid):
        # Todo: optimise...
        for pop_id in self.pop_indices_vs_gids:
            for index in self.pop_indices_vs_gids[pop_id]:
                if self.pop_indices_vs_gids[pop_id][index] == gid:
                    return pop_id, index

    def get_gid(self, pop_id, index):
        return self.pop_indices_vs_gids[pop_id][index]

    # (6) The num_cells method that returns the total number of cells in the model
    # must be implemented.
    def num_cells(self):
        ncells = sum(
            [
                len(self.pop_indices_vs_gids[pop_id])
                for pop_id in self.pop_indices_vs_gids
            ]
        )
        print_v("Getting num cells: %s" % (ncells))
        return ncells

    # (7) The cell_description method returns a cell
    def cell_description(self, gid):
        pop_id, index = self.get_pop_index(gid)
        comp = self.pops_vs_components[pop_id]

        a_cell = self.create_arbor_cell(
            self.nl_network.get_child(comp, "cells"), gid, pop_id, index
        )
        return a_cell


    # The kind method returns the type of cell with gid.
    # Note: this must agree with the type returned by cell_description.
    def cell_kind(self, gid):
        cell_kind = arbor.cell_kind.cable
        print_v("Getting cell_kind: %s" % (cell_kind))
        return cell_kind

    # (8) Make a ring network. For each gid, provide a list of incoming connections.
    def connections_on(self, gid):
        # Todo: optimise!!
        pop_id, index = self.get_pop_index(gid)
        conns = []
        for proj in self.nl_network.projections:
            if pop_id == proj.postsynaptic:
                w = self.proj_weights[proj.id]
                in_w = w.T[index]
                d = self.proj_delays[proj.id]
                in_d = d.T[index]
                print_v(
                    "Incoming connections for gid %i (%s[%s]), w: %s; d: %s"
                    % (gid, pop_id, index, in_w, in_d)
                )
                for src_index in range(len(in_w)):
                    if in_w[src_index] > 0:
                        src_gid = self.get_gid(proj.presynaptic, src_index)
                        conns.append(
                            arbor.connection(
                                (src_gid, "detector"),
                                "syn",
                                in_w[src_index],
                                in_d[src_index],
                            )
                        )

        print_v(
            "Making connections for gid %i (%s[%s]): %s" % (gid, pop_id, index, conns)
        )
        return conns

    def num_targets(self, gid):
        tot_in = len(self.connections_on(gid))
        print_v("num_targets for %i: %s" % (gid, tot_in))

        return 1

    def num_sources(self, gid):
        # Todo: optimise!!
        pop_id, index = self.get_pop_index(gid)
        tot_out = 0
        for proj in self.nl_network.projections:
            if pop_id == proj.presynaptic:
                w = self.proj_weights[proj.id]
                out_w = w[index]
                print_v(
                    "Outgoing connections for gid %i (%s[%s]), w: %s"
                    % (gid, pop_id, index, out_w)
                )
                for c in out_w:
                    if c > 0:
                        tot_out += 1

        print_v("num_sources for %i: %s" % (gid, tot_out))
        return 1

    # (9) Attach a generator to the first cell in the ring.
    def event_generators(self, gid):
        egs = []
        '''
        if gid == 0:
            sched = arbor.explicit_schedule([1])
            egs = [arbor.event_generator("syn", 0.1, sched)]'''

        print_v("Getting event_generators for %s: %s" % (gid, egs))
        return egs

    # (10) Place a probe at the root of each cell.
    def probes(self, gid):
        return [arbor.cable_probe_membrane_voltage('"root"')]

    def global_properties(self, kind):
        return self.props
