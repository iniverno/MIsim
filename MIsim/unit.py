##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################

import numpy as np
import math
import options as op 
import Queue as Q
import stats

class Unit:
  """This is the class which represents a single processing pipeline"""

  def __init__(self, system, verbose, clusterID, uid, NBin_nEntries, Ti, Tn, SB_size, cbInputRead, cbDataAvailable):
    self.system = system
    self.clusterID = clusterID
    self.unitID = uid
    self.VERBOSE = verbose
    self.NBin_nEntries = NBin_nEntries
    self.Ti = Ti
    self.Tn = Tn
    self.busy = False
    self.cbInputRead = cbInputRead
    self.cbDataAvailable = cbDataAvailable

    #instance variables 
    self.SB_ready = False
    self.SB_size = SB_size
    self.SB_available = SB_size
    self.SB_totalFilters = 0
    self.SB_filterIDtoEntry = {}
    self.SB_entryToFilterID = {}
    self.SB_data = 0 # initializeUnit will assign this var properly according to the filters of the layer
    self.NBin_data = np.zeros((Ti, NBin_nEntries))
    self.NBin_ready = False

    self.pipe = Q.Queue()
    self.headPipe = [] # aux var used to process the packet leaving the pipeline

    self.NBout = np.zeros((64, Tn))
    self.dataAvailable = False

    #These pointers are used when computing the data in the buffers (compute function)
    self.windowPointer = 0  #it tracks the next filter to compute



##################################################################################
###
##################################################################################
 
  # this function assigns SB with the right shape according to the filter size
  def initialize(self, filterSize):
    nFiltersFit = self.SB_size / filterSize
    self.SB_data = np.zeros((nFiltersFit, filterSize))

##################################################################################
###
  # filterData: list of a 1D ndarrays containing the filter data flat
  # filterIndexes: list containing filter indexes 
##################################################################################
  def fill_SB(self, filterData, filterIndexes):
    filterIndexes = [filterIndexes]
    filterData = [filterData]

    for i,e in enumerate(filterIndexes):
      filterSize = filterData[i].size
      nFilters = len(filterIndexes)

      # Check if there is enough space
      assert filterSize  <= self.SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unitID, filterSize, self.SB_size)

      if self.VERBOSE:
        print "SB in unit %d (cluster %d) is now storing filter #%d"%(self.unitID, self.clusterID, e)
      # store the filter data at the proper position
      self.SB_data[self.SB_totalFilters] = filterData[i]

      #record the entry that the filter is stored in at SB  
      self.SB_filterIDtoEntry[e] = self.SB_totalFilters
      self.SB_entryToFilterID[self.SB_totalFilters] = e
      self.SB_totalFilters += 1

      # update the available space
      self.SB_available -= filterSize 

    self.SB_ready = True

    # some initialization tasks to prepare the unit to process data
    self.NBout_nEntries = int(math.ceil(self.SB_totalFilters  / float(self.Tn)))

##################################################################################
###
##################################################################################
 
  def fill_NBin(self, inputData, offsets = []):
    #assert offsets != [] or self.Ti !=1, "Something is wrong with the parameters of fill_NBin"
    assert self.NBin_data.size >= inputData.size, "Something is wrong with the sizes at fill_NBin %d/%d"%(self.NBin_data.size,  inputData.size)

    if self.VERBOSE:
      print "fill_NBin in unit #%d (%d elements)"%(self.unitID, inputData.size)
    self.NBin_data = inputData 

    self.localWindowPointer = self.windowPointer

    self.filtersProcessed = 0
    self.filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed) 

    self.NBout_ptr = 0
    self.NBin_ptr = 0

    #the flag busy will indicate the cluster the data is ready and the unit is processing data so its computeCycle has to be called
    self.busy = True
    self.NBin_ready = True 

##################################################################################
###
##################################################################################
  def cycle(self):
 
    if self.headPipe == []:
      if not self.pipe.empty(): 
        self.headPipe = self.pipe.get()
    
    if self.headPipe != [] and self.headPipe[0] == self.system.now:
      #print self.system.now, " ", self.clusterID, " ", self.headPipe[1]
      # the cluster has to 
      # last in window?
      if self.headPipe[1]:
        self.cbDataAvailable(self.unitID, self.headPipe[2])
      #self.stats.NBout_reads+=1

      self.headPipe = []
      
    if self.NBin_ready:
      if self.VERBOSE: 
        print '[%d] unit %d (cluster %d), NBin entry %d, pos %d-%d, %d'%(self.system.now, self.unitID, self.clusterID, self.NBin_ptr, self.localWindowPointer , self.localWindowPointer + self.Ti, self.NBout_ptr)

      self.busy = True
      
      # an array with the proper filter data is prepared 
      # this arrays will be introduced in the pipeline queue
      SB_toPipe = np.zeros((self.Tn, self.Ti))
      NBin_toPipe = np.zeros((self.Ti))
      result = []

     # the input data is read
      NBin_toPipe = self.NBin_data[self.NBin_ptr * self.Ti : self.NBin_ptr * self.Ti + self.Ti]
 
      for f in range(self.filtersToProcess):  
        filterNow = self.NBout_ptr * self.Tn + f
        SB_toPipe[f] = self.SB_data[filterNow] [self.localWindowPointer : self.localWindowPointer + self.Ti]
        # the pipeline is modelled as a dummy queue where the correct result is stored for latencyPipeline cycles  
        result.append(np.sum(SB_toPipe[f] * NBin_toPipe))

        if self.VERBOSE and False:
          print '[%d] unit %d (cluster %d), NBin entry %d, computing filter #%d, pos %d-%d %d, %d'%(self.system.now, self.unitID, self.clusterID, self.NBin_ptr, self.SB_entryToFilterID[filterNow], self.localWindowPointer , self.localWindowPointer + self.Ti, self.NBout_ptr * self.Tn + f, self.NBout_ptr)
 
      #if the number of filters processed this cycle is less than Tn, fill with zeroes
      for cntFill in range(self.Tn - self.filtersToProcess):
        result.append(0)

      # we read the partial results from NBout       
      result += self.NBout[self.NBout_ptr]
      self.NBout[self.NBout_ptr] = result

      # this is the packet for the pipeline
      pipePacket = [self.system.now + op.latencyPipeline, result]
      assert self.pipe.qsize() < op.latencyPipeline, "Problem in the pipeline, Queue has too many elements"
      self.pipe.put(pipePacket)

      # NBin_ptr is incremented
      if self.NBin_ptr < min(self.NBin_nEntries, self.NBin_data.size / self.Ti) - 1:
        self.NBin_ptr += 1
        self.localWindowPointer += self.Ti
      else:
        self.NBin_ptr = 0
        self.filtersProcessed += self.filtersToProcess
        self.filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed)
        self.localWindowPointer = self.windowPointer

        if self.NBout_ptr < self.NBout_nEntries - 1:
          self.NBout_ptr += 1
        else:
        #the unit is done with this chunk
          self.windowPointer += self.NBin_data.size #min(self.NBin_nEntries, self.NBin_data.size / self.Ti) * self.Ti 
          self.localWindowPointer = self.windowPointer
 
          self.NBin_ready = False # no data to process in the buffer
          self.busy = False # The cluster can assign us work to do

          self.cbInputRead(self.unitID)


      if self.busy:
        # this means the unit is still processing the chunk in NBin, so we schedule it for next cycle
        self.system.schedule(self)
    # end of NBin_ready

