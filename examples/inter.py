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
import compute
import pdb
plt.rcParams['figure.figsize'] = (10, 10)
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

import os
if not os.path.isfile(caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'):
    print("Downloading pre-trained CaffeNet model...")

caffe.set_mode_cpu()



net = caffe.Net(caffe_root + 'models/bvlc_reference_caffenet/deploy.prototxt',
                caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel',
                caffe.TEST)


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

def limitPrec(n, k):
  aux = n * (np.power(2,k))
  aux = int(aux)
  return float(aux) / np.power(2,k)
  #return float(aux) / float(math.pow(10,k))

#vis_square(filters.transpose(0, 2, 3, 1))
#plt.show()
#print filters.transpose(0, 2, 3, 1).shape

def truncateMatrix(matrix, prec):
  dims = matrix.shape
#truncate the numbers
  for i in range(dims[0]):
    for c in range(dims[1]):
      for y in range(dims[2]):
        for x in range(dims[3]):
          matrix[i][c][y][x] = limitPrec(matrix[i][c][y][x], prec)

def zeroesAnalysis(m):
  print m.shape
  print 'total elements: ' + repr(m.size)
  print 'total zero elements: ' + repr(m.size - np.count_nonzero(m))
  print 'ratio of zero elements: ' + repr(float((m.size - np.count_nonzero(m))) / m.size)


# input preprocessing: 'data' is the name of the input blob == net.inputs[0]
transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2,0,1))
transformer.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy').mean(1).mean(1)) # mean pixel
transformer.set_raw_scale('data', 255)  # the reference model operates on images in [0,255] range instead of [0,1]
transformer.set_channel_swap('data', (2,1,0))  # the reference model has channels in BGR order instead of RGB

net.blobs['data'].data[...] = transformer.preprocess('data', caffe.io.load_image(caffe_root + 'examples/images/cat.jpg'))
out = net.forward()
print("Predicted class is #{}.".format(out['prob'].argmax()))

#plt.imshow(transformer.deprocess('data', net.blobs['data'].data[0]))


print 'Applying conv1'
aux = compute.computeConvolutionalLayer(net.blobs['data'].data[0], net.params['conv1'], 4, 0, 1)

print 'Applying ReLU1'
aux = compute.computeReLULayer(aux)
print aux.shape
#for i in range(aux.shape[0]):
#  for y in range(aux.shape[1]):
#    for x in range(aux.shape[2]):
#      if 
print 'Applying pool1'
aux = compute.computeMaxPoolLayer(aux, 3, 2, 0)
print aux.shape
print np.allclose(net.blobs['pool1'].data[0], aux, atol=1e-3)
print 'Applying LRN1'
aux = compute.computeLRNLayer(aux, 5, 0.0001, 0.75)
print aux.shape
print np.allclose(net.blobs['norm1'].data[0], aux, atol=1e-4)

print 'Applying conv2'
aux = compute.computeConvolutionalLayer(aux, net.params['conv2'], 1, 2, 2)
print 'Applying ReLU2' 
aux = compute.computeReLULayer(aux) 
print np.allclose(net.blobs['conv2'].data[0], aux, atol=1e-3)
print 'Applying pool2'
aux = compute.computeMaxPoolLayer(aux, 3, 2, 0) 
print 'Applying LRN2' 
aux = compute.computeLRNLayer(aux, 5, 0.0001, 0.75) 
print aux.shape

print 'Applying conv3'
aux = compute.computeConvolutionalLayer(aux, net.params['conv3'], 1, 1, 1) 
print 'Applying ReLU3' 
aux = compute.computeReLULayer(aux) 
print aux.shape

print 'Applying conv4'
aux = compute.computeConvolutionalLayer(aux, net.params['conv4'], 1, 1, 2) 
print 'Applying ReLU4'
aux = compute.computeReLULayer(aux)
print aux.shape

print 'Applying conv5'
aux = compute.computeConvolutionalLayer(aux, net.params['conv5'], 1, 1, 2)
print 'Applying ReLU5'
aux = compute.computeReLULayer(aux) 
print 'Applying pool5'
aux = compute.computeMaxPoolLayer(aux, 3, 2, 0)  

print 'Applying FC6'
aux = compute.computeFullyConnected(aux, net.params['fc6'])
print aux.shape
print 'Applying ReLU6'
aux = compute.computeReLULayer(aux) 
aux = compute.computeDropoutLayer(aux, 0.5)

print 'Applying FC7'
aux = compute.computeFullyConnected(aux, net.params['fc7'])
aux = compute.computeReLULayer(aux)   
aux = compute.computeDropoutLayer(aux, 0.5)  

print 'Applying FC8'
aux = compute.computeFullyConnected(aux, net.params['fc8']) 
aux = compute.computeSoftmaxLayer(aux)
   
print aux
print net.blobs['prob'].data[0]
print np.allclose(net.blobs['prob'].data[0], aux, atol=1e-3) 

imagenet_labels_filename = caffe_root + 'data/ilsvrc12/synset_words.txt'
labels = np.loadtxt(imagenet_labels_filename, str, delimiter='\t')

# sort top k predictions from softmax output
top_k = net.blobs['prob'].data[0].flatten().argsort()[-1:-6:-1]
print labels[top_k]
top_k = aux.flatten().argsort()[-1:-6:-1] 
print labels[top_k] 

print aux.shape


sys.exit(0)


i=0
layers=['conv1', 'conv2','pool2', 'conv3', 'conv4', 'conv5']
precision = [10, 8, 8, 8, 8]
for layerIt in net.layers:
  layer= net._layer_names[i]
  print '-------------------------------------'
  print layer
  print 'DATA'
  feat = net.blobs[layer]
  zeroesAnalysis(feat)
  #print 'FILTERS'
  #zeroesAnalysis(net.params[layer][0].data)

  #truncate data
  #truncate(net.blobs[layer].data, precision[i])
  #truncate filter weights
  #truncate(net.params[layer][0].data, 8)
  i+=1


