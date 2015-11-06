##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################



import director
import numpy as np
import random 
import options as op

d = director.LayerDirector(op.nClusters, op.nClusters * op.nUnitsCluster, op.Ti, op.Tn, op.nEntries, op.ZF)
#auxData = np.load("/aenao-99/juddpatr/net_traces/alexnet/conv2-0.npy")
#input_dim = auxData.shape[1:]
#print input_dim

auxData = np.zeros((1,96, 27, 27))

for i,e in enumerate(auxData.flat):
  auxData.flat[i] = random.randrange(2)
  
auxFilters = np.zeros( (256,96,3,3) )
print auxFilters.shape

nonzero = (auxData != 0).sum()
print "Non-zero =", nonzero, "/", auxData.size, " (%d%%)"%(nonzero*100/auxData.size)

#for i,e in enumerate(auxData.flat):
#  auxData.flat[i] = random.randrange(2)
#auxData [191, 2, 2] = 17
#print auxData
#auxFilters = np.zeros((384, 48, 3, 3))
#auxFilters [: , 47, 2, 2] = 2
stride = 1
padding = 0
group = 1
d.computeConvolutionalLayer(auxData[0], auxFilters, stride, padding, group)
