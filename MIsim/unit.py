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

  def __init__(self, system, clusterID, uid, NBin_nEntries, Ti, Tn, SB_size, cbInputRead, cbDataAvailable):
    self.system = system
    self.clusterID = clusterID
    self.unitID = uid
    self.VERBOSE = op.verboseUnit
    self.NBin_nEntries = NBin_nEntries
    self.Ti = Ti
    self.Tn = Tn
    self.busy = False
    self.cbInputRead = cbInputRead
    self.cbDataAvailable = cbDataAvailable
    self.lastTimeWokenUp = 0

    #instance variables 
    self.SB_ready = False
    self.SB_size = SB_size
    self.SB_available = SB_size
    self.SB_totalFilters = 0
    self.SB_filterIDtoEntry = {}
    self.SB_entryToFilterID = {}
    self.SB_data = 0 # initializeUnit will assign this var properly according to the filters of the layer
    self.NBin_data = np.zeros((Ti, NBin_nEntries))
    self.NBin_ready = float("inf")
    self.offsets = []
    self.skipThisChunk = False
    
    #Stuff for the dummy units
    self.dummyWhenCallInput = float("inf") 
    self.dummyWhenCallData = float("inf") 
    self.nullOutput = [0]*Tn
    self.latencyInput = 0
    self.latencyData = 0

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

    # divide slice into rows of (filterSize)
    nFiltersFit = self.SB_size / filterSize
    self.SB_data = np.zeros((nFiltersFit, filterSize))

##################################################################################
###
  # filterData: list of a 1D ndarrays containing the filter data flat
  # filterIndexes: list containing filter indexes 
##################################################################################
  def fill_SB(self, filterData, filterIndexes):
    #filterIndexes = [filterIndexes]
    #filterData = [filterData]

    for i,e in enumerate(filterIndexes):
      filterSize = filterData[i].size
      nFilters = len(filterIndexes)

      # Check if there is enough space
      assert filterSize  <= self.SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d/%d available)"%(self.unitID, filterSize, self.SB_available, self.SB_size)

      if self.VERBOSE:
        print "SB in unit %d (cluster %d) is now storing filter #%d (%d)"%(self.unitID, self.clusterID, e, filterSize)
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
  def compress(self, data):
    resData = []
    resOffsets = []
    
    for i,e in enumerate(data):
      if e:
        resData.append(e)
        resOffsets.append(i)
    if self.VERBOSE: print "compress: ", data, resData, resOffsets
    return [np.asarray(resData), np.asarray(resOffsets)]
 
##################################################################################
###
##################################################################################
 
  def fill_offsets(self, offsetData):
    if self.VERBOSE:
      print "fill_offsets in unit %d (cluster %d) (%d elements)"%(self.unitID, self.clusterID, offsetData.size)
    self.offsets = offsetData

##################################################################################
###
##################################################################################
 
  def fill_NBin(self, address, data, final):
    #assert offsets != [] or self.Ti !=1, "Something is wrong with the parameters of fill_NBin"
    assert self.Ti*self.NBin_nEntries >= data.size, "Something is wrong with the sizes at fill_NBin %d/%d"%(self.Ti*self.NBin_nEntries,  data.size)

    if self.VERBOSE:
      print "fill_NBin @%d in unit %d (cluster %d) (%d elements)"%(address, self.unitID, self.clusterID, data.size)
    self.NBin_data = data 
    self.localWindowPointer = self.windowPointer

    self.filtersProcessed = 0
    self.filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed) 

    self.NBout_ptr = 0
    self.NBin_ptr = 0

    #the flag busy will indicate the cluster the data is ready and the unit is processing data so its computeCycle has to be called
    self.busy = True
    self.NBin_ready = self.system.now + 1

    if self.VERBOSE: print "final:", final  
    self.finalFragmentOfWindow = final
    #if self.system.ZF:
    #  self.NBin_data, self.offsets = self.compress(data)
    if op.dummyUnits:
      self.latencyInput = (max(1, self.NBin_data.size) / self.Ti) * self.NBout_nEntries
      self.latencyData = (max(1,self.NBin_data.size) / self.Ti) + op.latencyPipeline
      assert self.latencyInput > 0
      assert self.latencyData > 0

    self.system.schedule(self)

