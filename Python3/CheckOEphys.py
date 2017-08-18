#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 21:20:00 2017

@author: Abby
"""
import os
import numpy as np
import scipy.signal
import scipy.io
import time
import struct
from copy import deepcopy

# constants
NUM_HEADER_BYTES = 1024
SAMPLES_PER_RECORD = 1024
BYTES_PER_SAMPLE = 2
RECORD_SIZE = 4 + 8 + SAMPLES_PER_RECORD * BYTES_PER_SAMPLE + 10 # size of each continuous record in bytes
RECORD_MARKER = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 255])

# constants for pre-allocating matrices:
MAX_NUMBER_OF_SPIKES = int(1e6)
MAX_NUMBER_OF_RECORDS = int(1e6)
MAX_NUMBER_OF_EVENTS = int(1e6)

def checkFolder(folderpath,**kwargs):
    # load all continuous files in a folder
    print('reloaded')
    checks = { }
    gChannels = []

    # load all continuous files in a folder
    if 'channels' in kwargs.keys():
        if kwargs['channels'] == 'all':
            channels = _get_sorted_channels(folderpath)
        else:
            channels = kwargs['channels']
        filelist = ['100_CH'+x+'.continuous' for x in map(str,channels)]
    else:
        filelist = os.listdir(folderpath)

    t0 = time.time()
    numFiles = 0

    for i, f in enumerate(filelist):
        if '.continuous' in f:
            corrupt = checkContinuous(os.path.join(folderpath, f))
            checks[f.replace('.continuous','')] = corrupt
            numFiles += 1
            
            if corrupt ==0 and 'CH' in f:
                fstr = f.replace('.continuous','')
                gChannels.append([int(s) for s in fstr.split('CH')
                                  if s.isdigit()][0])
                
    print(''.join(('Avg. Load Time: ', str((time.time() - t0)/numFiles),' sec')))
    print(''.join(('Total Load Time: ', str((time.time() - t0)),' sec')))

    return checks, gChannels

def checkContinuous(filepath, dtype = float):

    assert dtype in (float, np.int16), \
      'Invalid data type specified for loadContinous, valid types are float and np.int16'

    print("Loading continuous data...")
    print(filepath)
    
#    ch = { }
    corrupt = 0;
    #read in the data
    f = open(filepath,'rb')

    fileLength = os.fstat(f.fileno()).st_size

    # calculate number of samples
    recordBytes = fileLength - NUM_HEADER_BYTES
    if  recordBytes % RECORD_SIZE != 0:
        corrupt = 1
        print("File size is not consistent with a continuous file: may be corrupt")
    nrec = recordBytes // RECORD_SIZE
    #nsamp = nrec * SAMPLES_PER_RECORD
    # pre-allocate samples
    #samples = np.zeros(nsamp, dtype)
    timestamps = np.zeros(nrec)
    recordingNumbers = np.zeros(nrec)
    #indices = np.arange(0, nsamp + 1, SAMPLES_PER_RECORD, np.dtype(np.int64))

    header = readHeader(f)

    recIndices = np.arange(0, nrec)

    for recordNumber in recIndices:

        timestamps[recordNumber] = np.fromfile(f,np.dtype('<i8'),1) # little-endian 64-bit signed integer
        N = np.fromfile(f,np.dtype('<u2'),1)[0] # little-endian 16-bit unsigned integer

        #print index

        if N != SAMPLES_PER_RECORD:
            corrupt = 1
            print('Found corrupted record in block ' + str(recordNumber))
            break
        
        recordingNumbers[recordNumber] = (np.fromfile(f,np.dtype('>u2'),1)) # big-endian 16-bit unsigned integer

        if dtype == float: # Convert data to float array and convert bits to voltage.
            data = np.fromfile(f,np.dtype('>i2'),N) * float(header['bitVolts']) # big-endian 16-bit signed integer, multiplied by bitVolts
        else:  # Keep data in signed 16 bit integer format.
            data = np.fromfile(f,np.dtype('>i2'),N)  # big-endian 16-bit signed integer
#        samples[indices[recordNumber]:indices[recordNumber+1]] = data
#
        marker = f.read(10) # dump

    #print recordNumber
    #print index

#    ch['header'] = header
#    ch['timestamps'] = timestamps
#    ch['data'] = samples  # OR use downsample(samples,1), to save space
#    ch['recordingNumber'] = recordingNumbers
    f.close()
    return corrupt

def readHeader(f):
    header = { }
    h = f.read(1024).decode().replace('\n','').replace('header.','')
    for i,item in enumerate(h.split(';')):
        if '=' in item:
            header[item.split(' = ')[0]] = item.split(' = ')[1]
    return header

def _get_sorted_channels(folderpath):
    return sorted([int(f.split('_CH')[1].split('.')[0]) for f in os.listdir(folderpath)
                    if '.continuous' in f and '_CH' in f])