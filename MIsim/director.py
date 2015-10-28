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
# in:
# 	data : numpy 3D ndarray of dimensions i * Wx * Wy, i=# input features, Wx=Wy= size of input
#	filters: a list with two elements, we will use the field "data" of both, 
#		filters[0].data = numpy 4D ndarray  of dimensions N * i * Fx * Fy with the filter values
#		filters[1].data = numpy 1D vector with the N biases 
#		N = # filters, Fx=Fy= filter size
##################################################################################

  def computeConvolutionalLayer(self, data, filters, stride, padding, group):
    # TODO: when data come from modelzoo
    #weights = filters[0].data
    #biases  = filters[1].data
    weights = filters


    N	  = weights.shape[0]
    i	  = weights.shape[1]
    Fx	  = weights.shape[2]
    Fy	  = weights.shape[3]
  
    Ix 	  = data.shape[1]
    Iy	  = data.shape[2]
  
  
    if padding != 0:
      data = adjustDataPadding(data, padding)
      Ix      = data.shape[1]
      Iy      = data.shape[2]
  
  
    assert weights.shape[1]*group==data.shape[0], "#filters (%d) is not equal to #input features (%d)" %(weights.shape[1], data.shape[0])  
    assert Ix==Iy, "Input width (%d) is not equal to Input height (%d)" %(data.shape[1], data.shape[2]) 
    assert Fx==Fy, "Filter width (%d) is not equal to Filter height (%d)" %(Fx, Fy)
  
     # initialize the layer (filters are sent to SB in the units)
    self.initializeLayer(weights)
 
    #### Main loop ###
    # Horizontal shifting for window generation  
    output = np.zeros((N, (Ix-Fx)/stride+1, (Iy-Fy)/stride+1))
    windowID = 0
    outPosX = 0
    for posInputX in range(0, Ix-Fx+1, stride):
      outPosY = 0
      print posInputX
      for posInputY in range(0, Iy-Fy+1, stride):

      # process each window
        auxWindow  = data[:, posInputY:posInputY+Fy, posInputX:posInputX+Fx]
 
        self.initializeWindow(auxWindow, windowID)
        self.startWindowProcessing(auxWindow, windowID)
    
        while self.clustersProcWindow[windowID] > 0:
          self.cycle()
          
          #output[cntFilter, outPosY, outPosX] += biases[cntFilter]
        outPosY += 1
      outPosX += 1
  
    return output


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


