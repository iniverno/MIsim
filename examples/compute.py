import chunk
import numpy as np
# in:
# 	data : numpy 3D ndarray of dimensions i * Wx * Wy, i=# input features, Wx=Wy= size of input
#	filters: a list with two elements, we will use the field "data" of both, 
#		filters[0].data = numpy 4D ndarray  of dimensions N * i * Fx * Fy with the filter values
#		filters[1].data = numpy 1D vector with the N biases 
#		N = # filters, Fx=Fy= filter size
 

def computeConvolutionalLayer(data, filters, stride, padding):
  weights = filters[0].data
  biases  = filters[1].data
  N	  = weights.shape[0]
  i	  = weights.shape[1]
  Fx	  = weights.shape[2]
  Fy	  = weights.shape[3]

  Ix 	  = data.shape[1]
  Iy	  = data.shape[2]


  if padding != 0:
    adjustDataPadding(data, padding)
    Ix      = data.shape[1]
    Iy      = data.shape[2]


  assert weights.shape[1]==data.shape[0], "#filters (%d) is not equal to #input features (%d)" %(weights.shape[1], data.shape[0])  
  assert Ix==Iy, "Input width (%d) is not equal to Input height (%d)" %(data.shape[1], data.shape[2]) 
  assert Fx==Fy, "Filter width (%d) is not equal to Filter height (%d)" %(Fx, Fy)


    
  output = np.zeros((N, Ix/stride+1, Iy/stride+1))
  outPosX = 0
  for posInputX in range(0, Ix-Fx, stride):
    outPosY = 0
    print posInputX
    for posInputY in range(0, Iy-Fy, stride):
      for cntFilter in range(N): #for each filter we are going to calculate the convolution of the filter at the particular x,y position 

        #output[cntFilter, outPosY, outPosX] 
        aux = computeWindow(weights[cntFilter], data[:, posInputY:posInputY+Fy, posInputX:posInputX+Fx])
        
        for posFilterX in range(Fx):
          for posFilterY in range(Fy): 
            for posFilterI in range(i):
              output[cntFilter, outPosY, outPosX] += weights[cntFilter][posFilterI][posFilterY][posFilterX] * \
                                                     data[posFilterI][posInputY + posFilterY][posInputX + posFilterX]
        print repr(cntFilter) + '  ' + repr(outPosY) + ' ' + repr(outPosX) + ' a:' + repr(aux) + ' ' + repr(output[cntFilter, outPosY, outPosX]) 
        output[cntFilter, outPosY, outPosX] += biases[cntFilter]
      outPosY += 1
    outPosX += 1

  return output


def computeWindow(filter, data):
  return np.sum(filter*data)

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
  aux[:, padding:, padding:] = data
  data = aux

def computeMaxPoolLayer(data, filterSize, stride, padding):
  if padding !=0: adjustPadding(data, padding)
  
  Ix = data.shape[1]
  Iy = data.shape[2]
  output = np.zeros((data.shape[0], Ix/stride+1, Iy/stride+1))
  
  outPosX = 0
  for posInputX in range(0, Ix - filterSize, stride):
    outPosY = 0
    for posInputY in range(0, Iy - filterSize, stride):
      for cntFeature in range(0, data.shape[0]):
        output[cntFeature, outPosY, outPosX] = np.max(data[cntFeature, posInputY:posInputY+filterSize, posInputX:posInputX+filterSize])
      outPosY += 1
    outPosX +=1
  return output   

def computeLRNLayer(data, size, alpha, beta):
  aux = np.zeros(data.shape)
  for posX in range(data.shape[1]):
    for posY in range(data.shape[2]):
      for posI in range(data.shape[0]):
        aux[posI, posY, posX] = computePosLRN(data, posX, posY, posI, size, alpha, beta)
  return aux

def computePosLRN(data, x, y, i, size, a, b):
  value = 0.0
  for cnt in range(-(size/2), size/2 + 1):
    pos = i + cnt
    if pos >= 0 and pos < data.shape[0]:
      value += data[pos, y, x]**2
  value = math.pow((1 + a/float(size) * value), b)
  return data[i,y,x] / value  

def computeReLULayer(data):
  aux = np.zeros(data.shape)
  for posX in range(data.shape[1]):
    for posY in range(data.shape[2]):
      for posI in range(data.shape[0]):
        if data[i, y, x] < 0: aux[i, y, x] = 0.0
        else: aux[i, y, x] = data[i, y, x]
  return aux



