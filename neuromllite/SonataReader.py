
import tables   # pytables for HDF5 support
import os
import random

from neuroml.hdf5.NetworkContainer import *
from neuromllite.BaseTypes import NetworkReader

from neuromllite.utils import print_v, load_json

'''
    Search the strings in a config file for a substitutable value, e.g. 
    "morphologies_dir": "$COMPONENT_DIR/morphologies",
'''
def subs(path, substitutes):
    print_v('Checking for %s in %s'%(substitutes.keys(),path))
    for s in substitutes:
        if s in path:
            path = path.replace(s,substitutes[s])
    return path

'''
    Load a generic csv file as used in Sonata
'''
def load_csv_props(info_file):
    info = {}
    columns = {}
    for line in open(info_file):
        w = line.split()
        if len(columns)==0:
            for i in range(len(w)):
                columns[i] = w[i]
        else:
            info[int(w[0])] = {}
            for i in range(len(w)):
                if i!=0:
                    info[int(w[0])][columns[i]] = w[i]
    return info
            
'''
    Main class for reading a Sonata model. For typical usage, see main method below
'''
class SonataReader(NetworkReader):
    
    component_objects = {} # Store cell ids vs objects, e.g. NeuroML2 based object
    
    def __init__(self, **parameters):
                     
        print_v("Creating SonataReader with %s..."%parameters)
        self.parameters = parameters
        self.current_node = None
        self.current_node_group = None
        self.cell_info = {}
        
        self.current_edge = None
        
        self.pre_pop = None
        self.post_pop = None
        
        self.myrandom = random.Random(12345)
        

    def parse(self, handler):

        filename = os.path.abspath(self.parameters['filename'])
        
        data = load_json(filename)
        substitutes = {'./':'%s/'%os.path.dirname(filename),
                       '${configdir}':'%s'%os.path.dirname(filename),
                       '../':'%s/'%os.path.dirname(os.path.dirname(filename))}
            
        import pprint; pp = pprint.PrettyPrinter(depth=6)
        # pp.pprint(data)
        for m in data['manifest']:
            path = subs(data['manifest'][m],substitutes)
            substitutes[m] = path
            
        # pp.pprint(substitutes)
        
        
        if 'id' in self.parameters:
            id = self.parameters['id']
        else:
            id = 'SonataNetwork'
        
        self.handler = handler
    
        notes = "Network read in from Sonata: %s"%filename
        handler.handle_document_start(id, notes)
        
        handler.handle_network(id, notes)
        self.nodes_info = {}
        
        for n in data['networks']['nodes']:
            nodes_file = subs(n['nodes_file'],substitutes)
            node_types_file = subs(n['node_types_file'],substitutes)
            
            print_v("\nLoading nodes from %s and %s"%(nodes_file,node_types_file))

            h5file=tables.open_file(nodes_file,mode='r')

            print_v("Opened HDF5 file: %s"%(h5file.filename))
            self.parse_group(h5file.root.nodes)
            h5file.close()
            self.nodes_info[self.current_node] = load_csv_props(node_types_file)
            # pp.pprint(self.nodes_info)
            self.current_node = None
            
        self.edges_info = {}
        self.conn_info = {}
        
        for e in data['networks']['edges']:
            edges_file = subs(e['edges_file'],substitutes)
            edge_types_file = subs(e['edge_types_file'],substitutes)
            
            print_v("\nLoading edges from %s and %s"%(edges_file,edge_types_file))

            h5file=tables.open_file(edges_file,mode='r')

            print_v("Opened HDF5 file: %s"%(h5file.filename))
            self.parse_group(h5file.root.edges)
            h5file.close()
            self.edges_info[self.current_edge] = load_csv_props(edge_types_file)
            self.current_edge = None
            
        # pp.pprint(self.edges_info)
            
        for node in self.cell_info:
            types_vs_pops = {}
            for type in self.cell_info[node]['type_numbers']:
                info = self.nodes_info[node][type]
                
                ref = info['model_name'] if 'model_name' in info else info['model_type']
                pop_id = '%s_%s_%s'%(node,ref,type) 
                size = self.cell_info[node]['type_numbers'][type]

                properties = {}

                properties['type_id']=type
                properties['node_id']=node
                properties['region']=node
                for i in info:
                    properties[i]=info[i]
                    if i=='ei':
                        properties['type']=info[i].upper()
                        
                
                color = '%s %s %s'%(self.myrandom.random(),self.myrandom.random(),self.myrandom.random())
                
                try:
                    import opencortex.utils.color as occ
                    interneuron = 'SOM' in pop_id or 'PV' in pop_id
                    if 'L23' in pop_id:
                        color = occ.L23_INTERNEURON if interneuron else occ.L23_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L23'))
                    if 'L4' in pop_id:
                        color = occ.L4_INTERNEURON if interneuron else occ.L4_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L4'))
                    if 'L5' in pop_id:
                        color = occ.L5_INTERNEURON if interneuron else occ.L5_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L5'))
                    if 'L6' in pop_id:
                        color = occ.L6_INTERNEURON if interneuron else occ.L6_PRINCIPAL_CELL
                        pop.properties.append(neuroml.Property('region','L6'))
                except:
                    pass # Don't add anything, not a problem...
                    
                properties['color']=color
                
                self.handler.handle_population(pop_id, 
                                         self.parameters['DEFAULT_CELL_ID'], 
                                         size,
                                         component_obj=None,
                                         properties=properties)
                types_vs_pops[type] = pop_id
            self.cell_info[node]['pop_count'] = {}  
            self.cell_info[node]['pop_map'] = {}   
            
            for i in self.cell_info[node]['types']:
                
                pop = types_vs_pops[self.cell_info[node]['types'][i]]
                
                if not pop in self.cell_info[node]['pop_count']:
                    self.cell_info[node]['pop_count'][pop] = 0
                    
                index = self.cell_info[node]['pop_count'][pop]
                self.cell_info[node]['pop_map'][i] = (pop, index)
                
                if i in self.cell_info[node]['0']['locations']:
                    pos = self.cell_info[node]['0']['locations'][i]
                    self.handler.handle_location(index, 
                                                 pop, 
                                                 self.parameters['DEFAULT_CELL_ID'], 
                                                 pos['x'] if 'x' in pos else 0, 
                                                 pos['y'] if 'y' in pos else 0, 
                                                 pos['z'] if 'z' in pos else 0)
                
                self.cell_info[node]['pop_count'][pop]+=1
        
        projections_created = []
        for conn in self.conn_info:
            
            pre_node = self.conn_info[conn]['pre_node']
            post_node = self.conn_info[conn]['post_node']
            
            # print('-- Conn %s -> %s'%(pre_node,post_node))
            
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
                proj_id = '%s_%s_%s'%(pre_pop,post_pop,synapse)
                
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
                                             delay = 0, \
                                             weight = 1)
                

        
        # pp.pprint(self.conn_info)
        # pp.pprint(self.cell_info)


    def parse_group(self, g):
        #print("+++++++++++++++Parsing group: "+ str(g)+", name: "+g._v_name)

        for node in g:
            #print("   ------Sub node: %s, class: %s, name: %s (parent: %s)"   % (node,node._c_classid,node._v_name, g._v_name))

            if node._c_classid == 'GROUP':
                if g._v_name=='nodes':
                    node_id = node._v_name.replace('-','_')
                    self.current_node = node_id
                    self.cell_info[self.current_node] = {}
                    self.cell_info[self.current_node]['types'] = {}
                    self.cell_info[self.current_node]['type_numbers'] = {}
                    #self.pop_locations[self.current_population] = {}
                    
                if g._v_name==self.current_node:
                    node_group = node._v_name
                    self.current_node_group = node_group
                    self.cell_info[self.current_node][self.current_node_group] = {}
                    self.cell_info[self.current_node][self.current_node_group]['locations'] = {}
                    
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
                
        self.current_population = None
        self.current_node_group = None
        

    def _is_dataset(self, node):
          return node._c_classid == 'ARRAY' or node._c_classid == 'CARRAY'   



    def parse_dataset(self, d):
        print_v("Parsing dataset/array: %s; at node: %s, node_group %s"%(str(d), self.current_node, self.current_node_group))
                
        if self.current_node_group:
            for i in range(0, d.shape[0]):
                #index = 0 if d.name=='x' else (1 if d.name=='y' else 2)
                
                if not i in self.cell_info[self.current_node][self.current_node_group]['locations']:
                    self.cell_info[self.current_node][self.current_node_group]['locations'][i] = {}
                self.cell_info[self.current_node][self.current_node_group]['locations'][i][d.name] = d[i]
                
        elif self.current_node:
            
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
                    self.cell_info[self.current_node]['types'][i] = d[i]
                    if not d[i] in self.cell_info[self.current_node]['type_numbers']:
                        self.cell_info[self.current_node]['type_numbers'][d[i]]=0
                    self.cell_info[self.current_node]['type_numbers'][d[i]]+=1
           
        elif d.name=='source_node_id':
            self.conn_info[self.current_edge]['pre_id'] = [i for i in d]
        elif d.name=='edge_type_id':
            self.conn_info[self.current_edge]['edge_type_id'] = [int(i) for i in d]
        elif d.name=='target_node_id':
            self.conn_info[self.current_edge]['post_id'] = [i for i in d]
              
        else:
            print_v("Unhandled dataset: %s"%d.name)
        
        # Population
        '''
        if self.current_population and d.name=='locations':
            
            perc_cells = self.parameters['percentage_cells_per_pop'] if 'percentage_cells_per_pop' in self.parameters else 100
            if perc_cells>100: perc_cells = 100
            
            size = max(0,int((perc_cells/100.)*d.shape[0]))
            
            if size>0:
                properties = {}
                if self._is_interneuron(self.current_population):
                    properties['radius'] = 5
                    type='I'
                else:
                    properties['radius'] = 10
                    type='E'
                properties['type'] = type
                    
                layer = self.current_population.split('_')[0]
                properties['region'] = layer
                try:
                    import opencortex.utils.color as occ
                    if layer == 'L23':
                        if type=='E': color = occ.L23_PRINCIPAL_CELL
                        if type=='I': color = occ.L23_INTERNEURON
                    if layer == 'L4':
                        if type=='E': color = occ.L4_PRINCIPAL_CELL
                        if type=='I': color = occ.L4_INTERNEURON
                    if layer == 'L5':
                        if type=='E': color = occ.L5_PRINCIPAL_CELL
                        if type=='I': color = occ.L5_INTERNEURON
                    if layer == 'L6':
                        if type=='E': color = occ.L6_PRINCIPAL_CELL
                        if type=='I': color = occ.L6_INTERNEURON
                            
                    properties['color'] = color
                except:
                    # Don't worry about it, it's just metadata
                    pass
                
                component_obj = None
                
                if self.parameters['DEFAULT_CELL_ID'] in self.component_objects:
                    component_obj = self.component_objects[self.parameters['DEFAULT_CELL_ID']]
                else:
                    if 'cell_info' in self.parameters:
                        def_cell_info = self.parameters['cell_info'][self.parameters['DEFAULT_CELL_ID']]
                        if def_cell_info.neuroml2_source_file:
                            from pyneuroml import pynml
                            nml2_doc = pynml.read_neuroml2_file(def_cell_info.neuroml2_source_file, 
                                                    include_includes=True)
                            component_obj = nml2_doc.get_by_id(self.parameters['DEFAULT_CELL_ID'])
                            print_v("Loaded NeuroML2 object %s from %s "%(component_obj,def_cell_info.neuroml2_source_file))
                            self.component_objects[self.parameters['DEFAULT_CELL_ID']] = component_obj
                        

                self.handler.handle_population(self.current_population, 
                                         self.parameters['DEFAULT_CELL_ID'], 
                                         size,
                                         component_obj=component_obj,
                                         properties=properties)

                print_v("   There are %i cells in: %s"%(size, self.current_population))
                for i in range(0, d.shape[0]):

                    if i<size:
                        row = d[i,:]
                        x = row[0]
                        y = row[1]
                        z = row[2]
                        self.pop_locations[self.current_population][i]=(x,y,z)
                        self.handler.handle_location(i, self.current_population, self.parameters['DEFAULT_CELL_ID'], x, y, z)
                    
                
        # Projection
        elif self.pre_pop!=None and self.post_pop!=None:
            
            proj_id = 'Proj__%s__%s'%(self.pre_pop,self.post_pop)
            synapse = 'gaba'
            if 'PC' in self.pre_pop or 'SS' in self.pre_pop: # TODO: better choice between E/I cells
                synapse = 'ampa'
                
            (ii, jj) = np.nonzero(d)
            conns_here = False
            pre_num = len(self.pop_locations[self.pre_pop]) if self.pre_pop in self.pop_locations else 0
            post_num = len(self.pop_locations[self.post_pop]) if self.post_pop in self.pop_locations else 0
            
            if pre_num>0 and post_num>0:
                for index in range(len(ii)):
                    if ii[index]<pre_num and \
                       jj[index]<post_num:
                        conns_here=True
                        break

                if conns_here:
                    print_v("Conn %s -> %s (%s)"%(self.pre_pop,self.post_pop, synapse))
                    self.handler.handle_projection(proj_id, 
                                         self.pre_pop, 
                                         self.post_pop, 
                                         synapse)

                    conn_count = 0

                    for index in range(len(ii)):
                        i = ii[index]
                        j = jj[index]
                        if i<pre_num and j<post_num:
                            #print("  Conn5 %s[%s] -> %s[%s]"%(self.pre_pop,i,self.post_pop,j))
                            delay = 1.111
                            weight =1
                            self.handler.handle_connection(proj_id, 
                                             conn_count, 
                                             self.pre_pop, 
                                             self.post_pop, 
                                             synapse, \
                                             i, \
                                             j, \
                                             delay = delay, \
                                             weight = weight)
                            conn_count+=1


                    self.handler.finalise_projection(proj_id, 
                                         self.pre_pop, 
                                         self.post_pop, 
                                         synapse)

            self.post_pop=None
            
        '''
                
    
