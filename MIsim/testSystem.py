##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


import options as op

import director
import numpy as np
import random 
import re

net_name = 'alexnet'
layer = 'conv2'

layer_file = layer + '-0.npy'

d = director.LayerDirector(op.nClusters, op.nClusters * op.nUnitsCluster, op.Ti, op.Tn, op.nEntries, op.ZF)

# get layer data from net trace
auxData = np.load( "/aenao-99/juddpatr/net_traces/%s/%s"%(net_name, layer_file) )

# get other layer params from param file
f = open("/aenao-99/juddpatr/net_traces/%s/%s_trace_params.csv"%(net_name, net_name))
for line in f:
  if re.match(layer,line):
    params = line
    break
print params
vals = params.split(',')
Nn, Kx, Ky, stride, pad  = [int(v) for v in vals[1:]]

input_dim = auxData.shape[1:]
print "data:",input_dim

#auxData = np.zeros((1,96, 27,27,))
#for i,e in enumerate(auxData.flat):
#  auxData.flat[i] = random.randrange(2)
  
#auxFilters = np.zeros( (256,96,3,3) )
auxFilters = np.zeros( (Nn,input_dim[0],Kx,Ky) )
print auxFilters.shape

nonzero = (auxData != 0).sum()
print "Non-zero =", nonzero, "/", auxData.size, " (%d%%)"%(nonzero*100/auxData.size)

#for i,e in enumerate(auxData.flat):
#  auxData.flat[i] = random.randrange(2)
#auxData [191, 2, 2] = 17
#print auxData
#auxFilters = np.zeros((384, 48, 3, 3))
#auxFilters [: , 47, 2, 2] = 2
group = 1
d.computeConvolutionalLayer(auxData[0], auxFilters, stride, pad, group)
