import shutil
import sys
import os
import numpy as np
import parse
import astropy.time as astrotime
import getopt
import time
import glob
import astropy.units as astrounit

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

def prepare_par_line(line):
    return line.strip().replace('\t',' ').replace('\n','')

def rad_to_hms(α):
    # α will be in [-pi,pi]
    if α<0:
        α += 2*np.pi
    hrs = α * 12 / np.pi
    
    hh = int(hrs)
    mm = int((hrs - hh)*60)
    ss = int((hrs - hh - mm/60)*3600)
    sf = (hrs - hh - mm/60)*3600 - ss
    sfs = str(sf).split('.')[1]
    
    return f'{hh:02}:{mm:02}:{ss:02}.{sfs}'    

def rad_to_dms(δ):
    # δ will be in [-pi/2, pi/2]
    sgn = np.sign(δ)
    pm = '-' if sgn<0 else '+'
    
    degs = np.abs(δ) * 180 / np.pi
    
    dd = int(degs)
    mm = int((degs - dd)*60)
    ss = int((degs - dd - mm/60)*3600)
    sf = (degs - dd - mm/60)*3600 - ss
    sfs = str(sf).split('.')[1]
    
    return f'{pm}{dd:02}:{mm:02}:{ss:02}.{sfs}'

def ecliptic_to_equatorial(elat, elong):
    """
    https://en.wikipedia.org/wiki/Astronomical_coordinate_systems#Equatorial_%E2%86%94_ecliptic
    """
    
    # Obliquity value taken from PINT
    # https://github.com/nanograv/PINT/blob/master/src/pint/data/runtime/ecliptic.dat
    ε = astrounit.Quantity(84381.406000, astrounit.arcsec).to(astrounit.rad).value
    
    β = astrounit.Quantity(elat,  astrounit.deg).to(astrounit.rad).value 
    λ = astrounit.Quantity(elong, astrounit.deg).to(astrounit.rad).value 
    
    α = np.arctan2(np.cos(β)*np.sin(λ)*np.cos(ε) - np.sin(β)*np.sin(ε),
                   np.cos(β)*np.cos(λ))
    δ = np.arcsin(np.sin(β)*np.cos(ε) + np.cos(β)*np.sin(λ)*np.sin(ε))
    
    return rad_to_hms(α), rad_to_dms(δ)

def fetch_RAJ_DECJ(parfile_name):
    with open(parfile_name, 'r') as par_file:
        par_lines = par_file.readlines()
        
        par_tokens = dict([list(filter(lambda x: len(x)>0, 
                                       prepare_par_line(line).split(' ')
                                      )
                               )[:2] for line in par_lines
                          ])
        
        if "RAJ" in par_tokens and "DECJ" in par_tokens:
            raj = par_tokens["RAJ"]
            decj = par_tokens["DECJ"]
            return raj, decj
        elif "ELAT" in par_tokens and "ELONG" in par_tokens:
            elat = par_tokens["ELAT"]
            elong = par_tokens["ELONG"]
            return ecliptic_to_equatorial(elat, elong)
        elif "LAMBDA" in par_tokens and "BETA" in par_tokens:
            elat = par_tokens["BETA"]
            elong = par_tokens["LAMBDA"]
            return ecliptic_to_equatorial(elat, elong)
        else:
            print("[ERROR] Unable to read coordinates from par file. Setting 00:00:00+00:00:00.")
            return "00:00:00","+00:00:00"

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
    
aux_files_wcards = [    "bandshape.gpt", 
                        "benchmark_fillTime.gpt", 
                        "benchmark.gpt", 
                        "benchmark_readtime.gpt", 
                        "benchmark_threadtime.gpt", 
                        "benchmark_threadtime_indv.gpt",
                        "log.gpt",
                        "stats.gpt",
                        "gptool.in",
                        "gptool.in.oldver",
                        "pdmp.per",
                        "pdmp.posn",
                        "*-ttemp-gm.info" ]

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

def find_nyquist_nbin(session, item):
    F0 = item.f0psr
    Tsmpl = item.tsmpl
    nbin_nyq = 2**( int(np.log2( 1/(Tsmpl*F0) )) )
    print ("[INFO] Default NBin =  %d"%nbin_nyq)
    return nbin_nyq

def find_band_number(session, item):
    freq_lo = item.freq_lo
    
    if freq_lo>119 and freq_lo<=250:
        return 2
    elif freq_lo>250 and freq_lo<501:
        return 3
    elif freq_lo>549 and freq_lo<851:
        return 4
    elif freq_lo>1059 and freq_lo<1461:
        return 5
    else:
        raise ValueError("The value of freq_lo is outside valid ranges for uGMRT bands.")

def find_rcvr_name(session, item):
    band_num = find_band_number(session, item)
    return "uGMRT_B{}".format(band_num)

def find_gwb_mode(session, item):
    return "CD" if item.cohded else "IA/PA"


