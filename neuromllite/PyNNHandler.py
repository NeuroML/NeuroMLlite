#
#
#   A class to handle events by PyNN...
#
#

from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from importlib import import_module


class PyNNHandler(DefaultNetworkHandler):
        
    populations = {}
    projections = {}
    input_sources = {}
    input_info = {}
    
    def __init__(self, simulator, dt, reference):
        print_v("Initiating PyNN with simulator %s"%simulator)
        self.sim = import_module("pyNN.%s" % simulator)
        self.dt = dt
        self.sim.setup(timestep=self.dt, 
                       debug=True,
                       reference=reference,
                       save_format='xml')

    def set_cells(self, cells):
        self.cells = cells
        
    def set_receptor_types(self, receptor_types):
        self.receptor_types = receptor_types
        
    def add_input_source(self, input_source):
        input_params = input_source.parameters if input_source.parameters else {}
        exec('self.input_sources["%s"] = self.sim.%s(**input_params)'%(input_source.id,input_source.pynn_input))

    def handle_document_start(self, id, notes):
            
        print_v("Document: %s"%id)
        

    def handle_network(self, network_id, notes, temperature=None):
            
        print_v("Network: %s"%network_id)
        if temperature:
            print_v("  Temperature: "+temperature)
        if notes:
            print_v("  Notes: "+notes)


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
        
        exec('self.POP_%s = self.sim.Population(%s, self.cells["%s"], label="%s")'%(population_id,size,component,population_id))
        #exec('print_v(self.POP_%s)'%(population_id))
        exec('self.populations["%s"] = self.POP_%s'%(population_id,population_id))


    #
    #  Should be overridden to create specific cell instance
    #    
    def handle_location(self, id, population_id, component, x, y, z):
        #self.printLocationInformation(id, population_id, component, x, y, z)
        
        exec('self.POP_%s.positions[0][%s] = %s'%(population_id,id,x))
        exec('self.POP_%s.positions[1][%s] = %s'%(population_id,id,y))
        exec('self.POP_%s.positions[2][%s] = %s'%(population_id,id,z))


    def handle_projection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):

        synInfo=""
        if synapse_obj:
            synInfo += " (syn: %s)"%synapse_obj.__class__.__name__
            
        if pre_synapse_obj:
            synInfo += " (pre comp: %s)"%pre_synapse_obj.__class__.__name__

        print_v("Projection: "+projName+" ("+type+") from "+prePop+" to "+postPop+" with syn: "+synapse+synInfo)
        
        exec('self.projection__%s_conns = []'%(projName))


    #
    #  Should be overridden to handle network connection
    #  
    def handle_connection(self, projName, id, prePop, postPop, synapseType, \
                                                    preCellId, \
                                                    postCellId, \
                                                    preSegId = 0, \
                                                    preFract = 0.5, \
                                                    postSegId = 0, \
                                                    postFract = 0.5, \
                                                    delay = 0, \
                                                    weight = 1):
        
        self.print_connection_information(projName, id, prePop, postPop, synapseType, preCellId, postCellId, weight)
        print_v("Src cell: %d, seg: %f, fract: %f -> Tgt cell %d, seg: %f, fract: %f; weight %s, delay: %s ms" % (preCellId,preSegId,preFract,postCellId,postSegId,postFract, weight, delay))
         
        import random
        exec('self.projection__%s_conns.append((%s,%s,float(%s),float(%s)))'%(projName,preCellId,postCellId,weight,delay))

        
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
        
        
