#!/usr/bin/python
###################################################
# Response surface interpolator from PSUADE
#==================================================
# This file contains information for interpolation
# using response surface. Follow the steps below:
#  1. move this file to *.py file (e.g. interpolate.py)
#  2. make sure the first line points to your Python
#  3. prepare your new sample points to be interpolated
#     in a text file (e.g. infile) having the format below:
#    <number of sample points M> <number of inputs n>
#    1 input1 input2 ...inputn
#    2 input1 input2 ...inputn
#    ....
#    M input1 input2 ...inputn
#  4. run: interpolate.py infile outfile
#     where <outfile> will have the interpolated values.
#==================================================
import sys
import string
import math

#==================================================
# Regression interpolation
#==================================================
###################################################
# Function to get input data from PSUADE-generated
# parameter files (standard format, do not change).
# The return data will contain the inputs values.
#==================================================
format = 0
def getInputData(inFileName):
   inFile  = open(inFileName, 'r')
   lineIn  = inFile.readline()
   nCols   = lineIn.split()
   if len(nCols) == 1:
     format  = 1
     nInputs = eval(nCols[0])
     inData  = (nInputs) * [0]
     for ind in range(nInputs):
       lineIn = inFile.readline()
       nCols  = lineIn.split()
       inData[ind] = eval(nCols[0])
   else:
     format  = 2
     nSamp   = eval(nCols[0])
     nInputs = eval(nCols[1])
     inData  = (nSamp * nInputs) * [0]
     for cnt in range(nSamp):
       lineIn = inFile.readline()
       nCols  = lineIn.split()
       for ind in range(nInputs):
         inData[cnt*nInputs+ind] = eval(nCols[ind+1])
   inFile.close()
   return inData
###################################################
# Function to generate output file
# This function writes the output data (which should
# have been generated in outData) to the PSUADE-based
# output file.
#==================================================
def genOutputFile(outFileName, outData):
   if format == 1:
      nLeng = len(outData)
      for ind in range(nLeng):
         outfile.write("%e " % outData[ind])
   else:
      nLeng = len(outData) / 2
      nLeng = math.ceil(nLeng)
      outfile = open(outFileName, 'w')
      for ind in range(nLeng):
         outfile.write("%d " % (ind+1))
         outfile.write("%e " % outData[2*ind])
         outfile.write("%e \n" % outData[2*ind+1])
   outfile.close()
   return
###################################################
regCoefs = [
   8.4213366134975234e+05,
  -7.2010334185907177e+03,
  -2.8371705003996340e+04,
  -3.9838615319647644e+04,
  -4.8309753160079745e+04,
  -1.1863671925411936e+04 ]
invCovMat = [
 [   4.9080360292016220e+08,  -5.9604644775390625e-08,  -8.1956386566162109e-08,   0.0000000000000000e+00,  -2.0861625671386719e-07,  -1.9744038581848145e-07 ],
 [  -6.7055225372314453e-08,   5.0218726006321126e+08,   2.9802322387695312e-08,   0.0000000000000000e+00,   1.4901161193847656e-08,   0.0000000000000000e+00 ],
 [  -1.0430812835693359e-07,  -2.9802322387695312e-08,   5.2319442464530140e+08,   0.0000000000000000e+00,   5.9604644775390625e-08,   1.4901161193847656e-08 ],
 [   0.0000000000000000e+00,   0.0000000000000000e+00,   0.0000000000000000e+00,   5.2637501581335485e+08,   0.0000000000000000e+00,   0.0000000000000000e+00 ],
 [  -1.8626451492309570e-07,   2.9802322387695312e-08,   5.9604644775390625e-08,   0.0000000000000000e+00,   5.4560469172877252e+08,   1.4901161193847656e-08 ],
 [  -1.8626451492309570e-07,  -2.2351741790771484e-08,  -1.4901161193847656e-08,   0.0000000000000000e+00,  -1.4901161193847656e-08,   5.8582131920861745e+08 ],
]
###################################################
# Regression interpolation function  
# X[0], X[1],   .. X[m-1]   - first point
# X[m], X[m+1], .. X[2*m-1] - second point
# ... 
#==================================================
def interpolate(X): 
  nSamp = int(len(X) / 5)
  Xt = 5 * [0.0]
  X2 = 6 * [0.0]
  Ys = 2 * nSamp * [0.0]
  for ss in range(nSamp) : 
    for ii in range(5) : 
      Xt[ii] = X[ss*5+ii]
    X2[0] = 1.0;
    X2[1] = (Xt[0] - -3.795593e-04) / 5.779225e+00;
    X2[2] = (Xt[1] - 1.541606e-04) / 5.779364e+00;
    X2[3] = (Xt[2] - 1.702648e-04) / 5.779224e+00;
    X2[4] = (Xt[3] - 8.304650e-05) / 5.779754e+00;
    X2[5] = (Xt[4] - 5.939995e-04) / 5.779825e+00;
    Y = regCoefs[0]
    Y = Y + regCoefs[1] * X2[1];
    Y = Y + regCoefs[2] * X2[2];
    Y = Y + regCoefs[3] * X2[3];
    Y = Y + regCoefs[4] * X2[4];
    Y = Y + regCoefs[5] * X2[5];
    Ys[ss*2] = Y * 1.000000e+00 + 0.000000e+00
    std = 0.0
    for jj in range(6): 
      dtmp = 0.0
      for kk in range(6): 
        dtmp = dtmp + invCovMat[jj][kk] * X2[kk]
      std = std + dtmp * X2[jj]
    Ys[ss*2+1] = math.sqrt(std)
  return Ys
###################################################
# main program
#==================================================
infileName  = sys.argv[1]
outfileName = sys.argv[2]
inputs = getInputData(infileName)
outputs = interpolate(inputs)
genOutputFile(outfileName, outputs)
###################################################
