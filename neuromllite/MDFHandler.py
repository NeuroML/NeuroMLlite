#
#
#   A class to write to the MDF format (https://github.com/ModECI/MDF)...
#
#

from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
from neuromllite.utils import print_v
from neuromllite.NetworkGenerator import _extract_pynn_components_to_neuroml

from modelspec.utils import save_to_json_file
from modelspec.utils import save_to_yaml_file
from modelspec.utils import locate_file
from modelspec.utils import evaluate
from pyneuroml.pynml import get_value_in_si

import lems.api as lems  # from pylems

import numpy

DEFAULT_CURRENT_INPUT_PORT = "synapses_i"
SPIKE_INPUT_PORT_ID = "spike_input"
WEIGHTED_SPIKE_INPUTS = "weighted_inputs"


class MDFHandler(DefaultNetworkHandler):
    def __init__(self, nl_network):
        print_v("Initiating MDF handler")
        self.nl_network = nl_network

        self.input_list_vs_comps = {}
        self.input_list_vs_pops = {}

        self.pop_ids_vs_size = {}

    def handle_document_start(self, id, notes):
        print_v("Parsing for MDF export: %s" % id)
        self.id = id

        self.mdf_info = {}

        # from modeci_mdf import MODECI_MDF_VERSION
        MODECI_MDF_VERSION = "0.4"

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

    def _get_input_port_name(self, name):
        if name == "in":
            return SPIKE_INPUT_PORT_ID
        else:
            return name

    def _convert_value(self, val):
        funcs = ["exp"]
        for f in funcs:
            if "%s(" % f in val:
                val = val.replace("%s(" % f, "numpy.%s(" % f)

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

        self.pop_ids_vs_size[population_id] = size

        info = (
            "Population: "
            + population_id
            + ", component: "
            + component
            + compInfo
            + sizeInfo
            + ", properties: %s" % properties
        )
        print_v("  = %s" % info)

        node_id = "%s" % (population_id)

        cell_comp = self.nl_network.get_child(component, "cells")

        if cell_comp is not None:
            node = self._comp_to_mdf_node(
                nmllite_comp=cell_comp,
                lems_comp_id=component,
                size=size,
                properties=properties,
            )

        self.mdf_graph["nodes"][node_id] = node

    def _comp_to_mdf_node(self, nmllite_comp, lems_comp_id, size=1, properties=None):
        base_dir = "./"  # for now...

        node = {}

        if properties:
            node["metadata"] = properties

        node["parameters"] = {}
        node["input_ports"] = {}
        node["output_ports"] = {}

        if nmllite_comp.lems_source_file:
            print_v("  It's a component defined in custom lems...")
            fname = locate_file(nmllite_comp.lems_source_file, base_dir)
            model = MDFHandler._load_lems_file_with_neuroml2_types(fname)
            lems_comp = model.components.get(lems_comp_id)

        elif (
            hasattr(nmllite_comp, "neuroml2_cell")
            and nmllite_comp.neuroml2_cell is not None
        ):
            print_v(
                "  It is a NeuroML2 cell (%s, %s)..."
                % (nmllite_comp.id, nmllite_comp.neuroml2_cell)
            )
            model = MDFHandler._get_lems_model_with_neuroml2_types()
            lems_comp = lems.Component(
                id_=nmllite_comp.id, type_=nmllite_comp.neuroml2_cell
            )
            if nmllite_comp.parameters is not None:
                for p in nmllite_comp.parameters:
                    lems_comp.set_parameter(
                        p,
                        evaluate(
                            nmllite_comp.parameters[p], self.nl_network.parameters
                        ),
                    )
        elif nmllite_comp.neuroml2_source_file is not None:
            print_v(
                "  It is a NeuroML2 cell (%s, %s)..."
                % (nmllite_comp.id, nmllite_comp.neuroml2_source_file)
            )
            model = MDFHandler._get_lems_model_with_neuroml2_types()
            lems_comp = lems.Component(
                id_=nmllite_comp.id, type_=nmllite_comp.neuroml2_cell
            )
            if nmllite_comp.parameters is not None:
                for p in nmllite_comp.parameters:
                    lems_comp.set_parameter(
                        p,
                        evaluate(
                            nmllite_comp.parameters[p], self.nl_network.parameters
                        ),
                    )

        elif hasattr(nmllite_comp, "pynn_cell"):
            print_v("  It's a PyNN cell...")

            nml2_doc_temp = _extract_pynn_components_to_neuroml(self.nl_network)

            model = MDFHandler._get_lems_model_with_neuroml2_types(nml2_doc_temp)

            lems_comp = model.components[nmllite_comp.id]

            for p in nmllite_comp.parameters:
                lems_comp.set_parameter(
                    p,
                    evaluate(nmllite_comp.parameters[p], self.nl_network.parameters),
                )

        elif hasattr(nmllite_comp, "pynn_synapse_type"):
            print_v("  It's a PyNN synapse...")

            nml2_doc_temp = _extract_pynn_components_to_neuroml(self.nl_network)

            model = MDFHandler._get_lems_model_with_neuroml2_types(nml2_doc_temp)

            lems_comp = model.components[nmllite_comp.id]

            for p in nmllite_comp.parameters:
                lems_comp.set_parameter(
                    p,
                    evaluate(nmllite_comp.parameters[p], self.nl_network.parameters),
                )

        elif (
            hasattr(nmllite_comp, "neuroml2_input")
            and nmllite_comp.neuroml2_input is not None
        ):
            print_v("  It's a NeuroML input...")
            model = MDFHandler._get_lems_model_with_neuroml2_types()
            lems_comp = lems.Component(
                id_=nmllite_comp.id, type_=nmllite_comp.neuroml2_input
            )
            for p in nmllite_comp.parameters:
                lems_comp.set_parameter(
                    p,
                    evaluate(nmllite_comp.parameters[p], self.nl_network.parameters),
                )

        elif hasattr(nmllite_comp, "pynn_input"):
            print_v(
                "  It's a PyNN input: %s - %s..."
                % (nmllite_comp.id, nmllite_comp.pynn_input)
            )

            nml2_doc_temp = _extract_pynn_components_to_neuroml(self.nl_network)

            model = MDFHandler._get_lems_model_with_neuroml2_types(nml2_doc_temp)

            lems_comp = model.components[nmllite_comp.id]
            """
            for p in nmllite_comp.parameters:
                lems_comp.set_parameter(
                    p,
                    evaluate(
                        nmllite_comp.parameters[p], self.nl_network.parameters
                    ),
                )"""

        else:
            raise Exception(
                "Can't determine the source of the component definition in: %s"
                % nmllite_comp
            )

        print_v(
            "All LEMS Components in known LEMS model: %s"
            % sorted(list(model.components.keys()))
        )
        print_v(
            "All LEMS ComponentTypes in known LEMS model: %s"
            % sorted(list(model.component_types.keys()))
        )
        print_v("This LEMS comp: %s" % lems_comp)
        comp_type_name = lems_comp.type
        lems_comp_type = model.component_types.get(comp_type_name)
        print_v("lems_comp_type: %s" % lems_comp_type)
        notes = "Cell: [%s] is defined in %s and in Lems is: %s" % (
            nmllite_comp,
            nmllite_comp.lems_source_file,
            lems_comp,
        )

        node["notes"] = notes

        for p in lems_comp.parameters:
            node["parameters"][p] = {
                "value": [get_value_in_si(evaluate(lems_comp.parameters[p]))] * size
            }

        properties = self._get_all_elements_in_lems(lems_comp_type, model, "properties")
        for prop in properties:
            node["parameters"][prop.name] = {
                "value": [get_value_in_si(evaluate(prop.default_value))] * size
            }

        # if lems_comp_types.is_or_extends()

        consts = self._get_all_elements_in_lems(lems_comp_type, model, "constant")
        for c in consts:
            node["parameters"][c.name] = {"value": [get_value_in_si(c.value)] * size}

        event_ports = self._get_all_elements_in_lems(
            lems_comp_type, model, "event_port"
        )
        for ep in event_ports:
            if ep.direction == "out":
                node["parameters"][ep.name] = {"value": [0] * size}
                node["output_ports"][ep.name] = {"value": ep.name}
            elif ep.direction == "in":
                ep_name = self._get_input_port_name(ep.name)
                node["input_ports"][ep_name] = {"shape": [size], "reduce": "add"}

        if hasattr(lems_comp_type, "dynamics"):
            for sv in lems_comp_type.dynamics.state_variables:
                node["parameters"][sv.name] = {}

            for reg in lems_comp_type.dynamics.regimes:
                node["parameters"]["ACTIVE_REGIME"] = {"value": [1] * size}
                node["parameters"]["INACTIVE_REGIME"] = {"value": [0] * size}

                reg_param = "REGIME_%s" % reg.name
                # node["parameters"][reg_param] = {"value": 'ACTIVE_REGIME' if reg.initial else 'INACTIVE_REGIME'}

                if not reg_param in node["parameters"]:
                    node["parameters"][reg_param] = {}
                node["parameters"][reg_param]["value"] = reg_param
                node["parameters"][reg_param]["default_initial_value"] = (
                    "ACTIVE_REGIME" if reg.initial else "INACTIVE_REGIME"
                )

                node["output_ports"][reg_param] = {"value": reg_param}

                for td in reg.time_derivatives:
                    node["parameters"][td.variable][
                        "time_derivative"
                    ] = self._convert_value("%s * (%s)" % (reg_param, td.value))

                for eh in reg.event_handlers:
                    print_v(
                        "Converting the event handler: %s (type: %s)" % (eh, type(eh))
                    )

                    if type(eh) == lems.OnCondition:
                        # TODO: remove when global t available
                        node["parameters"]["t"] = {
                            "default_initial_value": 0,
                            "time_derivative": "1",
                        }

                        test = "(%s == ACTIVE_REGIME) * (%s)" % (
                            reg_param,
                            self._replace_in_condition_test(eh.test),
                        )
                        # test = "%s == ACTIVE_REGIME" % (reg_param)
                        if not "conditions" in node["parameters"][reg_param]:
                            node["parameters"][reg_param]["conditions"] = {}

                        node["parameters"][reg_param]["conditions"][
                            "regime_exit_condition"
                        ] = {"test": test, "value": "INACTIVE_REGIME"}

                        for a in eh.actions:
                            if type(a) == lems.Transition:
                                reg_to_id = a.regime
                                print_v(
                                    "  Transition: %s -> %s" % (reg_param, reg_to_id)
                                )
                                reg_to_param = "REGIME_%s" % reg_to_id
                                if not reg_to_param in node["parameters"]:
                                    node["parameters"][reg_to_param] = {}
                                reg_to = lems_comp_type.dynamics.regimes[reg_to_id]
                                if not "conditions" in node["parameters"][reg_to_param]:
                                    node["parameters"][reg_to_param]["conditions"] = {}

                                node["parameters"][reg_to_param]["conditions"][
                                    "regime_entry_condition"
                                ] = {"test": test, "value": "ACTIVE_REGIME"}

                                for eh in reg_to.event_handlers:
                                    print_v(
                                        "Converting an event handler: %s (type: %s)"
                                        % (eh, type(eh))
                                    )

                                    if type(eh) == lems.OnEntry:
                                        for a in eh.actions:
                                            if type(a) == lems.StateAssignment:
                                                if (
                                                    not "conditions"
                                                    in node["parameters"][a.variable]
                                                ):
                                                    node["parameters"][a.variable][
                                                        "conditions"
                                                    ] = {}

                                                node["parameters"][a.variable][
                                                    "conditions"
                                                ]["entering_regime_%s" % reg_to_id] = {
                                                    "test": test,
                                                    "value": a.value,
                                                }

                            if type(a) == lems.EventOut:
                                del node["parameters"][a.port]["value"]
                                node["parameters"][a.port] = {
                                    "default_initial_value": [0] * size
                                }

                                if not "conditions" in node["parameters"][a.port]:
                                    node["parameters"][a.port]["conditions"] = {}

                                node["parameters"][a.port]["conditions"][
                                    "condition_%s_on" % a.port
                                ] = {"test": test, "value": 1}
                                node["parameters"][a.port]["conditions"][
                                    "condition_%s_off" % a.port
                                ] = {"test": "%s > 0" % a.port, "value": 0}

            for sv in lems_comp_type.dynamics.state_variables:
                # node["parameters"][sv.name]["value"] = [0]*size

                node["output_ports"][sv.name] = {"value": sv.name}
                print_v("Adding %s as an output port" % sv.name)
                if sv.exposure:
                    node["output_ports"][sv.exposure] = {"value": sv.name}

            for dv in lems_comp_type.dynamics.derived_variables:
                print_v(
                    "Converting derived variable: %s (exp: %s) = [%s] or [%s]"
                    % (dv.name, dv.exposure, dv.value, dv.select)
                )
                if dv.name == "INPUT":
                    node["input_ports"][dv.name] = {}
                else:
                    if dv.value is not None:
                        dv_name = dv.name
                        node["parameters"][dv_name] = {
                            "value": self._convert_value(dv.value)
                        }
                        if dv.exposure:
                            node["output_ports"][dv.exposure] = {"value": dv_name}
                    if dv.select is not None:
                        in_port = dv.select.replace("[*]/", "_").replace("/", "_")
                        node["input_ports"][in_port] = {}
                        """ "shape": [size],
                            "reduce": "add","""

                        node["parameters"][dv.name] = {"value": in_port}

            conditions = 0
            for eh in lems_comp_type.dynamics.event_handlers:
                print_v("Converting an event handler: %s (type: %s)" % (eh, type(eh)))

                if type(eh) == lems.OnEvent:
                    ep_name = self._get_input_port_name(eh.port)
                    for a in eh.actions:
                        if type(a) == lems.StateAssignment:
                            if not "conditions" in node["parameters"][a.variable]:
                                node["parameters"][a.variable]["conditions"] = {}

                            to_check = ep_name
                            if to_check == SPIKE_INPUT_PORT_ID:
                                to_check = WEIGHTED_SPIKE_INPUTS
                            node["parameters"][a.variable]["conditions"][
                                "condition_%s_on_eh" % ep_name
                            ] = {"test": "%s > 0" % to_check, "value": a.value}

                if type(eh) == lems.OnStart:
                    for a in eh.actions:
                        if type(a) == lems.StateAssignment:
                            node["parameters"][a.variable][
                                "default_initial_value"
                            ] = a.value
                        if "value" in node["parameters"][a.variable]:
                            node["parameters"][a.variable].pop("value")

                if type(eh) == lems.OnCondition:
                    test = self._replace_in_condition_test(eh.test)

                    for a in eh.actions:
                        if type(a) == lems.StateAssignment:
                            if not "conditions" in node["parameters"][a.variable]:
                                node["parameters"][a.variable]["conditions"] = {}

                            node["parameters"][a.variable]["conditions"][
                                "condition_%i" % conditions
                            ] = {"test": test, "value": a.value}

                        if type(a) == lems.EventOut:
                            del node["parameters"][a.port]["value"]
                            node["parameters"][a.port] = {
                                "default_initial_value": [0] * size
                            }

                            if not "conditions" in node["parameters"][a.port]:
                                node["parameters"][a.port]["conditions"] = {}

                            node["parameters"][a.port]["conditions"][
                                "condition_%i_on" % conditions
                            ] = {"test": test, "value": 1}
                            node["parameters"][a.port]["conditions"][
                                "condition_%i_off" % conditions
                            ] = {"test": "%s > 0" % a.port, "value": 0}

                    conditions += 1

            for td in lems_comp_type.dynamics.time_derivatives:
                node["parameters"][td.variable][
                    "time_derivative"
                ] = self._convert_value(td.value)

                if not "default_initial_value" in node["parameters"][td.variable]:
                    node["parameters"][td.variable]["default_initial_value"] = [
                        0
                    ] * size

        return node

    def _replace_in_condition_test(self, test):
        return (
            test.replace(".gt.", ">")
            .replace(".geq.", ">=")
            .replace(".lt.", "<")
            .replace(".leq.", "<=")
            .replace(".eq.", "==")
            .replace(".and.", "and")
        )

    # TODO: move to pylems!
    @classmethod
    def _get_all_elements_in_lems(cls, component_type, model, child_type):
        ee = []
        if child_type == "exposure":
            if hasattr(component_type, "exposures"):
                for e in component_type.exposures:
                    ee.append(e)
        elif child_type == "constant":
            if hasattr(component_type, "constants"):
                for c in component_type.constants:
                    ee.append(c)
        elif child_type == "event_port":
            if hasattr(component_type, "event_ports"):
                for e in component_type.event_ports:
                    ee.append(e)
        elif child_type == "properties":
            if hasattr(component_type, "properties"):
                for p in component_type.properties:
                    ee.append(p)
        else:
            raise Exception("Cannot get child of type: %s in LEMS model" % child_type)

        if hasattr(component_type, "extends") and component_type.extends:
            ect = model.component_types[component_type.extends]
            ee.extend(cls._get_all_elements_in_lems(ect, model, child_type))

        return ee

    # TODO: move to pyneuroml!
    @classmethod
    def _get_lems_model_with_neuroml2_types(cls, nml_doc=None):
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
        new_lems = jar.read("NeuroML2CoreTypes/Inputs.xml")
        parser.parse(new_lems)

        if nml_doc is not None:
            import io

            sf = io.StringIO()

            from neuroml.writers import NeuroMLWriter

            print(
                "Adding nml elements from this doc to new lems model: %s"
                % nml_doc.summary()
            )

            NeuroMLWriter.write(nml_doc, sf, close=False)
            sf.seek(0)
            parser.parse(sf.read())

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
            "  = Projection: "
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

        syn_node_id = "%s_%s" % (projName, synapse)
        syn_node = {}

        syn_comp = self.nl_network.get_child(synapse, "synapses")

        print("Converting syn %s; %s" % (synapse_obj, syn_comp))

        pre_pop_size = self.pop_ids_vs_size[prePop]
        post_pop_size = self.pop_ids_vs_size[postPop]

        syn_node = self._comp_to_mdf_node(
            nmllite_comp=syn_comp,
            lems_comp_id=synapse,
            size=post_pop_size,
            properties={},
        )
        if SPIKE_INPUT_PORT_ID in syn_node["input_ports"]:
            syn_node["input_ports"][SPIKE_INPUT_PORT_ID]["shape"] = [pre_pop_size]
            syn_node["parameters"][WEIGHTED_SPIKE_INPUTS] = {
                "value": numpy.zeros([pre_pop_size, post_pop_size]).tolist()
            }
            syn_node["parameters"]["weight"] = {}
            syn_node["parameters"]["weight"]["function"] = "MatMul"
            syn_node["parameters"]["weight"]["args"] = {
                "A": SPIKE_INPUT_PORT_ID,
                "B": WEIGHTED_SPIKE_INPUTS,
            }

        self.mdf_graph["nodes"][syn_node_id] = syn_node

        #### Edge pre_node -> syn

        pre_node_id = prePop
        pre_node = self.mdf_graph["nodes"][pre_node_id]

        pre_syn_edge_id = "%s_TO_%s" % (pre_node_id, syn_node_id)
        pre_syn_edge = {}
        pre_syn_edge["name"] = pre_syn_edge_id

        pre_ports = list(pre_node["output_ports"].keys())
        pre_syn_edge["sender_port"] = (
            "OUTPUT" if "OUTPUT" in pre_ports else pre_ports[0]
        )

        post_ports = list(syn_node["input_ports"].keys())
        pre_syn_edge["receiver_port"] = (
            "INPUT" if "INPUT" in post_ports else post_ports[0]
        )
        pre_syn_edge["sender"] = pre_node_id
        pre_syn_edge["receiver"] = syn_node_id

        self.mdf_graph["edges"][pre_syn_edge_id] = pre_syn_edge

        #### Edge syn -> post_node

        post_node_id = postPop
        post_node = self.mdf_graph["nodes"][post_node_id]

        syn_post_edge_id = "%s_TO_%s" % (syn_node_id, post_node_id)
        syn_post_edge = {}
        syn_post_edge["name"] = syn_post_edge_id

        syn_ports = list(syn_node["output_ports"].keys())

        syn_post_edge["sender_port"] = (
            "OUTPUT"
            if "OUTPUT" in syn_ports
            else ("i" if "i" in syn_ports else syn_ports[0])
        )

        post_ports = list(post_node["input_ports"].keys())
        syn_post_edge["receiver_port"] = (
            "INPUT"
            if "INPUT" in post_ports
            else ("synapses_i" if "synapses_i" in post_ports else post_ports[0])
        )
        syn_post_edge["sender"] = syn_node_id
        syn_post_edge["receiver"] = post_node_id

        self.mdf_graph["edges"][syn_post_edge_id] = syn_post_edge

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
            ">>>>>> Src pop: %s, cell: %d, seg: %f, fract: %f -> Tgt pop %s, cell %d, seg: %f, fract: %f; syn: %s, weight %s, delay: %s ms"
            % (
                prePop,
                preCellId,
                preSegId,
                preFract,
                postPop,
                postCellId,
                postSegId,
                postFract,
                synapseType,
                weight,
                delay,
            )
        )

        if preSegId != 0 or postSegId != 0:
            raise Exception(
                "MDF export does not support connections on anything other than segment id = 0"
            )

        syn_node_id = "%s_%s" % (projName, synapseType)
        node = self.mdf_graph["nodes"][syn_node_id]
        if WEIGHTED_SPIKE_INPUTS in node["parameters"]:
            # Weight used inside input
            node["parameters"][WEIGHTED_SPIKE_INPUTS]["value"][preCellId][
                postCellId
            ] = weight
            print(node["parameters"][WEIGHTED_SPIKE_INPUTS]["value"])

    def _get_input_list_node_id(self, inputListId):
        return "InputList_%s" % (inputListId)
        # return "%s" % (inputListId)

    #
    #  Should be overridden to create input source array
    #
    def handle_input_list(
        self, inputListId, population_id, component, size, input_comp_obj=None
    ):
        self.input_list_vs_comps[inputListId] = component
        self.input_list_vs_pops[inputListId] = population_id

        print_v(
            "InputList: %s, population_id: %s, component: %s, size: %i, input_comp_obj: %s"
            % (inputListId, population_id, component, size, input_comp_obj)
        )

        node_id = self._get_input_list_node_id(inputListId)

        comp = self.nl_network.get_child(component, "input_sources")

        node = self._comp_to_mdf_node(nmllite_comp=comp, lems_comp_id=component, size=1)

        # TODO: remove when global t available
        node["parameters"]["t"] = {"default_initial_value": 0, "time_derivative": "1"}

        pop_size = self.pop_ids_vs_size[population_id]
        node["parameters"]["weight"] = {"value": [0.0] * pop_size}

        self.mdf_graph["nodes"][node_id] = node

        pre_node_id = node_id
        post_node_id = "%s" % population_id
        edge_id = "Edge %s to %s" % (pre_node_id, post_node_id)
        edge = {}
        edge["name"] = edge_id
        edge["sender_port"] = "i"
        edge["receiver_port"] = DEFAULT_CURRENT_INPUT_PORT
        edge["sender"] = pre_node_id
        edge["receiver"] = post_node_id

        self.mdf_graph["edges"][edge_id] = edge

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(
        self, inputListId, id, cellId, segId=0, fract=0.5, weight=1
    ):
        if segId != 0:
            raise Exception(
                "MDF export does not support inputs on anything other than segment id = 0"
            )

        component = self.input_list_vs_comps[inputListId]
        print_v(
            "Input: %s[%s], cellId: %i, seg: %i, fract: %f, weight: %f, component: %s"
            % (inputListId, id, cellId, segId, fract, weight, component)
        )

        node = self.mdf_graph["nodes"][self._get_input_list_node_id(inputListId)]

        # Weight used inside input
        node["parameters"]["weight"]["value"][cellId] = weight

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input : %s completed" % inputName)


if __name__ == "__main__":
    lems_model = MDFHandler._load_lems_file_with_neuroml2_types(
        "../../git/MDF/examples/NeuroML/LEMS_SimIzhikevichTest.xml"
    )

    print(
        "Loaded LEMS with\n > Dims: %s\n\n > CompTypes: %s\n\n > Comps: %s"
        % (
            lems_model.dimensions.keys(),
            lems_model.component_types.keys(),
            lems_model.components.keys(),
        )
    )
