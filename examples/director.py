import numpy as np
import unit

class LayerDirector:

  verboseUnits = True

  def __init__(self, nClusters, nTotalUnits, Ti, Tn, NBin_nEntries):
    self.VERBOSE = True
    self.clusters = []
    self.nClusters = nClusters
    self.nUnitsCluster = nTotalUnits / nClusters
    self.Tn = Tn
    self.Ti = Ti
    self.NBin_nEntries = NBin_nEntries
    self.windowsDataFlat = {}
    self.filtersToUnits = {}
    self.unitToWindow = {}
    for i in range(nClusters):
      self.units.append(cluster.Cluster(self.nUnitsCluster, Ti, Tn, NBin_nEntries)

##################################################################################
###
### windowID: 
###  
###
##################################################################################
  # this function copy the filter weights into the unit eDRAM
  def initializeLayer(self, weights):
    nTotalFilters = weights.shape[0]
    #how many filters have to go to each cluster
    nFiltersPerCluster = nTotalFilters / self.nClusters
    print "%d filters per cluster" % (nFiltersPerCluster)
    # if the total number of filters is not a multiple of nClusters
    nAdditionalFilters = nTotalFilters - (nFiltersPerCluster * self.nClusters)
    print "plus %d additional filters"%(nAdditionalFilters)
   
    # send the units the size of the filters so they can configure SB properly (simulation) 
    for i in range(self.nClusters): 
      self.clusters[i].initialize(weights[0].size)

    for idxFilter in range(nTotalFilters):
      self.clusters[(idxFilter / self.nClusters) % self.nClusters].fill_SB(weights[idxFilter], idxFilter)

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
    auxWindow = np.zeros((192, 3, 3))
    # process each window
    self.initializeWindow(auxWindow, 17)
    self.processWindow(17)

##################################################################################
###
##################################################################################
  def initializeWindow(self, windowData, windowID):
    if self.VERBOSE: print "Initializing window #%d"%(windowID)

    #self.windowsDataFlat[windowID] = np.swapaxes(windowData, 0, 2).flatten()
    self.clustersProcWindow[windowID] = self.nClusters

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
        if not self.units[cntUnit].busy:
          auxPos = self.unitLastPosInWindow[cntUnit][1] #pos 0 is the window id but only one window will be considered for the time being
	           
          # copy the input data in NBin
          self.units[cntUnit].fill_NBin(self.windowsDataFlat[windowID][auxPos : min(auxPos + nElements, self.windowsDataFlat[windowID].size) ])
          print 'SIZE: %d %d'%(auxPos + nElements, self.windowsDataFlat[windowID].size)

          self.unitToWindow[cntUnit] = windowID # track which window is computing each unit
          self.units[cntUnit].compute()  	# compute

          # increase pointer indicating last processed element
          self.unitLastPosInWindow[cntUnit][1] += nElements
          
          if self.unitLastPosInWindow[cntUnit][1] >= self.windowsDataFlat[windowID].size:
            self.unitsProcWindow[self.unitToWindow[cntUnit]] -= 1
          

    if self.VERBOSE: print "It seems window #%d has been processed"%(windowID)
 
    # TODO: in the baseline, all the units have to process every window
    # the solution to deal with the new system and how it slices computation,
    # will be to add clusterDirector that will take care of slicing the computation 
    # among the narrow units conforming a cluster  

  def processDataFromUnits(self, unitID):
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
     
