##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################


ZF = True
latencyPipeline = 8
verboseUnit = 0
verboseCluster = 0
verboseDirector = 1
verboseMemory = 0
# Central Memory
CM_nPorts = 2
CM_bytesCyclePort = 2
CM_size = 1 << 22

if ZF:
  nClusters = 16
  nUnitsCluster = 16
  Ti = 1
  Tn = 16
  nEntries = 16

else:
  nClusters = 16
  nUnitsCluster = 1
  Ti = 16
  Tn = 16
  nEntries = 16


