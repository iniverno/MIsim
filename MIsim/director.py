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
import simpleMemory 
import options as op

def adjustDataPadding(data, padding):
  # FYI there is actually a numpy pad function
  assert padding != 0, "Padding is zero"
  aux = np.zeros((data.shape[0], data.shape[1] + 2*padding, data.shape[2] + 2*padding))
  aux[:, padding:-padding, padding:-padding] = data
  return aux

class LayerDirector:

  verboseUnits = True

  def __init__(self, nClusters, nTotalUnits, Ti, Tn, NBin_nEntries, ZF):

    #schedule
    self.wakeQ = SortedDict()
    self.now = 0

    self.ZF = ZF
    self.VERBOSE = op.verboseDirector
    self.nClusters = nClusters
    self.Tn = Tn  # it is used when assigning filters to clusters
    self.nUnitsCluster = nTotalUnits / nClusters
 
    #components
    self.centralMem = simpleMemory.SimpleMemory(self, op.CM_size, op.CM_nPorts, op.CM_bytesCyclePort)
    self.clusters = []
    self.coordsWindow = {}
    self.clustersProcWindow = {} # [windowID] -> count of clusters processing this window
    self.filtersPending = {}
    self.clustersReadingWindow = {}
    self.output = []
    for i in range(nClusters):
      self.clusters.append(cluster.Cluster(self, i, self.nUnitsCluster, Ti, Tn, NBin_nEntries, op.SB_size_per_cluster, self.cbClusterDoneReading, self.cbClusterDone))


  def schedule(self, entity, when = 1):
    when += self.now
    if when in self.wakeQ:
      self.wakeQ[when].add(entity)
    else:
      self.wakeQ[when] = set([entity])


  def cycle(self):
    if self.VERBOSE > 1: print "layerdirector, cycle ", self.now, len(self.wakeQ)
    entities = [] 
    if len(self.wakeQ) !=0:
      aux, entities = self.wakeQ.popitem(False)
      if self.VERBOSE > 1: print "layerdirector, cycle ", self.now, aux, len(entities), " objects to wakeup"
      self.now = aux
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
    self.nTotalFilters = weights.shape[0]
    #how many filters have to go to each cluster
    nFiltersPerCluster = self.nTotalFilters / self.nClusters
    if self.VERBOSE: print "%d filters per cluster" % (nFiltersPerCluster)
    # if the total number of filters is not a multiple of nClusters
    nAdditionalFilters = self.nTotalFilters - (nFiltersPerCluster * self.nClusters)
    if self.VERBOSE: print "plus %d additional filters"%(nAdditionalFilters)
   
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
      listFilterData = []
      listFilterIdxs = []
      while cntFilterCluster < min(self.Tn, nFiltersPerCluster-filtersAssignedSoFar ): 
        listFilterData.append(weights[idxFilter])
        listFilterIdxs.append(idxFilter)
        cntFilterCluster += 1
        idxFilter += 1
      self.clusters[cntCluster].fill_SB(listFilterData, listFilterIdxs)
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
    self.output = np.zeros((N, (Ix-Fx)/stride+1, (Iy-Fy)/stride+1))
    windowID = 0
    outPosX = 0
    for posInputX in range(0, Ix-Fx+1, stride):
      outPosY = 0
      #print posInputX
      for posInputY in range(0, Iy-Fy+1, stride):
      # process each window
        auxWindow  = data[:, posInputY:posInputY+Fy, posInputX:posInputX+Fx]
        self.filtersPending[windowID] = [True] * self.nTotalFilters
 
        self.initializeWindow(auxWindow, windowID)
        self.startWindowProcessing(auxWindow, windowID)
        self.coordsWindow[windowID] = [outPosX, outPosY]
 
        timeout=10000
        while not self.isFinished(windowID) and timeout > 0:
          self.cycle()
          timeout -= 1
        assert timeout, "Simulation Timed Out"
          
          #output[cntFilter, outPosY, outPosX] += biases[cntFilter]
        windowID += 1
        outPosY += 1
      outPosX += 1
    print "Total cycles: ", self.now 
  

  def isFinished(self, windowID):
    #print "Pending Count = ", np.sum(self.filtersPending[windowID])
    for i,e in enumerate(self.filtersPending[windowID]):
      if e:
        if self.VERBOSE > 1: print "pendingFilters for window %d"%(windowID)
        return False
    if self.VERBOSE > 1: print "pendingFilters for window %d  LISTO"%(windowID)
    return True
    

##################################################################################
###
##################################################################################
  def initializeWindow(self, windowData, windowID):
    if self.VERBOSE: print "[director] [%d] Initializing window #%d"%(self.now, windowID)

    #self.windowsDataFlat[windowID] = np.swapaxes(windowData, 0, 2).flatten()
    self.clustersProcWindow[windowID] = self.nClusters
    self.clustersReadingWindow[windowID] = self.nClusters 
    for cntCluster in range(self.nClusters):
      self.clusters[cntCluster].initializeWindow(windowData, windowID)

##################################################################################
###
##################################################################################

  def startWindowProcessing(self, windowData, windowID):
    if self.VERBOSE: print "[director] Processing of window #%d"%(windowID)

    for cntCluster in range(self.nClusters):
      self.schedule(self.clusters[cntCluster])

##################################################################################
###
##################################################################################
  def cbClusterDoneReading(self, clusterID, windowID):
    self.clustersReadingWindow[windowID] -= 1 

  def cbClusterDone(self, clusterID, windowID):
    self.clustersProcWindow[windowID] -= 1 


  def putData(self, windowID, data, filterIDs):
    if self.VERBOSE > 1: print "windowID: ", windowID, " filterIDs:", filterIDs 
    for f in filterIDs:
      self.filtersPending[windowID][f] = False

    x, y = self.coordsWindow[windowID]
    self.output[filterIDs, x, y] = data  

