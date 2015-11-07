##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################

# verbose message settings
memVerbose      = 1
clusterVerbose  = 1
unitVerbose     = 1
directorVerbose = 2

ZF = 1
latencyPipeline = 8
verboseUnit = 0
verboseCluster = 0
verboseDirector = 1
verboseMemory = 0

dummyUnits = True

# Central Memory
CM_nPorts = 2
CM_size = 1 << 22

do_comp = 0

# SB
SB_size_per_cluster = 1<<22 # 2^22 = 4MB

if ZF:
  CM_bytesCyclePort = 32
  nClusters = 16
  nUnitsCluster = 16
  Ti = 1
  Tn = 16
  nEntries = 16

else:
  CM_bytesCyclePort = 256
  nClusters = 16
  nUnitsCluster = 1
  Ti = 16
  Tn = 16
  nEntries = 16


