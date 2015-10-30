##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


import numpy as np
import unit 

class Cluster:
  def __init__(self, system, clusterID, nUnits, Ti, Tn, NBin_nEntries, SB_sizeCluster, cbClusterDone):
    # cluster things 
    self.system = system
    self.cbClusterDone = cbClusterDone
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
    self.unitsProcWindow = {}
    self.filtersToUnits = {}
    self.unitToWindow = {}
    for i in range(nUnits):
      self.units.append(unit.Unit(system, True, clusterID, i, NBin_nEntries, Ti, Tn, SB_sizeCluster/nUnits, self.cbInputRead, self.cbDataAvailable))

##################################################################################
###
##################################################################################
 
  # this function receives the filter complete and it divides it among the units in the cluster
  def fill_SB(self, filterData, filterID):
    featsUnit = filterData.shape[0] / self.nUnits
    assert featsUnit *  self.nUnits == filterData.shape[0], "the number of units per cluster (%d) is not multiple of the number of features (%d)"%(self.nUnits, filterData.shape[0])

    for cntUnit in range(self.nUnits):
      # the filter is firstly made flat
      # the axes are swapped to made it accross features first 

      filterSegment = np.array(filterData[cntUnit*featsUnit : (cntUnit+1)*featsUnit,:,:])
      filterSegmentFlat = np.swapaxes(filterSegment, 0, 2).flatten()
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
    self.unitsProcWindow[self.windowID] = self.nUnits
    featsUnit = windowData.shape[0] / self.nUnits 

    for cntUnit in range(self.nUnits): 
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
    if self.unitsProcWindow[self.windowID] > 0: 
      for cntUnit in range(self.nUnits):
        if not self.units[cntUnit].busy:
          #this cluster is busy because there is some unit working
          self.busy = True

          auxPos = self.unitLastPosInWindow[cntUnit][1]
           
          self.units[cntUnit].fill_NBin(self.subWindowDataFlat[cntUnit][auxPos : min(auxPos + nElements, self.subWindowDataFlat[cntUnit].size)])

          self.system.schedule(self.units[cntUnit])

          #functional
          #self.units[cntUnit].compute()

          # increase pointer indicating last processed element
          self.unitLastPosInWindow[cntUnit][1] += nElements

            
##################################################################################
###
##################################################################################
    
  def cbDataAvailable(self, unitID, entry):
    #print "cbInputRead"

            
##################################################################################
###
##################################################################################
    
  def cbInputRead(self, unitID):
    #check if the unit has finished processing the window
    if self.units[unitID].windowPointer >= self.subWindowDataFlat[unitID].size:
      self.unitsProcWindow[self.windowID] -= 1
      if self.unitsProcWindow[self.windowID] == 0:
        self.cbClusterDone(self.clusterID, self.windowID)
    else:  
    # the unit did not finish the window so next cycle we will fill its NBin
    # if we wanted to allow processing more than one window in a cluster, this synch point should 
    # be moved to the cycle function
      self.system.schedule(self)
            
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
