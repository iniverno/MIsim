import numpy as np
import unit

class layerDirector:

    verboseUnits = True

  def __init__(self, nUnits, Ti, Tn, NBin_nEntries):
    self.units = []
    self.nUnits = nUnits
    self.Tn = Tn
    self.Ti = Ti
    self.Nbin_nEntries = NBin_nEntries
    self.unitLastPosInWindow = np.zeros((nUnits, 2))  #it records the last position of the actual window that was sent to each unit (nWindow, pos)
    self.windowsDataFlat = {}
    self.unitsProcWindow = {}
    self.filtersToUnits = {}
    for i in range(nUnits):
      units.append(Unit(i, verboseUnits, i, NBin_nEntries, Ti, Tn, (1<<20)), processDataFromUnits)

##################################################################################
###
### windowID: 
###  
###
##################################################################################
  # this function copy the filter weights into the unit eDRAM
  def initializeLayer(self, weights):
    nUnits = len(units)
    nTotalFilters = weights.shape[0]
    #how many filters have to go to each unit
    nFiltersPerUnit = nTotalFilters / nUnits
    print "%d filters per unit" % (nFiltersPerUnit)
    # if the total number of filters is not a multiple of nUnits
    nAdditionalFilters = nTotalFilters - (nFiltersPerUnit * nUnits)
    print "plus %d additional filters"%(nAdditionalFilters)
    
    for idxFilter in range(nTotalFilters):
      # the filter is firstly made flat
      # the axes are swapped to made it accross features first 
      filterFlat = weights[idxFilter]
      filterFlat = np.swapaxes(filterFlat, 0, 2).flatten()

      self.units[idxFilter % nUnits].fill_SB((filterFlat), (idxFilter))

##################################################################################
###
### windowID: 
###  
###
##################################################################################
  def computeConvolutional(self, inputData, filterWeights):
    # initialize the layer
    self.initializeLayer(filterWeights)

    # generate windows
    auxWindow = np.zeros((256, 3, 3))
    # process each window
    self.initializeWindow(auxWindow, 17)
    self.processWindow(17)

##################################################################################
###
##################################################################################
  def initializeWindow(self, windowData, windowID):
    if self.VERBOSE: print "Initializing window #%d"%(windowID)

    self.windowsDataFlat[windowID] = np.swapaxes(windowData, 0, 2).flatten()
    self.unitsProcWindow[windowID] = self.nUnits

##################################################################################
###
##################################################################################

  def processWindow(self, windowID):
    if self.VERBOSE: print "Processing of window #%d"%(windowID)

    # the window has to be processed by each unit
    # divide the window in chunks as big as NBin
    nElements = self.Ti * self.NBin_nEntries
    
    while self.unitsProcWindow[windowID] > 0:
      for cntUnit in range(self.nUnits):
        if not units[cntUnit].busy:
          auxPos = self.unitLastPosInWindow[cntUnit][1] #pos 0 is the window id but only one window will be considered for the time being
          self.units.[cntUnit].fill_NBin(self.windowsDataFlat[windowID][auxPos : max(auxPos + nElements, windowData.size) ])
          self.unitToWindow[cntUnit] = windowID
          self.units.[cntUnit].compute()
          self.unitLastPosInWindow[cntUnit][1] += nElements

    if self.VERBOSE: print "It seems window #%d has been processed"%(windowID)
 
    # TODO: in the baseline, all the units have to process every window
    # the solution to deal with the new system and how it slices computation,
    # will be to add clusterDirector that will take care of slicing the computation 
    # among the narrow units conforming a cluster  

  def processDataFromUnits(self, unitID):
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
    self.unitsProcWindow[self.unitToWindow[unitID]] -= 1
     
