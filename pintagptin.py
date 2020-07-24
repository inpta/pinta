
def write_file_title(f, title):
    f.write("#*#*#{}#*#*#\n".format(title))

def write_section_separator(f):
    f.write("-------------------------------------------------\n")

def write_section_title(f, title):
    f.write("#****{}****#\n".format(title))

def write_param(f, name, value):
    padded_value_str = str(value).ljust(8, ' ')
    f.write("{}: {}\n".format(padded_value_str,name))

def write_str(f, string):
    f.write(string+'\n')

def pol_mode(item):
    return 0 if item.npol==1 else 1

def lowest_freq(item):
    if item.sideband == 'LSB':
        return item.freq_lo - item.bandwidth
    else:
        return item.freq_lo

def sideband_flag(item):
    if item.sideband == 'LSB':
        return "-1"
    else:
        return "+1"

def nchan_flag(item):
    return int(50*item.nchan/1024)

def write_gptool_in(filename, item):
    with open(filename, 'w') as f:
        write_file_title(f, "gptool input file v2.0")
        write_section_separator(f)
        
        write_section_title(f, "Mode of observation")
        write_param(f, "Beam mode", "PA")
        write_param(f, "Polarization mode (0-> intesity, 1-> stokes data)", pol_mode(item))
        write_param(f, "Sample size of data (in bytes, usually 2)", 2)
        write_section_separator(f)

        write_section_title(f, "Observation Paramaters")
        write_param(f, "Frequency band (lowest value in MHz)", lowest_freq(item))
        write_param(f, "Bandwidth(in Mhz)", item.bandwidth)
        write_param(f, "Sideband flag (-1-> decreasing +1-> increasing)", sideband_flag(item))
        write_param(f, "Number of channels", item.nchan)
        write_param(f, "Sampling Interval (in ms)", item.tsmpl*1000)
        write_section_separator(f)

        write_section_title(f, "Pulsar Parameters")
        write_param(f, "Pulsar name", item.jname)
        write_param(f, "Pulsar period (in milliseconds)", round(1000/item.f0psr,3))
        write_param(f, "DM (in pc/cc)", 0.0)
        write_section_separator(f)
        
        write_section_title(f, "Dedispersion & Folding parameters")
        write_param(f, "Number of bins in folded profile (-1 for native resolution)", -1)
        write_param(f, "Phase offset for folding", 0)
        write_param(f, "Number of coefficients for each polyco span (nCoeff)", 12)
        write_param(f, "Validity of each span (nSpan in mins)", 60)
        write_param(f, "Maximum hour angle", 12)
        write_section_separator(f)

        write_section_title(f, "Display Parameters")
        write_param(f, "Polarization channel to display (0-3 or -1 for all four)", 0)
        write_param(f, "Display window size (seconds, 0-> pulsar period)", 5)
        write_param(f, "Update mode (0-> automatic, 1-> manual)", 0)
        write_param(f, "Time delay between window updates (0-> no delay, 1-> emulate real time)", 0)
        write_param(f, "Maximum hour angle", 12)
        write_section_separator(f)
        
        write_section_title(f, "Spectral line RFI mitigation options")
        write_param(f, "Number of channels to flag at band beginning", nchan_flag(item))
        write_param(f, "Number of channels to flag at band end", nchan_flag(item))
        write_param(f, "Frequency flagging options (0-> no flagging, 1-> real time calculation)", 1)
        write_param(f, "Bandshape to use for frequency flagging (1-> normalized bandshape, 2-> mean-to-rms bandshape, 3-> Both)", 3)
        write_param(f, "Threshold for frequency flagging (in units of RMS deviation)", 2.5)
        write_section_separator(f)
        
        write_section_title(f, "Time domain impulsive RFI mitigation options")
        write_param(f, "Time flagging options (0-> no flagging, 1-> real time calculation)", 1)
        write_param(f, "Data normalization before filtering (0-> no, 1-> yes)", 1)
        write_param(f, "Time flagging algorithm   (1-> histogram based, 2-> MAD based)", 1)
        write_param(f, "Threshold for time flagging (in units of RMS deviation)", 2.5)
        write_section_separator(f)
        
        write_section_title(f, "Other options")
        write_param(f, "Smoothing window size for bandshape normalization (in number of channels)", 20)
        write_param(f, "Normalization procedure (1-> cumulative smooth bandshape, 2-> externally supplied bandshape.dat)", 1)
        write_param(f, "Replace by median values (0-> Ignore flagged samples, 1-> Replace flagged samples by window median)", 0)
        write_section_separator(f)
        
        write_section_title(f, "I/O options")
        write_param(f, "Write channel flag file (0-> no,1-> yes)", 0)
        write_param(f, "Write time flag file (0-> no, 1-> yes)", 0)
        write_param(f, "Write out filtered 2D raw data (0-> no, 1-> yes)", 1)
        write_param(f, "Write out fullDM.raw  (0-> no, 1-> yes)", 0)
        write_section_separator(f)
        
        write_section_title(f, "manual flagging options")
        write_param(f, "Number of bad channel blocks", 0)
        write_param(f, "#in next line, example: [200,400],[1200,1400]", "List")

if __name__=="__main__":
    from pintasession import session
    
    for idx, item in enumerate(session.pipeline_items):
        write_gptool_in("gptool.in.{}".format(idx), item)
