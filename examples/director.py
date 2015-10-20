import numpy as np
import unit
import cluster

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
    self.clustersProcWindow = {}
    for i in range(nClusters):
      self.clusters.append(cluster.Cluster(i, self.nUnitsCluster, Ti, Tn, NBin_nEntries))

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
    self.processWindow(auxWindow, 17)

##################################################################################
###
##################################################################################
  def initializeWindow(self, windowData, windowID):
    if self.VERBOSE: print "Initializing window #%d"%(windowID)

    #self.windowsDataFlat[windowID] = np.swapaxes(windowData, 0, 2).flatten()
    self.clustersProcWindow[windowID] = self.nClusters
    for cntCluster in range(self.nClusters):
      self.clusters[cntCluster].initializeWindow(windowData, windowID)
    

##################################################################################
###
##################################################################################

  def processWindow(self, windowData, windowID):
    if self.VERBOSE: print "Processing of window #%d"%(windowID)

    #while self.clustersProcWindow[windowID] > 0:
    for cntCluster in range(self.nClusters):
      if not self.clusters[cntCluster].busy:
        self.clusters[cntCluster].processWindow(windowData, windowID)
          
    if self.VERBOSE: print "It seems window #%d has been processed"%(windowID)
 
    # TODO: in the baseline, all the units have to process every window
    # the solution to deal with the new system and how it slices computation,
    # will be to add clusterDirector that will take care of slicing the computation 
    # among the narrow units conforming a cluster  

  def processDataFromUnits(self, unitID):
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
     
