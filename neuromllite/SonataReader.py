
import tables   # pytables for HDF5 support
import os
import sys
import random

from neuroml.hdf5.NetworkContainer import *
from neuromllite.BaseTypes import NetworkReader
from neuromllite.utils import print_v, load_json
from pyneuroml.lems import generate_lems_file_for_neuroml

import pprint
pp = pprint.PrettyPrinter(depth=6)

DUMMY_CELL = 'dummy_cell'
DEFAULT_NEST_SPIKE_SYN = 'DEFAULT_NEST_SPIKE_SYN'

REPORT_FILE = 'report.txt'

def _get_default_nest_syn(nml_doc):
    
    if nml_doc.get_by_id(DEFAULT_NEST_SPIKE_SYN):
        return nml_doc.get_by_id(DEFAULT_NEST_SPIKE_SYN)
    
    from neuroml import AlphaCurrSynapse
    nest_syn = AlphaCurrSynapse(id=DEFAULT_NEST_SPIKE_SYN, tau_syn="2")
    nml_doc.alpha_curr_synapses.append(nest_syn)
    return nest_syn

def _parse_entry(w):
    """
    Check whether it's an int, float or string & return with that type
    """
    try:
        return int(w)
    except:
        try:
            return float(w)
        except:
            return w


def load_csv_props(info_file):
    """
    Load a generic csv file as used in Sonata
    """
    info = {}
    columns = {}
    for line in open(info_file):
        w = line.split()
        if len(columns)==0:
            for i in range(len(w)):
                columns[i] = _parse_entry(w[i])
        else:
            info[int(w[0])] = {}
            for i in range(len(w)):
                if i!=0:
                    info[int(w[0])][columns[i]] = _parse_entry(w[i])
    return info
    
    
def _matches_node_set_props(type_info, node_set_props):
    """
        Check whether the node_set properties match the given model type definition
    """
    matches = None
    for key in node_set_props:
        ns_val = node_set_props[key]
        if key in type_info:
            if ns_val==type_info[key]:
                if matches:
                    matches = matches and True
                else:
                    matches = True
            else:
                matches = False
    return matches
                    
    
