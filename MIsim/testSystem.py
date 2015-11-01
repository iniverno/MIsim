##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################



import director
import numpy as np

d = director.LayerDirector(16, 256, 1, 16, 16)
auxData = np.zeros((192,3,3))
auxData [191, 2, 2] = 17
auxFilters = np.zeros((384, 192, 3, 3))
auxFilters [: , 191, 2, 2] = 2
d.computeConvolutionalLayer(auxData, auxFilters, 1, 0, 1)
