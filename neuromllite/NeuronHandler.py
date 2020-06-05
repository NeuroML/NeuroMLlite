from neuromllite.utils import print_v
from neuromllite.DefaultNetworkHandler import DefaultNetworkHandler

from neuron import hoc

################################################################################
# 
#    Not a full implementation of a native Neuron Handler yet!!
# 
#    This will probably not evolve into a full Neuron handler, it is useful 
#    though as a means of loading in and positioning cells for checking 3D
#    layout
#
################################################################################


class NeuronHandler(DefaultNetworkHandler):
    
    h = hoc.HocObject()
        
    globalPreSynId = 10000000
    
    preSectionsVsGids = dict()
    

    #
    #   Helper function for printing hoc before executing it
    #
    def executeHoc(self, command):

        cmdPrefix = "hoc >>>>>>>>>>: "

        if (len(command)>0):
            print_v(cmdPrefix+command)
            self.h(command)
        
    #
    #  Overridden from NetworkHandler
    #    
    def handlePopulation(self, population_id, component, size=-1, component_obj=None):
      
        if (size>=0):
            sizeInfo = ", size "+ str(size)+ " cells"
            
            print_v("Creating population: "+population_id+", component: "+component+sizeInfo)

            self.executeHoc("{ n_"+population_id+" = "+ str(size)+" }")
            self.executeHoc("{ n_"+population_id+"_local = 0 } ")
            self.executeHoc("objectvar a_"+population_id+"[n_"+population_id+"]")

        else:
                
            print_v("Population: "+population_id+", component: "+component+" specifies no size. Will lead to errors!")
        
  
    #
    #  Overridden from NetworkHandler
    #    
    def handleLocation(self, id, population_id, component, x, y, z):
        self.printLocationInformation(id, population_id, component, x, y, z)
                
        newCellName = population_id+"_"+str(id)
        
        createCall = "new "+component+"(\""+newCellName+"\", \"" +component+"\", \"New Cell: "+newCellName+" of type: "+component+"\")"
        
        cellInArray = "a_"+population_id+"["+str(id)+"]"
        
        setupCreate = "obfunc newCell() { {"+cellInArray+" = "+createCall+"} return "+cellInArray+" }"
        
        self.executeHoc(setupCreate)
        
        newCell = self.h.newCell()
        
        newCell.position(float(x), float(y), float(z))
        

        self.executeHoc("{n_"+population_id+"_local = n_"+population_id+"_local + 1}")
        
        print_v("Have just created cell: "+ component+" at ("+str(x)+", "+str(y)+", "+str(z)+")")
        

    #
    #  Should be overridden to create cell group/population array
    #
    def handleProjection(self, projName, prePop, postPop, synapse, hasWeights=False, hasDelays=False, type="projection", synapse_obj=None, pre_synapse_obj=None):

        print_v("Projection: "+projName+" from "+prePop+" to "+postPop)

        
    #
    #  Overridden from NetworkHandler
    #    
    def handleConnection(self, projName, id, prePop, postPop, synapseType, \
                                                    preCellId, \
                                                    postCellId, \
                                                    preSegId = 0, \
                                                    preFract = 0.5, \
                                                    postSegId = 0, \
                                                    postFract = 0.5, \
                                                    delay = 0, \
                                                    weight = 1):
        
        #self.printConnectionInformation(projName, id, prePop, postPop, synapseType, preCellId, postCellId, localWeight)
          

        print_v("\n           --------------------------------------------------------------")
        print_v("Going to create a connection of type " +projName+", id: "+str(id)+", synapse type: "+synapseType)
        print_v("From: "+prePop+", id: "+str(preCellId)+", segment: "+str(preSegId)+", fraction: "+str(preFract))
        print_v("To  : "+postPop+", id: "+str(postCellId)+", segment: "+str(postSegId)+", fraction: "+str(postFract))
        print_v("   **** Connectivity not yet implemented!!  **** ")
