##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


import numpy as np
import unit 
import sets

class Cluster:
  def __init__(self, system, clusterID, nUnits, Ti, Tn, NBin_nEntries, SB_sizeCluster, cbClusterDoneReading, cbClusterDone):
    # cluster things 
    self.system = system
    self.cbClusterDoneReading = cbClusterDoneReading
    self.VERBOSE = True
    self.clusterID = clusterID
    self.busy = False

    self.windowID = 0

    #The units
    self.SB_sizeCluster = SB_sizeCluster
    self.units = []
    self.nUnits = nUnits
    self.Tn = Tn
    self.Ti = Ti
    self.NBin_nEntries = NBin_nEntries
    self.unitLastPosInWindow = np.zeros((nUnits, 2))  #it records the last position of the actual window that was sent to each unit (nWindow, pos)
    self.subWindowDataFlat = {}
    self.unitsReadingWindow = {}
    self.filtersToUnits = {}
    self.unitToWindow = {}
    self.filterIDs = []
    self.unitFilterCnt = [0]*nUnits
    for i in range(nUnits):
      self.units.append(unit.Unit(system, True, clusterID, i, NBin_nEntries, Ti, Tn, SB_sizeCluster/nUnits, self.cbInputRead, self.cbDataAvailable))

##################################################################################
###
##################################################################################
 
  # this function receives the filter complete and it divides it among the units in the cluster
  def fill_SB(self, filterData, filterID):
    featsUnit = filterData[0].shape[0] / self.nUnits
    assert featsUnit *  self.nUnits == filterData[0].shape[0], "the number of units per cluster (%d) is not multiple of the number of features (%d)"%(self.nUnits, filterData[0].shape[0])
    
    #list of list containing the filters of the cluster
    self.filterIDs.append(filterID) 
    
    for cntUnit in range(self.nUnits): 
      filterSegmentFlat = []
      for auxFilterData in filterData:
      # the filter is firstly made flat
      # the axes are swapped to made it accross features first
        filterSegment = np.array(auxFilterData[cntUnit*featsUnit : (cntUnit+1)*featsUnit,:,:])
        filterSegmentFlat.append(np.swapaxes(filterSegment, 0, 2).flatten())
   
      self.units[cntUnit].fill_SB(filterSegmentFlat, filterID) 
      #np.delete(filterSegment)

##################################################################################
###
##################################################################################
 
  def initialize(self, size):
      #configure the size of SB at the unit
    for cntUnit in range(self.nUnits):      
      self.units[cntUnit].initialize(size / self.nUnits) 
##################################################################################
###
##################################################################################
 
  def initializeWindow(self, windowData, windowID):
    self.windowID = windowID
    featsUnit = windowData.shape[0] / self.nUnits 

    self.unitsReadingWindow[self.windowID] = sets.Set()
    for cntUnit in range(self.nUnits): 
      self.unitsReadingWindow[self.windowID].add(cntUnit)
      self.unitFilterCnt[cntUnit] = 0

      # divide the windowData and flat it
      self.subWindowDataFlat[cntUnit] = np.array(windowData[cntUnit*featsUnit : (cntUnit+1) * featsUnit])
      self.subWindowDataFlat[cntUnit] = np.swapaxes(self.subWindowDataFlat[cntUnit], 0, 2).flatten()


##################################################################################
###
##################################################################################
  def cycle(self):
    if 0 and self.VERBOSE: print "[%d] Processing of window #%d in cluster #%d"%(self.system.now, windowID, self.clusterID) 

    # this will probably change when units are asynch
    nElements = self.Ti * self.NBin_nEntries

    # the cluster has to divide the window in as many subwindows as units are present in the cluster
    # each unit in the cluster has to process the subwindow
    # this processing can be synchronous or asynch
    # let's consider synch first
    if len(self.unitsReadingWindow[self.windowID]) > 0: 
      for cntUnit in range(self.nUnits):
        if not self.units[cntUnit].busy:
          #this cluster is busy because there is some unit working
          self.busy = True

          # the cluster feeds the unit with new data
          auxPos = self.unitLastPosInWindow[cntUnit][1]
          rangeToProcess = range(int(auxPos), int(min(auxPos + nElements, self.subWindowDataFlat[cntUnit].size)))

          # is the last fragment of the window for that unit?
          final = False
          if rangeToProcess[-1] >= self.subWindowDataFlat[cntUnit].size-1:
            print "[",self.system.now, "] LastFragment of window being copied in (cluster ", self.clusterID, ") ", self.units[cntUnit].windowPointer, " ", len(rangeToProcess), " ", self.subWindowDataFlat[cntUnit].size
            final = True

          self.units[cntUnit].fill_NBin(self.subWindowDataFlat[cntUnit][rangeToProcess], final)
          self.system.schedule(self.units[cntUnit])

          #functional
          #self.units[cntUnit].compute()

          # increase pointer indicating last processed element
          self.unitLastPosInWindow[cntUnit][1] += nElements

            
##################################################################################
###
##################################################################################
    
  def cbDataAvailable(self, unitID, entry):
    #this function is only called when the unit has processed the last entry corresponding 
    #corresponding to each group of filters
    #e.g., the NBout entry contains the final values for the corresponding filters
 
    # which are the filters corresponding to the data sent by the unit?
    auxFilterIDs = self.filterIDs[self.unitFilterCnt[unitID]]
    # group of filters that the unit will produce the result for next
    self.unitFilterCnt[unitID] += 1

    #TODO: here we should add the results of multiple subwindows if nUnits > 1
    # processSubwindows()
    # if all the units finished its part then ... todo
     
    print "[",self.system.now, "] (cluster ", self.clusterID, ") copying the output for filters ",  auxFilterIDs
    self.system.putData(self.windowID, entry[:len(auxFilterIDs)], auxFilterIDs)
   
    #self.unitsProcWindow[self.windowID] -= 1
    #if self.unitsProcWindow[self.windowID] == 0:
    #  self.cbClusterDone(self.clusterID, self.windowID)
 
            
##################################################################################
###
##################################################################################
    
  def cbInputRead(self, unitID):
    #check if the unit has finished processing the window
    if self.units[unitID].windowPointer >= self.subWindowDataFlat[unitID].size:
      self.unitsReadingWindow[self.windowID].remove(unitID)
      if len(self.unitsReadingWindow[self.windowID]) == 0:
        self.cbClusterDoneReading(self.clusterID, self.windowID)
    else:  
    # the unit did not finish the window so next cycle we will fill its NBin
    # if we wanted to allow processing more than one window in a cluster, this synch point should 
    # be moved to the cycle function
      self.system.schedule(self)
            
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
