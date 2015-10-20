import director
import numpy as np

d = director.LayerDirector(16, 16, 16, 16, 16)
auxData = np.zeros((1))
auxFilters = np.zeros((384, 192, 3, 3))
d.computeConvolutional(auxData, auxFilters)
