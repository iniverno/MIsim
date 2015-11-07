##################################################################################3
#
#      Jorge Albericio, 2015
#      jorge@ece.utoronto.ca
#
##################################################################################

import options as op
from collections import deque
from sets import Set
import numpy as np
import options as op

# request = [cycle, type, address, size, ready]
# some asumptions:
# the word is as big as bytesCyclePort
# same type of requests to the same address are group together

class SimpleMemory:
  class Request:
    def __init__(self, addr, typeReq, size, requestor=[], data=[], final=False):
      self.addr = addr
      self.typeReq = typeReq # 0: read, 1: write
      self.size = size
      self.left = size
      self.data = data
      self.final = final
      self.requestors = Set([requestor])
    
  def __init__(self, system, size, nPorts, bytesCyclePort):
    self.VERBOSE = op.verboseMemory
    self.system = system
    self.nPorts = nPorts
    self.beingServed = []*nPorts
    self.reqsQ = deque()
    self.data = np.zeros((size))
    self.bytesCyclePort = bytesCyclePort

##################################################################################
### Issue requests if there are available ports
### 
##################################################################################
 
  def cycle(self):
    #if there is ports available and requests waiting
    if self.VERBOSE: print "len beingServed:%d, nports: %d"%(len(self.beingServed), self.nPorts)
    if len(self.beingServed) < self.nPorts:
      for i in range(self.nPorts - len(self.beingServed)):
        if len(self.reqsQ) > 0:
          self.beingServed.append(self.reqsQ.popleft())
    
    if len(self.beingServed) > 0:
      auxBeingServed = []
      for req in self.beingServed:
        req.left -= self.bytesCyclePort
        if req.left <= 0:
          #read
          if req.typeReq==0:
            if self.VERBOSE: print "simpleMemory serving read to ", req.addr, ", ", len(req.requestors), " requestors queue:", len(self.reqsQ)
            for requestor in req.requestors:
            
              requestor(req.addr, self.data[req.addr : req.addr + req.size], req.final)
          #write
          else:
            self.data[req.address : req.address + req.size] = req.data
        else:
          if self.VERBOSE: print "reintroduced ", req.addr, " ", req.left, " ", len(self.reqsQ) 
          auxBeingServed.append(req)
      self.beingServed = auxBeingServed
      if self.VERBOSE: print "SimpleMemory beingServed: ", len(self.beingServed )
      
      if len(self.beingServed) > 0 or len(self.reqsQ) > 0:
        self.system.schedule(self)

##################################################################################
### adds request to reqsQ 
##################################################################################
  
  def write(self, address, data):
    auxReq = self.Request(address, 1, data.size, data = data)
    self.reqsQ.append(auxReq)
    self.system.schedule(self)

##################################################################################
### adds request to reqsQ, reads can have multiple units requesting the same 
### word
##################################################################################
 
  def read(self, address, size, requestor, final=False):
    if self.VERBOSE: 
      print "SimpleMemory.read address:", address, " size:", size 
    present = False
    for r in self.reqsQ:
      if r.addr == address and r.typeReq == 0: # typeReq = 0 = read
        r.requestors.add(requestor)
        present = True
    if not present:
      auxReq = self.Request(address, 0, size, requestor = requestor, final = final) 
      self.reqsQ.append(auxReq)
    self.system.schedule(self)
    if self.VERBOSE: print "queue: ",len(self.reqsQ) 

##################################################################################
### write to memory directly, bypassing the reqsQ
##################################################################################
 
  def magicWrite(self, address, data):
    for i,e in enumerate(data):
      self.data[address + i] = e