if __name__ == '__main__':


    id = '9_cells'
    id = '300_cells'
    filename = '../../git/bmtk/docs/examples/bio_basic_features/config_iclamp.json'
    filename = '../../git/sonata/examples/%s/circuit_config.json'%id
    #filename = '../../git/bmtk/docs/examples/bio_14cells/config.json'
    #filename = '../../git/bmtk/docs/examples/point_120cells/config.json'
    filename = '../../git/sonatakd/examples/300_intfire/circuit_config.json'
    
    '''sr = SonataReader(filename=filename, 
                      id=id,
                      DEFAULT_CELL_ID='hhcell')
    
    from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
    def_handler = DefaultNetworkHandler()
    
    sr.parse(def_handler)   '''
    
    from neuroml.hdf5.NetworkBuilder import NetworkBuilder

    neuroml_handler = NetworkBuilder()
    
    sr = SonataReader(filename=filename, 
                      id=id,
                      DEFAULT_CELL_ID='hhcell')
    sr.parse(neuroml_handler)  
    
    nml_file_name = '%s.net.nml'%id

    from neuroml.writers import NeuroMLWriter
    NeuroMLWriter.write(neuroml_handler.get_nml_doc(),nml_file_name)
    print('Written to: %s'%nml_file_name)  
    
    nml_file_name += '.h5'

    from neuroml.writers import NeuroMLHdf5Writer
    NeuroMLHdf5Writer.write(neuroml_handler.get_nml_doc(),nml_file_name)
    print('Written to: %s'%nml_file_name)  
    