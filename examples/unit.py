import numpy as np

class Unit:
  """This is the class which represents a single processing pipeline"""
  NBin_num_entries = 16
  Ti = 16
  Tn = 16

  def __init__(self, verbose, uid, NBin_nEntries, Ti, Tn, SB_size, directorCallback):
    self.unitID = uid
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
  # filterData: list of a 1D ndarrays containing the filter data flat
  # filterIndexes: list containing filter indexes 
  def fill_SB(self, filterData, filterIndexes):
    for i,e in enumerate(filterIndexes):
      filterSize = filterData[i].size
      nFilters = len(filterIndexes)

      # Check if there is enough space
      assert filterSize  <= SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unitId, filterSize, self.SB_size)

      if self.VERBOSE:
        print "SB in unit %d is now storing filter #%d"%(self.unitId, f)
      self.SB_data[f] = filterData[i]

      # update the available space
      self.SB_available -= filterSize 

  def fill_NBin(self, inputData, offsets = []):
    assert offsets != [] or Ti !=1, "Something is wrong with the parameters of fill_NBin"
    self.NBin_data = inputData 

  def compute(self):
    if self.VERBOSE: print "unit #%d computing"%(self.unitID)
    self.directorCallbackWhenReady(self.unitID)


