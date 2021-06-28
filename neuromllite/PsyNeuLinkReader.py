
import os

from neuroml.hdf5.NetworkContainer import *
from neuromllite.BaseTypes import NetworkReader

from neuromllite.utils import print_v, load_json

class PsyNeuLinkReader(NetworkReader):
    
    component_objects = {} # Store cell ids vs objects, e.g. NeuroML2 based object
    
    PRE_SYN = 'silentSyn'
    POST_SYN = 'rsDL'
    
    def __init__(self, **parameters):
                     
        print_v("Creating PsyNeuLinkReader with %s..."%parameters)
        self.parameters = parameters
        self.current_population = None
        self.pre_pop = None
        self.post_pop = None
        
    def _generate_id(self, name):
        return name.replace(' ','_').replace('[','_').replace(']','_').replace('-','_')

    def parse(self, handler):

        FORMAT = 'BIDS-MDF'
        filename = os.path.abspath(self.parameters['filename'])
        id=filename.split('/')[-1].split('.')[0]
        
        self.handler = handler
    
        bids_mdf = load_json(filename)
        
        print(bids_mdf)
        
        if len(bids_mdf['graphs'])!=1:
            raise Exception('Can only parse %s files with a single graph'%(FORMAT))
        
        graph = bids_mdf['graphs'][0]
        net_id = self._generate_id(graph['name'])
        
        if 'id' in self.parameters:
            id = self._generate_id(self.parameters['id'])
        else:
            id = net_id
            
        notes = "Network (%s) read in from PsyNeuLink/%s: %s"%(id, FORMAT, filename)
        handler.handle_document_start(id, notes)
        
        handler.handle_network(id, notes)
        
        for node_id in graph['nodes']:
            node = graph['nodes'][node_id]
            pop_id = self._generate_id(node['name'])
            size = 1
            properties = {}
            self.handler.handle_population(pop_id, 
                                         self.parameters['DEFAULT_CELL_ID'], 
                                         size,
                                         properties=properties)
                                         
        for edge_id in graph['edges']:
            edge = graph['edges'][edge_id]
            pre_pop = self._generate_id(edge['sender'])
            post_pop = self._generate_id(edge['receiver'])
            weight = float(edge['weight']) if 'weight' in edge else 1
            proj_id = self._generate_id(edge_id)
            self.handler.handle_projection(proj_id, 
                                           pre_pop, 
                                           post_pop, 
                                           synapse=self.PRE_SYN,
                                           type='continuousProjection')
                                           
            self.handler.handle_connection(proj_id, 
                                           0, 
                                           pre_pop, 
                                           post_pop, 
                                           self.PRE_SYN,
                                           0,
                                           0, 
                                           delay = 0, \
                                           weight = weight)

    '''
    def parse_group(self, g):
        #print("+++++++++++++++Parsing group: "+ str(g)+", name: "+g._v_name)

        for node in g:
            #print("   ------Sub node: %s, class: %s, name: %s (parent: %s)"   % (node,node._c_classid,node._v_name, g._v_name))

            if node._c_classid == 'GROUP':
                if g._v_name=='populations':
                    pop_id = node._v_name.replace('-','_')
                    self.current_population = pop_id
                    self.pop_locations[self.current_population] = {}
                    
                if g._v_name=='connectivity':
                    self.pre_pop = node._v_name.replace('-','_')
                    self.post_pop=None
                    #print("Conn %s -> ?"%(self.pre_pop))
                elif self.pre_pop!=None and self.post_pop==None:
                    self.post_pop = node._v_name.replace('-','_')
                    #print("Conn2 %s -> %s"%(self.pre_pop,self.post_pop))
                elif self.pre_pop!=None and self.post_pop!=None:
                    #print("Conn3 %s -> %s"%(self.pre_pop,self.post_pop))
                    pass
                    
                self.parse_group(node)

            if self._is_dataset(node):
                self.parse_dataset(node)
                
        self.current_population = None
        

    def _is_dataset(self, node):
          return node._c_classid == 'ARRAY' or node._c_classid == 'CARRAY'   


    def _is_interneuron(self, pop_id):
        if 'PC' in pop_id or 'SS' in pop_id or 'SP' in pop_id:
            return False
        else:
            return True


    def parse_dataset(self, d):
        #print_v("Parsing dataset/array: "+ str(d))
        
        # Population
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

            self.post_pop=None'''
                
    
if __name__ == '__main__':

    test_files = ['../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/PsyNeuLink/model_with_simple_graph.json']
    test_files.append('../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/NeuroML2/ABC.bids-mdf.json')
    test_files.append('../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/PsyNeuLink/tests/ColorMotionTask_SIMPLE.json')
    test_files.append('../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/PsyNeuLink/tests/StroopModelEVC.json')
    test_files.append('../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/PsyNeuLink/tests/GilzenratModel.json')
    test_files.append('../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/NeuroML2/ABCD.bids-mdf.json')
    
    test_files = ['../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/NeuroML2/ABCD.bids-mdf.json']
    test_files = ['../../neuroConstruct/osb/showcase/PsyNeuLinkShowcase/NeuroML2/FN.bids-mdf.json']

    
    
    for filename in test_files:
        pnl_parser = PsyNeuLinkReader(filename=filename, 
                                  DEFAULT_CELL_ID='hhcell')

        from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler
        def_handler = DefaultNetworkHandler()

        pnl_parser.parse(def_handler)   

        from neuroml.hdf5.NetworkBuilder import NetworkBuilder

        neuroml_handler = NetworkBuilder()


        pnl_parser = PsyNeuLinkReader(filename=filename, 
                                  DEFAULT_CELL_ID='hhcell')
        pnl_parser.parse(neuroml_handler) 

        from neuroml.writers import NeuroMLWriter

        nml_file_name = '%s.net.nml'%neuroml_handler.get_nml_doc().id

        NeuroMLWriter.write(neuroml_handler.get_nml_doc(),nml_file_name)

        print('Written NeuroML file to: %s'%nml_file_name)
