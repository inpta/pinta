import subprocess
import time
import pintautils as utils

def exec_cmd(session, item, branch, program):
    logfile = log_file_name(session, item, branch, program)
    
    if branch == 'gptool' and program == 'gptool':
        cmd = "gptool -f {} -nodedisp -o {}".format(item.rawdatafile, session.working_dir)
    elif program == 'dspsr':
        fil_file = output_file_name(session, item, branch, 'fil')
        fits_file = output_file_name(session, item, branch, 'fits')
        cmd = "dspsr -N {} -d {} -b {} -E {} -L {} -A {} -O {}".format(item.jname, item.npol, item.nbin, item.parfile, item.tsubint, fil_file, fits_file)
    elif program == 'pdmp':
        fits_file = output_file_name(session, item, branch, 'fits')
        summary_file = output_file_name(session, item, branch, 'summary.ps')
        cmd = "pdmp -mc 64 -g {}/cps {}".format(summary_file, fits_file)
    elif branch == 'rfiClean' and program == 'rfiClean':
        fil_file = output_file_name(session, item, branch, 'fil')
        rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
        Nprocess = 16
        cmd = 'crp_rficlean_gm.sh {} {} {} {} {} "-psrf {} -psrfbins 32 -gmtstamp {}"'.format(fil_file, session.rfic_conf_file, Nprocess, item.rawdatafile, rfic_hdrfilename, item.f0psr, item.timestampfile)
    
    print("cmd :: ", cmd)
    
    cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
     
    try:
        if not session.test_mode:
            start_time = time.time()    
            
            lf = open(logfile, 'w')
            p = subprocess.Popen(cmd_split, stdout=logfile)
            p.wait()
            lf.close()
        
            stop_time = time.time()
            exec_time = stop_time-start_time
            print_exec_time(branch, program, exectime)
    except:
        raise OSError("Error while executing command.\ncmd :: "+cmd)

def output_file_name(session, item, branch, ext):
    return "{}/{}.{}.{}".format(session.working_dir, item.output_root, branch, ext)

def log_file_name(session, item, branch, program):
    return "{}/{}.{}.log".format(session.logdir, program, branch)

def print_exec_time(branch, program, exectime):
    print("[TIME] Execution time for {}/{} = {} s".format(branch, program, exectime))

def remove_tmp_file(session, item, branch, ext):
    if (not session.test_mode) and session.delete_tmp_files:
        filename = output_file_name(session, item, branch, ext)
        print("Removing file", filename)
        os.remove(filename)
    
def run_gptool(session, item, branch):
    program = 'gptool'
    exec_cmd(session, item, branch, program)
    
    if not session.test_mode:
        gptfilename = "{}/{}.gpt".format(session.working_dir, os.path.basename(item.rawdatafile))
        gptfilename_new = output_file_name(session, item, branch, 'gpt.dat')
        os.rename(gptfilename, gptfilename_new)

def run_filterbank(session, item, branch):
    program = 'filterbank'
    
    if branch == 'gptool':
        filterbank_in_file = output_file_name(session, item, branch, 'gpt.dat')
    else:
        filterbank_in_file = item.rawdatafile
    
    fil_file = output_file_name(session, item, branch, 'fil')
    cmd = "filterbank {} -mjd {:0.18f} -rf {} -nch {} -bw {} -ts {} -df {} > {}".format(filterbank_in_file, item.timestamp, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband_code, fil_file)
    
    print("cmd :: ", cmd)
    
    if not session.test_mode:
        start_time = time.time()
        os.system(cmd)
        stop_time = time.time()
        
        print_exec_time(branch, program, exectime)

def run_dspsr(session, item, branch):
    program = 'dspsr'
    exec_cmd(session, item, branch, program)
        
def run_pdmp(session, item, branch):
    program = 'pdmp'
    exec_cmd(session, item, branch, program)

def run_rficlean(session, item, branch):
    print("Trying to make the rficlean-gmhdr file ...")
    rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
    if not utils.make_rficlean_hdrfile(rfic_hdrfilename, item.jname, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband):
        print ("Could not make the rficlean-gmhdr file!")
        sys.exit(0)
        
    program = 'rfiClean'
    exec_cmd(session, item, branch, program)

def norfix_branch(session, item):
    branch = 'norfix'
    run_filterbank(session, item, branch)
    run_dspsr(session, item, branch)
    remove_tmp_file(session, item, branch, 'fil')
    run_pdmp(session, item, branch)

def gptool_branch(session, item):
    branch = 'gptool'
    run_gptool(session, item, branch)
    run_filterbank(session, item, branch)
    remove_tmp_file(session, item, branch, 'gpt.dat')
    run_dspsr(session, item, branch)
    remove_tmp_file(session, item, branch, 'fil')
    run_pdmp(session, item, branch)

def rficlean_branch(session, item):
    branch = 'rfiClean'
    run_rficlean(session, item, branch)
    run_dspsr(session, item, branch)
    remove_tmp_file(session, item, branch, 'fil')
    run_pdmp(session, item, branch)

