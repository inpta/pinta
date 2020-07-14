
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

                

        write_section_title(f, "Dedispersion & Folding parameters")
        write_param(f, "Number of bins in folded profile (-1 for native resolution)", -1)

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


#*** Observation Paramaters****#