class SonataReader(NetworkReader):        
    """
        Main class for reading a Sonata model. For typical usage, see main method below
    """
    
    component_objects = {} # Store cell ids vs objects, e.g. NeuroML2 based object
    
    nml_includes = ['PyNN.xml']
    
    def __init__(self, **parameters):
                     
        print_v("Creating SonataReader with %s..."%parameters)
        self.parameters = parameters
        
        self.current_sonata_pop = None
        self.current_node_group = None
        self.cell_info = {}
        self.node_set_mappings = {}
        
        self.pop_comp_info = {}
        self.syn_comp_info = {}
        self.input_comp_info = {}
        self.nml_pop_vs_comps = {}
        self.nml_pops_having_locations = []
        self.nml_ids_vs_gids = {}
        
        self.init_substitutes = {}
        self.substitutes = {}
        
        self.current_edge = None
        
        self.pre_pop = None
        self.post_pop = None
        
        self.myrandom = random.Random(12345)
        

    def subs(self, path):
        """
            Search the strings in a config file for a substitutable value, e.g. 
            "morphologies_dir": "$COMPONENT_DIR/morphologies",
        """
        #print_v('Checking for: \n  %s, \n  %s \n  in %s'%(self.substitutes,self.init_substitutes,path))
        if type(path) == int or type(path) == float:
            return path
        for s in self.init_substitutes:
            if path.startswith(s):
                path = path.replace(s,self.init_substitutes[s], 1)
        #print_v('  So far: %s'%path)
        for s in self.substitutes:
            if s in path:
                path = path.replace(s,self.substitutes[s])
        #print_v('  Returning: %s'%path)
        return path


    def parse(self, handler):
        """
        Main method to parse the Sonata files and call the appropriate methods
        in the handler
        """

        ########################################################################
        #  load the main configuration scripts    
    
        main_config_filename = os.path.abspath(self.parameters['filename'])
        
        config = load_json(main_config_filename)
        
        self.init_substitutes = {'.':'%s/'%os.path.dirname(main_config_filename),
                                 '../':'%s/'%os.path.dirname(os.path.dirname(main_config_filename))}
        
        self.substitutes = {'${configdir}':'%s'%os.path.dirname(main_config_filename)}
        
        if 'network' in config:
            self.network_config = load_json(self.subs(config['network']))
        else:
            self.network_config = config
            
        if 'simulation' in config:
            self.simulation_config = load_json(self.subs(config['simulation']))
        else:
            self.simulation_config = None
            
        for m in self.network_config['manifest']:
            path = self.subs(self.network_config['manifest'][m])
            self.substitutes[m] = path
        
        if 'id' in self.parameters:
            id = self.parameters['id']
        else:
            id = 'SonataNetwork'
            
        if id[0].isdigit():  # id like 9_cells is not a valid id for NeuroML
            id='NML2_%s'%id
        
        ########################################################################
        #  Feed the handler the info on the network   
        
        self.handler = handler
    
        notes = "Network read in from Sonata: %s"%main_config_filename
        handler.handle_document_start(id, notes)
        
        handler.handle_network(id, notes)
        
        self.node_types = {}
        
        ########################################################################
        #  Get info from nodes files    
        
        for n in self.network_config['networks']['nodes']:
            nodes_file = self.subs(n['nodes_file'])
            node_types_file = self.subs(n['node_types_file'])
            
            print_v("\nLoading nodes from %s and %s"%(nodes_file,node_types_file))

            h5file=tables.open_file(nodes_file,mode='r')

            print_v("Opened HDF5 file: %s"%(h5file.filename))
            self.parse_group(h5file.root.nodes)
            h5file.close()
            self.node_types[self.current_sonata_pop] = load_csv_props(node_types_file)
            self.current_sonata_pop = None
            
        
        
        ########################################################################
        #  Get info from edges files    
        
        self.edges_info = {}
        self.conn_info = {}
        
        if 'edges' in self.network_config['networks']:
            for e in self.network_config['networks']['edges']:
                edges_file = self.subs(e['edges_file'])
                edge_types_file = self.subs(e['edge_types_file'])

                print_v("\nLoading edges from %s and %s"%(edges_file,edge_types_file))

                h5file=tables.open_file(edges_file,mode='r')

                print_v("Opened HDF5 file: %s"%(h5file.filename))
                self.parse_group(h5file.root.edges)
                h5file.close()
                self.edges_info[self.current_edge] = load_csv_props(edge_types_file)
                self.current_edge = None
            
            
        ########################################################################
        #  Use extracted node/cell info to create populations
            
        for sonata_pop in self.cell_info:
            types_vs_pops = {}
            
            for type in self.cell_info[sonata_pop]['type_count']:
                node_type_info = self.node_types[sonata_pop][type]
                
                model_name_type = node_type_info['model_name'] if 'model_name' in node_type_info \
                                  else (node_type_info['pop_name'] if 'pop_name' in node_type_info else node_type_info['model_type'])
                
                model_type = node_type_info['model_type']
                model_template = node_type_info['model_template'] if 'model_template' in node_type_info else '- None -'
                
                nml_pop_id = '%s_%s_%s'%(sonata_pop,model_name_type,type) 
                    
                print_v(" - Adding population: %s which has model info: %s"%(nml_pop_id, node_type_info))
                
                size = self.cell_info[sonata_pop]['type_count'][type]
                
                if model_type=='point_process' and model_template=='nrn:IntFire1':
                    raise Exception('Point process model not currently supported: %s\nTry expressing the I&F cell in NEST format with nest:iaf_psc_alpha'%model_template)
                    pop_comp = 'cell_%s'%nml_pop_id #model_template.replace(':','_')
                    self.pop_comp_info[pop_comp] = {}
                    self.pop_comp_info[pop_comp]['model_type'] = model_type
                    
                    dynamics_params_file = self.subs(self.network_config['components']['point_neuron_models_dir']) +'/'+node_type_info['dynamics_params']
                    self.pop_comp_info[pop_comp]['dynamics_params'] = load_json(dynamics_params_file)
                    
                elif model_type=='point_process' and model_template=='nest:iaf_psc_alpha':
                    pop_comp = 'cell_%s'%nml_pop_id # = model_template.replace(':','_')
                    self.pop_comp_info[pop_comp] = {}
                    self.pop_comp_info[pop_comp]['model_type'] = model_type
                    self.pop_comp_info[pop_comp]['model_template'] = model_template
                    
                    dynamics_params_file = self.subs(self.network_config['components']['point_neuron_models_dir']) +'/'+node_type_info['dynamics_params']
                    self.pop_comp_info[pop_comp]['dynamics_params'] = load_json(dynamics_params_file)
                else:
                    pop_comp = DUMMY_CELL
                    self.pop_comp_info[pop_comp] = {}
                    self.pop_comp_info[pop_comp]['model_type'] = pop_comp
                    
                self.nml_pop_vs_comps[nml_pop_id] = pop_comp
                    
                properties = {}

                properties['type_id']=type
                properties['sonata_population']=sonata_pop
                properties['region']=sonata_pop
                
                for i in node_type_info:
                    properties[i]=node_type_info[i]
                    if i=='ei':
                        properties['type']=node_type_info[i].upper()
                        
                color = '%s %s %s'%(self.myrandom.random(),self.myrandom.random(),self.myrandom.random())
                
                try:
                    import opencortex.utils.color as occ
                    interneuron = 'SOM' in nml_pop_id or 'PV' in nml_pop_id
                    if 'L23' in nml_pop_id:
                        color = occ.L23_INTERNEURON if interneuron else occ.L23_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L23'))
                    if 'L4' in nml_pop_id:
                        color = occ.L4_INTERNEURON if interneuron else occ.L4_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L4'))
                    if 'L5' in nml_pop_id:
                        color = occ.L5_INTERNEURON if interneuron else occ.L5_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L5'))
                    if 'L6' in nml_pop_id:
                        color = occ.L6_INTERNEURON if interneuron else occ.L6_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L6'))
                except:
                    pass # Don't specify a particular color, use random, not a problem...
                    
                properties['color']=color
                if True or not 'locations' in self.cell_info[sonata_pop]['0']:
                    
                    properties={}  #############  temp for LEMS...
                    
                if model_type != 'virtual':
                
                    self.handler.handle_population(nml_pop_id, 
                                             pop_comp, 
                                             size,
                                             component_obj=None,
                                             properties=properties)
                                         
                types_vs_pops[type] = nml_pop_id
            self.cell_info[sonata_pop]['pop_count'] = {}  
            self.cell_info[sonata_pop]['pop_map'] = {}   
            
            for i in self.cell_info[sonata_pop]['types']:
                
                pop = types_vs_pops[self.cell_info[sonata_pop]['types'][i]]
                
                if not pop in self.cell_info[sonata_pop]['pop_count']:
                    self.cell_info[sonata_pop]['pop_count'][pop] = 0
                    
                index = self.cell_info[sonata_pop]['pop_count'][pop]
                self.cell_info[sonata_pop]['pop_map'][i] = (pop, index)
                
                if not pop in self.nml_ids_vs_gids:
                    self.nml_ids_vs_gids[pop] = {}
                self.nml_ids_vs_gids[pop][index] = (sonata_pop, i)
                
                if i in self.cell_info[sonata_pop]['0']['locations']: 
                    if not pop in self.nml_pops_having_locations: 
                        self.nml_pops_having_locations.append(pop)
                    pos = self.cell_info[sonata_pop]['0']['locations'][i]
                    #print('Adding pos %i: %s'%(i,pos))
                    self.handler.handle_location(index, 
                                                 pop, 
                                                 pop_comp, 
                                                 pos['x'] if 'x' in pos and pos['x'] is not None else 0, 
                                                 pos['y'] if 'y' in pos and pos['y'] is not None else 0, 
                                                 pos['z'] if 'z' in pos and pos['z'] is not None else 0)
                
                self.cell_info[sonata_pop]['pop_count'][pop]+=1
                
                
        ########################################################################
        #  Load simulation info into self.simulation_config
        
        if self.simulation_config:
            
            if self.simulation_config:
                for m in self.simulation_config['manifest']:
                    path = self.subs(self.simulation_config['manifest'][m])
                    self.substitutes[m] = path
                    
            for s1 in ['output']:
                for k in self.simulation_config[s1]:
                    self.simulation_config[s1][k] = self.subs(self.simulation_config[s1][k])
                    
            for s1 in ['inputs']:
                for s2 in self.simulation_config[s1]:
                    for k in self.simulation_config[s1][s2]:
                        self.simulation_config[s1][s2][k] = self.subs(self.simulation_config[s1][s2][k])
                        
            if 'node_sets_file' in self.simulation_config:
                node_sets = load_json(self.subs(self.simulation_config['node_sets_file']))
                self.simulation_config['node_sets'] = node_sets 
                
            if not 'node_sets' in self.simulation_config:
                self.simulation_config['node_sets'] = {}
                
            for sonata_pop in self.cell_info:
                self.node_set_mappings[sonata_pop] = {}
                for sindex in self.cell_info[sonata_pop]['pop_map']:
                    nml_pop = self.cell_info[sonata_pop]['pop_map'][sindex][0]
                    nml_index = self.cell_info[sonata_pop]['pop_map'][sindex][1]

                    # Add all in this sonata_pop to a 'node_set' named after the sonata_pop
                    if not nml_pop in self.node_set_mappings[sonata_pop]:
                        self.node_set_mappings[sonata_pop][nml_pop] = []
                    self.node_set_mappings[sonata_pop][nml_pop].append(nml_index)
                
            #pp.pprint(self.simulation_config)
            #pp.pprint(self.pop_comp_info)
                
            for node_set in self.simulation_config['node_sets']:
                self.node_set_mappings[node_set] = {}
                node_set_props = self.simulation_config['node_sets'][node_set]
                #print_v('===========Checking which cells in pops match node_set: %s = %s'%(node_set,node_set_props))
                
                for sonata_pop in self.cell_info:
                    for sindex in self.cell_info[sonata_pop]['pop_map']:
                        #print('Does %s %s match %s?'%(sonata_pop, sindex, node_set_props))
                        
                        type = self.cell_info[sonata_pop]['types'][sindex]
                        type_info = self.node_types[sonata_pop][type]
                        nml_pop = self.cell_info[sonata_pop]['pop_map'][sindex][0]
                        nml_index = self.cell_info[sonata_pop]['pop_map'][sindex][1]
                        
                        if 'population' in node_set_props and node_set_props['population'] == sonata_pop:
                            if 'node_id' in node_set_props and sindex in node_set_props['node_id']:
                                if not nml_pop in self.node_set_mappings[node_set]:
                                    self.node_set_mappings[node_set][nml_pop] = []
                                self.node_set_mappings[node_set][nml_pop].append(nml_index)
                                
                        matches = _matches_node_set_props(type_info, node_set_props)
                        #print_v('Node %i in %s (NML: %s[%i]) has type %s (%s); matches: %s'%(sindex, sonata_pop, nml_pop, nml_index, type, type_info, matches))
                        if matches:
                            if not nml_pop in self.node_set_mappings[node_set]:
                                self.node_set_mappings[node_set][nml_pop] = []
                            self.node_set_mappings[node_set][nml_pop].append(nml_index)
            
            ##pp.pprint(self.node_set_mappings)
            
    
        ########################################################################
        #  Extract info from inputs in simulation_config
        #pp.pprint(self.simulation_config)
        
        for input in self.simulation_config['inputs']:
            info = self.simulation_config['inputs'][input]
            #print_v(" - Adding input: %s which has info: %s"%(input, info)) 
            
            self.input_comp_info[input] = {}
            self.input_comp_info[input][info['input_type']] = {}
            
            node_set = info['node_set']
            
            if info['input_type'] == 'current_clamp':
                
                comp = 'PG_%s'%input
                self.input_comp_info[input][info['input_type']][comp] = {'amp':info['amp'],'delay':info['delay'],'duration':info['duration']}
                
                for nml_pop_id in self.node_set_mappings[node_set]:
                    
                    input_list_id = 'il_%s_%s'%(input,nml_pop_id)
                    indices = self.node_set_mappings[node_set][nml_pop_id]
                    
                    self.handler.handle_input_list(input_list_id, 
                                                   nml_pop_id, 
                                                   comp, 
                                                   len(indices))
                    count = 0
                    for index in indices:
                        self.handler.handle_single_input(input_list_id, 
                                                         count, 
                                                         cellId = index, 
                                                         segId = 0, 
                                                         fract = 0.5)
                        count+=1
                    
                
            elif info['input_type'] == 'spikes':
                node_info = self.cell_info[node_set]
                
                from pyneuroml.plot.PlotSpikes import read_sonata_spikes_hdf5_file
                from pyneuroml.plot.PlotSpikes import POP_NAME_SPIKEFILE_WITH_GIDS

                ids_times = read_sonata_spikes_hdf5_file(self.subs(info['input_file']))
                for id in ids_times[POP_NAME_SPIKEFILE_WITH_GIDS]:
                    times = ids_times[POP_NAME_SPIKEFILE_WITH_GIDS][id]
                    if id in node_info['pop_map']:
                        nml_pop_id, cell_id = node_info['pop_map'][id] 
                        print_v("Cell %i in Sonata node set %s (cell %s in nml pop %s) has %i spikes"%(id, node_set, nml_pop_id, cell_id, len(times)))

                        component = '%s__%i'%(nml_pop_id,cell_id)

                        self.input_comp_info[input][info['input_type']][component] ={'id': cell_id, 'times': times}

                        '''
                        input_list_id = 'il_%s_%i'%(input,cell_id)
                        self.handler.handle_input_list(input_list_id, 
                                                       nml_pop_id, 
                                                       component, 
                                                       1)

                        self.handler.handle_single_input(input_list_id, 
                                                          0, 
                                                          cellId = cell_id, 
                                                          segId = 0, 
                                                          fract = 0.5)
                                                         '''
                    else:
                        print_v("Cell %i in Sonata node set %s NOT FOUND!"%(id, node_set))
                
            else:
                raise Exception("Sonata input type not yet supported: %s"%(info['input_type']))


        ########################################################################
        #  Use extracted edge info to create connections
        
        projections_created = []
        for conn in self.conn_info:
            
            pre_node = self.conn_info[conn]['pre_node']
            post_node = self.conn_info[conn]['post_node']
            
            for i in range(len(self.conn_info[conn]['pre_id'])):
                pre_id = self.conn_info[conn]['pre_id'][i]
                post_id = self.conn_info[conn]['post_id'][i]
                nsyns = self.conn_info[conn]['nsyns'][i] if 'nsyns' in self.conn_info[conn] else 1
                type = self.conn_info[conn]['edge_type_id'][i]
                #print_v('   Conn with %i syns, type %s: %s(%s) -> %s(%s)'%(nsyns,type,pre_node,pre_id,post_node,post_id))
                pre_pop,pre_i = self.cell_info[pre_node]['pop_map'][pre_id]
                post_pop,post_i = self.cell_info[post_node]['pop_map'][post_id]
                #print_v('   Mapped: Conn %s(%s) -> %s(%s)'%(pre_pop,pre_i,post_pop,post_i))
                # print self.edges_info[conn][type]
                #print self.cell_info[pre_node]
                #print 11
                #print self.node_types[pre_node]
                #print 22
                cell_type_pre = self.cell_info[pre_node]['types'][pre_id]
                #print cell_type_pre
                #print 444
                pop_type_pre = self.node_types[pre_node][cell_type_pre]['model_type']
                #print pop_type_pre
                #print 333
                
                synapse = self.edges_info[conn][type]['dynamics_params'].split('.')[0]
                self.syn_comp_info[synapse] = {}
                #print self.edges_info[conn][type]
                #pp.pprint(self.init_substitutes)
                #pp.pprint(self.substitutes)
                dynamics_params_file = self.subs(self.network_config['components']['synaptic_models_dir']) +'/'+self.edges_info[conn][type]['dynamics_params']
                #print_v('Adding syn %s (at %s)'%(self.edges_info[conn][type]['dynamics_params'], dynamics_params_file))
                
                #TODO: don't load this file every connection!!!
                self.syn_comp_info[synapse]['dynamics_params'] = load_json(dynamics_params_file)
                proj_id = '%s_%s_%s'%(pre_pop,post_pop,synapse)
                
                sign = self.syn_comp_info[synapse]['dynamics_params']['sign'] if 'sign' in self.syn_comp_info[synapse]['dynamics_params'] else 1
                weight = self.edges_info[conn][type]['syn_weight'] if 'syn_weight' in self.edges_info[conn][type] else 1.0
                
                syn_weight_edge_group_0 = self.conn_info[conn]['syn_weight_edge_group_0'][i] if 'syn_weight_edge_group_0' in self.conn_info[conn] else None
                
                # Assume this overrides value from csv file...
                if syn_weight_edge_group_0:
                    weight = syn_weight_edge_group_0
                
                #print_v('Adding syn %s (at %s), weight: %s, sign: %s, nsyns: %s'%(self.edges_info[conn][type]['dynamics_params'], dynamics_params_file, weight, sign, nsyns))
                
                weight_scale = 0.001
                if 'level_of_detail' in self.syn_comp_info[synapse]['dynamics_params']:
                    weight_scale = 1
                
                
                weight=weight_scale * sign * weight * nsyns
                
                delay = self.edges_info[conn][type]['delay'] if 'delay' in self.edges_info[conn][type] else 0
                
                if not pop_type_pre == 'virtual':
                    if not proj_id in projections_created:

                        self.handler.handle_projection(proj_id, 
                                             pre_pop, 
                                             post_pop, 
                                             synapse)

                        projections_created.append(proj_id)

                    self.handler.handle_connection(proj_id, 
                                                 i, 
                                                 pre_pop, 
                                                 post_pop, 
                                                 synapse, \
                                                 pre_i, \
                                                 post_i, \
                                                 weight=weight, \
                                                 delay=delay)
                                                 
                else:
                    component = '%s__%i'%(pre_pop,pre_i)
                    #print_v('   ---  Connecting %s to %s[%s]'%(component, post_pop, post_i))
                    
                    
                    #self.input_comp_info[input][info['input_type']][component] ={'id': cell_id, 'times': times}


                    input_list_id = 'il_%s_%s_%i_%i'%(component,post_pop,post_i,i)
                    
                    self.handler.handle_input_list(input_list_id, 
                                                   post_pop, 
                                                   component, 
                                                   1)

                    self.handler.handle_single_input(input_list_id, 
                                                      0, 
                                                      cellId = post_i, 
                                                      segId = 0, 
                                                      fract = 0.5,
                                                      weight=weight)
                        
        """
        print('~~~~~~~~~~~~~~~')
        print('node_types:')
        pp.pprint(self.node_types)
        print('~~~~~~~~~~~~~~~')
        print('cell_info:')
        pp.pprint(self.cell_info)
        print('================')"""

    def parse_group(self, g):
        #print("+++++++++++++++Parsing group: "+ str(g)+", name: "+g._v_name)

        for node in g:
            #print("   ------Sub node: %s, class: %s, name: %s (parent: %s)"   % (node,node._c_classid,node._v_name, g._v_name))

            if node._c_classid == 'GROUP':
                if g._v_name=='nodes':
                    son_pop_id = node._v_name.replace('-','_')
                    self.current_sonata_pop = son_pop_id
                    self.cell_info[self.current_sonata_pop] = {}
                    self.cell_info[self.current_sonata_pop]['types'] = {}
                    self.cell_info[self.current_sonata_pop]['type_count'] = {}
                    
                if g._v_name==self.current_sonata_pop:
                    node_group = node._v_name
                    self.current_node_group = node_group
                    self.cell_info[self.current_sonata_pop][self.current_node_group] = {}
                    self.cell_info[self.current_sonata_pop][self.current_node_group]['locations'] = {}
                    
                if g._v_name=='edges':
                    edge_id = node._v_name.replace('-','_')
                    # print('  Found edge: %s'%edge_id)
                    self.current_edge = edge_id
                    self.conn_info[self.current_edge] = {}
                
                if g._v_name==self.current_edge:
                    
                    self.current_pre_node = g._v_name.split('_to_')[0]
                    self.current_post_node = g._v_name.split('_to_')[1]
                    # print('  Found edge %s -> %s'%(self.current_pre_node, self.current_post_node))
                    self.conn_info[self.current_edge]['pre_node'] = self.current_pre_node
                    self.conn_info[self.current_edge]['post_node'] = self.current_post_node
                    
                self.parse_group(node)

            if self._is_dataset(node):
                self.parse_dataset(node)
                
        self.current_node_group = None
        

    def _is_dataset(self, node):
          return node._c_classid == 'ARRAY' or node._c_classid == 'CARRAY'   


    def parse_dataset(self, d):
        #print_v("Parsing dataset/array: %s; at node: %s, node_group %s"%(str(d), self.current_sonata_pop, self.current_node_group))
                
        if self.current_node_group:  # e.g. parent group is 0 with child datasets x,y,z
            for i in range(0, d.shape[0]):                
                if not i in self.cell_info[self.current_sonata_pop][self.current_node_group]['locations']:
                    self.cell_info[self.current_sonata_pop][self.current_node_group]['locations'][i] = {}
                self.cell_info[self.current_sonata_pop][self.current_node_group]['locations'][i][d.name] = d[i]
                
        elif self.current_sonata_pop: # e.g. parent group is cortex with child datasets node_id etc.
            
            if d.name=='node_group_id':
                for i in range(0, d.shape[0]):
                    if not d[i]==0:
                        raise Exception("Error: currently only support node_group_id==0!")
            if d.name=='node_id':
                for i in range(0, d.shape[0]):
                    if not d[i]==i:
                        raise Exception("Error: currently only support dataset node_id when index is same as node_id (fails in %s)...!"%d)
            if d.name=='node_type_id':
                for i in range(0, d.shape[0]):
                    self.cell_info[self.current_sonata_pop]['types'][i] = d[i]
                    if not d[i] in self.cell_info[self.current_sonata_pop]['type_count']:
                        self.cell_info[self.current_sonata_pop]['type_count'][d[i]]=0
                    self.cell_info[self.current_sonata_pop]['type_count'][d[i]]+=1
           
        elif d.name=='source_node_id':
            self.conn_info[self.current_edge]['pre_id'] = [i for i in d]
        elif d.name=='edge_type_id':
            self.conn_info[self.current_edge]['edge_type_id'] = [int(i) for i in d]
        elif d.name=='target_node_id':
            self.conn_info[self.current_edge]['post_id'] = [i for i in d]
        elif d.name=='nsyns':
            self.conn_info[self.current_edge]['nsyns'] = [i for i in d]
        elif d.name=='edge_group_id':
            for i in range(0, d.shape[0]):
                if not d[i]==0:
                    raise Exception("Error: currently only support edge_group_id==0!")
        elif d.name=='syn_weight':
            # Has to be edge_group_id==0, as above check would fail...
            self.conn_info[self.current_edge]['syn_weight_edge_group_0'] = [i for i in d]
        else:
            print_v("Unhandled dataset: %s"%d.name)
        
        
    def add_neuroml_components(self, nml_doc):
        """
            Based on cell & synapse properties found, create the corresponding NeuroML components
        """
        
        is_nest = False
        print_v("Adding NeuroML cells to: %s"%nml_doc.id)
        #pp.pprint(self.pop_comp_info)
        
        for c in self.pop_comp_info:
            info = self.pop_comp_info[c]
            
            model_template = info['model_template'] if 'model_template' in info else \
                             (info['dynamics_params']['type'] if 'dynamics_params' in info else
                             info['model_type'])
            
            print_v(" - Adding %s: %s"%(model_template, info))
            
            if info['model_type'] == 'point_process' and model_template == 'nest:iaf_psc_alpha':
                
                is_nest = True
                from neuroml import IF_curr_alpha
                pynn0 = IF_curr_alpha(id=c, 
                                      cm=info['dynamics_params']['C_m']/1000.0, 
                                      i_offset="0", 
                                      tau_m=info['dynamics_params']['tau_m'], 
                                      tau_refrac=info['dynamics_params']['t_ref'], 
                                      tau_syn_E="1", 
                                      tau_syn_I="1", 
                                      v_init='-70', 
                                      v_reset=info['dynamics_params']['V_reset'], 
                                      v_rest=info['dynamics_params']['E_L'], 
                                      v_thresh=info['dynamics_params']['V_th'])
                                      
                nml_doc.IF_curr_alpha.append(pynn0)
                
            elif info['model_type'] == 'point_process' and model_template == 'NEURON_IntFire1':
                
                contents = '''<Lems>
    <intFire1Cell id="%s" thresh="1mV" reset="0mV" tau="%sms" refract="%sms"/>
</Lems>'''%(c, info['dynamics_params']['tau']*1000, info['dynamics_params']['refrac']*1000)

                cell_file_name = '%s.xml'%c
                cell_file = open(cell_file_name,'w')
                cell_file.write(contents)
                cell_file.close()
                
                self.nml_includes.append(cell_file_name)
                self.nml_includes.append('../../../examples/sonatatest/IntFireCells.xml')
                
                
            else:
                
                from neuroml import IafRefCell
                IafRefCell0 = IafRefCell(id=DUMMY_CELL,
                           C=".2 nF",
                           thresh = "1mV",
                           reset="0mV",
                           refract="3ms",
                           leak_conductance="1.2 nS",
                           leak_reversal="0mV")

                print_v("   - Adding: %s"%IafRefCell0)
                nml_doc.iaf_ref_cells.append(IafRefCell0)
                
        print_v("Adding NeuroML synapses to: %s"%nml_doc.id)
        
        #pp.pprint(self.syn_comp_info)
        
        for s in self.syn_comp_info:
            dyn_params = self.syn_comp_info[s]['dynamics_params']
            
            print_v("     -  Syn: %s: %s"%(s, dyn_params))
            
            if 'level_of_detail' in dyn_params and dyn_params['level_of_detail'] == 'exp2syn':
                from neuroml import ExpTwoSynapse

                syn = ExpTwoSynapse(id=s, 
                                    gbase="1nS",
                                    erev="%smV"%dyn_params['erev'],
                                    tau_rise="%sms"%dyn_params['tau1'],
                                    tau_decay="%sms"%dyn_params['tau2'])
                                    
                #print("Adding syn: %s"%syn)
                nml_doc.exp_two_synapses.append(syn)
                
            elif 'level_of_detail' in dyn_params and dyn_params['level_of_detail'] == 'instanteneous':
                
                contents = '''<Lems>
    <impulseSynapse id="%s"/>
</Lems>'''%(s)

                syn_file_name = '%s.xml'%s
                syn_file = open(syn_file_name,'w')
                syn_file.write(contents)
                syn_file.close()
                
                self.nml_includes.append(syn_file_name)
                #self.nml_includes.append('../examples/sonatatest/IntFireCells.xml')
                
            else:
                from neuroml import AlphaCurrSynapse
                pynnSynn0 = AlphaCurrSynapse(id=s, tau_syn="2")
                #print("Adding syn: %s"%pynnSynn0)
                nml_doc.alpha_curr_synapses.append(pynnSynn0)
            
                
        print_v("Adding NeuroML inputs to: %s"%nml_doc.id)
                
        #pp.pprint(self.input_comp_info)
        
        for input in self.input_comp_info:
            for input_type in self.input_comp_info[input]:
                if input_type == 'spikes':
                    for comp_id in self.input_comp_info[input][input_type]:
                        info = self.input_comp_info[input][input_type][comp_id]
                        print_v("Adding input %s: %s"%(comp_id, info.keys()))
                        
                        nest_syn = _get_default_nest_syn(nml_doc)
                        from neuroml import TimedSynapticInput, Spike

                        tsi = TimedSynapticInput(id=comp_id, synapse=nest_syn.id, spike_target="./%s"%nest_syn.id)
                        nml_doc.timed_synaptic_inputs.append(tsi)
                        for ti in range(len(info['times'])):
                            tsi.spikes.append(Spike(id=ti, time='%sms'%info['times'][ti]))
                elif input_type == 'current_clamp':
                    from neuroml import PulseGenerator
                    for comp_id in self.input_comp_info[input][input_type]:
                        info = self.input_comp_info[input][input_type][comp_id]
                        #TODO remove when https://github.com/AllenInstitute/sonata/issues/42 is fixed!
                        amp_template = '%spA' if is_nest else '%snA' # 
                        pg = PulseGenerator(id=comp_id,delay='%sms'%info['delay'],duration='%sms'%info['duration'],amplitude=amp_template%info['amp'])
                        nml_doc.pulse_generators.append(pg)
    
    
    def generate_lems_file(self, nml_file_name, nml_doc):
        """
            Generate a LEMS file to use in simulations of the NeuroML file
        """
        
        #pp.pprint(self.simulation_config)
        #pp.pprint(self.pop_comp_info)
        #pp.pprint(self.node_set_mappings)
        
        if 'output' in self.simulation_config:
            gen_spike_saves_for_all_somas = True
        
        target = nml_doc.networks[0].id
        sim_id = 'Sim_%s'%target
        
        duration = self.simulation_config['run']['tstop']
        dt = self.simulation_config['run']['dt']
        lems_file_name = 'LEMS_%s.xml'%sim_id
        target_dir = "./"
        gen_saves_for_quantities = {}
        gen_plots_for_quantities = {}
        
        if 'reports' in self.simulation_config:
            if 'membrane_potential' in self.simulation_config['reports']:
                mp = self.simulation_config['reports']['membrane_potential']
                node_set = self.node_set_mappings[mp['cells']]
                for nml_pop in node_set:
                    comp = self.nml_pop_vs_comps[nml_pop]
                    ids = node_set[nml_pop]
                    display = 'Voltages_%s'%nml_pop
                    file_name = '%s.v.dat'%nml_pop
                    
                    for id in ids:
                        quantity = '%s/%i/%s/%s'%(nml_pop,id,comp,'v')
                        if not nml_pop in self.nml_pops_having_locations:
                            quantity = '%s[%i]/%s'%(nml_pop,id,'v')
                            
                        if not display in gen_plots_for_quantities:
                            gen_plots_for_quantities[display] = []
                        gen_plots_for_quantities[display].append(quantity)
                        if not file_name in gen_saves_for_quantities:
                            gen_saves_for_quantities[file_name] = []
                        gen_saves_for_quantities[file_name].append(quantity)
                

        generate_lems_file_for_neuroml(sim_id, 
                                       nml_file_name, 
                                       target, 
                                       duration, 
                                       dt, 
                                       lems_file_name,
                                       target_dir,
                                       include_extra_files = self.nml_includes,
                                       gen_plots_for_all_v = False,
                                       plot_all_segments = False,
                                       gen_plots_for_quantities = gen_plots_for_quantities,   #  Dict with displays vs lists of quantity paths
                                       gen_saves_for_all_v = False,
                                       save_all_segments = False,
                                       gen_saves_for_quantities = gen_saves_for_quantities,  #  List of populations, all pops if = []
                                       gen_spike_saves_for_all_somas = gen_spike_saves_for_all_somas,
                                       report_file_name = REPORT_FILE,
                                       copy_neuroml = True,
                                       verbose=True)
                                       
        return lems_file_name
                                       
                                     
