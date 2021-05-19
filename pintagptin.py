
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

def create_gptin_file(template_file, gptin_opts, filename):
    with open(template_file, mode='r') as gptin_templ_file:
        gptin_templ = gptin_templ_file.read()
    
        gptin_str = gptin_templ.format(**gptin_opts)
        
        with open(filename, mode='w') as fout:
            fout.write(gptin_str)
        
def create_gptin_file_from_session(session, item, filename="gptool.in"):

    gptin_templ_filename = "{}/gptool.in.templ".format(session.gptdir)
    
    gptin_opts = dict(  BM      = "PA",
                        pol     = 1,
                        Nbytes  = 2,
                        Fmin    = lowest_freq(item),
                        BW      = item.bandwidth,
                        SB      = sideband_flag(item),
                        Nchan   = item.nchan,
                        Tsmpl   = item.tsmpl*1000,
                        JNAME   = item.jname,
                        P0      = round(1000/item.f0psr,3),
                        DM      = 0.0,    
    )
    
    output_filename = "{}/{}".format(session.working_dir, filename)
    
    create_gptin_file(gptin_templ_filename, gptin_opts, output_filename)
    
    print("[INFO] Generated gptool.in file from template {}".format(gptin_templ_filename))
    
