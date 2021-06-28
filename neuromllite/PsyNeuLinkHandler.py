#
#
#   A class to write to the PsyNeuLink/MDF format...
#
#

from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
from neuromllite.utils import print_v
from neuromllite.utils import save_to_json_file
from neuromllite.utils import locate_file
from neuromllite.utils import evaluate
                
import lems.api as lems  # from pylems

class PsyNeuLinkHandler(DefaultNetworkHandler):
       
        
    bids_mdf_info = {}
    bids_mdf_info["graphs"] = []
    
    bids_mdf_info_hl = {}
    bids_mdf_info_hl["graphs"] = []
    

    def __init__(self, nl_network):
        print_v("Initiating PsyNeuLink handler")
        self.nl_network = nl_network


    def handle_document_start(self, id, notes):
            
        print_v("Parsing for PsyNeuLink export: %s"%id)
        self.id = id
        
        
    def finalise_document(self):
                
        print_v("Writing file for...: %s"%self.id)

        save_to_json_file(self.bids_mdf_info, '%s.bids-mdf.json'%self.id, indent=4)
        '''save_to_json_file(self.bids_mdf_info_hl, '%s.bids-mdf.highlevel.json'%self.id, indent=4)'''
        
        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
        self.network_id = network_id
        
        if temperature:
            print_v("  Temperature: "+temperature)
        if notes:
            print_v("  Notes: "+notes)
        
        self.bids_mdf_graph = {}
        self.bids_mdf_graph['name'] = network_id
        self.bids_mdf_graph['notes'] = notes
        self.bids_mdf_graph['controller'] = None
        self.bids_mdf_graph['nodes'] = {}
        self.bids_mdf_graph['edges'] = {}
        self.bids_mdf_graph['parameters'] = {}
        self.bids_mdf_graph['parameters']['PNL'] = {"required_node_roles": []}
        self.bids_mdf_info["graphs"].append(self.bids_mdf_graph)
        self.bids_mdf_graph["type"] = {"PNL": "Composition","generic": "graph"}
            
        
        self.bids_mdf_graph_hl = {}
        self.bids_mdf_graph_hl['name'] = network_id+"_hl"
        self.bids_mdf_graph_hl['notes'] = notes+" High Level (population/projection based) description"
        self.bids_mdf_graph_hl['nodes'] = {}
        self.bids_mdf_graph_hl['edges'] = {}
        self.bids_mdf_graph_hl['parameters'] = {}
        self.bids_mdf_info_hl["graphs"].append(self.bids_mdf_graph_hl)
        

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
                node['type'] = {}
                node['name'] = node_id
                #node['type']['NeuroML'] = component
                
                comp = self.nl_network.get_child(component, 'cells')
                base_dir = './' # for now...
                fname = locate_file(comp.lems_source_file, base_dir)
                model = lems.Model()
                model.import_from_file(fname)
                lems_comp = model.components.get(component)
                print('Cell: [%s] comes from %s and in Lems is: %s'%(comp,fname, lems_comp))
                comp_type = lems_comp.type
                
                type = "The type of %s"%comp_type
                function = "The function of %s"%comp_type
                
                if comp_type == 'pnlLinearFunctionTM':
                    function = 'Linear'
                    type = "TransferMechanism" 
                elif comp_type == 'inputNode':
                    function = 'Linear'
                    type = "TransferMechanism"
                elif comp_type == 'pnlLogisticFunctionTM':
                    function = 'Logistic'
                    type = "TransferMechanism"
                elif comp_type == 'pnlExponentialFunctionTM':
                    function = 'Exponential'
                    type = "TransferMechanism"
                elif comp_type == 'pnlSimpleIntegratorMechanism':
                    function = 'SimpleIntegrator'
                    type = "IntegratorMechanism"
                elif comp_type == 'fnCell':
                    function = 'FitzHughNagumoIntegrator'
                    type = "IntegratorMechanism"
                
                
                
                node['type']["PNL"] = type
                node['type']["generic"] = None
                node['parameters'] = {}
                node['parameters']['PNL'] = {}
                node['functions'] = []
                func_info = {}
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
                
                node['functions'].append(func_info)
                self.bids_mdf_graph['nodes'][node_id] = node

            pop_node_id = '%s'%(population_id)
            pop_node = {}
            pop_node['type'] = {}
            pop_node['name'] = pop_node_id
            pop_node['type']['NeuroML'] = component
            pop_node['parameters'] = {}
            pop_node['parameters']['size'] = size
            pop_node['functions'] = {}
            self.bids_mdf_graph_hl['nodes'][pop_node_id] = pop_node
        
 
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
        edge['type'] = {}
        edge['type']['NeuroML'] = synapseType
        edge['parameters'] = {}
        edge['functions'] = {}
        edge['sender_port'] = 'OutputPort'
        edge['receiver_port'] = 'InputPort'
        edge['sender'] = pre_node_id
        edge['receiver'] = post_node_id
        edge['weight'] = weight
        
        edge['type'] =  {
                        "PNL": "MappingProjection",
                        "generic": None
                    }
        
        self.bids_mdf_graph['edges'][edge_id] = edge
        
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
        

