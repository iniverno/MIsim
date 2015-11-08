##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################

# verbose message settings
verboseUnit     = 0
verboseCluster  = 0
verboseDirector = 0
verboseMemory   = 0

# just run one window
fast = 1

ZF = 1

latencyPipeline = 8

# don't compute results
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


