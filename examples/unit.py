import numpy as np
import math
class Unit:
  """This is the class which represents a single processing pipeline"""
  NBin_num_entries = 16
  Ti = 16
  Tn = 16

  def __init__(self, verbose, uid, NBin_nEntries, Ti, Tn, SB_size, directorCallback):
    self.unitID = uid
    self.VERBOSE = verbose
    self.NBin_nEntries = NBin_nEntries
    self.Ti = Ti
    self.Tn = Tn
    self.busy = False
    self.directorCallbackWhenReady = directorCallback

    #instance variables 
    self.SB_size = SB_size
    self.SB_available = SB_size
    self.SB_nextFilterIdx = 0
    self.SB_filterIDtoEntry = {}
    self.SB_entryToFilterID = {}
    self.SB_data = 0 # initializeUnit will assign this var properly according to the filters of the layer
    self.NBin_data = np.zeros((Ti, NBin_nEntries))

    #These pointers are used when computing the data in the buffers (compute function)
    self.windowPointer = 0  #it tracks the next filter to compute

  # this function assigns SB with the right shape according to the filter size
  def initializeUnit(self, filterSize):
    nFiltersFit = self.SB_size / filterSize
    self.SB_data = np.zeros((nFiltersFit, filterSize))

  # TODO: what happens if the computation is broken in subbricks ????
  # filterData: list of a 1D ndarrays containing the filter data flat
  # filterIndexes: list containing filter indexes 
  def fill_SB(self, filterData, filterIndexes):
    for i,e in enumerate(filterIndexes):
      filterSize = filterData[i].size
      nFilters = len(filterIndexes)

      # Check if there is enough space
      assert filterSize  <= self.SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unitID, filterSize, self.SB_size)

      if self.VERBOSE:
        print "SB in unit %d is now storing filter #%d"%(self.unitID, e)
      # store the filter data at the proper position
      self.SB_data[self.SB_nextFilterIdx] = filterData[i]

      #record the entry that the filter is stored in at SB  
      self.SB_filterIDtoEntry[e] = self.SB_nextFilterIdx
      self.SB_entryToFilterID[self.SB_nextFilterIdx] = e
      self.SB_nextFilterIdx += 1

      # update the available space
      self.SB_available -= filterSize 

  def fill_NBin(self, inputData, offsets = []):
    assert offsets != [] or self.Ti !=1, "Something is wrong with the parameters of fill_NBin"
    assert self.NBin_data.size >= inputData.size, "Something is wrong with the sizes at fill_NBin %d/%d"%(self.NBin_data.size,  inputData.size)

    self.NBin_data = inputData 

  def compute(self):
    if self.VERBOSE: print "unit #%d computing"%(self.unitID)
    # there are Ti * Tn multipliers available meaning that Ti elements from Tn filters (I know, review naming)
    # There are NBin_nEntries which have to be combined with all the filters

    # an array with the proper filter data is prepared 
    SB_head = np.zeros((self.Tn, self.Ti))
    NB_head = np.zeros((self.Ti))

    
    NBout_nEntries = int(math.ceil((self.SB_nextFilterIdx ) / self.Tn))
    if self.VERBOSE: print "%d reuses of each input data (idx %d, SBdata %d, Tn %d) "%(NBout_nEntries, self.SB_nextFilterIdx, self.SB_data.size, self.Tn)


    for t in range( NBout_nEntries):
      localWindowPointer = self.windowPointer
      for e in range(min(self.NBin_nEntries, self.NBin_data.size / self.Ti)):
        NB_head = self.NBin_data[e * self.Ti : e * self.Ti + self.Ti]
        # for each filter that fits     
        for f in range(self.Tn):
          filterNow = t * self.Tn + f
          if self.VERBOSE:
            print 'unit %d, NBin entry %d, computing filter #%d, pos %d-%d %d'%(self.unitID, e, self.SB_entryToFilterID[filterNow], localWindowPointer , localWindowPointer + self.Ti, t * self.Tn + f)
          SB_head[f] = self.SB_data[filterNow] [localWindowPointer : localWindowPointer + self.Ti]
        localWindowPointer += self.Ti

    # Update the filter skipping all the elements already processed 
    self.windowPointer += min(self.NBin_nEntries, self.NBin_data.size / self.Ti) * self.Ti 
     
    self.directorCallbackWhenReady(self.unitID)


