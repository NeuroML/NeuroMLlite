#
#
#   A class to write to the GraphViz format...
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from graphviz import Digraph, Graph

from neuromllite.utils import evaluate


class GraphVizHandler(DefaultNetworkHandler):
        
    positions = {}
    pop_indices = {}
    
    def __init__(self, level=10, nl_network=None):
        print_v("Initiating GraphViz handler")
        self.nl_network = nl_network
        self.level = level
    

    def handle_document_start(self, id, notes):
            
        print_v("Document: %s"%id)
        
    def finalise_document(self):
        
        print_v("Writing file...: %s"%id)
        #self.sonata_nodes.close()
        self.f.view()
        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
        engine = 'dot'
        #if self.level<=2:
        #    engine = 'neato'
            
        self.f = Digraph(network_id, filename='%s.gv'%network_id, engine=engine)
        

    def handle_population(self, population_id, component, size=-1, component_obj=None, properties={}):
        sizeInfo = " as yet unspecified size"
        if size>=0:
            sizeInfo = ", size: "+ str(size)+ " cells"
        if component_obj:
            compInfo = " (%s)"%component_obj.__class__.__name__
        else:
            compInfo=""
            
        print_v("Population: "+population_id+", component: "+component+compInfo+sizeInfo+", properties: %s"%properties)
        color = 'lightgrey' 
        fcolor= '#ffffff'
        
        if properties and 'color' in properties:
            rgb = properties['color'].split()
            color = '#'
            for a in rgb:
                color = color+'%02x'%int(float(a)*255)
            
            # https://stackoverflow.com/questions/3942878
            if (float(rgb[0])*0.299 + float(rgb[1])*0.587 + float(rgb[2])*0.114) > .6:
                fcolor= '#000000'
            else:
                fcolor= '#ffffff'
                
            print('Color %s -> %s -> %s'%(properties['color'], rgb, color))
            
        
        if properties and 'region' in properties:
            
            with self.f.subgraph(name='cluster_%s'%properties['region']) as c:
                c.attr(color='darkgrey')
                c.attr('node', color=color, style='filled', fontcolor = fcolor)
                c.node(population_id)
                c.attr(label=properties['region'])
    
        else:
            self.f.attr('node', color=color, style='filled', fontcolor = fcolor)
            self.f.node(population_id, _attributes={})
        
 
    def handle_location(self, id, population_id, component, x, y, z):
        '''
        if not population_id in self.positions:
            self.positions[population_id] = np.array([[x,y,z]])
            self.pop_indices[population_id] = np.array([id])
        else:
            self.positions[population_id] = np.concatenate((self.positions[population_id], [[x,y,z]]))
            self.pop_indices[population_id] = np.concatenate((self.pop_indices[population_id], [id]))
        '''
        pass
        

    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):

        shape = 'normal'
        '''
        if synapse_obj:
            print synapse_obj.erev
            shape = 'dot'''
            
        weight = 1
        
        if self.nl_network:
            #print synapse
            #print self.nl_network.synapses
            syn = self.nl_network.get_child(synapse,'synapses')
            if syn:
                #print syn
                if syn.parameters:
                    #print syn.parameters
                    if 'e_rev' in syn.parameters and syn.parameters['e_rev']<-50:
                        shape = 'dot'
            
            proj = self.nl_network.get_child(projName,'projections')  
            if proj:
                if proj.weight:
                    proj_weight = evaluate(proj.weight, self.nl_network.parameters)
                    if proj_weight<0:
                        shape = 'dot'
                    weight = abs(proj_weight)
                if proj.random_connectivity:
                    weight *= proj.random_connectivity.probability
                #print 'w: %s'%weight
                        
            
        if self.level>=2:
            #self.f.attr('edge', penwidth=random())
            self.f.attr('edge', arrowhead=shape, arrowsize='%s'%(max(.5,1*weight)), penwidth='%s'%(max(.5,3*weight)))
            self.f.edge(prePop, postPop)


    def handle_connection(self, projName, id, prePop, postPop, synapseType, \
                                                    preCellId, \
                                                    postCellId, \
                                                    preSegId = 0, \
                                                    preFract = 0.5, \
                                                    postSegId = 0, \
                                                    postFract = 0.5, \
                                                    delay = 0, \
                                                    weight = 1):
        
        pass

    '''      
    #
    #  Should be overridden to handle end of network connection
    #  
    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        print_v("Projection finalising: "+projName+" from "+prePop+" to "+postPop+" completed")
        
        #exec('print(self.projection__%s_conns)'%projName)
        exec('self.projection__%s_connector = self.sim.FromListConnector(self.projection__%s_conns, column_names=["weight", "delay"])'%(projName,projName))

        exec('self.projections["%s"] = self.sim.Projection(self.populations["%s"],self.populations["%s"], ' % (projName,prePop,postPop) + \
                                                          'connector=self.projection__%s_connector, ' % projName + \
                                                          'synapse_type=self.sim.StaticSynapse(weight=%s, delay=%s), ' % (1,5) + \
                                                          'receptor_type="%s", ' % (self.receptor_types[synapse]) + \
                                                          'label="%s")'%projName)
        
        #exec('print(self.projections["%s"].describe())'%projName)
        

        
    #
    #  Should be overridden to create input source array
    #  
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):
        
        self.print_input_information(inputListId, population_id, component, size)
        
        if size<0:
            self.log.error("Error! Need a size attribute in sites element to create spike source!")
            return
             
        self.input_info[inputListId] = (population_id, component)
        
    #
    #  Should be overridden to to connect each input to the target cell
    #  
    def handle_single_input(self, inputListId, id, cellId, segId = 0, fract = 0.5, weight=1):
        
        print_v("Input: %s[%s], cellId: %i, seg: %i, fract: %f, weight: %f" % (inputListId,id,cellId,segId,fract,weight))
        
        population_id, component = self.input_info[inputListId]
        
        #exec('print  self.POP_%s'%(population_id))
        #exec('print  self.POP_%s[%s]'%(population_id,cellId))
       
        exec('self.POP_%s[%s].inject(self.input_sources[component]) '%(population_id,cellId))
        #exec('self.input_sources[component].inject_into(self.populations["%s"])'%(population_id))
        
        #exec('pulse = self.sim.DCSource(amplitude=0.9, start=19, stop=89)')
        #pulse.inject_into(pop_pre)
        #exec('self.populations["pop0"][0].inject(pulse)')

        
    #
    #  Should be overridden to to connect each input to the target cell
    #  
    def finalise_input_source(self, inputName):
        print_v("Input : %s completed" % inputName)
        
'''
