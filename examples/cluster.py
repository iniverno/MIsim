##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


import numpy as np
import unit 

class Cluster:
  def __init__(self, clusterID, nUnits, Ti, Tn, NBin_nEntries):
    self.VERBOSE = True
    self.clusterID = clusterID
    self.units = []
    self.nUnits = nUnits
    self.Tn = Tn
    self.Ti = Ti
    self.NBin_nEntries = NBin_nEntries
    self.busy = 0
    self.unitLastPosInWindow = np.zeros((nUnits, 2))  #it records the last position of the actual window that was sent to each unit (nWindow, pos)
    self.subWindowDataFlat = {}
    self.unitsProcWindow = {}
    self.filtersToUnits = {}
    self.unitToWindow = {}
    for i in range(nUnits):
      self.units.append(unit.Unit(True, clusterID, i, NBin_nEntries, Ti, Tn, (1<<20), self.processDataFromUnits))

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


  def initialize(self, size):
      #configure the size of SB at the unit
    for cntUnit in range(self.nUnits):      
      self.units[cntUnit].initialize(size / self.nUnits) 

  def initializeWindow(self, windowData, windowID):
    self.windowID = windowID
    self.unitsProcWindow = self.nUnits
    featsUnit = windowData.shape[0] / self.nUnits 

    for cntUnit in range(self.nUnits): 
      # divide the windowData and flat it
      self.subWindowDataFlat[cntUnit] = np.array(windowData[cntUnit*featsUnit : (cntUnit+1) * featsUnit])
      self.subWindowDataFlat[cntUnit] = np.swapaxes(self.subWindowDataFlat[cntUnit], 0, 2).flatten()


  def processWindow(self, windowData, windowID):
    if self.VERBOSE: print "Processing of window #%d in cluster #%d"%(windowID, self.clusterID) 

    # this will probably change when units are asynch
    nElements = self.Ti * self.NBin_nEntries

    # the cluster has to divide the window in as many subwindows as units are present in the cluster
    # each unit in the cluster has to process the subwindow
    # this processing can be synchronous or asynch
    # let's consider synch first
    while self.unitsProcWindow > 0: 
      for cntUnit in range(self.nUnits):
        if not self.units[cntUnit].busy:
          auxPos = self.unitLastPosInWindow[cntUnit][1]
          
          self.units[cntUnit].fill_NBin(self.subWindowDataFlat[cntUnit][auxPos : min(auxPos + nElements, self.subWindowDataFlat[cntUnit].size)])
          print 'SIZE: %d %d'%(auxPos + nElements, self.subWindowDataFlat[cntUnit].size) 

          self.units[cntUnit].compute()

          # increase pointer indicating last processed element
          self.unitLastPosInWindow[cntUnit][1] += nElements
            
          if self.unitLastPosInWindow[cntUnit][1] >= self.subWindowDataFlat[cntUnit].size:
              self.unitsProcWindow -= 1
          
  def processDataFromUnits(self, unitID):
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
