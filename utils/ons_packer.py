'''
Created on 3 Apr 2015
Packs ONS download into a minimised binary format
You can download latest at https://geoportal.statistics.gov.uk/geoportal/catalog/main/home.page

LEN    1 byte   Length of packed postcode (upper case, all spaces removed)
                eg AB12 1PY -> AB121PY = 7
                this will be 6,7 or 8 chars
TXT    N bytes  ASCII postcode, length determined from LEN
EAST   3 bytes  Eastings 
NOR    3 bytes  Northings 

@author: steven
'''

import csv
from struct import *
import re
import os.path

'''
where you downloaded ONS data to
'''

FNAME='/home/steven/infoviz2/uk postcodes/ONSPD_NOV_2014_UK.csv'

THISDIR = os.path.dirname(os.path.realpath(__file__))
OFNAME= os.path.join(THISDIR,'..','ons-packed.bin')

def packpostcode(pcode, eastings, northings):
    '''
    pack into minimal binary representation
    '''
    lenn = len(pcode)
    east1 = (eastings & 0xFF0000)>>16
    east2 = (eastings & 0xFF00)>>8
    east3 = (eastings & 0xFF)
    north1 = (northings & 0xFF0000)>>16
    north2 = (northings & 0xFF00)>>8
    north3 = (northings & 0xFF)
    p = pack('B%dsBBBBBB' % lenn,lenn,pcode,east1,east2,east3,north1,north2,north3)
    return p



dic={}
with open(FNAME,'r') as fi:
    with open(OFNAME,'wb') as fo:
        rdr = csv.reader(fi,delimiter=',')
        ix = 0
        nongeo = 0
        for line in rdr:
            try:
                pcode = line[0]
                pcode = pcode.upper()
                pcode = re.sub("\s+","",pcode)
                eastings = int(line[9])
                northings = int(line[10])
                fo.write(packpostcode(pcode,eastings,northings))
            except:
                # drop non-geographic (missing coords)
                fo.write(packpostcode(pcode,0,0))
                nongeo += 1
            ix += 1
            if ix%100000 == 0:
                print ix
                
print "Finished"
print "%d postcodes" % ix
print "%d non-geo postcodes" % nongeo