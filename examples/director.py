import unit

class directorLayer:

    verboseUnits = True

  def __init__(self, n_units, Ti, Tn, NBin_nEntries):
    units = []
    self.Tn = Tn
    self.Ti = Ti
    self.Nbin_nEntries = NBin_nEntries
    self.filtersToUnits = {}
    for i in range(n_units):
      units.append(Unit(i, verboseUnits, i, NBin_nEntries, Ti, Tn, (1<<20)))

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
      # the filter is firstly made flat
      # the axes are swapped to made it accross features first 
      filterFlat = weights[idxFilter]
      filterFlat = np.swapaxes(filterFlat, 0, 2).flatten()

      self.units[idxFilter % nUnits].fill_NBin(filterFlat, idxFilter)


  def computeConvolutional(self, inputData):
    # generate windows

    # process each window

  def processWindow(self, windowData):
    # the window has to be processed by each unit
    # divide the window in chunks as big as NBin
    nElements = self.Ti * self.NBin_nEntries

    windowData = np.swapaxes(windowData, 0, 2
    dataToTransfer = np.zeros((NBin_nEntries, self.Ti))
    for posWinX in range(windowData.shape[1]):
      for posWinY in range(windowData.shape[2]):
        for posWinI in range(windowData.shape[0]):
          
        
 
    # TODO: in the baseline, all the units have to process every window
    # the solution to deal with the new system and how it slices computation,
    # will be to add clusterDirector that will take care of slicing the computation 
    # among the narrow units conforming a cluster  
