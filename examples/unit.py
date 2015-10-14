import numpy as np

class Unit:
  """This is the class which represents a single processing pipeline"""
  NBin_num_entries = 16
  Ti = 16
  Tn = 16

  def __init__(self, verbose, uid, NBin_nEntries, Ti, Tn, SB_size, directorCallback):
    self.unitId = uid
    self.VERBOSE = verbose
    self.NBin_nEntries = NBin_nEtries
    self.Ti = Ti
    self.Tn = Tn
    self.busy = False
    self.directorCallbackWhenReady = directorCallback

    #instance variables 
    self.SB_size = SB_size
    self.SB_available = SB_size
    self.SB_data = {}
    self.NBin_data = np.zeros((Ti, NBin_nEntries))
    

  # TODO: what happens if the computation is broken in subbricks ????
  # TODO: this function is copying ONLY ONE filter rigth now
  # filterData: vector containing the filter data flat
  # filterIndexes: index corresponding to the filter identifier
  def fill_SB(self, filterData, filterIndexes):
    #filterSize = filterData.shape[1]*filter_data.shape[2]*filter_data.shape[3] 
    filterSize = filterData.size
    nFilters = len(filterIndexes)

    # Check if there is enough space
    assert filterSize * nFilters <= SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unitId, filterSize, self.SB_size)

    for f in filterIndexes:
      if self.VERBOSE:
        print "SB in unit %d is now storing filter #%d"%(self.unitId, f)
      self.SB_data[f] = filterData[f]

    # update the available space
    self.SB_available -= filterSize * nFilters

  def fill_NBin(self, inputData, offsets = []):
    assert offsets != [] or Ti !=1, "Something is wrong with the parameters of fill_NBin"
    self.NBin_data = inputData 

  def compute(self):

