import numpy as np

class Unit:
  """This is the class which represents a single processing pipeline"""
  unit_id = 0
  NBin_num_entries = 16
  Ti = 16
  Tn = 16
  NBin_data = np.zeros((Ti, NBin_num_entries))
  SB_size = (1 << 20) # in elements 2MB / 16bits
  SB_data = {} #a dictionary with the filters included in SB, indexed by filter index

  def __init__(self, uid, NBin_num_entries, Ti, Tn, SB_size):
    self.unit_id = uid
    self.NBin_num_entries = NBin_num_entries
    self.Ti = Ti
    self.Tn = Tn
    self.SB_size = SB_size

  # TODO: what happens if the computation is broken in subbricks ????
  def fill_SB(filter_data, filter_indexes):
    filter_size = filter_data.shape[1]*filter_data.shape[2]*filter_data.shape[3] * len(filter_indexes)
    assert filter_size <= SB_size, "The filters being loaded in SB of unit %d are too big (%d vs. %d available)"%(self.unit_id, filter_size, self.SB_size)
    for f in filter_indexes:
      SB_data[f] = filter_data[f]

  def fill_NBin(input_data, offsets = []):
    assert offsets != [] or Ti !=1, "Something is wrong with the parameters of fill_NBin"
    NBin_data = input_data 
