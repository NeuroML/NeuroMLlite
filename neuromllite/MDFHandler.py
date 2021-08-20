#
#
#   A class to write to the MDF format (https://github.com/ModECI/MDF)...
#
#

from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
from neuromllite.utils import print_v
from neuromllite.utils import save_to_json_file
from neuromllite.utils import save_to_yaml_file
from neuromllite.utils import locate_file
from neuromllite.utils import evaluate
from pyneuroml.pynml import get_value_in_si

import lems.api as lems  # from pylems

class MDFHandler(DefaultNetworkHandler):


    def __init__(self, nl_network):
        print_v("Initiating PsyNeuLink handler")
        self.nl_network = nl_network


    def handle_document_start(self, id, notes):

        print_v("Parsing for PsyNeuLink export: %s"%id)
        self.id = id

        self.mdf_info = {}


        from modeci_mdf import MODECI_MDF_VERSION


        self.mdf_info[self.id] = {}
        self.mdf_info[self.id]['format'] = 'ModECI MDF v%s'%MODECI_MDF_VERSION
        self.mdf_info[self.id]["graphs"] = {}

        self.pnl_additions = False


    def finalise_document(self):

        print_v("Writing file for...: %s"%self.id)

        save_to_json_file(self.mdf_info, '%s.mdf.json'%self.id, indent=4)
        save_to_yaml_file(self.mdf_info, '%s.mdf.yaml'%self.id, indent=4)
        '''save_to_json_file(self.mdf_info_hl, '%s.bids-mdf.highlevel.json'%self.id, indent=4)'''



    def handle_network(self, network_id, notes, temperature=None):

        print_v("Network: %s"%network_id)
        self.network_id = network_id

        if temperature:
            print_v("  Temperature: "+temperature)
        if notes:
            print_v("  Notes: "+notes)

        self.mdf_graph = {}
        self.mdf_graph['notes'] = notes
        self.mdf_graph['nodes'] = {}
        self.mdf_graph['edges'] = {}
        #self.mdf_graph['parameters'] = {}

        '''
        if self.pnl_additions:
            self.mdf_graph['controller'] = None
            self.mdf_graph["type"] = {"PNL": "Composition","generic": "graph"}
            self.mdf_graph['parameters']['PNL'] = {"required_node_roles": []}'''

        self.mdf_info[self.id]["graphs"][network_id] = self.mdf_graph


        '''
        self.mdf_graph_hl = {}
        self.mdf_graph_hl['name'] = network_id+"_hl"
        self.mdf_graph_hl['notes'] = notes+" High Level (population/projection based) description"
        self.mdf_graph_hl['nodes'] = {}
        self.mdf_graph_hl['edges'] = {}
        self.mdf_graph_hl['parameters'] = {}
        self.mdf_info_hl["graphs"].append(self.mdf_graph_hl)'''

    def _convert_value(self, val):

        funcs = ['exp']
        for f in funcs:
            if '%s('%f in val:
                val = val.replace('%s('%f, 'math.%s('%f)

        val = evaluate(val) # catch if it's an int etc.
        return val


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

        if size>=0:
            for i in range(size):
                node_id = '%s_%i'%(population_id, i)
                node = {}
                #node['type'] = {}
                #node['name'] = node_id
                #node['type']['NeuroML'] = component

                comp = self.nl_network.get_child(component, 'cells')
                base_dir = './' # for now...

                node['parameters'] = {}
                node['input_ports'] = {}
                node['output_ports'] = {}
                if comp is not None and comp.lems_source_file:
                    fname = locate_file(comp.lems_source_file, base_dir)

                    model = MDFHandler._load_lems_file_with_neuroml2_types(fname)

                    #print('All comp types: %s'%model.component_types.keys())
                    #print('All comps: %s'%model.components.keys())
                    lems_comp = model.components.get(component)
                    comp_type_name = lems_comp.type
                    lems_comp_type = model.component_types.get(comp_type_name)
                    notes = 'Cell: [%s] is defined in %s and in Lems is: %s'%(comp, fname, lems_comp)

                    node['notes'] = notes

                    for p in lems_comp.parameters:
                        node['parameters'][p] = {'value': get_value_in_si(evaluate(lems_comp.parameters[p]))}

                    for c in lems_comp_type.constants:
                        node['parameters'][c.name] = {'value': get_value_in_si(c.value)}


                    for dv in lems_comp_type.dynamics.derived_variables:

                        if dv.name=='INPUT':
                            node['input_ports'][dv.name] = {}
                        else:
                            if dv.exposure:
                                #<DerivedVariable name="OUTPUT" dimension="none" exposure="OUTPUT" value="variable"/>
                                node['output_ports'][dv.exposure] = {'value':self._convert_value(dv.value)}


                    for sv in lems_comp_type.dynamics.state_variables:
                        node['parameters'][sv.name] = {}

                    print(dir(lems_comp_type.dynamics))

                    for os in lems_comp_type.dynamics.event_handlers:
                        if type(os)==lems.OnStart:
                            for a in os.actions:
                                if type(a)==lems.StateAssignment:
                                    node['parameters'][a.variable]['default_initial_value'] = a.value

                    for td in lems_comp_type.dynamics.time_derivatives:
                        node['parameters'][td.variable]['time_derivative'] = self._convert_value(td.value)




                if self.pnl_additions:
                    node['type']["PNL"] = type
                    node['type']["generic"] = None
                #node['parameters']['PNL'] = {}
                '''
                node['functions'] = []
                func_info = {}

                if self.pnl_additions:
                    func_info['type']={}
                    func_info['type']['generic']=function
                func_info['name']='Function_%s'%function
                func_info['args']={}
                for p in lems_comp.parameters:
                    func_info['args'][p] = {}
                    func_info['args'][p]['type'] = 'float'
                    func_info['args'][p]['source'] = '%s.input_ports.%s'%(node_id,p)

                    if comp.parameters is not None and p in comp.parameters:
                        func_info['args'][p]['value'] = evaluate(comp.parameters[p], self.nl_network.parameters)
                    else:
                        func_info['args'][p]['value'] = evaluate(lems_comp.parameters[p]) # evaluate to ensure strings -> ints/floats etc

                node['functions'].append(func_info)'''
                self.mdf_graph['nodes'][node_id] = node
            '''
            pop_node_id = '%s'%(population_id)
            pop_node = {}
            pop_node['type'] = {}
            pop_node['name'] = pop_node_id
            #pop_node['type']['NeuroML'] = component
            pop_node['parameters'] = {}
            pop_node['parameters']['size'] = size
            pop_node['functions'] = {}
            self.mdf_graph['nodes'][pop_node_id] = pop_node'''


    # TODO: move to pylems!
    @classmethod
    def _get_all_children_in_lems(cls, component_type, model, child_type):
        c = []
        if child_type=='exposure':
            for e in component_type.exposures: c.append(e)

        if component_type.extends:
            ect = model.component_types[component_type.extends]
            c.extend(cls._get_all_children_in_lems(ect, model, child_type))

        return c


    # TODO: move to pyneuroml!
    @classmethod
    def _load_lems_file_with_neuroml2_types(cls, lems_filename):

        from pyneuroml.pynml import get_path_to_jnml_jar
        from pyneuroml.pynml import read_lems_file
        from lems.parser.LEMS import LEMSFileParser
        import zipfile

        lems_model = lems.Model(include_includes=False)
        parser = LEMSFileParser(lems_model)

        jar_path = get_path_to_jnml_jar()
        # print_comment_v("Loading standard NeuroML2 dimension/unit definitions from %s"%jar_path)
        jar = zipfile.ZipFile(jar_path, 'r')
        new_lems = jar.read('NeuroML2CoreTypes/NeuroMLCoreDimensions.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/NeuroMLCoreCompTypes.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/Cells.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/Networks.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/Simulation.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/Synapses.xml')
        parser.parse(new_lems)
        new_lems = jar.read('NeuroML2CoreTypes/PyNN.xml')
        parser.parse(new_lems)

        model = read_lems_file(lems_filename,
                               include_includes=False,
                               fail_on_missing_includes=True,
                               debug=True)

        for cid, c in model.components.items(): lems_model.components[cid] = c
        for ctid, ct in model.component_types.items(): lems_model.component_types[ctid] = ct


        return lems_model

    def handle_location(self, id, population_id, component, x, y, z):
        pass


    def finalise_population(self, population_id):

        pass

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

        #self.print_connection_information(projName, id, prePop, postPop, synapseType, preCellId, postCellId, weight)
        print_v(">>>>>> Src cell: %d, seg: %f, fract: %f -> Tgt cell %d, seg: %f, fract: %f; weight %s, delay: %s ms" % (preCellId,preSegId,preFract,postCellId,postSegId,postFract, weight, delay))

        pre_node_id = '%s_%i'%(prePop, preCellId)
        post_node_id = '%s_%i'%(postPop, postCellId)
        edge_id = 'Edge %s to %s'%(pre_node_id,post_node_id)
        edge = {}
        edge['name'] = edge_id
        #edge['type'] = {}
        #edge['type']['NeuroML'] = synapseType
        #edge['parameters'] = {}
        #edge['functions'] = {}
        edge['sender_port'] = 'OUTPUT'
        edge['receiver_port'] = 'INPUT'
        edge['sender'] = pre_node_id
        edge['receiver'] = post_node_id
        edge['weight'] = weight

        '''edge['type'] =  {
                        "PNL": "MappingProjection",
                        "generic": None
                    }'''

        self.mdf_graph['edges'][edge_id] = edge

    #
    #  Should be overridden to create input source array
    #
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):

        pass

    #
    #  Should be overridden to to connect each input to the target cell
    #
    def handle_single_input(self, inputListId, id, cellId, segId = 0, fract = 0.5, weight=1):

        print_v("Input: %s[%s], cellId: %i, seg: %i, fract: %f, weight: %f" % (inputListId,id,cellId,segId,fract,weight))



    #
    #  Should be overridden to to connect each input to the target cell
    #
    def finalise_input_source(self, inputName):
        print_v("Input : %s completed" % inputName)


if __name__ == "__main__":

    lems_model = MDFHandler._load_lems_file_with_neuroml2_types('../../git/MDFTests/NeuroML/LEMS_SimABCD.xml')

    print('Loaded LEMS with\n > Dims: %s\n > CompTypes: %s\n > Comps: %s'%( \
                       lems_model.dimensions.keys(),
                       lems_model.component_types.keys(),
                       lems_model.components.keys()))
