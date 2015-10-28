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

    self.NBout = []
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

##################################################################################
###
##################################################################################
 
  def fill_NBin(self, inputData, offsets = []):
    #assert offsets != [] or self.Ti !=1, "Something is wrong with the parameters of fill_NBin"
    assert self.NBin_data.size >= inputData.size, "Something is wrong with the sizes at fill_NBin %d/%d"%(self.NBin_data.size,  inputData.size)

    if self.VERBOSE:
      print "fill_NBin in unit #%d (%d elements)"%(self.unitID, inputData.size)
    self.NBin_data = inputData 

    # some initialization tasks to prepare the unit to process data
    self.NBout_nEntries = int(math.ceil(self.SB_totalFilters  / float(self.Tn)))
    self.NBout_ptr = 0
    self.NBin_ptr = 0

    self.localWindowPointer = self.windowPointer

    self.filtersProcessed = 0
    self.filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed) 

    #the flag busy will indicate the cluster the data is ready and the unit is processing data so its computeCycle has to be called
    self.busy = True
    self.NBin_ready = True 

##################################################################################
###
##################################################################################
  def cycle(self):
 
    if self.dataAvailable and self.whenDataAvailable <= self.system.now:
      # the cluster has to 
      self.cbDataAvailable(self.unitID)
      
    if self.NBin_ready:
      self.busy = True
      
      # an array with the proper filter data is prepared 
      # this arrays will be introduced in the pipeline queue
      SB_head = np.zeros((self.Tn, self.Ti))
      NB_head = np.zeros((self.Ti))


      print '[%d] unit %d (cluster %d), NBin entry %d, pos %d-%d, %d'%(self.system.now, self.unitID, self.clusterID, self.NBin_ptr, self.localWindowPointer , self.localWindowPointer + self.Ti, self.NBout_ptr)

      # the input data is read
      NB_head = self.NBin_data[self.NBin_ptr * self.Ti : self.NBin_ptr * self.Ti + self.Ti]

      for f in range(self.filtersToProcess):  
        filterNow = self.NBout_ptr * self.Tn + f

        if self.VERBOSE and False:
          print '[%d] unit %d (cluster %d), NBin entry %d, computing filter #%d, pos %d-%d %d, %d'%(self.system.now, self.unitID, self.clusterID, self.NBin_ptr, self.SB_entryToFilterID[filterNow], self.localWindowPointer , self.localWindowPointer + self.Ti, self.NBout_ptr * self.Tn + f, self.NBout_ptr)
                
        SB_head[f] = self.SB_data[filterNow] [self.localWindowPointer : self.localWindowPointer + self.Ti]
        print np.sum(SB_head[f] * NB_head), " "
        print "++++++++++++++++++++++++++++++++++++++++"


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
          self.dataAvailable = True
          self.whenDataAvailable = self.system.now + op.latencyPipeline
          self.system.schedule(self) 


      if self.busy:
        # this means the unit is still processing the chunk in NBin, so we schedule it for next cycle
        self.system.schedule(self)
    # end of NBin_ready


##################################################################################
###
##################################################################################
     
  def compute(self):
    self.computeCycle()
    if self.VERBOSE: print "unit #%d (cluster %d) computing"%(self.unitID, self.clusterID)
    # there are Ti * Tn multipliers available meaning that Ti elements from Tn filters (I know, review naming)
    # There are NBin_nEntries which have to be combined with all the filters

    # an array with the proper filter data is prepared 
    SB_head = np.zeros((self.Tn, self.Ti))
    NB_head = np.zeros((self.Ti))

    
    NBout_nEntries = int(math.ceil(self.SB_totalFilters  / float(self.Tn)))
    self.filtersProcessed = 0
 
    if self.VERBOSE: print "%d reuses of each input data (idx %d, SBdata %d, Tn %d) "%(NBout_nEntries, self.SB_totalFilters, self.SB_data.size, self.Tn)

    for t in range( NBout_nEntries):
      localWindowPointer = self.windowPointer
      for e in range(min(self.NBin_nEntries, self.NBin_data.size / self.Ti)):
        NB_head = self.NBin_data[e * self.Ti : e * self.Ti + self.Ti]
        # for each filter that fits
        filtersToProcess = min(self.Tn, self.SB_totalFilters - self.filtersProcessed)     
        for f in range(filtersToProcess):
          filterNow = t * self.Tn + f
          SB_head[f] = self.SB_data[filterNow] [localWindowPointer : localWindowPointer + self.Ti]
         
          if self.VERBOSE:
            print 'unit %d (cluster %d), NBin entry %d, computing filter #%d, pos %d-%d %d, %d'%(self.unitID, self.clusterID, e, self.SB_entryToFilterID[filterNow], localWindowPointer , localWindowPointer + self.Ti, t * self.Tn + f, t)
       
        localWindowPointer += self.Ti
      self.filtersProcessed += filtersToProcess

    # Update the filter skipping all the elements already processed 
    self.windowPointer += min(self.NBin_nEntries, self.NBin_data.size / self.Ti) * self.Ti 
     
    self.directorCallbackWhenReady(self.unitID)


