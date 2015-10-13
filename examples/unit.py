class Unit:
  """This is the class which represents a single processing pipeline"""
  unit_id = 0
  NBin_num_entries = 16
  Ti = 16
  Tn = 16
  SB_size = (1 << 20) # 2MB / 16bits
  filters_contained = [] #an index with the filters included in SB

  def __init__(self, uid, NBin_num_entries, Ti, Tn, SB_size):
    self.unit_id = uid
    self.NBin_num_entries = NBin_num_entries
    self.Ti = Ti
    self.Tn = Tn
    self.SB_size = SB_size
  def fill_SB(filter_data, filter_indexes):
  
