#
#
#   A class to write the network connectivity in matrix format...
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from neuromllite.utils import evaluate
            
from pyneuroml.pynml import convert_to_units
import numpy as np


class MatrixHandler(DefaultNetworkHandler):
        
    CUTOFF_INH_SYN_MV = -50 # erev below -50mV => inhibitory, above => excitatory
    
    positions = {}
    
    pop_sizes = {}
    pop_colors = {}
    pop_types = {}
    
    proj_weights = {}
    proj_types = {}
    proj_pre_pops = {}
    proj_post_pops = {}
    proj_conns = {}
    proj_tot_weight = {}
    proj_syn_objs = {}
    
    max_weight = -1e100
    min_weight = 1e100
    
    weight_arrays = {}
    
    def __init__(self, 
                 level=10, 
                 nl_network=None,
                 include_inputs=True):
                     
        self.nl_network = nl_network
        self.level = level
        self.include_inputs = include_inputs
        print_v("Initiating Matrix handler, level %i"%(level))
    

    def handle_document_start(self, id, notes):
            
        print_v("Document: %s"%id)
        
        
    def format_float(self, f, d=3, approx=False):
        if int(f)==f:
            return int(f)
        
        template = '%%.%if' % d # e.g. '%.2f'
        
        ff = float(template%f)
        if f==ff:
            return '%s'%ff
        return '%s%s'%('~' if approx else '',ff)
        
    def _get_proj_class(self, proj_type):
        if proj_type == 'excitatory' or proj_type == 'inhibitory':
            return 'chemical'
        elif proj_type == 'excitatorycontinuous' or proj_type == 'inhibitorycontinuous':
            return 'continuous'
        else:
            return proj_type
        
        
    def finalise_document(self):
        
        all_pops = []
        for v in self.proj_pre_pops.values():
            if not v in all_pops:
                all_pops.append(v)
        for v in self.proj_post_pops.values():
            if not v in all_pops:
                all_pops.append(v)

        all_pops = sorted(all_pops)
        
        title_single_conns = '%s (single conns)'
        title_number_conns = '%s (number conns)'
        title_total_conns = '%s (weight*number)'
        
        for proj_type in self.proj_types.values():
            pclass = self._get_proj_class(proj_type)
            self.weight_arrays[title_single_conns%pclass] = np.zeros((len(all_pops),len(all_pops)))
            self.weight_arrays[title_number_conns%pclass] = np.zeros((len(all_pops),len(all_pops)))
            self.weight_arrays[title_total_conns%pclass] = np.zeros((len(all_pops),len(all_pops)))
                
        for projName in self.proj_weights:
            
            pre_pop = self.proj_pre_pops[projName]
            pre_pop_i = all_pops.index(pre_pop)
            post_pop = self.proj_post_pops[projName]
            post_pop_i = all_pops.index(post_pop)
            proj_type = self.proj_types[projName]
            

            if self.level>=2:
                pclass = self._get_proj_class(proj_type)
                sign = -1 if 'inhibitory' in proj_type else 1
                
                print_v("MATRIX PROJ: %s (%s -> %s, %s): w %s; wtot: %s; sign: %s; all: %s -> %s"%(projName, pre_pop, post_pop, proj_type, self.proj_weights[projName], self.proj_tot_weight[projName], sign, self.max_weight,self.min_weight))

                self.weight_arrays[title_total_conns%pclass][pre_pop_i][post_pop_i] = \
                     abs(self.proj_tot_weight[projName]) * sign
                     
                if abs(self.proj_tot_weight[projName])!=abs(self.proj_weights[projName]):

                    self.weight_arrays[title_single_conns%pclass][pre_pop_i][post_pop_i] = \
                         abs(self.proj_weights[projName]) * sign
                         
                    self.weight_arrays[title_number_conns%pclass][pre_pop_i][post_pop_i] = \
                         abs(self.proj_conns[projName])
                
                '''
                self.f.attr('edge', 
                            style = self.proj_lines[projName], 
                            arrowhead = self.proj_shapes[projName], 
                            arrowsize = '%s'%(min(1,lweight)), 
                            penwidth = '%s'%(lweight), 
                            color=self.pop_colors[self.proj_pre_pops[projName]],
                            fontcolor = self.pop_colors[self.proj_pre_pops[projName]])

                if self.level>=4:
                    label='<'
                    
                    if self.level>=5:
                        if projName in self.proj_syn_objs:
                            syn = self.proj_syn_objs[projName]
                            label+='%s<br/> '%syn.id
                        
                    if self.proj_weights[projName]!=1.0:
                        label+='weight: %s<br/> '%self.format_float(self.proj_weights[projName])
                       
                    if self.proj_tot_weight[projName]>0:
                        avg_weight = float(float(self.proj_tot_weight[projName])/self.proj_conns[projName])
                        label+='avg weight: %s<br/> '%self.format_float(avg_weight, approx=True)

                    if self.nl_network:
                        proj = self.nl_network.get_child(projName,'projections')
                        if proj and proj.random_connectivity:
                            label += 'p: %s<br/> '%proj.random_connectivity.probability
                        
                    if self.proj_conns[projName]>0:
                        label += '%s conns<br/> '%self.proj_conns[projName]
                        
                    if self.level>=5:
                        
                        if self.proj_conns[projName]>0:
                            
                            pre_avg = float(self.proj_conns[projName])/self.pop_sizes[self.proj_pre_pops[projName]]
                            post_avg = float(self.proj_conns[projName])/self.pop_sizes[self.proj_post_pops[projName]]
                            
                            label+=' %s/pre &#8594; %s/post<br/> '%(self.format_float(pre_avg,approx=True), self.format_float(post_avg,approx=True))
                            
                            if projName in self.proj_syn_objs:
                                syn = self.proj_syn_objs[projName]
                                
                                if hasattr(syn,'gbase'):
                                    gbase = syn.gbase
                                elif hasattr(syn,'conductance'):
                                    gbase = syn.conductance
                                    
                                gbase_si = convert_to_units(gbase, 'nS')
                                label+='%s*%s*%s = %s nS<br/> '%(self.format_float(post_avg), self.format_float(avg_weight), gbase, self.format_float(post_avg*avg_weight*gbase_si))
                        
                    if not label[-1]=='>':
                        label += '>'
                    
                    self.f.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName], label=label)
                else:
                    self.f.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName])
                '''
        
        #print_v("Writing file...: %s"%id)
        
        #self.f.view()
        
        import matplotlib.pyplot as plt
        import matplotlib
        
        for proj_type in self.weight_arrays:
            weight_array = self.weight_arrays[proj_type]
            if not (weight_array.max()==0 and weight_array.min()==0):

                fig, ax = plt.subplots()
                title = 'Connections: %s'%(proj_type)
                plt.title(title)
                fig.canvas.set_window_title(title)

                abs_max_w = max(weight_array.max(), -1*(weight_array.min()))
                
                if weight_array.min()<0:
                    cm = matplotlib.cm.get_cmap('bwr')
                else:
                    cm = matplotlib.cm.get_cmap('binary')
                    if 'number' in proj_type:
                        cm = matplotlib.cm.get_cmap('jet')
                        

                print_v("Plotting weight matrix: %s with values from %s to %s"%(title, weight_array.min(), weight_array.max()))

                im = plt.imshow(weight_array, cmap=cm, interpolation='nearest',norm=None)

                if weight_array.min()<0:
                    plt.clim(-1*abs_max_w,abs_max_w)
                else:
                    plt.clim(0,abs_max_w)

                ax = plt.gca();

                # Gridlines based on minor ticks
                if weight_array.shape[0]<40:
                    ax.grid(which='minor', color='grey', linestyle='-', linewidth=.3)

                xt = np.arange(weight_array.shape[1]) + 0
                ax.set_xticks(xt)
                ax.set_xticks(xt[:-1]+0.5,minor=True)
                ax.set_yticks(np.arange(weight_array.shape[0]) + 0)
                ax.set_yticks(np.arange(weight_array.shape[0]) + 0.5,minor=True)


                ax.set_yticklabels(all_pops)
                ax.set_xticklabels(all_pops)
                ax.set_ylabel('presynaptic')
                tick_size = 10 if weight_array.shape[0]<20 else (8 if weight_array.shape[0]<40 else 6)
                ax.tick_params(axis='y', labelsize=tick_size)
                ax.set_xlabel('postsynaptic')
                ax.tick_params(axis='x', labelsize=tick_size)
                fig.autofmt_xdate()
                
                
                for i in range(len(all_pops)):
                    alpha = 1
                    lwidth = 7
                    offset = -1*lwidth*len(all_pops)/500.
                    
                    if self.pop_colors[all_pops[i]]:
                        from matplotlib import lines
                        x,y = [[-0.5+offset,-0.5+offset], [i-0.5,i+0.5]]
                        line = lines.Line2D(x, y, lw=lwidth, color=self.pop_colors[all_pops[i]], alpha=alpha)
                        line.set_solid_capstyle('butt')
                        line.set_clip_on(False)
                        ax.add_line(line)
                        
                        x,y = [[i-0.5,i+0.5], [len(all_pops)-0.5-offset,len(all_pops)-0.5-offset]]
                        line = lines.Line2D(x, y, lw=lwidth, color=self.pop_colors[all_pops[i]], alpha=alpha)
                        line.set_solid_capstyle('butt')
                        line.set_clip_on(False)
                        ax.add_line(line)

                cbar = plt.colorbar(im)
        plt.show()
        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
            

    def handle_population(self, population_id, component, size=-1, component_obj=None, properties={}):
        sizeInfo = " as yet unspecified size"
        
        if size>=0:
            sizeInfo = ", size: "+ str(size)+ " cells"
            
        if component_obj:
            compInfo = " (%s)"%component_obj.__class__.__name__
        else:
            compInfo=""
            
        self.pop_sizes[population_id] = size
            
        print_v("Population: "+population_id+", component: "+component+compInfo+sizeInfo+", properties: %s"%properties)
        
        color = None 
        
        
        if properties and 'color' in properties:
            rgb = properties['color'].split()
            color = '#'
            for a in rgb:
                color = color+'%02x'%int(float(a)*255)
            
            # https://stackoverflow.com/questions/3942878
            if (float(rgb[0])*0.299 + float(rgb[1])*0.587 + float(rgb[2])*0.2) > .25:
                fcolor= '#000000'
            else:
                fcolor= '#ffffff'
                
            print_v('Color %s -> %s -> %s'%(properties['color'], rgb, color))
        
        if properties and 'type' in properties:
            self.pop_types[population_id] = properties['type']
            if properties['type']=='E':
                pass
                #shape = self.EXC_POP_SHAPE
            if properties['type']=='I':
                pass
                #shape = self.INH_POP_SHAPE
            
        self.pop_colors[population_id] = color
        
        label = population_id
        
        region=properties['region'] if 'region' in properties else None
    
        
 
    def handle_location(self, id, population_id, component, x, y, z):
        
        pass
        

    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):
            
        
        weight = 1.0
        self.proj_pre_pops[projName] = prePop
        self.proj_post_pops[projName] = postPop
        
        proj_type = 'excitatory'
        
        if prePop in self.pop_types:
            if 'I' in self.pop_types[prePop]:
                proj_type = 'inhibitory'
                
        if type=='electricalProjection':
            proj_type = 'gap_junction'
            
            
        if synapse_obj:
            self.proj_syn_objs[projName] = synapse_obj
            if hasattr(synapse_obj,'erev') and convert_to_units(synapse_obj.erev,'mV')<self.CUTOFF_INH_SYN_MV:
                proj_type = 'inhibitory'
                
        if self.nl_network:
            syn = self.nl_network.get_child(synapse,'synapses')
            if syn:
                if syn.parameters:
                    if 'e_rev' in syn.parameters and syn.parameters['e_rev']<self.CUTOFF_INH_SYN_MV:
                        proj_type = 'inhibitory'
            
            proj = self.nl_network.get_child(projName,'projections')  
            if proj:
                if proj.weight:
                    proj_weight = evaluate(proj.weight, self.nl_network.parameters)
                    if proj_weight<0:
                        proj_type = 'inhibitory'
                    weight = abs(proj_weight)
                    
        if type=='continuousProjection':
            proj_type += 'continuous'
                        
        self.max_weight = max(self.max_weight, weight)
        self.min_weight = min(self.min_weight, weight)
        
        self.proj_weights[projName] = weight
        self.proj_types[projName] = proj_type
        self.proj_conns[projName] = 0
        self.proj_tot_weight[projName] = 0


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
        self.proj_tot_weight[projName]+=weight

  
    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        print_v("Projection finalising: "+projName+" -> "+prePop+" to "+postPop+" completed (%s; w: %s, conns: %s, tot w: %s)" % \
                   (self.proj_types[projName], self.proj_weights[projName], self.proj_conns[projName], self.proj_tot_weight[projName]))

    sizes_ils = {}
    pops_ils = {}
    weights_ils = {}
    input_comp_obj_ils = {}
    
    
    def handle_input_list(self, inputListId, population_id, component, size, input_comp_obj=None):
        if self.include_inputs:
            #self.print_input_information('INIT:  '+inputListId, population_id, component, size)
            self.sizes_ils[inputListId] = 0
            self.pops_ils[inputListId] = population_id
            self.input_comp_obj_ils[inputListId] = input_comp_obj
            self.weights_ils[inputListId] = 0
            

    def handle_single_input(self, inputListId, id, cellId, segId = 0, fract = 0.5, weight=1):
        if self.include_inputs:
            self.sizes_ils[inputListId]+=1
            self.weights_ils[inputListId]+=weight
        

    def finalise_input_source(self, inputListId):
        
        if self.include_inputs:
            #self.print_input_information('FINAL: '+inputListId, self.pops_ils[inputListId], '...', self.sizes_ils[inputListId])

            if self.level>=2:

                pass
                '''
                label = '<%s'%inputListId
                if self.level>=3:
                    size = self.sizes_ils[inputListId]
                    label += '<br/><i>%s input%s</i>'%( size, '' if size==1 else 's')

                if self.level>=4:

                    from neuroml import PulseGenerator
                    from neuroml import TransientPoissonFiringSynapse
                    from neuroml import PoissonFiringSynapse
                    from pyneuroml.pynml import convert_to_units

                    input_comp_obj = self.input_comp_obj_ils[inputListId]

                    if input_comp_obj and isinstance(input_comp_obj,PulseGenerator):
                        start = convert_to_units(input_comp_obj.delay, 'ms')
                        if start == int(start): start = int(start)
                        duration = convert_to_units(input_comp_obj.duration,'ms')
                        if duration == int(duration): duration = int(duration)
                        amplitude = convert_to_units(input_comp_obj.amplitude,'pA')
                        if amplitude == int(amplitude): amplitude = int(amplitude)

                        label += '<br/>Pulse %s-%sms@%spA'%(start,start+duration, amplitude)

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

                        label += '<br/>Syn: %s<br/>%s-%sms @ %sHz'%(input_comp_obj.synapse,start,start+duration, average_rate)

                label += '>'

                self.f.attr('node', color='#444444', style='', fontcolor = '#444444')
                self.f.node(inputListId, label=label)

                label = None
                if self.level>=5:
                    label='<'
                    if self.sizes_ils[inputListId]>0:
                        percent = 100*float(self.sizes_ils[inputListId])/self.pop_sizes[self.pops_ils[inputListId]]

                        if percent<=100:
                            label+='%s%s%% of population<br/> '%(' ' if percent!=100 else '', self.format_float(percent))
                        else:
                            label+='%s%s per cell<br/> '%(' ', self.format_float(percent/100))

                        avg_weight = float(self.weights_ils[inputListId])/self.sizes_ils[inputListId]
                        label+='avg weight: %s<br/> '%(self.format_float(avg_weight,approx=True))

                    if not label[-1]=='>':
                        label += '>'

                self.f.edge(inputListId, self.pops_ils[inputListId], arrowhead=self.INPUT_ARROW_SHAPE, label=label)
                
                '''
                
                