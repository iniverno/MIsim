##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################

from sortedcontainers import SortedDict
import numpy as np
import unit
import cluster

class LayerDirector:

  verboseUnits = True

  def __init__(self, nClusters, nTotalUnits, Ti, Tn, NBin_nEntries):

    #schedule
    self.wakeQ = SortedDict()
    self.now = 0

    #components
    self.VERBOSE = True
    self.clusters = []
    self.nClusters = nClusters
    self.Tn = Tn  # it is used when assigning filters to clusters
    self.nUnitsCluster = nTotalUnits / nClusters
    self.clustersProcWindow = {}
    for i in range(nClusters):
      self.clusters.append(cluster.Cluster(self, i, self.nUnitsCluster, Ti, Tn, NBin_nEntries, (1<<20), self.callbackClusterDone))


  def schedule(self, entity, when = 1):
    when += self.now
    if when in self.wakeQ:
      self.wakeQ[when].add(entity)
    else:
      self.wakeQ[when] = set([entity])


  def cycle(self):
    entities = [] 
    self.now, entities = self.wakeQ.popitem(False)
    print "layerdirector, cycle ", self.now, len(entities), " objects to wakeup"
    for obj in entities:
      obj.cycle()


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
    windowID = 17
    auxWindow = np.zeros((192, 3, 3))
    
    # process each window
    self.initializeWindow(auxWindow, windowID)
    self.startWindowProcessing(auxWindow, windowID)

    while self.clustersProcWindow[windowID] > 0:
      self.cycle()

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

  def startWindowProcessing(self, windowData, windowID):
    if self.VERBOSE: print "[director] Processing of window #%d"%(windowID)

    for cntCluster in range(self.nClusters):
      if not self.clusters[cntCluster].busy:
        self.schedule(self.clusters[cntCluster])

##################################################################################
###
##################################################################################

  def callbackClusterDone(self, clusterID, windowID):
    self.clustersProcWindow[windowID] -= 1 


