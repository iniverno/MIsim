##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


ZF = True
latencyPipeline = 8

# Central Memory
CM_nPorts = 2
CM_bytesCyclePort = 2
CM_size = 100000

if ZF:
  nClusters = 16
  nUnitsCluster = 16
  Ti = 1
  Tn = 16
  nEntries = 16
  ZF = True

else:
  nClusters = 4
  nUnitsCluster = 1
  Ti = 16
  Tn = 16
  nEntries = 16