def get_neuroml_from_sonata(sonata_filename, id, generate_lems = True, format='xml'):
    """
    Return a NeuroMLDocument with (most of) the contents of the Sonata model 
    """
    
    from neuroml.hdf5.NetworkBuilder import NetworkBuilder
    neuroml_handler = NetworkBuilder()
    
    sr = SonataReader(filename=sonata_filename, id=id)
                      
    sr.parse(neuroml_handler)  
    
    nml_doc = neuroml_handler.get_nml_doc()
    
    sr.add_neuroml_components(nml_doc)
    
    if format == 'xml':
        nml_file_name = '%s.net.nml'%id
        from neuroml.writers import NeuroMLWriter
        NeuroMLWriter.write(nml_doc, nml_file_name)
        
    elif format == 'hdf5':
        nml_file_name = '%s.net.nml.h5'%id
        from neuroml.writers import NeuroMLHdf5Writer
        NeuroMLHdf5Writer.write(nml_doc, nml_file_name)
    
    print_v('Written to: %s'%nml_file_name)  
    
    if generate_lems:
        lems_file_name = sr.generate_lems_file(nml_file_name, nml_doc)
        
        return sr, lems_file_name, nml_file_name, nml_doc
    
    return nml_doc


def process_args():
    """ 
    Parse command-line arguments.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Read Sonata format configuration file and execute using jNeuroML export formats")
    
    parser.add_argument('network_reference', 
                        type=str, 
                        metavar='<network reference>', 
                        help='Reference/id for network (to be used for NeuroML files)')
                        
    parser.add_argument('sonata_config_file', 
                        type=str, 
                        metavar='<sonata config file>', 
                        help='Sonata configuration file')
                        
    parser.add_argument('-h5', 
                        action='store_true',
                        default=False,
                        help='Save NeuroML as HDF5, as opposed to XML')
                        
    parser.add_argument('-jnml', 
                        action='store_true',
                        default=False,
                        help='Execute the generated LEMS/NeuroML2 model with jNeuroML')
                        
    parser.add_argument('-neuron', 
                        action='store_true',
                        default=False,
                        help='Execute the generated LEMS/NeuroML2 model with jNeuroML_NEURON')
                        
    return parser.parse_args()

def _get_nml_pop_id(quantity):
    
    if '[' in quantity:
        nml_pop = quantity.split('[')[0]
        nml_index = int(quantity.split('[')[1].split(']')[0])
        return nml_pop, nml_index
    
    else:
        nml_pop = quantity.split('/')[0]
        nml_index = int(quantity.split('/')[1])
        return nml_pop, nml_index
    
def run(args):
    
    print_v("Reading Sonata file: %s and generating network: %s"%(args.sonata_config_file,args.network_reference))
    
    sr, lems_file_name, nml_file_name, nml_doc = get_neuroml_from_sonata(args.sonata_config_file, 
                                      args.network_reference, 
                                      generate_lems=True,
                                      format = ('hdf5' if args.h5 else 'xml'))
                        
    #pp.pprint(sr.cell_info)
    #pp.pprint(sr.nml_ids_vs_gids)
    
    print_v("Generated NeuroML 2 network: %s"%(nml_file_name))
    print_v("Generated LEMS file to run network: %s"%(lems_file_name))
    
    if args.jnml or args.neuron:

        traces = None
        events = None

        if args.jnml:

            from pyneuroml import pynml

            traces, events = pynml.run_lems_with_jneuroml(lems_file_name, 
                                                nogui=True, 
                                                verbose=True,
                                                load_saved_data=True,
                                                reload_events=True)
        if args.neuron:

            from pyneuroml import pynml

            traces, events = pynml.run_lems_with_jneuroml_neuron(lems_file_name, 
                                                nogui=True, 
                                                verbose=True,
                                                load_saved_data=True,
                                                reload_events=True)

        if traces:
            trace_file = sr.simulation_config['output']["output_dir"] + '/membrane_potential.h5'
            print_v('Resaving data to %s'%trace_file)
            import tables   # pytables for HDF5 support
            h5file=tables.open_file(trace_file,mode='w')
            report_grp = h5file.create_group("/", 'report')

            node_info = {}

            t = traces['t']
            time_start = t[0]*1000.
            time_stop = t[-1]*1000.
            time_dt = (t[1]-t[0])*1000.
            time = [time_start, time_stop, time_dt]

            nml_q_vs_node_id = {}

            for nml_q in traces.keys():

                if nml_q!='t':
                    nml_pop, nml_index = _get_nml_pop_id(nml_q)
                    (sonata_node, sonata_node_id)  = sr.nml_ids_vs_gids[nml_pop][nml_index]
                    nml_q_vs_node_id[nml_q] = sonata_node_id

            ordered = sorted(nml_q_vs_node_id, key=nml_q_vs_node_id.get)

            for nml_q in ordered:

                if nml_q!='t':
                    v = traces[nml_q]
                    nml_pop, nml_index = _get_nml_pop_id(nml_q)
                    (sonata_node, sonata_node_id)  = sr.nml_ids_vs_gids[nml_pop][nml_index]

                    if not sonata_node in node_info:
                        node_info[sonata_node] = {}
                        node_info[sonata_node]['data'] = []
                        node_info[sonata_node]['gids'] = []

                    node_info[sonata_node]['data'].append([vv*1000. for vv in v])
                    node_info[sonata_node]['gids'].append(sonata_node_id)

            for sonata_node in node_info:

                node_grp = h5file.create_group(report_grp, sonata_node)
                mapping_grp = h5file.create_group(node_grp, 'mapping')

                #node_grp = h5file.root
                #mapping_grp = h5file.create_group(report_grp, 'mapping')
                gids = node_info[sonata_node]['gids']
                h5file.create_array(mapping_grp, 'gids', gids)
                h5file.create_array(mapping_grp, 'node_ids', gids)
                h5file.create_array(mapping_grp, 'index_pointer', [i for i in range(len(gids)+1)])
                h5file.create_array(mapping_grp, 'element_ids', [0 for g in gids])
                h5file.create_array(mapping_grp, 'element_pos', [0.5 for g in gids])
                h5file.create_array(mapping_grp, 'time', time)

                d = h5file.create_array(node_grp, 'data', np.array(node_info[sonata_node]['data']).T)
                d.attrs.units = 'mV'
                d.attrs.variable_name = 'V_m'

            h5file.close()

        if events:
            event_file = sr.simulation_config['output']["output_dir"] + '/' + sr.simulation_config['output']["spikes_file"]
            print_v('Resaving data to %s'%event_file)
            import tables   # pytables for HDF5 support
            h5file=tables.open_file(event_file,mode='w')
            spike_grp = h5file.create_group("/", 'spikes')
            gids = []
            spiketimes = []
            for nml_q in events:
                nml_pop, nml_index = _get_nml_pop_id(nml_q)
                (sonata_node, sonata_node_id)  = sr.nml_ids_vs_gids[nml_pop][nml_index]
                for t in events[nml_q]:
                    gids.append(sonata_node_id)
                    spiketimes.append(t*1000.0)

            h5file.create_array(spike_grp, 'gids', gids)
            h5file.create_array(spike_grp, 'timestamps', spiketimes)

            h5file.close()

        if sr.simulation_config['output']["log_file"]:
            log_file = sr.simulation_config['output']["output_dir"] + '/' + sr.simulation_config['output']["log_file"]
            from shutil import copyfile 
            copyfile(REPORT_FILE, log_file)


def main(args=None):
    
    if '-test' in sys.argv:
        id = '9_cells'
        id = '300_cells'
        #id = '5_cells_iclamp'

        id = '300_intfire'
        id = 'small_intfire'
        id = 'small_iclamp'
        ## https://github.com/pgleeson/sonata/tree/intfire
        filename = '../../git/sonatapg/examples/%s/config.json'%id

        id = 'ten_cells_spikes2'

        id = 'ten_cells_spikes_nrn'
        id = 'one_cell_iclamp_nest'
        id = 'ten_cells_iclamp_nest'
        id = 'ten_cells_spikes_nest'
        filename = '/home/padraig/git/sonatapg/examples/sim_tests/intfire/%s/input/config.json'%id
        #id = '300_pointneurons'
        #filename = '/home/padraig/git/sonatapg/examples/%s/config.json'%id

        nml_doc = get_neuroml_from_sonata(filename, id, generate_lems=True)
        '''
        nml_file_name = '%s.net.nml'%id
        nml_file_name += '.h5'

        from neuroml.writers import NeuroMLHdf5Writer
        NeuroMLHdf5Writer.write(nml_doc,nml_file_name)
        print('Written to: %s'%nml_file_name) '''
    else:

        if args is None:
            args = process_args()
        run(args=args)
        
if __name__ == "__main__":
    main()
    
 
    