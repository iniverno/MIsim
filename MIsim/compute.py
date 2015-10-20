##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################



import chunk
import numpy as np
import math 


# in:
# 	data : numpy 3D ndarray of dimensions i * Wx * Wy, i=# input features, Wx=Wy= size of input
#	filters: a list with two elements, we will use the field "data" of both, 
#		filters[0].data = numpy 4D ndarray  of dimensions N * i * Fx * Fy with the filter values
#		filters[1].data = numpy 1D vector with the N biases 
#		N = # filters, Fx=Fy= filter size
 

def computeConvolutionalLayer(data, filters, stride, padding, group):
  weights = filters[0].data
  biases  = filters[1].data
  N	  = weights.shape[0]
  i	  = weights.shape[1]
  Fx	  = weights.shape[2]
  Fy	  = weights.shape[3]

  Ix 	  = data.shape[1]
  Iy	  = data.shape[2]


  if padding != 0:
    data = adjustDataPadding(data, padding)
    Ix      = data.shape[1]
    Iy      = data.shape[2]


  assert weights.shape[1]*group==data.shape[0], "#filters (%d) is not equal to #input features (%d)" %(weights.shape[1], data.shape[0])  
  assert Ix==Iy, "Input width (%d) is not equal to Input height (%d)" %(data.shape[1], data.shape[2]) 
  assert Fx==Fy, "Filter width (%d) is not equal to Filter height (%d)" %(Fx, Fy)


    
  output = np.zeros((N, (Ix-Fx)/stride+1, (Iy-Fy)/stride+1))
  outPosX = 0
  for posInputX in range(0, Ix-Fx+1, stride):
    outPosY = 0
    print posInputX
    for posInputY in range(0, Iy-Fy+1, stride):
      for cntFilter in range(N): #for each filter we are going to calculate the convolution of the filter at the particular x,y position 
        # This implementation will work as long as group is 1 or 2, IT WON'T WORK FOR OTHER VALUES Of GROUP
        if cntFilter < N/group: 
          output[cntFilter, outPosY, outPosX]  = computeWindow(weights[cntFilter], data[:(data.shape[0]/group), posInputY:posInputY+Fy, posInputX:posInputX+Fx])
        else:
          output[cntFilter, outPosY, outPosX]  = computeWindow(weights[cntFilter], data[(data.shape[0]/group):, posInputY:posInputY+Fy, posInputX:posInputX+Fx])
        
        output[cntFilter, outPosY, outPosX] += biases[cntFilter]
      outPosY += 1
    outPosX += 1

  return output


def computeWindow(filter, data):
  return np.sum(filter*data)


# this is simply an implementation of the previous function but using loops
def computeWindowLoops(filter, data):
  aux = 0
  for posFilterX in range(filter.shape[1]):
    for posFilterY in range(filter.shape[2]):
      for posFilterI in range(filter.shape[0]):
        aux += filter[posFilterI][posFilterX][posFilterY] * \
               data[posFilterI][posFilterX][posFilterY]
  return aux

def adjustDataPadding(data, padding):
  assert padding != 0, "Padding is zero"
  aux = np.zeros((data.shape[0], data.shape[1] + 2*padding, data.shape[2] + 2*padding))
  aux[:, padding:-padding, padding:-padding] = data
  return aux

def computeMaxPoolLayer(data, filterSize, stride, padding):
  if padding !=0: adjustPadding(data, padding)
  
  Ix = data.shape[1]
  Iy = data.shape[2]
  output = np.zeros((data.shape[0], (Ix-filterSize)/stride+1, (Iy-filterSize)/stride+1))
  
  outPosX = 0
  for posInputX in range(0, Ix - filterSize + 1, stride):
    outPosY = 0
    for posInputY in range(0, Iy - filterSize + 1, stride):
      for cntFeature in range(0, data.shape[0]):
        output[cntFeature, outPosY, outPosX] = np.max(data[cntFeature, posInputY:posInputY+filterSize, posInputX:posInputX+filterSize])
      outPosY += 1
    outPosX +=1
  return output   


# It computes a Local Response Normalization Layer
# for each element in the data array, it uses an auxiliar function to compute the proper value
# return: a matrix with the values after applying the function in the input data
def computeLRNLayer(data, size, alpha, beta):
  aux = np.zeros(data.shape)
  for posX in range(data.shape[1]):
    for posY in range(data.shape[2]):
      for posI in range(data.shape[0]):
        aux[posI, posY, posX] = computePosLRN(data, posX, posY, posI, size, alpha, beta)
  return aux



# it computes the LocalResponse normalization at a particular position
# it is defined by the equation result = data[i,y,x] / pow(1+a/size*sum(data[i-2:i+2, y, x]), b)
# data: complete input data
# x,y,i: position
# size: number of positions in the i dimension to take into account
# a, b: paramemeters in the equation
def computePosLRN(data, x, y, i, size, a, b):
  value = 0.0
  for cnt in range(-(size/2), size/2 + 1):
    pos = i + cnt
    if pos >= 0 and pos < data.shape[0]:
      value += data[pos, y, x]**2
  value = math.pow((1 + a/float(size) * value), b)
  return data[i,y,x] / value  

def computeSoftmaxLayer(x):
    e_x = np.exp(x - np.max(x))
    out = e_x / e_x.sum()
    return out

def computeDropoutLayer(data, dropoutFactor):
  return data * dropoutFactor 

def computeReLULayer(data):
  
  aux = np.copy(data)
  for i,e in enumerate(aux.flat):
    if e<0: aux.flat[i] = 0
  return aux

  for posX in range(data.shape[1]):
    for posY in range(data.shape[2]):
      for posI in range(data.shape[0]):
        if data[posI, posY, posX] < 0: aux[posI, posY, posX] = 0.0
        else: aux[posI, posY, posX] = data[posI, posY, posX]
  return aux


def computeFullyConnected(data, filters):
  filters = filters[0].data
  aux = np.zeros((filters.shape[0]))
  for i in range(filters.shape[0]):
    aux[i] = np.sum(filters[i] * data.flatten())
  return aux
