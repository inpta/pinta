import shutil
import sys
import os
import numpy as np
import parse
import astropy.time as astrotime
import getopt
import time
import glob

def touch_file(fname):
    with open(fname, 'w'):
        os.utime(fname, None)

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
    print ("[INPUT] Pulsar spin-frequency found :  %f "%f0)
    return f0

def make_rficlean_hdrfile(file_name, psrj,frequency,nchannels,bandwidth,samplingtime,whichband):
        print('[INFO] Removing any previous rfiClean-gmhdr file %s   ...  '%(file_name), end=' ')
        try: 
            os.remove("%s"%(file_name))
            print("Done.")
        except:
            print("[ERROR] Could not delete the rfiClean-gmhdr file!")

        with open(file_name, 'w') as hdrfile:
            try:
                hdrfile.write(str(float(samplingtime)*1000.0) + '\n')
                hdrfile.write(str(frequency) + '\n')
                if whichband == 'USB':
                     hdrfile.write(str(-1.0*float(nchannels)*float(bandwidth)) + '\n')
                elif whichband == 'LSB':
                     hdrfile.write(str(float(nchannels)*float(bandwidth)) + '\n')
                else:
                     print("[ERROR] Unrecognizable sideband. Quitting...")
                     sys.exit(0)
                hdrfile.write(str(nchannels) + '\n')
                hdrfile.write(psrj)
                print ("[INFO] The rfiClean-gmhdr file written out!")
            except:
                return False
        return True

def choose_int_freq(freq):
    int_freqs = np.array((499,749,1459))
    i = np.argmin(np.abs(int_freqs-freq))
    return int_freqs[i]

def process_sideband(sideband_):
    if sideband_ == 'USB':
        sideband = 'gmgwbf'
    elif sideband_ == 'LSB':
        sideband = 'gmgwbr'
    else:
        raise ValueError("The given sideband {} is invalid.".format(sideband_))
    return sideband

def process_freq(freq_lo, nchan, chanwidth, cohded):
    return freq_lo

def copy_gptool_in(gptdir, current_dir, intfreq):
    src = "{}/gptool.in.{}".format(gptdir, intfreq)
    dst = "{}/gptool.in".format(current_dir)
    shutil.copy(src, dst)
    print("[INFO] Copied gptool.in file for freq {}".format(intfreq))

def check_mkdir(dirname):
    if not os.access(dirname, os.F_OK):
        print("[INFO] Creating directory", dirname)
        os.mkdir(dirname)
    
aux_files_wcards = ["*.info", "*.gpt", "pdmp.*"]

def move_aux_files(session, item):
    glb = lambda f : glob.glob("{}/{}".format(session.working_dir, f))
    aux_files = set(sum(map(glb, aux_files_wcards), []))
    for src in aux_files:
        print("[INFO] Moving file {} to aux.".format(src))
        shutil.move(src, item.auxdir)
    
def remove_aux_files(session, item):
    glb = lambda f : glob.glob("{}/{}".format(session.working_dir, f))
    aux_files = set(sum(map(glb, aux_files_wcards), []))
    for src in aux_files:
        print("[INFO] Removing file {}".format(src))
        os.unlink(src)
    