##################################################################################
###
##################################################################################
  def wakeup(self):
    if self.lastTimeWokenUp == self.system.now:
      assert False, "woken up twice unit %d (cluster %d)"%(self.unitID, self.clusterID)
    self.lastTimeWokenUp = self.system.now

    if op.dummyUnits:
      if self.skipThisChunk:
        if self.VERBOSE > 1: 
          print "unit %d (cluster %d), skipThis Chunk"%(self.unitID, self.clusterID)
        self.skipThisChunk= False 
        self.windowPointer += self.NBin_dataOriginalSize
        self.dummyWhenCallInput = float("inf") 
        self.NBin_ready = float("inf")
        self.busy = False # The cluster can assign us work to do
        self.cbInputRead(self.unitID) 
        if self.finalFragmentOfWindow:
          for i in range(self.NBout_nEntries):
            self.cbDataAvailable(self.unitID, self.nullOutput)  


      if self.NBin_ready == self.system.now:
        self.busy = True
        self.system.schedule(self, self.latencyInput)
        self.dummyWhenCallInput = self.system.now + self.latencyInput

        if self.VERBOSE > 1: print "unit %d (cluster %d) callInput:%d"%(self.unitID, self.clusterID, self.dummyWhenCallInput)

        if self.finalFragmentOfWindow:
          self.system.schedule(self, self.latencyData)
          self.dummyWhenCallData = self.system.now + self.latencyData
          if self.VERBOSE > 1: print "unit %d (cluster %d) callData:%d"%(self.unitID, self.clusterID, self.dummyWhenCallData)

      if self.system.now == self.dummyWhenCallInput:
        self.dummyWhenCallInput = float("inf")
        self.windowPointer += self.NBin_dataOriginalSize
        if self.VERBOSE: print  "unit %d (cluster %d) pointer: %d"%(self.unitID, self.clusterID, self.windowPointer)
        self.NBin_ready = float("inf") # no data to process in the buffer
        self.busy = False # The cluster can assign us work to do

        self.cbInputRead(self.unitID)
      if self.system.now == self.dummyWhenCallData:
        #the unit has to write results as many times as we are reusing the input
        if self.NBout_ptr + 1 == self.NBout_nEntries:
          self.dummyWhenCallData = float("inf")
          self.busy = False
          self.NBout_ptr = 0
        else:
          self.NBout_ptr += 1
          self.system.schedule(self, self.latencyData)
          self.dummyWhenCallData = self.system.now + self.latencyData

        self.cbDataAvailable(self.unitID, self.nullOutput)

      return

    #print "[%d] (cluster %d) unit %d"%(self.system.now, self.clusterID, self.unitID) 
    if self.headPipe == []:
      if not self.pipe.empty(): 
        self.headPipe = self.pipe.get()
    
    if self.headPipe != [] and self.headPipe[0] == self.system.now:
      #print self.system.now, " ", self.clusterID, " ", self.headPipe[1]
      # last in window?
      if self.headPipe[1]:
        self.cbDataAvailable(self.unitID, self.headPipe[2])
       
      self.headPipe = []

    if self.NBin_ready == self.system.now and not self.skipThisChunk:
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
      if self.VERBOSE and self.system.ZF:
        print "unit %d (cluster %d)"%(self.unitID, self.clusterID), "NBin_ptr:", self.NBin_ptr, " pointer:",self.windowPointer, " NBin_data:", self.NBin_data.size, " NBout_ptr:", self.NBout_ptr, " offset.size:", self.offsets.size, " offset:", self.offsets[self.NBin_ptr]
      if self.VERBOSE and not self.system.ZF:
        print "unit %d (cluster %d)"%(self.unitID, self.clusterID), "NBin_ptr:", self.NBin_ptr, " pointer:",self.windowPointer, " NBin_data:", self.NBin_data.size, " NBout_ptr:", self.NBout_ptr
 
      for f in range(self.filtersToProcess):  
        filterNow = self.NBout_ptr * self.Tn + f
        # select the proper filter weights:
        #if Zero-Free: offsets must be used
        if self.system.ZF:
          start = self.windowPointer + self.offsets[self.NBin_ptr]
          end = self.windowPointer + self.offsets[self.NBin_ptr] + self.Ti
          SB_toPipe[f] = self.SB_data[filterNow] [start : end ]
        else:
          SB_toPipe[f] = self.SB_data[filterNow] [self.localWindowPointer : self.localWindowPointer + self.Ti]
        # the pipeline is modelled as a dummy queue where the correct result is stored for latencyPipeline cycles  
        if op.do_comp:
          result.append(np.sum(SB_toPipe[f] * NBin_toPipe))
        else:
          result.append(np.array( (self.Ti*self.Tn) ))

        if self.VERBOSE and False:
          print '[%d] unit %d (cluster %d), NBin entry %d, computing filter #%d, pos %d-%d %d, %d'%(self.system.now, self.unitID, self.clusterID, self.NBin_ptr, self.SB_entryToFilterID[filterNow], self.localWindowPointer , self.localWindowPointer + self.Ti, self.NBout_ptr * self.Tn + f, self.NBout_ptr)
 
      #if the number of filters processed this cycle is less than Tn, fill with zeroes
      for cntFill in range(self.Tn - self.filtersToProcess):
        result.append(0)

      # we read the partial results from NBout       
      result += self.NBout[self.NBout_ptr]
      self.NBout[self.NBout_ptr] = result

      #we insert the packet later when we now if this the final result for that NBout entry or not
      # after the next block of instructions
      useData = self.finalFragmentOfWindow

     # NBin_ptr is incremented
      if self.NBin_ptr < min(self.NBin_nEntries, self.NBin_data.size / self.Ti) - 1:
        self.NBin_ptr += 1
        self.localWindowPointer += self.Ti
        useData = False
      else:
        self.NBin_ptr = 0
        self.filtersProcessed += self.filtersToProcess
        self.filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed)
        self.localWindowPointer = self.windowPointer
        #This is the last time accumulating results on this NBout entry, so if cluster said 
        # it is the last fragment of the window --> data has to be used
        #(no need to modify useData value)

        if self.NBout_ptr < self.NBout_nEntries - 1:
          self.NBout_ptr += 1
        else:
        #the unit is done with this chunk
          self.windowPointer += self.NBin_dataOriginalSize #min(self.NBin_nEntries, self.NBin_data.size / self.Ti) * self.Ti 
          self.localWindowPointer = self.windowPointer
 
          self.NBin_ready = float("inf") # no data to process in the buffer
          self.busy = False # The cluster can assign us work to do

          self.cbInputRead(self.unitID)

      # this is the packet for the pipeline
      pipePacket = [self.system.now + op.latencyPipeline, useData, result]
      assert self.pipe.qsize() < op.latencyPipeline, "Problem in the pipeline, Queue has too many elements"
      self.pipe.put(pipePacket)

    if self.skipThisChunk:
      self.skipThisChunk = False
      self.windowPointer += self.NBin_dataOriginalSize
      self.localWindowPointer = self.windowPointer
      self.NBin_ready = float("inf") # no data to process in the buffer
      self.busy = False # The cluster can assign us work to do
      self.cbInputRead(self.unitID)

      pipePacket = [self.system.now + op.latencyPipeline, self.finalFragmentOfWindow, [0]*self.Tn]
      assert self.pipe.qsize() < op.latencyPipeline, "Problem in the pipeline, Queue has too many elements"
      self.pipe.put(pipePacket)
   

    if self.busy or self.headPipe != [] or not self.pipe.empty():
        # this means the unit is still processing the chunk in NBin, so we schedule it for next cycle
      self.system.schedule(self)
    # end of NBin_ready

##################################################################################
###
##################################################################################
 
  def skipElements(self, nElements):
    self.skipThisChunk = True
    self.system.schedule(self)

