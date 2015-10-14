import numpy as np

class Unit:
  """This is the class which represents a single processing pipeline"""
  NBin_num_entries = 16
  Ti = 16
  Tn = 16

  def __init__(self, verbose, uid, NBin_num_entries, Ti, Tn, SB_size):
    self.unit_id = uid
    self.VERBOSE = verbose
    self.NBin_num_entries = NBin_num_entries
    self.Ti = Ti
    self.Tn = Tn
    self.busy = False

    #instance variables 
    self.SB_size = SB_size
    self.SB_available = SB_size
    self.SB_data = {}
    self.NBin_data = np.zeros((Ti, NBin_num_entries))
    

  # TODO: what happens if the computation is broken in subbricks ????
  def fill_SB(self, filter_data, filter_indexes):
    filter_size = filter_data.shape[1]*filter_data.shape[2]*filter_data.shape[3] 
    nFilters = len(filter_indexes)

    # Check if there is enough space
    assert filter_size * nFilters <= SB_available, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unit_id, filter_size, self.SB_size)

    for f in filter_indexes:
      if self.VERBOSE:
        print "SB in unit %d is now storing filter #%d"%(unit_id, f)
      self.SB_data[f] = filter_data[f]

    # update the available space
    self.SB_available -= filter_size * nFilters

  def fill_NBin(self, input_data, offsets = []):
    assert offsets != [] or Ti !=1, "Something is wrong with the parameters of fill_NBin"
    self.NBin_data = input_data 
