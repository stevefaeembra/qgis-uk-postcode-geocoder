'''
Created on 3 Apr 2015
Example code to expands out the compact binary representation
@author: steven
'''

from struct import *
import time
import os.path

THISDIR = os.path.dirname(os.path.realpath(__file__))
FNAME= os.path.join(THISDIR,'..','ons_packed.bin')

def unpackpostcodes(fin):
    while True:
        lenn = unpack('B',fin.read(1))
        lenn = lenn[0]
        pcode = unpack('%ds' % int(lenn), fin.read(lenn))
        b1 = unpack('B',fin.read(1))
        b2 = unpack('B',fin.read(1))
        b3 = unpack('B',fin.read(1))
        eastings = (b1[0]<<16)|(b2[0]<<8)|(b3[0])
        b1 = unpack('B',fin.read(1))
        b2 = unpack('B',fin.read(1))
        b3 = unpack('B',fin.read(1))
        northings =  (b1[0]<<16)|(b2[0]<<8)|(b3[0])
        yield (pcode[0], eastings, northings)
    
tick = time.time()
ix = 0    
with open(FNAME,"r") as fi:
    try:
        for x in unpackpostcodes(fi):
            ix += 1
            print x
    except:
        pass
    
took = time.time()-tick
print 'Read back %d postcodes in %2.4f secs' % (ix,took)
        