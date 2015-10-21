##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


import numpy as np
import unit
import cluster

class LayerDirector:

  verboseUnits = True

  def __init__(self, nClusters, nTotalUnits, Ti, Tn, NBin_nEntries):
    self.cycle = 0
    self.VERBOSE = True
    self.clusters = []
    self.nClusters = nClusters
    self.Tn = Tn  # it is used when assigning filters to clusters
    self.nUnitsCluster = nTotalUnits / nClusters
    self.clustersProcWindow = {}
    for i in range(nClusters):
      self.clusters.append(cluster.Cluster(self, i, self.nUnitsCluster, Ti, Tn, NBin_nEntries, (1<<20)))

##################################################################################
###
### This function copy the filter weights into the unit eDRAM
###
### weights: ndarray containing the weights of the filters  
###
##################################################################################
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

    ##for idxFilter in range(nTotalFilters):
      ##self.clusters[(idxFilter / self.nClusters) % self.nClusters].fill_SB(weights[idxFilter], idxFilter)
    
    filtersAssignedSoFar = 0
    idxFilter = 0
    cntCluster = 0

    while filtersAssignedSoFar < nFiltersPerCluster:
      cntFilterCluster = 0
      while cntFilterCluster < min(self.Tn, nFiltersPerCluster-filtersAssignedSoFar ): 
        self.clusters[cntCluster].fill_SB(weights[idxFilter], idxFilter)
        cntFilterCluster += 1
        idxFilter += 1
      cntCluster += 1
      if cntCluster == self.nClusters:
        filtersAssignedSoFar += cntFilterCluster
        cntCluster = 0
      #print '%d %d %d %d %d'%(nFiltersPerCluster, filtersAssignedSoFar, cntFilterCluster, self.Tn, self.nClusters)

##################################################################################
###
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
    while self.processWindowCycle(auxWindow, 17):
      self.cycle += 1
      pass

##################################################################################
###
##################################################################################
  def initializeWindow(self, windowData, windowID):
    if self.VERBOSE: print "[director] Initializing window #%d"%(windowID)

    #self.windowsDataFlat[windowID] = np.swapaxes(windowData, 0, 2).flatten()
    self.clustersProcWindow[windowID] = self.nClusters
    for cntCluster in range(self.nClusters):
      self.clusters[cntCluster].initializeWindow(windowData, windowID)
    

##################################################################################
###
##################################################################################

  def processWindowCycle(self, windowData, windowID):
    if self.VERBOSE: print "[director] Processing of window #%d"%(windowID)

    if self.clustersProcWindow[windowID] > 0:
      for cntCluster in range(self.nClusters):
        if not self.clusters[cntCluster].processWindowCycle(windowData, windowID):
          #this means there is not unit in that cluster processing the window   
          self.clustersProcWindow[windowID] -= 1            
    return self.clustersProcWindow[windowID] > 0
    
    #if self.VERBOSE: print "It seems window #%d has been processed"%(windowID)
 

##################################################################################
###
##################################################################################

  def processDataFromUnits(self, unitID):
    if self.VERBOSE: print "director callback for unit #%d"%(unitID) 
     
