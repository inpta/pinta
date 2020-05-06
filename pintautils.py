#!/usr/bin/python3
""" Generate and execute commands to reduce the raw uGMRT data into psrfits format.

    Original developer:  Abhimanyu Susobhanan

    Contributing developer: Yogesh Maan

    (included appropriate modules and commands to rfiClean the raw-gmrt-data and
     then generate a rfiCleaned fits file as well.  -- yogesh, July 28)
"""


import shutil
import sys
import os
import numpy as np
import parse
import astropy.time as astrotime
import getopt
import time

def touch_file(fname):
    with open(fname, 'w'):
        os.utime(fname, None)

def check_program(program):
    print("Checking for %s..."%program, end=" ")
    program_found = shutil.which(program) is not None
    if program_found:
        print("OK...")
    else:
        print("Not found... Quitting...")
    return program_found

def check_dir(folder):
    print('Checking directory %s for permissions...'%folder, end=" ")
    if not os.access(folder, os.F_OK):
        print("%s does not exist... Quitting..."%folder)
        return False
    elif not os.path.isdir(folder):
        print("%s is not a directory... Quitting..."%folder)
        return False
    elif not os.access(folder, os.R_OK):
        print("%s not readable... Quitting..."%folder)
        return False
    elif not os.access(folder, os.W_OK):
        print("%s not writable... Quitting..."%folder)
        return False
    else:
        print("OK... ")
        return True

def check_read_dir(folder):
    print('Checking directory %s for permissions...'%folder, end=" ")
    if not os.access(folder, os.F_OK):
        print("%s does not exist... Quitting..."%folder)
        return False
    elif not os.path.isdir(folder):
        print("%s is not a directory... Quitting..."%folder)
        return False
    elif not os.access(folder, os.R_OK):
        print("%s not readable... Quitting..."%folder)
        return False
    else:
        print("OK... ")
        return True

def check_input_file(file_path):
    print('Checking file %s for permissions...'%file_path, end=' ')
    if not os.access(file_path, os.F_OK):
        print("%s does not exist... Quitting..."%file_path)
        return False
    elif not os.path.isfile(file_path):
        print("%s is not a file... Quitting..."%file_path)
        return False
    elif not os.access(file_path, os.R_OK):
        print("%s not readable... Quitting..."%file_path)
        return False
    else:
        print("OK... ")
        return True

def process_timestamp(timestamp_file_name):
    timestamp_file = open(timestamp_file_name,'r')
    timestamp_file_lines = timestamp_file.readlines()
    timestr = parse.parse("IST Time: {}\n",timestamp_file_lines[1])[0]
    datestr = parse.parse("Date: {}\n",timestamp_file_lines[2])[0]
    timestamp_file.close()
    day,month,year = parse.parse("{}:{}:{}",datestr)
    datetime_IST = "%s-%s-%sT%s"%(year,month,day,timestr)

    datetime = astrotime.Time(datetime_IST, format='isot', scale='utc')
    IST_diff = astrotime.TimeDelta(3600*5.5, format='sec')    

    return (datetime-IST_diff).mjd

def fetch_f0(parfile_name):
    f0 = -10.0
    with open(parfile_name, 'r') as par_file:
        for cnt, line in enumerate(par_file):
            if f0<0.0:
                try:
                    thestr = parse.parse("F0 {}\n",line)[0]
                    #print ("found in line %s \n "%line)
                    f0 = float(thestr.split()[0])
                    #print ("fetched F0 :  %f \n "%f0)
                except:
                    pass #print ("F0 is not in this line. ")
    print ("Pulsar spin-frequency found :  %f \n "%f0)
    return f0

def make_rficlean_hdrfile(file_name, psrj,frequency,nchannels,bandwidth,samplingtime,whichband):
        print('Removing any previous rfiClean-gmhdr file %s   ...  '%(file_name), end=' ')
        try:
            os.remove("%s"%(file_name))
            print("Done.")
        except:
            print("Could not delete the rfiClean-gmhdr file!")

        with open(file_name, 'w') as hdrfile:
            try:
                hdrfile.write(str(float(samplingtime)*1000.0) + '\n')
                hdrfile.write(str(frequency) + '\n')
                if whichband == 'USB':
                     hdrfile.write(str(-1.0*float(nchannels)*float(bandwidth)) + '\n')
                elif whichband == 'LSB':
                     hdrfile.write(str(float(nchannels)*float(bandwidth)) + '\n')
                else:
                     print("Unrecognizable sideband. Quitting...")
                     sys.exit(0)
                hdrfile.write(str(nchannels) + '\n')
                hdrfile.write(psrj)
                print ("The rfiClean-gmhdr file written out!")
            except:
                return False
        return True

def choose_int_freq(freq):
    int_freqs = np.array((499,749,1459))
    i = np.argmin(np.abs(int_freqs-freq))
    return int_freqs[i]

