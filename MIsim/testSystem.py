##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################



import director
import numpy as np
import random 

d = director.LayerDirector(4, 64, 1, 16, 16, True)
auxData = np.zeros((48,3,3))
for i,e in enumerate(auxData.flat):
  auxData.flat[i] = random.randrange(2)
#auxData [191, 2, 2] = 17
print auxData
auxFilters = np.zeros((384, 48, 3, 3))
auxFilters [: , 47, 2, 2] = 2
d.computeConvolutionalLayer(auxData, auxFilters, 1, 0, 1)