##        
##        threshold = 0
##        
##        postPopCell = "a_"+postPop+"["+str(postCellId)+"]"
##        prePopCell = "a_"+prePop+"["+str(preCellId)+"]"
##        
##            
##            
##        # Create post syn object    
##            
##        '''if self.h.isCellOnNode(str(postPop), int(postCellId)) == 1:'''
##        
##        print_v("++++++++++++ PostCell: "+postPopCell+" is on this host...")
##
##        synObjName = projName+"_"+synapseType+"["+str(id)+"]"
##
##        ##########self.executeHoc("objref "+synObjName) 
##        '''
#        self.executeHoc("{ "+postPopCell+".accessSectionForSegId("+str(postSegId)+") }")
#
#        self.executeHoc("{ "+"fractSecPost = "+postPopCell+".getFractAlongSection("+str(postFract)+", "+str(postSegId)+") }")
#
#        print_v("Synapse object at: "+str(h.fractSecPost) +" on sec: "+h.secname()+", or: "+str(postFract)+" on seg id: "+ str(postSegId))
#        #'''
##        self.executeHoc("{ "+synObjName+" = new "+synapseType+"(0) }")
##
##        self.executeHoc("{ "+postPopCell+".synlist.append("+synObjName+") }")
##
##        self.executeHoc("{ "+"localSynapseId = "+postPopCell+".synlist.count()-1 }")
##            
##            
##        
##        # Create pre syn object  
##
##
##        self.executeHoc("{ "+prePopCell+".accessSectionForSegId("+str(preSegId)+") }")
##        self.executeHoc("{ fractSecPre = "+prePopCell+".getFractAlongSection("+str(preFract)+", "+str(preSegId)+") }")
##
##        print_v("NetCon object at: "+str(h.fractSecPre) +" on sec: "+h.secname()+", or: "+str(preFract)+" on seg id: "+ str(preSegId))
##
##        self.executeHoc("{"+prePopCell+".synlist.append(new NetCon(&v(fractSecPre), " \
##                  +synObjName+", "+str(threshold)+", "+str(delay)+", "+str(weight)+")) }")
##        
##        '''
#        else:
#          
#            netConRef = "NetCon_"+str(self.globalPreSynId)
#            netConRefTemp = netConRef+"_temp"
#            
#            
#            preCellSegRef = str(prePopCell+"_"+str(preSegId))
#            
#            gidToUse = self.globalPreSynId
#            
#            if  preCellSegRef in self.preSectionsVsGids:
#                gidToUse = self.preSectionsVsGids[preCellSegRef]
#                print_v("Using *existing* NetCon with gid for pre syn: "+str(gidToUse)+"")
#            else:
#                print_v("Using new gid for pre syn: "+str(gidToUse)+"")
#                self.preSectionsVsGids[preCellSegRef] = self.globalPreSynId
#                
#                
#            if self.h.isCellOnNode(str(prePop), int(preCellId)) == 1: 
#                print_v("++++++++++++ PreCell: "+prePopCell+" is here!!")
#
#                self.executeHoc("objref "+netConRef)
#                if  gidToUse == self.globalPreSynId:  # First time use of gid so create NetCon
#                    
#                    self.executeHoc("{ "+prePopCell+".accessSectionForSegId("+str(preSegId)+")"+" }")
#                    
#                    self.executeHoc("{ "+"pnm.pc.set_gid2node("+str(gidToUse)+", hostid)"+" }")
#                    self.executeHoc("{ "+netConRef+" = new NetCon(&v("+str(preFract) +"), nil)"+" }")
#                    
#                    self.executeHoc("{ "+netConRef+".delay = "+str(delayTotal)+" }")
#                    self.executeHoc("{ "+netConRef+".weight = "+str(localWeight)+" }")
#                    self.executeHoc("{ "+netConRef+".threshold = "+str(localThreshold)+" }")
#                    
#                    self.executeHoc("{ "+"pnm.pc.cell("+str(gidToUse)+", "+netConRef+")"+" }")
#                    
#          
#                
#            else: 
#                print_v("------------ PreCell: "+prePopCell+" not on this host...")
#                
#            
#            # Connect pre to post  
#            
#            
#            if self.isParallel == 1 and self.h.isCellOnNode(str(postPop), int(postCellId)) == 1:
#                self.executeHoc("objref "+netConRefTemp)
#                self.executeHoc(netConRefTemp+" = pnm.pc.gid_connect("+str(gidToUse)+","+postPopCell+".synlist.object(localSynapseId))")
#           
#                self.executeHoc("{ "+netConRefTemp+".delay = "+str(delayTotal)+" }")
#                self.executeHoc("{ "+netConRefTemp+".weight = "+str(localWeight)+" }")
#                self.executeHoc("{ "+netConRefTemp+".threshold = "+str(localThreshold)+" }")
#                
#            
#            #self.executeHoc("netConInfoParallel("+netConRef+")")
#            #self.executeHoc("netConInfoParallel("+netConRefTemp+")")    #'''
##                
##        self.globalPreSynId+=1


        
        