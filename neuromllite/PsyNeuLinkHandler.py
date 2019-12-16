#
#
#   A class to write to the Sonata format...
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

import h5py
import numpy as np
from neuromllite.utils import save_to_json_file
import os

class PsyNeuLinkHandler(DefaultNetworkHandler):
       
    '''
    positions = {}
    pop_indices = {}
    
    DEFAULT_NODE_GROUP_ID = 0
    pop_type_ids = {}
    node_type_csv_info = {}
    
    input_info = {}'''
        
    
    bids_mdf_info = {}
    bids_mdf_info["graphs"] = []
    

    def __init__(self):
        print_v("Initiating PsyNeuLink handler")


    def handle_document_start(self, id, notes):
            
        print_v("Parsing for PsyNeuLink export: %s"%id)
        self.id = id
        
        
    def finalise_document(self):
                
        print_v("Writing file for...: %s"%self.id)

        
        save_to_json_file(self.bids_mdf_info, '%s.bids-mdf.json'%self.id, indent=4)
        
        
        

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
        self.bids_mdf_graph['nodes'] = {}
        self.bids_mdf_graph['edges'] = {}
        self.bids_mdf_graph['parameters'] = {}
        self.bids_mdf_info["graphs"].append(self.bids_mdf_graph)
        

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
                node['type']['NeuroML'] = component
                node['parameters'] = {}
                node['functions'] = {}
                self.bids_mdf_graph['nodes'][node_id] = node
        
 
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
        

