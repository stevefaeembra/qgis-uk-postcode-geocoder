'''
Created on 3 Apr 2015
Packs OS CSV download into a minimised binary format
You can download latest at 
http://www.ordnancesurvey.co.uk/business-and-government/products/code-point-open.html

OS provide multiple CSVs, one per postcode region (e.g. ab.csv for aberdeen)

Extract all the csvs you want to their own directory, this script will go through each .csv in the path you
specify below.

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
import glob 

'''
where you downloaded OS Open Code Point data to (a directory of csv files)
'''

FNAME='/home/steven/infoviz2/uk postcodes/open code point'

THISDIR = os.path.dirname(os.path.realpath(__file__))
OFNAME= os.path.join(THISDIR,'..','os_packed.bin')

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
g = glob.glob(os.path.join(FNAME,'*.csv'))
ix = 0
nongeo = 0
with open(OFNAME,'wb') as fo:    
    for filename in g:
        with open(os.path.join(FNAME,filename),'r') as fi:
            rdr = csv.reader(fi,delimiter=',')
            for line in rdr:
                try:
                    pcode = line[0]
                    pcode = pcode.upper()
                    pcode = re.sub("\s+","",pcode)
                    eastings = int(line[2])
                    northings = int(line[3])
                    fo.write(packpostcode(pcode,eastings,northings))
                except:
                    # drop non-geographic (missing coords)
                    fo.write(packpostcode(pcode,0,0))
                    nongeo += 1
                ix += 1
        print "Processed %s, seen %d postcodes" % (filename,ix)

                
print "Finished"
print "%d postcodes" % ix
print "%d non-geo postcodes" % nongeo
print "%d postcodes" % ix
print "%d non-geo postcodes" % nongeo