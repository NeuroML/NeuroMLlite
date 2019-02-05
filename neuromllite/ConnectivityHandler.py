#
#
#   Helper class for parsing connectivity data
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from graphviz import Digraph

from neuromllite.utils import evaluate
            
from pyneuroml.pynml import convert_to_units

engines = {'d':'dot',
           'c':'circo',
           'n':'neato',
           't':'twopi',
           'f':'fdp',
           's':'sfdp',
           'p':'patchwork'}

class ConnectivityHandler(DefaultNetworkHandler):
        
    CUTOFF_INH_SYN_MV = -50 # erev below -50mV => inhibitory, above => excitatory
    
    include_inputs = False
    
    positions = {}
    
    pop_sizes = {}
    pop_colors = {}
    pop_types = {}
    
    proj_weights = {}
    proj_shapes = {}
    proj_lines = {}
    proj_pre_pops = {}
    proj_post_pops = {}
    proj_types = {}
    proj_conns = {}
    proj_tot_weight = {}
    proj_syn_objs = {}
    
    

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
        
    def get_size_pre_pop(self, projName):
        return self.pop_sizes[self.proj_pre_pops[projName]]
    
    
    def get_size_post_pop(self, projName):
        return self.pop_sizes[self.proj_post_pops[projName]]
        
        
    def _get_gbase_nS(self, projName, return_orig_string_also=False):
    
        gbase_nS = None
        gbase = '???'
        #print('Getting gbase for %s'%projName)
        if projName in self.proj_syn_objs:
            syn = self.proj_syn_objs[projName]
            if hasattr(syn,'gbase'):
                gbase = syn.gbase
                gbase_nS = convert_to_units(gbase, 'nS')
            elif hasattr(syn,'conductance'):
                gbase = syn.conductance
                gbase_nS = convert_to_units(gbase, 'nS')
                
        if return_orig_string_also:
            return gbase_nS, gbase
        
        return gbase_nS
        
        
    def _scale_weight(self, weight, projName):

        orig_weight = weight
        if self.scale_by_post_pop_size:
            weight /= self.get_size_post_pop(projName)

        if self.scale_by_post_pop_cond:
            gbase_nS = self._get_gbase_nS(projName)
            if gbase_nS:
                weight *= gbase_nS
        
        if not orig_weight==weight:
            #print(' - Weight for %s modified %s->%s'%(projName, orig_weight, weight))
            pass
            
        return weight
            
        
        
 
    def handle_location(self, id, population_id, component, x, y, z):
        
        pass
        



  
    def finalise_projection(self, projName, prePop, postPop, synapse=None, type="projection"):
   
        #weight = self.proj_tot_weight[projName]
        #self.max_weight = max(self.max_weight, weight)
        #self.min_weight = min(self.min_weight, weight)
        #print_v("Now weights range %s->%s"%(self.min_weight, self.max_weight))
        pass
        #print_v("Projection finalising: "+projName+" from "+prePop+" to "+postPop+" completed")
    
    
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
        

