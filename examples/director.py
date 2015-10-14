import unit

class directorLayer:
  def __init__(self, n_units):
    units = []
    for i in range(n_units):
      units.append(Unit(i, 16, 16, 16, (1<<20)))

  # this function copy the filter weights into the unit eDRAM
  def initializeLayer(self, weights):
    nUnits = len(units)
    nTotalFilters = weights.shape[0]
    #how many filters have to go to each unit
    nFiltersPerUnit = nTotalFilters / nUnits
    print "%d filters per unit" % (nFiltersPerUnit)
    # if the total number of filters is not a multiple of nUnits
    nAdditionalFilters = nTotalFilters - (nFiltersPerUnit * nUnits)
    print "plus %d additional filters"%(nAdditionalFilters)
    
    for idxFilter in range(nTotalFilters):
      self.units[idxFilter % nUnits].fill_NBin(weights, idxFilter)


  def computeConvolutional(self, inputData):
    # generate windows

    # process each window

  def processWindow(self, windowData):
    # the window has to be processed by each unit
    # divide the window in chunks as big as NBin
    # TODO: in the baseline, all the units have to process every window
    # the solution to deal with the new system and how it slices computation,
    # will be to add clusterDirector that will take care of slicing the computation 
    # among the narrow units conforming a cluster  
