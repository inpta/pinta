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
    hh, mm, ss = parse.parse("{}:{}:{}", timestr)    

    #datetime_IST = "%s-%s-%sT%s"%(year,month,day,timestr)
    date_IST = "%s-%s-%s"%(year,month,day)
    
    datemjd_int = astrotime.Time(date_IST, format='isot', scale='utc').mjd
    datemjd_frc = (float(hh) + float(mm)/60 + float(ss)/3600 - 5.5)/24

    if datemjd_frc<0:
        datemjd_frc += 1
        datemjd_int -= 1

    # This is an ugly hack. Will change this if there is a better option.
    datemjd_frc_str = "{:.15f}".format(datemjd_frc).split('.')[1]
    datetimemjd_str = "{}.{}".format(int(datemjd_int), datemjd_frc_str)

    return datetimemjd_str

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
            print("Could not delete the rfiClean-gmhdr file!")

        with open(file_name, 'w') as hdrfile:
            print("[INFO] Trying to make the rficlean-gmhdr file ...")
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
                print("[INFO] The rfiClean-gmhdr file written out! {}".format(file_name))
            except:
                print("[ERROR] Could not make the rficlean-gmhdr file! Quitting...")
                sys.exit(0)
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

def process_freq(freq_lo, nchan, bandwidth, sideband, cohded):
    if not cohded:
        if sideband == 'LSB':
            f1 = freq_lo
        else:
            f1 = freq_lo + bandwidth
    else:
        if sideband == 'LSB':
            f1 = freq_lo - bandwidth/nchan
        else:
            f1 = freq_lo + bandwidth*(1 - 1./nchan)
    
    return f1

def copy_gptool_in(gptdir, working_dir, intfreq):
    src = "{}/gptool.in.{}".format(gptdir, intfreq)
    #dst = "{}/gptool.in".format(current_dir)
    dst = "{}/gptool.in".format(working_dir)
    shutil.copyfile(src, dst)
    print("[INFO] Copied gptool.in file for freq {}".format(intfreq))
    print("[CMD] cp {} {}".format(src, dst))

def check_mkdir(dirname):
    if not os.access(dirname, os.F_OK):
        print("[INFO] Creating directory", dirname)
        os.mkdir(dirname)
    
aux_files_wcards = ["*.info", "*.gpt", "pdmp.*", 'gptool.in*']

def move_aux_files(session, item):
    glb = lambda f : glob.glob("{}/{}".format(session.working_dir, f))
    aux_files = set(sum(map(glb, aux_files_wcards), []))
    for src in aux_files:
        print("[INFO] Moving file {} to aux.".format(src))
        dst = "{}/{}".format(item.auxdir, os.path.basename(src))
        shutil.move(src, dst)
    
def remove_aux_files(session, item):
    glb = lambda f : glob.glob("{}/{}".format(session.working_dir, f))
    aux_files = set(sum(map(glb, aux_files_wcards), []))
    for src in aux_files:
        print("[INFO] Removing file {}".format(src))
        os.unlink(src)

def print_log(session, message):
    print(message)
    if session.log_to_file:
        session.logfile.write(message+"\n")

