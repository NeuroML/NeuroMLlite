
import tables   # pytables for HDF5 support
import os
import random

from neuroml.hdf5.NetworkContainer import *
from neuromllite.BaseTypes import NetworkReader

from neuromllite.utils import print_v, load_json

from pyneuroml.lems import generate_lems_file_for_neuroml

import pprint
pp = pprint.PrettyPrinter(depth=6)


def subs(path, substitutes):
    """
        Search the strings in a config file for a substitutable value, e.g. 
        "morphologies_dir": "$COMPONENT_DIR/morphologies",
    """
    #print_v('Checking for %s in %s'%(substitutes.keys(),path))
    if type(path) == int or type(path) == float:
        return path
    for s in substitutes:
        if s in path:
            path = path.replace(s,substitutes[s])
    return path


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
    
    
class SonataReader(NetworkReader):        
    """
        Main class for reading a Sonata model. For typical usage, see main method below
    """
    
    component_objects = {} # Store cell ids vs objects, e.g. NeuroML2 based object
    
    def __init__(self, **parameters):
                     
        print_v("Creating SonataReader with %s..."%parameters)
        self.parameters = parameters
        
        self.current_sonata_pop = None
        self.current_node_group = None
        self.cell_info = {}
        
        self.pop_comp_info = {}
        self.syn_comp_info = {}
        self.input_comp_info = {}
        
        self.current_edge = None
        
        self.pre_pop = None
        self.post_pop = None
        
        self.myrandom = random.Random(12345)
        

    def parse(self, handler):

        ########################################################################
        #  load the main configuration scripts    
    
        main_config_filename = os.path.abspath(self.parameters['filename'])
        
        config = load_json(main_config_filename)
        substitutes = {'./':'%s/'%os.path.dirname(main_config_filename),
                       '${configdir}':'%s'%os.path.dirname(main_config_filename),
                       '../':'%s/'%os.path.dirname(os.path.dirname(main_config_filename))}
        
        if 'network' in config:
            self.network_config = load_json(subs(config['network'],substitutes))
        else:
            self.network_config = config
            
        if 'simulation' in config:
            self.simulation_config = load_json(subs(config['simulation'],substitutes))
        else:
            self.simulation_config = None
            
        for m in self.network_config['manifest']:
            path = subs(self.network_config['manifest'][m],substitutes)
            substitutes[m] = path
        
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
            nodes_file = subs(n['nodes_file'],substitutes)
            node_types_file = subs(n['node_types_file'],substitutes)
            
            print_v("\nLoading nodes from %s and %s"%(nodes_file,node_types_file))

            h5file=tables.open_file(nodes_file,mode='r')

            print_v("Opened HDF5 file: %s"%(h5file.filename))
            self.parse_group(h5file.root.nodes)
            h5file.close()
            self.node_types[self.current_sonata_pop] = load_csv_props(node_types_file)
            print('~~~~~~~~~~~~~~~')
            print('node_types:')
            pp.pprint(self.node_types)
            print('~~~~~~~~~~~~~~~')
            print('cell_info:')
            pp.pprint(self.cell_info)
            print('================')
            self.current_sonata_pop = None
            
        
        
        ########################################################################
        #  Get info from edges files    
        
        self.edges_info = {}
        self.conn_info = {}
        
        if 'edges' in self.network_config['networks']:
            for e in self.network_config['networks']['edges']:
                edges_file = subs(e['edges_file'],substitutes)
                edge_types_file = subs(e['edge_types_file'],substitutes)

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
                    pop_comp = model_template.replace(':','_')
                    self.pop_comp_info[pop_comp] = {}
                    self.pop_comp_info[pop_comp]['model_type'] = model_type
                    
                    dynamics_params_file = subs(self.network_config['components']['point_neuron_models_dir'],substitutes) +'/'+node_type_info['dynamics_params']
                    self.pop_comp_info[pop_comp]['dynamics_params'] = load_json(dynamics_params_file)
                else:
                    pop_comp = 'hhcell'
                    
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
                if not 'locations' in self.cell_info[sonata_pop]['0']:
                    
                    properties={}  #############  temp for LEMS...
                
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
                
                if i in self.cell_info[sonata_pop]['0']['locations']:
                    pos = self.cell_info[sonata_pop]['0']['locations'][i]
                    self.handler.handle_location(index, 
                                                 pop, 
                                                 pop_comp, 
                                                 pos['x'] if 'x' in pos else 0, 
                                                 pos['y'] if 'y' in pos else 0, 
                                                 pos['z'] if 'z' in pos else 0)
                
                self.cell_info[sonata_pop]['pop_count'][pop]+=1
                
                
        ########################################################################
        #  Use extracted edge info to create connections
        
        projections_created = []
        for conn in self.conn_info:
            
            pre_node = self.conn_info[conn]['pre_node']
            post_node = self.conn_info[conn]['post_node']
            
            for i in range(len(self.conn_info[conn]['pre_id'])):
                pre_id = self.conn_info[conn]['pre_id'][i]
                post_id = self.conn_info[conn]['post_id'][i]
                type = self.conn_info[conn]['edge_type_id'][i]
                # print('   Conn (%s) %s(%s) -> %s(%s)'%(type,pre_node,pre_id,post_node,post_id))
                pre_pop,pre_i = self.cell_info[pre_node]['pop_map'][pre_id]
                post_pop,post_i = self.cell_info[post_node]['pop_map'][post_id]
                # print('   Mapped: Conn %s(%s) -> %s(%s)'%(pre_pop,pre_i,post_pop,post_i))
                # print self.edges_info[conn][type]
                
                synapse = self.edges_info[conn][type]['dynamics_params'].split('.')[0]
                self.syn_comp_info[synapse] = {}
                #print self.edges_info[conn][type]
                dynamics_params_file = subs(self.network_config['components']['synaptic_models_dir'],substitutes) +'/'+self.edges_info[conn][type]['dynamics_params']
                
                
                #TODO: don't load this file every connection!!!
                self.syn_comp_info[synapse]['dynamics_params'] = load_json(dynamics_params_file)
                proj_id = '%s_%s_%s'%(pre_pop,post_pop,synapse)
                
                sign = self.syn_comp_info[synapse]['dynamics_params']['sign'] if 'sign' in self.syn_comp_info[synapse]['dynamics_params'] else 1
                weight = self.edges_info[conn][type]['syn_weight'] if 'syn_weight' in self.edges_info[conn][type] else 1.0
                delay = self.edges_info[conn][type]['delay'] if 'delay' in self.edges_info[conn][type] else 0
                
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
                                             weight=sign * weight, \
                                             delay=delay)
                

        ########################################################################
        #  Load simulation info into self.simulation_config
        
        if self.simulation_config:
            
            if self.simulation_config:
                for m in self.simulation_config['manifest']:
                    path = subs(self.simulation_config['manifest'][m],substitutes)
                    substitutes[m] = path
                    
            for s1 in ['output']:
                for k in self.simulation_config[s1]:
                    self.simulation_config[s1][k] = subs(self.simulation_config[s1][k],substitutes)
                    
            for s1 in ['inputs']:
                for s2 in self.simulation_config[s1]:
                    for k in self.simulation_config[s1][s2]:
                        self.simulation_config[s1][s2][k] = subs(self.simulation_config[s1][s2][k],substitutes)
                        
            if 'node_sets_file' in self.simulation_config:
                node_sets = load_json('%s/%s'%(os.path.dirname(main_config_filename), subs(self.simulation_config['node_sets_file'],substitutes)))
                self.simulation_config['node_sets'] = node_sets
                    
    
        ########################################################################
        #  Extract info from inputs in simulation_config
        pp.pprint(self.simulation_config)
        
        for input in self.simulation_config['inputs']:
            info = self.simulation_config['inputs'][input]
            print_v(" - Adding input: %s which has info: %s"%(input, info)) 
            
            self.input_comp_info[input] = {}
            self.input_comp_info[input][info['input_type']] = {}
            
            node_set = info['node_set']
            
            if info['input_type'] == 'current_clamp':
                
                node_set_conds = self.simulation_config['node_sets'][node_set]
                pp.pprint(self.cell_info)
                node_info = self.cell_info[node_set_conds['model_type']]
                comp = 'PG_%s'%input
                
                self.input_comp_info[input][info['input_type']][comp] = {'amp':info['amp'],'delay':info['delay'],'duration':info['duration']}
                
                input_lists_added = {}
                
                for id in node_info['pop_map']:
                    nml_pop_id, cell_id = node_info['pop_map'][id] 
                    print_v("Cell %i in Sonata node set %s (cell %s in nml pop %s) has current clamp input %s"%(id, node_set, nml_pop_id, cell_id, '???'))
                    
                    input_list_id = 'il_%s_%s'%(input,nml_pop_id)
                    
                    if not input_list_id in input_lists_added:
                        self.handler.handle_input_list(input_list_id, 
                                                       nml_pop_id, 
                                                       comp, 
                                                       0)
                        input_lists_added[input_list_id] = 1
                    else:
                        input_lists_added[input_list_id] += 1
                    
                    self.handler.handle_single_input(input_list_id, 
                                                      input_lists_added[input_list_id]-1, 
                                                      cellId = cell_id, 
                                                      segId = 0, 
                                                      fract = 0.5)
                    
                
            elif info['input_type'] == 'spikes':
                node_info = self.cell_info[node_set]
                print node_info
                from pyneuroml.plot.PlotSpikes import read_sonata_spikes_hdf5_file

                ids_times = read_sonata_spikes_hdf5_file(subs(info['input_file'],substitutes))
                for id in ids_times:
                    times = ids_times[id]
                    nml_pop_id, cell_id = node_info['pop_map'][id] 
                    print_v("Cell %i in Sonata node set %s (cell %s in nml pop %s) has %i spikes"%(id, node_set, nml_pop_id, cell_id, len(times)))

                    component = '%s_timedInputs_%i'%(input,cell_id)

                    self.input_comp_info[input][info['input_type']][component] ={'id': cell_id, 'times': times}

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
            else:
                raise Exception("Sonata inout type not yet supported: %s"%(info['input_type']))



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
                        raise Exception("Error: only support node_group_id==0!")
            if d.name=='node_id':
                for i in range(0, d.shape[0]):
                    if not d[i]==i:
                        raise Exception("Error: only support dataset node_id when index is same as node_id (fails in %s)...!"%d)
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
              
        else:
            print_v("Unhandled dataset: %s"%d.name)
        
        
    def add_neuroml_components(self, nml_doc):
        """
            Based on cell & synapse properties found, create the corresponding NeuroML components
        """
        
        #pp.pprint(self.pop_comp_info)
        
        print_v("Adding NeuroML cells to: %s"%nml_doc.id)
        
        for c in self.pop_comp_info:
            info = self.pop_comp_info[c]
            if info['model_type'] == 'point_process':
                
                from neuroml import IF_curr_alpha
                
                pynn0 = IF_curr_alpha(id=c, 
                                      cm="1.0", 
                                      i_offset="0", 
                                      tau_m=info['dynamics_params']['tau']*1000, 
                                      tau_refrac=info['dynamics_params']['refrac']*1000, 
                                      tau_syn_E="0.5", 
                                      tau_syn_I="0.5", 
                                      v_init="-65", 
                                      v_reset="-62.0", 
                                      v_rest="-65.0", 
                                      v_thresh="-52.0")
                nml_doc.IF_curr_alpha.append(pynn0)
                
        print_v("Adding NeuroML synapses to: %s"%nml_doc.id)
        
        #pp.pprint(self.syn_comp_info)
        
        for s in self.syn_comp_info:
                
            from neuroml import ExpCurrSynapse
            
            pynnSynn0 = ExpCurrSynapse(id=s, tau_syn="5")
            nml_doc.exp_curr_synapses.append(pynnSynn0)
            
                
        print_v("Adding NeuroML inputs to: %s"%nml_doc.id)
                
        pp.pprint(self.input_comp_info)
        
        for input in self.input_comp_info:
            for input_type in self.input_comp_info[input]:
                print input_type
                if input_type == 'spikes':
                    for comp_id in self.input_comp_info[input][input_type]:
                        info = self.input_comp_info[input][input_type][comp_id]
                        print_v("Adding input %s: %s"%(comp_id, info))
                        from neuroml import TimedSynapticInput, Spike

                        tsi = TimedSynapticInput(id=comp_id, synapse="instanteneousExc", spike_target="./instanteneousExc")
                        nml_doc.timed_synaptic_inputs.append(tsi)
                        for ti in range(len(info['times'])):
                            tsi.spikes.append(Spike(id=ti, time='%sms'%info['times'][ti]))
                elif input_type == 'current_clamp':
                    from neuroml import PulseGenerator
                    for comp_id in self.input_comp_info[input][input_type]:
                        info = self.input_comp_info[input][input_type][comp_id]
                        print info
                        pg = PulseGenerator(id=comp_id,delay='%sms'%info['delay'],duration='%sms'%info['duration'],amplitude='%snA'%info['amp'])
                        nml_doc.pulse_generators.append(pg)
    
    
    def generate_lems_file(self, nml_file_name, nml_doc):
        """
            Generate a LEMS file to use in simulations of the NeuroML file
        """
        
        #pp.pprint(self.simulation_config)
        
        sim_id = 'SonataSim'
        
        target = nml_doc.networks[0].id
        
        duration = self.simulation_config['run']['tstop']
        dt = self.simulation_config['run']['dt']
        lems_file_name = 'LEMS_%s.xml'%sim_id
        target_dir = "./"

        generate_lems_file_for_neuroml(sim_id, 
                                       nml_file_name, 
                                       target, 
                                       duration, 
                                       dt, 
                                       lems_file_name,
                                       target_dir,
                                       include_extra_files = ['PyNN.xml'],
                                       gen_plots_for_all_v = True,
                                       plot_all_segments = False,
                                       gen_plots_for_quantities = {},   #  Dict with displays vs lists of quantity paths
                                       gen_plots_for_only_populations = [],   #  List of populations, all pops if = []
                                       gen_saves_for_all_v = True,
                                       save_all_segments = False,
                                       gen_saves_for_only_populations = [],  #  List of populations, all pops if = []
                                       gen_saves_for_quantities = {},   #  Dict with file names vs lists of quantity paths
                                       gen_spike_saves_for_all_somas = True,
                                       report_file_name = 'report.txt',
                                       copy_neuroml = True,
                                       verbose=True)
                                       
                                     
