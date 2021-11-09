#
#
#   A class to build networks in BindsNET (work in progress)...
#
#

from neuromllite.utils import print_v
from neuromllite.utils import evaluate
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from pyneuroml.pynml import convert_to_units

import numpy as np

import bindsnet


class BindsNETHandler(DefaultNetworkHandler):

    pops_vs_components = {}
    pops_vs_bn_layers = {}

    proj_weights = {}
    proj_delays = {}

    input_info = {}

    """
    populations = {}
    projections = {}
    input_sources = {}

    inputs = []
    cells = {}"""

    pop_indices_vs_gids = {}

    def __init__(self, nl_network):
        print_v("Initiating BindsNET...")
        self.nl_network = nl_network
        self.curr_gid = 0

        self.bn_network = bindsnet.network.Network(dt=1.0)

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

        self.input_info[inputListId] = (population_id, component)

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(
        self, inputListId, id, cellId, segId=0, fract=0.5, weight=1
    ):

        population_id, component = self.input_info[inputListId]

        print_v(
            "Input: %s[%s] (%s), pop: %s, cellId: %i, seg: %i, fract: %f, weight: %f"
            % (inputListId, id, component, population_id, cellId, segId, fract, weight)
        )

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input: %s completed" % inputName)

    def finalise_document(self):
        print_v("Building network with: %s" % self.pop_indices_vs_gids)
        print_v("Weights: %s" % self.proj_weights)
        print_v("Delays: %s" % self.proj_delays)

        for pop in self.pop_indices_vs_gids:
            size = len(self.pop_indices_vs_gids[pop])
            comp = self.pops_vs_components[pop]
            cell = self.nl_network.get_child(comp, "cells")
            layer_name = "%s_bn_pop" % pop
            cmd = "self.pops_vs_bn_layers['%s'] = bindsnet.network.nodes.%s(%s)" % (
                pop,
                cell.bindsnet_node,
                size,
            )
            print(
                "Creating a population %s with %s instances of %s using: <%s>"
                % (pop, size, cell, cmd)
            )
            exec(cmd)
