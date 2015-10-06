import numpy as np
import matplotlib.pyplot as plt
#@matplotlib inline
import math
import csv
from sets import Set
from scipy.stats import itemfreq
#from __future__ import print_function

# Make sure that caffe is on the python path:
caffe_root = '../'  # this file is expected to be in {caffe_root}/examples
import sys
sys.path.insert(0, caffe_root + 'python')

import caffe

plt.rcParams['figure.figsize'] = (10, 10)
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

import os
if not os.path.isfile(caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'):
    print("Downloading pre-trained CaffeNet model...")

caffe.set_mode_cpu()

networks={
  "alexnet": ["bvlc_alexnet", "deploy.prototxt", "bvlc_alexnet.caffemodel"], 
  "caffenet" : ["bvlc_reference_caffenet", "deploy.prototxt", "bvlc_reference_caffenet.caffemodel"],
  "rcnn" : ["bvlc_reference_rcnn_ilsvrc13", "deploy.prototxt", "bvlc_reference_rcnn_ilsvrc13.caffemodel"], 
  "googlenet" : ["bvlc_googlenet", "deploy.prototxt", "bvlc_googlenet.caffemodel"],
  "flickr" : ["finetune_flickr_style", "deploy.prototxt", "finetune_flickr_style.caffemodel"],
  "CNN_S" : ["fd8800eeb36e276cd6f9", "VGG_CNN_S_deploy.prototxt", "VGG_CNN_S.caffemodel"],
  "CNN_M_2048" : [ "78047f3591446d1d7b91",  "VGG_CNN_M_2048_deploy.prototxt", "VGG_CNN_M_2048.caffemodel" ] ,
  "hybridCNN" : [ "places-CNN", "hybridCNN_deploy.prototxt", "hybridCNN_iter_700000.caffemodel"],
  "placesCNN" : [ "places-CNN", "places205CNN_deploy.prototxt", "places205CNN_iter_300000.caffemodel"],
  "VGG19layers" : ["3785162f95cd2d5fee77", "VGG_ILSVRC_19_layers_deploy.prototxt", "VGG_ILSVRC_19_layers.caffemodel"],
  "nin" : [ "nin_imagenet", "deploy.prototxt", "nin_imagenet.caffemodel"],
  "lenet" : [ "lenet", "lenet.prototxt", "lenet_iter_10000.caffemodel"],
  "convnet" : [ "convnet", "deploy.prototxt", "cifar10_full_iter_70000.caffemodel"]
}


results = []
presentLayer = 0

def loadNet(netString):
  
  aux = networks[netString]
  net = caffe.Net(caffe_root + 'models/%s/%s'%(aux[0], aux[1]),
                caffe_root + 'models/%s/%s'%(aux[0], aux[2]),
                caffe.TEST)
  return net 
# input preprocessing: 'data' is the name of the input blob == net.inputs[0]
#transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
#transformer.set_transpose('data', (2,0,1))
#transformer.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy').mean(1).mean(1)) # mean pixel
#transformer.set_raw_scale('data', 255)  # the reference model operates on images in [0,255] range instead of [0,1]
#transformer.set_channel_swap('data', (2,1,0))  # the reference model has channels in BGR order instead of RGB
#net.blobs['data'].reshape(1,3,227,227)
#net.blobs['data'].data[...] = transformer.preprocess('data', caffe.io.load_image(caffe_root + 'examples/images/cat.jpg'))
#out = net.forward()
#print("Predicted class is #{}.".format(out['prob'].argmax()))




def vis_square(data, padsize=1, padval=0):
    data -= data.min()
    data /= data.max()
    
    # force the number of filters to be square
    n = int(np.ceil(np.sqrt(data.shape[0])))
    padding = ((0, n ** 2 - data.shape[0]), (0, padsize), (0, padsize)) + ((0, 0),) * (data.ndim - 3)
    data = np.pad(data, padding, mode='constant', constant_values=(padval, padval))
    
    # tile the filters into an image
    data = data.reshape((n, n) + data.shape[1:]).transpose((0, 2, 1, 3) + tuple(range(4, data.ndim + 1)))
    data = data.reshape((n * data.shape[1], n * data.shape[3]) + data.shape[4:])
    
    plt.imshow(data)

def truncateString(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def limitPrec(n, k):
  aux = n * (np.power(2,k))
  aux = int(aux)
  return float(aux) / np.power(2,k)
  #return float(aux) / float(math.pow(10,k))

#vis_square(filters.transpose(0, 2, 3, 1))
#plt.show()
#print filters.transpose(0, 2, 3, 1).shape

def truncate(matrix, prec):
  dims = matrix.shape
#truncate the numbers
  for i in range(dims[0]):
    for c in range(dims[1]):
      for y in range(dims[2]):
        for x in range(dims[3]):
          matrix[i][c][y][x] = limitPrec(matrix[i][c][y][x], prec)
# Inter-filter similarity analysis
def interFilterPerPositionAnalysis(m):
  dims = m.shape
  aux = np.zeros(dims)
  uniqueValues = Set([])
  replicatedValues = Set([])
  replicatedValuesPerPosAux = Set([])
  replicatedValuesPerPos = []
  interFilterSimil=np.zeros((dims[0]))
  differentValuesPerPos = np.zeros(dims[1:])  # per filter elemetn, it stores how many different values there are taking into account all the filters
  positionsWithValueSomewhereElse = np.zeros((dims[0])) #counter per filter, it stores how many of the filter elements have the same value, at the same position somewhere else 
  positionsWithNonZeroValueSomewhereElse = np.zeros((dims[0]))
  positionsWithNonZeroValue = np.zeros((dims[0]))
  #for each input feature
  for c in range(dims[1]):
    for y in range(dims[2]):
      for x in range(dims[3]):
        count = 0
        replicatedValuesPerPosAux = Set([])
        #for each filter
        for i in range(dims[0]):
          if m[i][c][y][x]!=0:
	    positionsWithNonZeroValue[i] += 1
          count = 0
          if aux[i][c][y][x] == 0: #this value has not been seen at this position yet
	    differentValuesPerPos[c][y][x] += 1  #it stores how many different values there are per filter position
            aux[i][c][y][x] = 1   #we set the bit corresponding to the origin to not check it again
            for j in range(i+1,dims[0]):  #we explore the next filters
              if m[i][c][y][x] == m[j][c][y][x]:  
	        positionsWithValueSomewhereElse[j] += 1 #
	        if m[i][c][y][x] != 0: positionsWithNonZeroValueSomewhereElse[j] += 1 #
                count += 1
                aux[j][c][y][x] = 1   #to not check it again
          else:
            #we use count to differentiate those values that have been matched with a previous filter
            count = -1 
          if count > 0: 
            positionsWithValueSomewhereElse[i] += 1 #the one where the comparison started
	    if m[i][c][y][x] != 0: positionsWithNonZeroValueSomewhereElse[i] += 1 #
            replicatedValuesPerPosAux.add(m[i][c][y][x])
            replicatedValues.add(m[i][c][y][x])  #replicatedValues will contain all the values unique among the filters
            interFilterSimil[count] += 1   # histogram = how many times "count" filters had the same value
          elif count == 0:
            #This value only exists once among all the filters
            uniqueValues.add(m[i][c][y][x])
        replicatedValuesPerPos.append(len(replicatedValuesPerPosAux)) 
      
  totalFilterPixelsPerChannel = dims[0]  * dims[2] * dims[3]
  totalFilterElements = dims[1] * dims[2] * dims[3]

  #return positionsWithNonZeroValueSomewhereElse / positionsWithNonZeroValue
  #aux = positionsWithNonZeroValueSomewhereElse / positionsWithNonZeroValue
  aux = np.cumsum(positionsWithNonZeroValueSomewhereElse) / (dims[1]*dims[2]*dims[3]*dims[0])
  #print np.average(aux)
  return aux
  #print differentValuesPerPos
  print positionsWithValueSomewhereElse / float(totalFilterElements)
  print (positionsWithNonZeroValueSomewhereElse / positionsWithNonZeroValue) [2]
  print positionsWithNonZeroValueSomewhereElse[2] /  positionsWithNonZeroValue[2]

  cinterFilterSimil=[]
  for i in range(interFilterSimil.size): 
    cinterFilterSimil.append(interFilterSimil[i]*i)
  
 # print 'totalFilterPixelsPerChannel: ' + repr(totalFilterPixelsPerChannel)
  results[presentLayer].append(totalFilterPixelsPerChannel)
  #print 'total inter filter overlaps: ' 
  #for i in range(dims[1]):
  #  print repr(sum(cinterFilterSimil[i]))  + ' '      

  ratio = 0
  #for i in range(dims[1]):
  #  cumul 
  #cumul.append(np.cumsum(cinterFilterSimil[i]) / float(totalFilterPixelsPerChannel))
  
  ratio = np.sum(cinterFilterSimil)
  cinterFilterSimil = np.sum(cinterFilterSimil, 0)
  cumul = np.cumsum(cinterFilterSimil)
  cumul /= float(totalFilterPixelsPerChannel) *  float(dims[1])
 
  ratio = ratio / float(totalFilterPixelsPerChannel) / float(dims[1])
  return [interFilterSimil, cinterFilterSimil, ratio, cumul, len(uniqueValues), len(replicatedValues), max(replicatedValuesPerPos)]

# m = vector of vectors
def boxplot(m, labels, cad): 
  fig, ax1 = plt.subplots(figsize=(10,3))
  fig.canvas.set_window_title('Redundant Fraction')
  plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)

  bp = plt.boxplot(m, notch=0, sym='+', vert=1, whis=1.5)
  plt.setp(bp['boxes'], color='black')
  plt.setp(bp['whiskers'], color='black')
  plt.setp(bp['fliers'], color='red', marker='+')
  plt.savefig(cad)
  plt.show()

def linesplot(m, labels, cad):
  lens=[]
  a = drange(0,1,1/float(SAMPLES))
  print len(a)
  print len(m[0])
  print len(m[1])
  fig, axes = plt.subplots(nrows=3, ncols=len(m)/2, figsize=(24,7))
  i=0
  for x in range(len(m)/2):
    for y in range(2):
      if y==0 and x==0: axes[y,x].set_ylabel("Low precision")
      if y==1 and x==0: axes[y,x].set_ylabel("High precision")
      if x !=0: axes[y,x].set_yticklabels([])
      if y==0:  axes[y,x].set_xticklabels([]) 
      if y==0: axes[ y,x].set_title(labels[i])
      axes[y,x].set_yticks([0, .2, .4, .6, .8,1])
      axes[y,x].set_xticks([ .2, .4, .6, .8])
      axes[y,x].set_ylim(0,1)
      axes[y,x].grid(True)
      for layer in range(len(m[i])):
        axes[y,x].plot(a, m[i][layer][:SAMPLES])
      i+=1
  
  fig.subplots_adjust(hspace=0.3, wspace=0.05)
  fig.tight_layout()
  #plt.savefig("%s.pdf", cad)
  plt.show()

def compareFilters(a, b):
  dims = a.shape
  equal = 0
  for c in range(dims[0]):
    for i in range(dims[1]):
      for j in range(dims[2]):
        if a[c][i][j] == b[c][i][j]:
          equal += 1
  return equal # / float(dims[0]*dims[1]*dims[2])
    
def toInteger(a):
  return int(a*(1<<PRECISION))

#The x-axis is the number of weights sorted by the number of times they are shared. 
#100% is the total number of produc ts. 
#We want to be able to say that just x weights hence products ts can cover y of the total
def redundancyAnalysis(m):
  CHECK = False
  dims = m.shape
  vals = np.zeros((dims[1]*dims[2]*dims[3], (1<<PRECISION+1)))
  
  #if CHECK:
  aux = np.zeros(257)
  auxVal = np.zeros(257)

  index = 0
  for c in range(dims[1]):
    for x in range(dims[2]):
      for y in range(dims[3]):
        for i in range(dims[0]):
          if CHECK:
            if aux[ toInteger(m[i][c][x][y]) ] > 0:
              if m[i][c][x][y] != auxVal[  toInteger(m[i][c][x][y]) ]:
                print "ALARM"
            auxVal[ toInteger(m[i][c][x][y]) ] = m[i][c][x][y]
            aux[ toInteger(m[i][c][x][y]) ] += 1
          
          vals[index][ toInteger(m[i][c][x][y]) ] += 1;
        index += 1 # same value for all the filters
  vals = vals.flatten()
  vals = np.sort(vals)
  #print vals
  vals = np.trim_zeros(vals)
  vals -= 1
  vals = np.trim_zeros(vals)
  vals = vals[::-1]
  #print vals
  vals = np.cumsum(vals)
  vals /= dims[1]*dims[2]*dims[3]*dims[0]
  vals = sample(vals,SAMPLES)
  return vals
  #print vals

def drange(start, stop, step):
  r = start
  res = []
  while r < stop:
    res.append(r)
    r += step
  return res

def sample(m, n):
  step = len(m) / float(n)
  res = []
  for i in drange(0,len(m),step):
    res.append(m[i])
  return res
#####
# in: m - matrix containing the filters
# out: 
#   r: diagonal matrix containing the ratios of exact correspondance between pairs of filters at the same position
#  genRatio: average ratio of the previous measure
#  nextRatio: average ratio of value overlap between one filter and the next one
#
#  genSavings: 
#
def interFilterWholeAnalysis(m):
  dims = m.shape
  genRatio = 0
  nextRatio = 0
  genRatioN = 0
  nextRatioN = 0 
  r=np.zeros((dims[0], dims[0]))
  mx=np.zeros(dims[0])
  for fi in range(dims[0]):
    #print "FILTER" + repr(fi)
    for fj in range(fi+1, dims[0]):
      aux = compareFilters(m[fi], m[fj])
      r[fi][fj] = aux
      if fj==fi+1: 
        nextRatio += aux 
        nextRatioN += 1 
      genRatio += aux
      genRatioN += 1
      #print float(aux) / float(dims[3]*dims[1]*dims[2])
    mx[fi]=np.amax(r[fi]) # this is the maximum overlap per filter 
    mx[fi]/= float(dims[1]*dims[2]*dims[3])
  aux = nextRatio
  nextRatio = nextRatio / float(nextRatioN)
  genRatio = genRatio / float(genRatioN)
  print 'whole ' + repr(np.average(mx))
  
  return [r, genRatio, nextRatio, aux / float(dims[0]*dims[1]*dims[2]*dims[3]), mx]

# Inter-filter similarity analysis
def interFeatureAnalysis(m):
  dims = m.shape
  aux = np.zeros(dims)
  interFilterSimil=np.zeros((dims[0],dims[1]))
  for i in range(dims[0]):
    for y in range(dims[2]):
      for x in range(dims[3]):
        count = 0
        for c in range(dims[1]):
          count=0
          if aux[i][c][y][x] == 0:
            aux[i][c][y][x] = 1   #we set the bit corresponding to the origin to not check it again
            for d in range(c+1,dims[1]):  #we explore the next filters
              if m[i][c][y][x] == m[i][d][y][x]:  
                count += 1
                aux[i][d][y][x] = 1   #to not check it again
          if count > 0: interFilterSimil[i][count] += 1   # histogram = how many times "count" filters had the same value
      
  totalPixelsPerFilter = dims[1]  * dims[2] * dims[3]
  cinterFilterSimil=[]
  for r in range(dims[0]):
    cinterFilterSimil.append([])
    for i in range(interFilterSimil[r].size): 
      cinterFilterSimil[r].append(interFilterSimil[r][i]*i)
  
  print 'totalPixelsPerFilter: ' + repr(totalPixelsPerFilter)
  #print 'total inter filter overlaps: ' 
  #for i in range(dims[0]):
  #  print repr(sum(cinterFilterSimil[i]))  + ' '      
  ratio = 0
  aux = np.zeros(dims[1])
  cumul = np.cumsum(cinterFilterSimil)
  cumul /= float(totalPixelsPerFilter)

  for i in range(dims[0]):
    ratio += sum(cinterFilterSimil[i]) 
    for j in range(dims[1]):  #this loop is going to add the overlaps for all the filter at a particular feature
      aux[j] += cinterFilterSimil[i][j]
  
  ratio = ratio / float(totalPixelsPerFilter) / float(dims[0])
  #print sum(interFilterSimil)
  return [sum(interFilterSimil), aux, ratio, cumul]


def intraFilterAnalysis(m): 
  #non-contiguous intra-filter similarity analysis
  dims = m.shape
  aux = np.zeros(dims)
  intraFilterSimil = np.zeros((dims[1],dims[2]*dims[3]))
  aux = np.zeros(dims)
  for c in range(dims[1]):
    for i in range(dims[0]):
      for y in range(dims[2]):
        for x in range(dims[3]):
          count = 0
          if aux[i][c][y][x] == 0:
            aux[i][c][y][x] = 1   #we set the bit corresponding to the origin to not check it again
            for s in range(dims[2]): 
              for r in range(dims[3]):  # we explore the same row to look for the same valuF
                if aux[i][c][s][r]==0 and  m[i][c][y][x] == m[i][c][s][r]:
                  count += 1
                  aux[i][c][s][r] = 1   #to not check it again
          if count > 0: intraFilterSimil[c][count] += 1

  totalFilterPixelsPerChannel = dims[0]  * dims[2] * dims[3]                
  cintraFilterSimil=[]
  for r in range(3):
    cintraFilterSimil.append([])
    for i in range(intraFilterSimil[r].size):
      cintraFilterSimil[r].append(intraFilterSimil[r][i]*i)
   
  print 'total intra filter overlaps: ' + repr(sum(cintraFilterSimil[0]))  + ' ' + repr(sum(cintraFilterSimil[1])) + ' ' + repr(sum(cintraFilterSimil[2]))     
  ratio = (sum(cintraFilterSimil[0]) + sum(cintraFilterSimil[1]) + sum(cintraFilterSimil[2])) / float(totalFilterPixelsPerChannel) /3.0
  return [intraFilterSimil, cintraFilterSimil, ratio]

def printFilters(m, nameFile):
  with open('%s'%nameFile, 'w') as f:
    dims = m.shape
    aux = m.reshape((dims[0], dims[1], dims[2]*dims[3]))
    print aux.shape
    for i in range(dims[0]):
      f.write("\nfilter %d\n"%i)
      for c in range(dims[1]):
        #f.write("\nfeature %d\n"%c)
        for y in range(dims[2]*dims[3]):
          f.write("%f,"%aux[i][c][y])
        f.write("\n")
      
def zerosAnalysis(filters):
  dims = filters.shape
  print dims
  if len(dims) >3:
    avg = 0.0
    for i in range(dims[0]):
      total = 0
      zeros = 0
      for c in range(dims[1]):
        for y in range(dims[2]):
          for x in range(dims[3]):
            total += 1
            if filters[i][c][y][x]==0:
              zeros += 1
      aux = float(zeros) / float(total)
      #print aux
      avg += aux
    print 'AVERAGE ' + repr(avg / dims[0])

def generateInterIntraFigure(filters, cad):
  ###################################################################################33
  ##
  ##  TRUNCATE
  ##
  interFilterSimil, cinterFilterSimil, ratio, cumul = interFilterAnalysis(filters)
  print "Inter-filter ratio"
  print ratio
  fig = plt.figure()
  ax = fig.add_subplot(111)
  n = len(cinterFilterSimil)
  ind = np.arange(n)
  print filters.shape
  print ind.shape
  print cumul.shape
  width = 0.25
  ax.set_title('Similarities inter-filter per feature,%dbits'%(PRECISION))
  ax.text(n*0.7, max(cinterFilterSimil)*0.9, 'total inter-filter overlap: %.3f'%ratio, style='italic',
          bbox={'facecolor':'red', 'alpha':0.5, 'pad':10})
  rects1 = ax.bar(ind, cinterFilterSimil[:n], width, color='red')
  ax2 = ax.twinx()
  points  = ax2.plot(ind, cumul, "b.")
  

   
  
 # interFeatureSimil, cinterFeatureSimil, ratio = interFeatureAnalysis(filters)
 # print "Inter-feature ratio"
 # print ratio
 # n = len(cinterFeatureSimil)
 # ind = np.arange(n)
 # ax = fig.add_subplot(212)
 # ax.text(n*0.7, max(cinterFeatureSimil)*0.9, 'total inter-feature overlap: %.3f'%ratio, style='italic',
 #         bbox={'facecolor':'red', 'alpha':0.5, 'pad':10})
 # width = 0.25
 # ax.set_title('Similarities inter-feature per filter,%dbits'%(PRECISION))
 # rects1 = ax.bar(ind, cinterFeatureSimil[:n], width, color='red')
  
  #aux, bins, patches = plt.hist(results[0], n, normed =0, histtype='step', cumulative=False)
  
  plt.savefig(cad)
  #plt.show()
  #vis_square(filter2.transpose(0, 2, 3, 1))
  #plt.show()
  
def generateInterFilterFigure(filters, cad, fun):
  interFilter, genRatio, nextRatio, savingsNextRatio, uniqueValues, replicatedValues, replicatedValuesPerPos  = fun(filters)
  results[presentLayer].append(uniqueValues)
  results[presentLayer].append(replicatedValues)
  results[presentLayer].append(replicatedValuesPerPos)
  #print "UNIQUE / REPLICATED / REPLICATED_POS " + repr(uniqueValues) + " " + repr(replicatedValues) + " " + repr(replicatedValuesPerPos)
 
  #fig, ax = plt.subplots()  
  
  #ax.pcolor(interFilter,cmap=plt.cm.Reds,edgecolors='k')
  #ax.text(filters.shape[0]*0.1, filters.shape[0]*0.9, 'savings using next:%.3f'%(savingsNextRatio), style='italic',
  #        bbox={'facecolor':'red', 'alpha':0.7, 'pad':10})
  results[presentLayer].append(nextRatio)
  #print 'tot Avg: %.3f, next avg:%.3f, savings using next:%.3f'%(genRatio, nextRatio, savingsNextRatio)
  
  #plt.savefig(cad)
  #plt.show()


###################################################################################33
##
## MAIN 
##
dirFigs = "fraction-filters"
PRECISION= 8
SAMPLES=1000
res = []
res2=[]
precWeights={"alexnet":[7,8],  "convnet":[7,8], "nin":[8,9], "VGG19layers":[9,10], "googlenet":[7,8],  "CNN_S":[9,10],"CNN_M_2048":[9,10]}
precData={"alexnet":[7,8],  "convnet":[7,8], "nin":[8,9], "VGG19layers":[9,10], "googlenet":[7,8],  "CNN_S":[9,10],"CNN_M_2048":[9,10]}
networkPrecision=1

labels=[]
#for network in [ "alexnet"]: #, "caffenet", "flickr", "rcnn", "googlenet", "VGG19layers", "hybridCNN", "placesCNN", "CNN_S" , "CNN_M_2048"]:
#for network in ["CNN_S" , "CNN_M_2048", "nin"]:
#for network,e in enumerate(networks) :
#for network in [ "alexnet", "convnet", "nin",  "VGG19layers", "googlenet", "CNN_S" , "CNN_M_2048"]:
for network in [ "alexnet"]:
  #PRECISION = precisions[network][networkPrecision] 
  #if network == "VGG19layers":
    #PRECISION = 9
  
  net = loadNet(network)
  print network
  print net.params
  for prec in [0,1]:
    res=[]
    i = -1
    PRECISION = precisions[network][prec]
    for layer in net.layers:
       
      i+=1
      #print getattr(layer)    
  #for j in net.layers
      #print repr(net.layers[0])
      #print type(layer)
      #if 'conv' in layer:
      if  layer.type == 'Convolution':
        layer= net._layer_names[i]
        print layer
        results.append([])
        results[presentLayer].append(layer)
        filters = net.params[layer][0].data
        dims = filters.shape
        results[presentLayer].append(dims)
  
    #printFilters(filters, "%s-filters-32bit.csv"%layer)
        truncate(filters, PRECISION)
        layerPlain = layer.replace("/", "-")
        #printFilters(filters, "%s_%s.csv"%(network, layerPlain))
    #plt.hist(filters.flatten())
        
        #totalNonZero = np.count_nonzero(filters)
        #print "zero elements" + repr(filters.size - totalNonZero) + " zero Ratio: " + repr(1.0 - float(totalNonZero)/float(filters.size))
        #results[presentLayer].append(1.0 - float(totalNonZero)/float(filters.size))
        if not os.path.exists(dirFigs):
          os.makedirs(dirFigs) 
  
        #cad = "%s/whole-%s-%s-%dbits.png"%(dirFigs,network, layerPlain, PRECISION)
        #zerosAnalysis(filters)
        #generateInterIntraFigure(filters, "%s/%s-%s-%dbits.png"%(dirFigs,network, layerPlain, PRECISION))
        #interFilterWholeAnalysis(filters)
        #generateInterFilterWholeFigure(filters, cad)
        cad = "values/redundancy-%dsamples-%s-%s-%dbits"%(SAMPLES, network, layerPlain, PRECISION)
        #np.savetxt("%s.gz"%cad, interFilterPerPositionAnalysis(filters))
        #aux = redundancyAnalysis(filters)
        #np.savetxt("%s.gz"%cad, aux)
        #res.append(aux)
        #np.savetxt("%s.gz"%cad, redundancyAnalysis(filters))
        #interFilterPerPositionAnalysis(filters)
        res.append(np.loadtxt("%s.gz"%cad))
        #res.append(redundancyAnalysis(filters))
        #generateInterFilterFigure(filters, cad, interFilterPerPositionAnalysis)
        presentLayer+=1
        #print itemfreq(filters)
        #plt.plot( bins[:-1], np.cumsum(hist) )
        #plt.show()
        #print results
        results = []
    labels.append(network)
    #cad = "%s/%s-%dbits.png"%(dirFigs,network, PRECISION)
    print "====================="
    res2.append(res)
cad = "%s/curves-low.pdf"%(dirFigs)
#boxplot(res, labels, cad)
linesplot(res2, labels, cad)
