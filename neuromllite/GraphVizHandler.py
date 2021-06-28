#
#
#   A class to write to the GraphViz format...
#
#

from neuromllite.utils import print_v
from neuromllite.utils import is_spiking_input_nml_cell
from neuromllite.ConnectivityHandler import ConnectivityHandler
from neuromllite.NetworkGenerator import _get_rng_for_network
from neuromllite.utils import evaluate
            
from pyneuroml.pynml import convert_to_units

from graphviz import Digraph
import numpy as np

engines = {'d':'dot',
           'c':'circo',
           'n':'neato',
           't':'twopi',
           'f':'fdp',
           's':'sfdp',
           'p':'patchwork'}

class GraphVizHandler(ConnectivityHandler):
        
    
    DEFAULT_POP_SHAPE = 'ellipse'
    EXC_POP_SHAPE = 'ellipse'
    INH_POP_SHAPE = 'ellipse'
    
    EXC_CONN_ARROW_SHAPE = 'normal'
    INH_CONN_ARROW_SHAPE = 'dot'
    GAP_CONN_ARROW_SHAPE = 'tee'
    CONT_CONN_ARROW_SHAPE = 'normal'
    INPUT_ARROW_SHAPE = 'empty'
    
    
    def __init__(self, 
                 level=10, 
                 engine='dot', 
                 nl_network=None,
                 include_ext_inputs=True,
                 include_input_pops=True,
                 scale_by_post_pop_size = True,
                 scale_by_post_pop_cond = True,
                 show_chem_conns = True,
                 show_elect_conns = True,
                 show_cont_conns = True,
                 min_weight_to_show=0,
                 output_format='png',
                 view_on_render=True):
                     
        self.nl_network = nl_network
        self.level = level
        self.engine = engine
        self.include_ext_inputs = include_ext_inputs
        self.include_input_pops = include_input_pops
        self.scale_by_post_pop_size = scale_by_post_pop_size
        self.scale_by_post_pop_cond = scale_by_post_pop_cond
        self.min_weight_to_show = min_weight_to_show
        self.show_chem_conns = show_chem_conns
        self.show_elect_conns = show_elect_conns
        self.show_cont_conns = show_cont_conns
        self.output_format = output_format
        self.view_on_render = view_on_render
        
        self.rng, seed = _get_rng_for_network(self.nl_network)
        
        print_v("Initiating GraphViz handler, level %i, engine: %s, seed: %s"%(level, engine, seed))
        
        
    def print_settings(self):
        print_v('**************************************')
        print_v('* Settings for GraphVizHandler: ')
        print_v('*')
        print_v('*    engine:                  %s'%self.engine)
        print_v('*    level:                   %s'%self.level)
        print_v('*    is_cell_level:           %s'%self.is_cell_level())
        print_v('*    CUTOFF_INH_SYN_MV:       %s'%self.CUTOFF_INH_SYN_MV)
        print_v('*    include_ext_inputs:      %s'%self.include_ext_inputs)
        print_v('*    include_input_pops:      %s'%self.include_input_pops)
        print_v('*    scale_by_post_pop_size:  %s'%self.scale_by_post_pop_size)
        print_v('*    scale_by_post_pop_cond:  %s'%self.scale_by_post_pop_cond)
        print_v('*    min_weight_to_show:      %s'%self.min_weight_to_show)
        print_v('*    show_chem_conns:         %s'%self.show_chem_conns)
        print_v('*    show_elect_conns:        %s'%self.show_elect_conns)
        print_v('*    show_cont_conns:         %s'%self.show_cont_conns)
        print_v('*    output_format:           %s'%self.output_format)
        print_v('*')
        print_v('* Used values: ')
        syns = sorted(self.syn_conds_used.keys())                             
        print_v('*    syn_conds_used:          %s'%'\n*                             '.join(['%s:\t %s'%(k,self.syn_conds_used[k]) for k in syns]))
        print_v('*')
        print_v('**************************************')
    
    
    def get_weight_fraction_and_line(self, w, max_w, min_w):
        
        if max_w==min_w:
            return 1.0, 1.0
        # fractional weight, 0->1
        fweight = (abs(w)-min_w)/(max_w-min_w)
        if fweight<0:
            fweight=0
        if fweight>1:
            fweight=1
            
        # Good weight for line based on fraction
        lweight = .7 + fweight*3.5
        
        return fweight, lweight
    
            
    def finalise_document(self):
        
        max_abs_weight = {}
        min_abs_weight = {}
        
        for t in ['projection','inhibitory','excitatory','electricalProjection','continuousProjection']:
            max_abs_weight[t] = -1e100
            min_abs_weight[t] = 1e100
        
        if self.is_cell_level() and self.level <= -1:
            
            for projName in self.proj_weights:
                #ws = self.proj_individual_weights[projName]
                ws = self.proj_individual_scaled_weights[projName]
                t = self.proj_types[projName]
                if np.max(ws)>0:
                    max_abs_weight[t] = max(max_abs_weight[t], np.max(ws[np.nonzero(ws)]))
                    min_abs_weight[t] = min(min_abs_weight[t], np.min(ws[np.nonzero(ws)]))
                    
                
            for projName in self.proj_weights:

                pre_pop = self.proj_pre_pops[projName] 
                post_pop = self.proj_post_pops[projName]
                proj_type = self.proj_types[projName]
                num_pre = self.get_size_pre_pop(projName)
                num_post = self.get_size_post_pop(projName)
                
                if self.proj_types[projName] == 'electricalProjection':
                    show = self.show_elect_conns
                elif self.proj_types[projName] == 'continuousProjection':
                    show = self.show_cont_conns
                else:
                    show = self.show_chem_conns
                    
                if show:
                    gbase_nS, gbase = self._get_gbase_nS(projName,return_orig_string_also=True)

                    pclass = self._get_proj_class(proj_type)
                    sign = -1 if 'inhibitory' in proj_type else 1

                    print_v("GRAPH PROJ: %s (%s (%i) -> %s (%i), %s): w %s; wtot: %s; sign: %s; cond: %s nS (%s); all: %s -> %s"%(projName, pre_pop, num_pre, post_pop, num_post, proj_type, self.proj_weights[projName], self.proj_tot_weight[projName], sign, gbase_nS, gbase, max_abs_weight,min_abs_weight))

                    for pre_i in range(num_pre):
                        for post_i in range(num_post):
                            pre_pop_i = self.get_cell_identifier(pre_pop,  pre_i)
                            post_pop_i = self.get_cell_identifier(post_pop, post_i)

                            w = self.proj_individual_scaled_weights[projName][pre_i][post_i]
                            w_unscaled = self.proj_individual_weights[projName][pre_i][post_i]
                            
                            num_indiv_conns = self.proj_individual_conn_numbers[projName][pre_i][post_i]

                            if w != 0:

                                weight_used = w
                                
                                cond_scale = None
                                if self.scale_by_post_pop_cond:
                                    cond_scale = gbase_nS if gbase_nS!=None else 1.0
                                    
                                print_v(' - conn %s -> %s: %s (%s)'%(pre_pop_i, post_pop_i, w, weight_used))

                                fweight, lweight = self.get_weight_fraction_and_line(weight_used, 
                                                                                     max_abs_weight[proj_type], 
                                                                                     min_abs_weight[proj_type])

                                self.graph.attr('edge', 
                                            style = self.proj_lines[projName], 
                                            arrowhead = self.proj_shapes[projName], 
                                            arrowsize = '%s'%(min(1,lweight)), 
                                            penwidth = '%s'%(lweight), 
                                            color=self.pop_colors[self.proj_pre_pops[projName]],
                                            fontcolor = self.pop_colors[self.proj_pre_pops[projName]])

                                label='<'
                                label += 'w: %s <br/> '%self.format_float(w_unscaled)
                                label += 'num: %i <br/> '%num_indiv_conns
                                
                                if num_indiv_conns!=1:
                                    wc = float(w_unscaled)/num_indiv_conns
                                    label += 'w/conn: %s <br/> '%self.format_float(wc)
                                    if w!=w_unscaled:
                                        label +='%s*%s*%snS = %snS<br/> '%(self.format_float(wc), num_indiv_conns, self.format_float(cond_scale), self.format_float(weight_used))
                                else:
                                    label +='%s*%snS = %snS<br/> '%(self.format_float(w), self.format_float(cond_scale), self.format_float(weight_used))
                                        
                                    
                                label +='scaled: %s<br/> '%(self.format_float(weight_used))
                                
                                label += 'f: %s <br/> '%fweight
                                label += 'l: %s <br/> '%lweight

                                delay = self.proj_delays[projName][pre_i][post_i]
                                if delay!=0:
                                    label += 'd: %sms <br/> '%self.format_float(delay)
                                    
                                if not label[-1]=='>':
                                    label += '>'
                                if self.level<=-2:
                                    self.graph.edge(pre_pop_i, post_pop_i, label=label)
                                else:
                                    self.graph.edge(pre_pop_i, post_pop_i)
                                
        else:

            for projName in self.proj_tot_weight:
                t = self.proj_types[projName]

                if self.proj_tot_weight[projName]!=0:

                    weight_used = float(self.proj_tot_weight[projName])
                    weight_used = self._scale_population_weight(weight_used, projName)

                    if abs(weight_used)>=self.min_weight_to_show:

                        max_abs_weight[t] = max(max_abs_weight[t], abs(weight_used))
                        min_abs_weight[t] = min(min_abs_weight[t], abs(weight_used))
                        print_v("EDGE: %s (%s): weight %s (all so far: %s -> %s)"%(projName, t, weight_used, max_abs_weight[t],min_abs_weight[t]))

                    else:
                        print_v("IGNORING EDGE: %s: weight %s, less than %s (all used so far: %s -> %s)"%(projName, weight_used, self.min_weight_to_show, max_abs_weight[t],min_abs_weight[t]))


            for projName in self.proj_tot_weight:
                
                proj_type = self.proj_types[projName]

                if self.proj_tot_weight[projName]!=0:

                    #weight_used = self.proj_weights[projName]
                    weight_used = float(self.proj_tot_weight[projName])
                    weight_used = self._scale_population_weight(weight_used, projName)

                    if abs(weight_used)>=self.min_weight_to_show:

                        if max_abs_weight[proj_type]==min_abs_weight[proj_type]:
                            fweight = 1
                            lweight = 1
                        elif self.proj_types[projName] == 'electricalProjection':
                            # Dotted lines look bad when thick...
                            fweight = 1
                            lweight = 1
                        else:
                            fweight, lweight = self.get_weight_fraction_and_line(weight_used, max_abs_weight[proj_type], min_abs_weight[proj_type])
                                                    
                        if self.proj_types[projName] == 'electricalProjection':
                            show = self.show_elect_conns
                        elif self.proj_types[projName] == 'continuousProjection':
                            show = self.show_cont_conns
                        else:
                            show = self.show_chem_conns
                            
                        pre_pop = self.proj_pre_pops[projName]
                        if pre_pop in self.pop_nml_component_objs:
                            if not self.include_input_pops and is_spiking_input_nml_cell(self.pop_nml_component_objs[pre_pop]):
                                show=False

                        if self.level>=2 and show:
                            print_v("EDGE: %s (%s): weight %s (all: %s -> %s); fw: %s; lw: %s"%(projName, proj_type, weight_used, max_abs_weight[proj_type],min_abs_weight[proj_type],fweight,lweight))

                            self.graph.attr('edge', 
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

                                        gbase_nS, gbase = self._get_gbase_nS(projName,return_orig_string_also=True)

                                        if gbase_nS!=None:
                                            label+='%s*%s*%s = %s nS<br/> '%(self.format_float(post_avg), self.format_float(avg_weight), gbase, self.format_float(post_avg*avg_weight*gbase_nS))

                                if self.level>=6:
                                    label+='scaled weight: %s<br/> '%(self.format_float(weight_used))
                                    label+='fract: %s<br/> '%(self.format_float(fweight))
                                    label+='line: %s<br/> '%(lweight)

                                if not label[-1]=='>':
                                    label += '>'

                                self.graph.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName], label=label)
                            else:
                                self.graph.edge(self.proj_pre_pops[projName], self.proj_post_pops[projName])

        print_v("Generating graph for: %s"%self.network_id)
        self.print_settings()
        
        if self.view_on_render:
            self.graph.view()
        else:
            self.graph.render()
            
        if self.nl_network:
            print_v("Finished generating graph with params: %s"%[p for p in self.nl_network.parameters] if self.nl_network.parameters is not None else '[]')

        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
        self.network_id = network_id
            
        self.graph = Digraph(network_id, filename='%s.gv'%network_id, engine=self.engine, format=self.output_format)
        

    def handle_population(self, population_id, component, size=-1, component_obj=None, properties={}, notes=None):
        sizeInfo = " as yet unspecified size"
        
        if size>=0:
            sizeInfo = ", size: "+ str(size)+ " cells"
            
        if component_obj:
            compInfo = " (%s)"%component_obj.__class__.__name__
        else:
            compInfo=""
            
        self.pop_nml_component_objs[population_id] = component_obj
        
        if not self.include_input_pops and is_spiking_input_nml_cell(component_obj):
            print("Ignoring %s as it's a spiking input population")
            return
        
        self.pop_sizes[population_id] = size
            
        print_v("Population: "+population_id+", component: "+component+compInfo+sizeInfo+", properties: %s"%properties)
        color = '#444444' 
        fcolor= '#ffffff'
        shape = self.DEFAULT_POP_SHAPE
        
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
                
            #print('Color %s -> %s -> %s'%(properties['color'], rgb, color))
        
        if properties and 'type' in properties:
            self.pop_types[population_id] = properties['type']
            if properties['type']=='E':
                shape = self.EXC_POP_SHAPE
            if properties['type']=='I':
                shape = self.INH_POP_SHAPE
            
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
                    
                label += '<br/>Spikes %s-%sms@%sHz'%(start,start+duration, rate)
                
            else:
                label += '<br/>%s'%(component)
            
        label += '>'
            
        if properties and 'region' in properties:
            
            with self.graph.subgraph(name='cluster_%s'%properties['region']) as c:
                c.attr(color='#444444', fontcolor = '#444444')
                c.attr(label=properties['region'])
                c.attr('node', color=color, style='filled', fontcolor = fcolor, shape=shape)
                
                if self.is_cell_level():
                    for i in range(size):
                        cell_info = self.get_cell_identifier(population_id, i)
                        c.node(cell_info, label=cell_info)
                else:
                    c.node(population_id, label=label)
    
        else:
            self.graph.attr('node', color=color, style='filled', fontcolor = fcolor, shape=shape)
            
            if self.is_cell_level():
                for i in range(size):
                    cell_info = self.get_cell_identifier(population_id, i)
                    self.graph.node(cell_info, label=cell_info)
            else:
                self.graph.node(population_id, label=label)
        

    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):

        shape = self.EXC_CONN_ARROW_SHAPE
        line = 'solid'
            
        # Could be used in a network with no explicit connections, but weight 
        # between populations set at high level projection element in NeuroMLlite
        projection_weight = 1.0
        
        if not (prePop in self.pop_sizes and postPop in self.pop_sizes):
            print_v('Ignoring projection, as one of pops empty...')
            return
        
        self.proj_pre_pops[projName] = prePop
        self.proj_post_pops[projName] = postPop
        self.proj_types[projName] = type
        
        if prePop in self.pop_types:
            if 'I' in self.pop_types[prePop]:
                shape = self.INH_CONN_ARROW_SHAPE
                
        if type=='electricalProjection':
                shape = self.GAP_CONN_ARROW_SHAPE
                line = 'dashed'
                
        if type=='continuousProjection':
                shape = self.CONT_CONN_ARROW_SHAPE
                line = 'solid'
            
        if synapse_obj:
            self.proj_syn_objs[projName] = synapse_obj
            erev = self.get_reversal_potential_mV(synapse_obj)
            if erev!=None and erev < self.CUTOFF_INH_SYN_MV:
                shape = self.INH_CONN_ARROW_SHAPE
                
        if self.nl_network:
            syn = self.nl_network.get_child(synapse,'synapses')
            if syn:
                if syn.parameters:
                    if 'e_rev' in syn.parameters and syn.parameters['e_rev']<self.CUTOFF_INH_SYN_MV:
                        shape = self.INH_CONN_ARROW_SHAPE
            
            proj = self.nl_network.get_child(projName,'projections')  
            if proj:
                if proj.weight:
                    proj_weight = evaluate(proj.weight, self.nl_network.parameters, self.rng)
                    if proj_weight<0:
                        shape = self.INH_CONN_ARROW_SHAPE
                    projection_weight = abs(proj_weight)
                        
        
        self.proj_weights[projName] = projection_weight
        self.proj_shapes[projName] = shape
        self.proj_lines[projName] = line
        self.proj_conns[projName] = 0
        self.proj_tot_weight[projName] = 0
        
        if self.is_cell_level():
            pre_size = self.pop_sizes[prePop]
            post_size = self.pop_sizes[postPop]
            self.proj_individual_weights[projName] = np.zeros((pre_size, post_size))
            self.proj_individual_conn_numbers[projName] = np.zeros((pre_size, post_size))
            self.proj_individual_scaled_weights[projName] = np.zeros((pre_size, post_size))
            self.proj_delays[projName] = np.zeros((pre_size, post_size))


    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        #weight = self.proj_tot_weight[projName]
        #self.max_weight = max(self.max_weight, weight)
        #self.min_weight = min(self.min_weight, weight)
        #print_v("Now weights range %s->%s"%(self.min_weight, self.max_weight))
        pass
        #print_v("Projection finalising: "+projName+" from "+prePop+" to "+postPop+" completed")
    

    def finalise_input_source(self, inputListId):
        
        if self.include_ext_inputs:
            #self.print_input_information('FINAL: '+inputListId, self.pops_ils[inputListId], '...', self.sizes_ils[inputListId])

            if self.level>=2:

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

                self.graph.attr('node', color='#444444', style='', fontcolor = '#444444')
                self.graph.node(inputListId, label=label)

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

                self.graph.edge(inputListId, self.pops_ils[inputListId], arrowhead=self.INPUT_ARROW_SHAPE, label=label)
