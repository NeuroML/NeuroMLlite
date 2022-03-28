#
#
#   A class to write to the MDF format (https://github.com/ModECI/MDF)...
#
#

from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
from neuromllite.utils import print_v
from modelspec.utils import save_to_json_file
from modelspec.utils import save_to_yaml_file
from modelspec.utils import locate_file
from modelspec.utils import evaluate
from pyneuroml.pynml import get_value_in_si

import lems.api as lems  # from pylems


class MDFHandler(DefaultNetworkHandler):
    def __init__(self, nl_network):
        print_v("Initiating PsyNeuLink handler")
        self.nl_network = nl_network

    def handle_document_start(self, id, notes):

        print_v("Parsing for PsyNeuLink export: %s" % id)
        self.id = id

        self.mdf_info = {}

        # from modeci_mdf import MODECI_MDF_VERSION
        MODECI_MDF_VERSION = "0.3"

        self.mdf_info[self.id] = {}
        self.mdf_info[self.id]["format"] = "ModECI MDF v%s" % MODECI_MDF_VERSION
        self.mdf_info[self.id]["graphs"] = {}

        self.pnl_additions = False

    def finalise_document(self):

        print_v("Writing file for...: %s" % self.id)

        save_to_json_file(self.mdf_info, "%s.mdf.json" % self.id, indent=4)
        save_to_yaml_file(self.mdf_info, "%s.mdf.yaml" % self.id, indent=4)
        """save_to_json_file(self.mdf_info_hl, '%s.bids-mdf.highlevel.json'%self.id, indent=4)"""

    def handle_network(self, network_id, notes, temperature=None):

        print_v("Network: %s" % network_id)
        self.network_id = network_id

        if temperature:
            print_v("  Temperature: " + temperature)
        if notes:
            print_v("  Notes: " + notes)

        self.mdf_graph = {}
        self.mdf_graph["notes"] = notes
        self.mdf_graph["nodes"] = {}
        self.mdf_graph["edges"] = {}

        self.mdf_info[self.id]["graphs"][network_id] = self.mdf_graph

    def _convert_value(self, val):

        funcs = ["exp"]
        for f in funcs:
            if "%s(" % f in val:
                val = val.replace("%s(" % f, "math.%s(" % f)

        val = evaluate(val)  # catch if it's an int etc.
        return val

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
            + ", properties: %s"% properties
        )

        if size >= 0:
            for i in range(size):
                node_id = "%s_%i" % (population_id, i)
                node = {}

                comp = self.nl_network.get_child(component, "cells")
                base_dir = "./"  # for now...

                if properties:
                    node["metadata"] = properties

                node["parameters"] = {}
                node["input_ports"] = {}
                node["output_ports"] = {}
                if comp is not None:
                    if comp.lems_source_file:
                        fname = locate_file(comp.lems_source_file, base_dir)
                        model = MDFHandler._load_lems_file_with_neuroml2_types(fname)
                        lems_comp = model.components.get(component)

                    if comp.neuroml2_cell:
                        model = MDFHandler._get_lems_model_with_neuroml2_types()
                        lems_comp = lems.Component(
                            id_=comp.id, type_=comp.neuroml2_cell
                        )
                        for p in comp.parameters:
                            lems_comp.set_parameter(
                                p,
                                evaluate(
                                    comp.parameters[p], self.nl_network.parameters
                                ),
                            )

                    print_v("All LEMS comps in model: %s" % model.components.keys())
                    print_v("This comp: %s" % lems_comp)
                    comp_type_name = lems_comp.type
                    lems_comp_type = model.component_types.get(comp_type_name)
                    notes = "Cell: [%s] is defined in %s and in Lems is: %s" % (
                        comp,
                        comp.lems_source_file,
                        lems_comp,
                    )

                    node["notes"] = notes

                    for p in lems_comp.parameters:
                        node["parameters"][p] = {
                            "value": get_value_in_si(evaluate(lems_comp.parameters[p]))
                        }

                    for c in lems_comp_type.constants:
                        node["parameters"][c.name] = {"value": get_value_in_si(c.value)}

                    for sv in lems_comp_type.dynamics.state_variables:
                        node["parameters"][sv.name] = {}
                        if sv.exposure:
                            node["output_ports"][sv.exposure] = {"value": sv.name}

                    for dv in lems_comp_type.dynamics.derived_variables:

                        print_v(
                            "Converting: %s (exp: %s) = [%s] or [%s]"
                            % (dv.name, dv.exposure, dv.value, dv.select)
                        )
                        if dv.name == "INPUT":
                            node["input_ports"][dv.name] = {}
                        else:
                            if dv.value is not None:
                                node["parameters"][dv.name] = {
                                    "value": self._convert_value(dv.value)
                                }
                                if dv.exposure:
                                    node["output_ports"][dv.exposure] = {
                                        "value": dv.name
                                    }
                            if dv.select is not None:
                                in_port = dv.select.replace("[*]/", "_")
                                node["input_ports"][in_port] = {}
                                node["parameters"][dv.name] = {"value": in_port}

                    conditions = 0
                    for eh in lems_comp_type.dynamics.event_handlers:

                        print_v("Converting: %s (type: %s)" % (eh, type(eh)))
                        if type(eh) == lems.OnStart:
                            for a in eh.actions:
                                if type(a) == lems.StateAssignment:
                                    node["parameters"][a.variable][
                                        "default_initial_value"
                                    ] = a.value
                        if type(eh) == lems.OnCondition:
                            test = (
                                eh.test.replace(".gt.", ">")
                                .replace(".geq.", ">=")
                                .replace(".lt.", "<")
                                .replace(".leq.", "<=")
                                .replace(".eq.", "==")
                            )
                            for a in eh.actions:
                                if type(a) == lems.StateAssignment:
                                    if (
                                        not "conditions"
                                        in node["parameters"][a.variable]
                                    ):
                                        node["parameters"][a.variable][
                                            "conditions"
                                        ] = {}

                                    node["parameters"][a.variable]["conditions"][
                                        "condition_%i" % conditions
                                    ] = {"test": test, "value": a.value}
                            conditions += 1

                    for td in lems_comp_type.dynamics.time_derivatives:
                        node["parameters"][td.variable][
                            "time_derivative"
                        ] = self._convert_value(td.value)

                self.mdf_graph["nodes"][node_id] = node

    # TODO: move to pylems!
    @classmethod
    def _get_all_children_in_lems(cls, component_type, model, child_type):
        c = []
        if child_type == "exposure":
            for e in component_type.exposures:
                c.append(e)

        if component_type.extends:
            ect = model.component_types[component_type.extends]
            c.extend(cls._get_all_children_in_lems(ect, model, child_type))

        return c

    # TODO: move to pyneuroml!
    @classmethod
    def _get_lems_model_with_neuroml2_types(cls):

        from pyneuroml.pynml import get_path_to_jnml_jar
        from pyneuroml.pynml import read_lems_file
        from lems.parser.LEMS import LEMSFileParser
        import zipfile

        lems_model = lems.Model(include_includes=False)
        parser = LEMSFileParser(lems_model)

        jar_path = get_path_to_jnml_jar()
        # print_comment_v("Loading standard NeuroML2 dimension/unit definitions from %s"%jar_path)
        jar = zipfile.ZipFile(jar_path, "r")
        new_lems = jar.read("NeuroML2CoreTypes/NeuroMLCoreDimensions.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/NeuroMLCoreCompTypes.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/Cells.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/Networks.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/Simulation.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/Synapses.xml")
        parser.parse(new_lems)
        new_lems = jar.read("NeuroML2CoreTypes/PyNN.xml")
        parser.parse(new_lems)

        return lems_model

    # TODO: move to pyneuroml!
    @classmethod
    def _load_lems_file_with_neuroml2_types(cls, lems_filename):

        from pyneuroml.pynml import read_lems_file

        lems_model = cls._get_lems_model_with_neuroml2_types()

        model = read_lems_file(
            lems_filename,
            include_includes=False,
            fail_on_missing_includes=True,
            debug=True,
        )

        for cid, c in model.components.items():
            lems_model.components[cid] = c
        for ctid, ct in model.component_types.items():
            lems_model.component_types[ctid] = ct

        return lems_model

    def handle_location(self, id, population_id, component, x, y, z):
        pass

    def finalise_population(self, population_id):

        pass

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

        # self.print_connection_information(projName, id, prePop, postPop, synapseType, preCellId, postCellId, weight)
        print_v(
            ">>>>>> Src cell: %d, seg: %f, fract: %f -> Tgt cell %d, seg: %f, fract: %f; weight %s, delay: %s ms"
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

        pre_node_id = "%s_%i" % (prePop, preCellId)
        post_node_id = "%s_%i" % (postPop, postCellId)
        edge_id = "Edge %s to %s" % (pre_node_id, post_node_id)
        edge = {}
        edge["name"] = edge_id
        # edge['type'] = {}
        # edge['type']['NeuroML'] = synapseType
        # edge['parameters'] = {}
        # edge['functions'] = {}
        edge["sender_port"] = "OUTPUT"
        edge["receiver_port"] = "INPUT"
        edge["sender"] = pre_node_id
        edge["receiver"] = post_node_id
        edge["weight"] = weight

        """edge['type'] =  {
                        "PNL": "MappingProjection",
                        "generic": None
                    }"""

        self.mdf_graph["edges"][edge_id] = edge

    #
    #  Should be overridden to create input source array
    #
    def handle_input_list(
        self, inputListId, population_id, component, size, input_comp_obj=None
    ):

        pass

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(
        self, inputListId, id, cellId, segId=0, fract=0.5, weight=1
    ):

        print_v(
            "Input: %s[%s], cellId: %i, seg: %i, fract: %f, weight: %f"
            % (inputListId, id, cellId, segId, fract, weight)
        )

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input : %s completed" % inputName)


if __name__ == "__main__":

    lems_model = MDFHandler._load_lems_file_with_neuroml2_types(
        "../../git/MDFTests/NeuroML/LEMS_SimABCD.xml"
    )

    print(
        "Loaded LEMS with\n > Dims: %s\n\n > CompTypes: %s\n\n > Comps: %s"
        % (
            lems_model.dimensions.keys(),
            lems_model.component_types.keys(),
            lems_model.components.keys(),
        )
    )
