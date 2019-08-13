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

class SonataHandler(DefaultNetworkHandler):
        
    positions = {}
    pop_indices = {}
    
    DEFAULT_NODE_GROUP_ID = 0
    pop_type_ids = {}
    node_type_csv_info = {}
    
    input_info = {}
        

    def __init__(self):
        print_v("Initiating Sonata handler")


    def handle_document_start(self, id, notes):
            
        print_v("Parsing for Sonata export: %s"%id)
        
        self.config_file_info = {}
        self.config_file_info["network"]="./circuit_config.json"
        self.config_file_info["simulation"]="./simulation_config.json"
        
        self.circuit_file_info = {}
        self.circuit_file_info["manifest"]={}
        self.circuit_file_info["manifest"]['$NETWORK_DIR']='./network'
        if not os.path.exists(self.circuit_file_info["manifest"]['$NETWORK_DIR']):
            os.mkdir(self.circuit_file_info["manifest"]['$NETWORK_DIR'])
            
        self.circuit_file_info["manifest"]['$COMPONENT_DIR']='./components'
        if not os.path.exists(self.circuit_file_info["manifest"]['$COMPONENT_DIR']):
            os.mkdir(self.circuit_file_info["manifest"]['$COMPONENT_DIR'])
        
        self.circuit_file_info["components"]={}
        self.circuit_file_info["components"]['synaptic_models_dir']='$COMPONENT_DIR/synaptic_models'
        
        if not os.path.exists('./components/synaptic_models'):
            os.mkdir('./components/synaptic_models')
            
        self.circuit_file_info["components"]['point_neuron_models_dir']='$COMPONENT_DIR/point_neuron_models_dir'
        if not os.path.exists('./components/point_neuron_models_dir'):
            os.mkdir('./components/point_neuron_models_dir')
        
        self.circuit_file_info["networks"]={}
        self.circuit_file_info["networks"]["nodes"]=[]
        self.circuit_file_info["networks"]["nodes"].append({})
        
        
    def finalise_document(self):
                
        print_v("Writing file...: %s"%id)
        self.sonata_nodes.close()
        
        node_type_filename = "%s_node_types.csv"%self.network_id
        
        self.circuit_file_info["networks"]["nodes"][0]["node_types_file"] = "$NETWORK_DIR/%s"%node_type_filename
        
        node_type_file = open(os.path.join(self.circuit_file_info["manifest"]['$NETWORK_DIR'],node_type_filename), "w")
        header = ''
        for var in self.node_type_csv_info[self.node_type_csv_info.keys()[0]]:
            header+='%s '%var
        node_type_file.write(header+'\n') 
        
        for pop_id in self.node_type_csv_info:
            line = ''
            for var in self.node_type_csv_info[pop_id]:
                line+='%s '%self.node_type_csv_info[pop_id][var]
            node_type_file.write(line+'\n') 
                
        node_type_file.close()
        
        
        save_to_json_file(self.config_file_info, 'config.json', indent=2)
        save_to_json_file(self.circuit_file_info, 'circuit_config.json', indent=2)
        
        
        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
        self.network_id = network_id
        
        if temperature:
            print_v("  Temperature: "+temperature)
        if notes:
            print_v("  Notes: "+notes)
            
        nodes_filename = "%s_nodes.sonata.h5"%network_id
        self.circuit_file_info["networks"]["nodes"][0]["nodes_file"] = "$NETWORK_DIR/%s"%nodes_filename
            
        self.sonata_nodes = h5py.File(os.path.join(self.circuit_file_info["manifest"]['$NETWORK_DIR'],nodes_filename), "w")
        self.sonata_nodes.attrs.create('version',[0,1], dtype=np.uint32)
        self.sonata_nodes.attrs.create('magic', np.uint32(0x0A7A))
        

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
        
        self.sonata_nodes.create_group("nodes/%s"%population_id)
        self.sonata_nodes.create_group("nodes/%s/0"%population_id)
        
        node_type_id = 100+len(self.pop_type_ids)
        self.pop_type_ids[population_id] = node_type_id
        
        self.node_type_csv_info[population_id] = {}
        self.node_type_csv_info[population_id]['node_type_id'] = node_type_id
        self.node_type_csv_info[population_id]['pop_name'] = population_id
        self.node_type_csv_info[population_id]['model_name'] = component
        ##self.node_type_csv_info[population_id]['location'] = '???'
        self.node_type_csv_info[population_id]['model_template'] = 'nest:iaf_psc_alpha'
        self.node_type_csv_info[population_id]['model_type'] = 'point_process'
        self.node_type_csv_info[population_id]['dynamics_params'] = '%s.json'%component
        
 
    def handle_location(self, id, population_id, component, x, y, z):
        
        if not population_id in self.positions:
            self.positions[population_id] = np.array([[x,y,z]])
            self.pop_indices[population_id] = np.array([id])
        else:
            self.positions[population_id] = np.concatenate((self.positions[population_id], [[x,y,z]]))
            self.pop_indices[population_id] = np.concatenate((self.pop_indices[population_id], [id]))
        
        
    def finalise_population(self, population_id):
        
        self.sonata_nodes.create_dataset("nodes/%s/0/positions"%population_id, data=self.positions[population_id])
        self.sonata_nodes.create_dataset("nodes/%s/node_group_index"%population_id, data=self.pop_indices[population_id])
        self.sonata_nodes.create_dataset("nodes/%s/node_group_id"%population_id, data=[self.DEFAULT_NODE_GROUP_ID for i in self.pop_indices[population_id]])
        self.sonata_nodes.create_dataset("nodes/%s/node_id"%population_id, data=self.pop_indices[population_id])
        
        self.sonata_nodes.create_dataset("nodes/%s/node_type_id"%population_id, data=[self.pop_type_ids[population_id] for i in self.pop_indices[population_id]])


        
    #
    #  Should be overridden to create input source array
    #  
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):
        
        self.print_input_information(inputListId, population_id, component, size)
        
        if size<0:
            self.log.error("Error! Need a size attribute in sites element to create spike source!")
            return
             
        self.input_info[inputListId] = (population_id, component, [])
        
    #
    #  Should be overridden to to connect each input to the target cell
    #  
    def handle_single_input(self, inputListId, id, cellId, segId = 0, fract = 0.5, weight=1):
        
        print_v("Input: %s[%s], cellId: %i, seg: %i, fract: %f, weight: %f" % (inputListId,id,cellId,segId,fract,weight))
        
        self.input_info[inputListId][2].append(cellId)
        
        

        
    #
    #  Should be overridden to to connect each input to the target cell
    #  
    def finalise_input_source(self, inputName):
        print_v("Input : %s completed" % inputName)
        

