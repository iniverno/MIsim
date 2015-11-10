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
import sys

def roundup_to_multiple(x, m):
    return int(np.ceil( x / float(m))) * m

def divide_roundup(x, m):
    return roundup_to_multiple(x,m) / m


args = sys.argv
script    = args.pop(0)
net_name  = args.pop(0)
layer     = args.pop(0)
assert len(args) == 0

layer_file = layer + '-0.npy'

d = director.LayerDirector(op.nClusters, op.nClusters * op.nUnitsCluster, op.Ti, op.Tn, op.nEntries, op.ZF)

use_traces = 1
if use_traces:

  # get layer data from net trace
  auxData = np.load( "net_traces/%s/%s"%(net_name, layer_file) )
  auxData = auxData[0] # just do one image
  input_dim = auxData.shape
  print "data:", input_dim

  nonzero = (auxData != 0).sum()
  print "Non-zero =", nonzero, "/", auxData.size, " (%d%%)"%(nonzero*100/auxData.size)

  # make sure data is a multiple of 16
  Ni = input_dim[0]
  Ni_pad = roundup_to_multiple(Ni, op.nUnitsCluster)
  if (Ni != Ni_pad):
    print "Padding", Ni, "to", Ni_pad
    pad_shape = list(auxData.shape)
    pad_shape[0] = Ni_pad
    print "pad_shape", pad_shape
    zdata = np.zeros(pad_shape)
    zdata[0:Ni,:,:] = auxData
    auxData = zdata
    Ni = Ni_pad


  # get other layer params from param file
  f = open("net_traces/%s/%s_trace_params.csv"%(net_name, net_name))
  for line in f:
    if re.match(layer,line):
      params = line
      break
  print params
  vals = params.split(',')
  Nn, Kx, Ky, stride, pad  = [int(v) for v in vals[1:]]

else:

  Ni, Nx, Ny = (96, 27, 27)
  auxData = np.zeros( (Ni, Nx, Ny) )
  for i,e in enumerate(auxData.flat):
    auxData.flat[i] = random.randrange(2)
  (Nn, Kx, Ky) = (256, 3, 3) 

input_dim = auxData.shape
print "data:",input_dim
auxFilters = np.zeros( (Nn,Ni,Kx,Ky) )
print "weights:", auxFilters.shape


if op.fast:
  auxData = auxData[:,:Kx,:Ky]

#for i,e in enumerate(auxData.flat):
#  auxData.flat[i] = random.randrange(2)
#auxData [191, 2, 2] = 17
#print auxData
#auxFilters = np.zeros((384, 48, 3, 3))
#auxFilters [: , 47, 2, 2] = 2
group = 1
d.computeConvolutionalLayer(auxData, auxFilters, stride, pad, group)