def get_neuroml_from_sonata(sonata_filename, id, generate_lems = True):
    """
    Return a NeuroMLDocument with (most of) the contents of the Sonata model 
    """
    
    from neuroml.hdf5.NetworkBuilder import NetworkBuilder
    neuroml_handler = NetworkBuilder()
    
    sr = SonataReader(filename=sonata_filename, id=id)
                      
    sr.parse(neuroml_handler)  
    
    nml_doc = neuroml_handler.get_nml_doc()
    
    sr.add_neuroml_components(nml_doc)
    
    nml_file_name = '%s.net.nml'%id
    
    from neuroml.writers import NeuroMLWriter
    NeuroMLWriter.write(nml_doc,nml_file_name)
    print_v('Written to: %s'%nml_file_name)  
    
    if generate_lems:
        sr.generate_lems_file(nml_file_name, nml_doc)
    
    return nml_doc


def main():
    id = '9_cells'
    id = '300_cells'
    id = '5_cells_iclamp'
    filename = '../../git/sonata/examples/%s/config.json'%id
    #filename = '../../git/bmtk/docs/examples/bio_14cells/config.json'
    #filename = '../../git/bmtk/docs/examples/point_120cells/config.json'
    
    #id = '300_intfire'
    #id = '5_cells_iclamp'
    #id = 'small_intfire'
    ## https://github.com/pgleeson/sonata/tree/intfire
    #filename = '../../git/sonatapg/examples/%s/config.json'%id
    #filename = '../../git/sonata/examples/%s/config.json'%id
    
    nml_doc = get_neuroml_from_sonata(filename, id, generate_lems=True)
    
    nml_file_name = '%s.net.nml'%id
    nml_file_name += '.h5'

    from neuroml.writers import NeuroMLHdf5Writer
    NeuroMLHdf5Writer.write(nml_doc,nml_file_name)
    print('Written to: %s'%nml_file_name) 
    
if __name__ == '__main__':
    main()

 
    