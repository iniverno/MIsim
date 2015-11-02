from collections import deque
from sets import Set
import numpy as np

# request = [cycle, type, address, size, ready]
# some asumptions:
# the word is as big as bytesCyclePort
# same type of requests to the same address are group together

class SimpleMemory:
  class Request:
    def __init__(self, addr, typeReq, size, requestor=[], data=[]):
      self.addr = addr
      self.typeReq = typeReq # 0: read, 1: write
      self.size = size
      self.data = data
      self.requestors = Set(requestor)
    
  def __init__(self, system, size, latency, nPorts, bytesCyclePort):
    self.system = system
    self.latency = latency
    self.nPorts = nPorts
    self.beingServed = []*nPorts
    self.reqsQ = deque()
    self.data = np.zeros((size))

  def cycle(self):
    #if there is ports available and requests waiting
    if len(self.beingServed) < self.nPorts:
      for i in range(self.nPorts - self.beingServed):
        if not self.reqsQ.empty():
          self.beingServed.append(self.reqsQ.get())

    if len(self.beingServed) > 0:
      auxBeingServed = []
      for req in self.beingServed:
        req.size -= self.bytesCyclePort
        if req.size <= 0:
          #read
          if req.typeReq==0:
            for requestor in req.requestors:
              requestor(req.address, self.data[address : address + req.size])
          #write
          else:
            self.data[req.address : req.address + req.size] = req.data
        else:
          auxBeingServed.append(req)
      req.beingServed = auxBeingServe
 
      if len(self.beingServed) > 0 or len(self.reqsQ) > 0:
        self.system.schedule(self)
  
  def write(self, address, data):
    auxReq = self.Request(address, 1, data.size, data = data)
    self.reqsQ.append(auxReq)
    self.system.schedule(self)

  def read(self, address, size, requestor):
    present = False
    for r in self.reqsQ:
      if r.address == address and r.typeReq == 0:
        self.requestors.add(requestor)
        present = True
    if not present:
      auxReq = self.Request(address, 0, size, requestor = requestor) 
      self.reqsQ.append(auxReq)
      self.system.schedule(self)




