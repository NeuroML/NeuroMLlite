#
#
#   A class to write to the GraphViz format...
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from graphviz import Digraph

from neuromllite.utils import evaluate
            
from pyneuroml.pynml import convert_to_units

class GraphVizHandler(DefaultNetworkHandler):
        
    CUTOFF_INH_SYN_MV = -50 # erev below -50mV => inhibitory, above => excitatory
    
    positions = {}
    pop_indices = {}
    
    pop_colors = {}
    pop_types = {}
    
    proj_weights = {}
    proj_shapes = {}
    proj_lines = {}
    proj_pre_pops = {}
    proj_post_pops = {}
    proj_conns = {}
    
    max_weight = -1e100
    min_weight = 1e100
    
    def __init__(self, level=10, nl_network=None):
        print_v("Initiating GraphViz handler")
        self.nl_network = nl_network
        self.level = level
    

    def handle_document_start(self, id, notes):
            
        print_v("Document: %s"%id)
        
    def finalise_document(self):
        
        for projName in self.proj_weights:
            
            if self.max_weight==self.min_weight:
                fweight = 1
                lweight = 1
            else:
                fweight = (self.proj_weights[projName]-self.min_weight)/(self.max_weight-self.min_weight)
                lweight = 0.5 + fweight*2.0

            if self.level>=2:
                #print("%s: weight %s -> %s; fw: %s; lw: %s"%(projName, self.max_weight,self.min_weight,fweight,lweight))
                self.f.attr('edge', 
                            style = self.proj_lines[projName], 
                            arrowhead = self.proj_shapes[projName], 
                            arrowsize = '%s'%(min(1,lweight)), 
                            penwidth = '%s'%(lweight), 
                            color=self.pop_colors[self.proj_pre_pops[projName]],
                            fontcolor = self.pop_colors[self.proj_pre_pops[projName]])

                if self.level>=4:
                    label='<'
                    if self.proj_weights[projName]!=1.0:
                        label+='weight: %s<br/>'%self.proj_weights[projName]

                    if self.nl_network:
                        proj = self.nl_network.get_child(projName,'projections')
                        if proj and proj.random_connectivity:
                            label += 'p: %s<br/>'%proj.random_connectivity.probability
                        
                    if self.proj_conns[projName]>0:
                        label += '%s conns'%self.proj_conns[projName]
                        
                            
                    if not label[-1]=='>':
                        label += '>'
                    
                    self.f.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName], label=label)
                else:
                    self.f.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName])
        
        print_v("Writing file...: %s"%id)
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
        color = '#444444' 
        fcolor= '#ffffff'
        
        if properties and 'color' in properties:
            rgb = properties['color'].split()
            color = '#'
            for a in rgb:
                color = color+'%02x'%int(float(a)*255)
            
            # https://stackoverflow.com/questions/3942878
            if (float(rgb[0])*0.299 + float(rgb[1])*0.587 + float(rgb[2])*0.114) > .4:
                fcolor= '#000000'
            else:
                fcolor= '#ffffff'
                
            #print('Color %s -> %s -> %s'%(properties['color'], rgb, color))
        
        if properties and 'type' in properties:
            self.pop_types[population_id] = properties['type']
            
        self.pop_colors[population_id] = color
        
        label = '<%s'%population_id
        if self.level>=3:
            label += '<br/><i>%s cell%s</i>'%( size, '' if size==1 else 's')
        if self.level>=4:
            
            from neuroml import SpikeSourcePoisson
            
            if component_obj and isinstance(component_obj,SpikeSourcePoisson):
                start = convert_to_units(component_obj.start, 'ms')
                if start == int(start): start = int(start)
                duration = convert_to_units(component_obj.duration,'ms')
                if duration == int(duration): duration = int(duration)
                rate = convert_to_units(component_obj.rate,'Hz')
                if rate == int(rate): rate = int(rate)
                    
                label += '<br/>Spikes %s-%sms @ %sHz'%(start,start+duration, rate)
                
            else:
                label += '<br/>%s'%(component)
            
        label += '>'
            
        if properties and 'region' in properties:
            
            with self.f.subgraph(name='cluster_%s'%properties['region']) as c:
                c.attr(color='#444444', fontcolor = '#444444')
                c.attr(label=properties['region'])
                c.attr('node', color=color, style='filled', fontcolor = fcolor)
                c.node(population_id, label=label)
    
        else:
            self.f.attr('node', color=color, style='filled', fontcolor = fcolor)
            self.f.node(population_id, label=label)
        
 
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
        line = 'normal'
            
        weight = 1.0
        self.proj_pre_pops[projName] = prePop
        self.proj_post_pops[projName] = postPop
        
        if prePop in self.pop_types:
            if 'I' in self.pop_types[prePop]:
                shape = 'dot'
                
        if type=='electricalProjection':
                shape = 'none'
                line = 'dashed'
            
        if synapse_obj:
            
            if hasattr(synapse_obj,'erev') and convert_to_units(synapse_obj.erev,'mV')<self.CUTOFF_INH_SYN_MV:
                shape = 'dot'
                
        if self.nl_network:
            syn = self.nl_network.get_child(synapse,'synapses')
            if syn:
                if syn.parameters:
                    if 'e_rev' in syn.parameters and syn.parameters['e_rev']<self.CUTOFF_INH_SYN_MV:
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
                        
        self.max_weight = max(self.max_weight, weight)
        self.min_weight = min(self.min_weight, weight)
        
        self.proj_weights[projName] = weight
        self.proj_shapes[projName] = shape
        self.proj_lines[projName] = line
        self.proj_conns[projName] = 0


    def handle_connection(self, projName, id, prePop, postPop, synapseType, \
                                                    preCellId, \
                                                    postCellId, \
                                                    preSegId = 0, \
                                                    preFract = 0.5, \
                                                    postSegId = 0, \
                                                    postFract = 0.5, \
                                                    delay = 0, \
                                                    weight = 1):
        
        self.proj_conns[projName]+=1

  
    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        print_v("Projection finalising: "+projName+" from "+prePop+" to "+postPop+" completed")

        
    #
    #  Should be overridden to create input source array
    #  
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):
        
        self.print_input_information(inputListId, population_id, component, size)
        
        if size<0:
            self.log.error("Error! Need a size attribute in sites element to create spike source!")
            return
             
        if self.level>=2:

            label = '<%s'%inputListId
            if self.level>=3:
                label += '<br/><i>%s input%s</i>'%( size, '' if size==1 else 's')
            if self.level>=4:
            
                from neuroml import PulseGenerator
                from neuroml import TransientPoissonFiringSynapse
                from neuroml import PoissonFiringSynapse
                from pyneuroml.pynml import convert_to_units

                if input_comp_obj and isinstance(input_comp_obj,PulseGenerator):
                    start = convert_to_units(input_comp_obj.delay, 'ms')
                    if start == int(start): start = int(start)
                    duration = convert_to_units(input_comp_obj.duration,'ms')
                    if duration == int(duration): duration = int(duration)
                    amplitude = convert_to_units(input_comp_obj.amplitude,'pA')
                    if amplitude == int(amplitude): amplitude = int(amplitude)

                    label += '<br/>Pulse %s-%sms @ %spA'%(start,start+duration, amplitude)
                    
                if input_comp_obj and isinstance(input_comp_obj,PoissonFiringSynapse):
                        
                    average_rate = convert_to_units(input_comp_obj.average_rate,'Hz')
                    if average_rate == int(average_rate): average_rate = int(average_rate)

                    label += '<br/>Syn: %s @ %sHz'%(input_comp_obj.synapse, average_rate)
                    
                if input_comp_obj and isinstance(input_comp_obj,TransientPoissonFiringSynapse):

                    start = convert_to_units(input_comp_obj.delay, 'ms')
                    if start == int(start): start = int(start)
                    duration = convert_to_units(input_comp_obj.duration,'ms')
                    if duration == int(duration): duration = int(duration)
                    average_rate = convert_to_units(input_comp_obj.average_rate,'Hz')
                    if average_rate == int(average_rate): average_rate = int(average_rate)

                    label += '<br/>Syn: %s %s-%sms @ %sHz'%(input_comp_obj.synapse,start,start+duration, average_rate)
                    
            label += '>'
            
            self.f.attr('node', color='#444444', style='', fontcolor = '#444444')
            self.f.node(inputListId, label=label)
            self.f.edge(inputListId, population_id, arrowhead='empty')
            
        
    '''          
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
