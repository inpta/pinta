import subprocess
import os
import time
import pintautils as utils
import sys

def exec_cmd(session, item, branch, program):
    outfile = log_file_name(session, item, branch, program, 'out')
    errfile = log_file_name(session, item, branch, program, 'err')
    
    print("[LOG] {}/{} stdout will be written to {}".format(branch, program, outfile))
    print("[LOG] {}/{} stderr will be written to {}".format(branch, program, errfile))
    
    if branch == 'gptool' and program == 'gptool':
        cmd = "gptool -f ./{} -nodedisp -o ./".format(os.path.basename(item.rawdatafile))
        #cmd = "gptool -f {} -nodedisp -o {}".format(item.rawdatafile, session.working_dir)
        #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
    elif program == 'dspsr':
        fil_file = output_file_name(session, item, branch, 'fil')
        #fits_file_prefix = "{}/{}.{}".format(session.working_dir, item.output_root, branch)
        fits_file_prefix = "./{}.{}".format(item.output_root, branch)
        cmd = "dspsr -N {} -d {} -b {} -E {} -L {} -A {} -O {} -e fits".format(item.jname, item.npol, item.nbin, item.parfile, item.tsubint, fil_file, fits_file_prefix)
        #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
    elif program == 'pdmp':
        fits_file = output_file_name(session, item, branch, 'fits')
        summary_file = output_file_name(session, item, branch, 'summary.ps')
        cmd = "pdmp -mc 64 -g {}/cps {}".format(summary_file, fits_file)
        #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
    elif branch == 'rfiClean' and program == 'rfiClean':
        fil_file = output_file_name(session, item, branch, 'fil')
        #rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
        Nprocess = 16
        cmd = 'crp_rficlean_gm.sh {} {} {} {} {} \"-psrf {} -psrfbins 32 -gmtstamp {}\"'.format(fil_file, session.rfic_conf_file, Nprocess, os.path.basename(item.rawdatafile), item.rfic_hdrfilename, item.f0psr, os.path.basename(item.timestampfile))
        #cmd_split = ["crp_rficlean_gm.sh", fil_file, session.rfic_conf_file, str(Nprocess), item.rawdatafile, rfic_hdrfilename, rficlean_flags]
    
    print("[CMD]", cmd)
    
    #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
     
    try:
        if not session.test_mode:
            start_time = time.time()    
            
            of = open(outfile, 'w')
            ef = open(errfile, 'w')
            p = subprocess.Popen(cmd, stdout=of, stderr=ef, shell=True)
            p.wait()
            of.close()
            ef.close()
        
            stop_time = time.time()
            exec_time = stop_time-start_time
            print_exec_time(branch, program, exec_time)
    except:
        raise OSError("Error while executing command.\ncmd :: "+cmd)

def output_file_name(session, item, branch, ext):
    #return "{}/{}.{}.{}".format(session.working_dir, item.output_root, branch, ext)
    return "{}/{}.{}.{}".format('.', item.output_root, branch, ext)

def log_file_name(session, item, branch, program, dev):
    return "{}/{}.{}.{}".format(item.logdir, program, branch, dev)

def print_exec_time(branch, program, exectime):
    print("[TIME] Execution time for {}/{} = {} s".format(branch, program, exectime))

def remove_tmp_file(session, item, branch, ext):
    if (not session.test_mode) and session.delete_tmp_files:
        filename = output_file_name(session, item, branch, ext)
        print("[INFO] Removing file", filename)
        os.remove(filename)
    
def run_gptool(session, item, branch):
    program = 'gptool'
    exec_cmd(session, item, branch, program)
    
    if not session.test_mode:
        gptfilename = "./{}.gpt".format(os.path.basename(item.rawdatafile))
        gptfilename_new = output_file_name(session, item, branch, 'gpt.dat')
        os.rename(gptfilename, gptfilename_new)
        print("[CMD] mv {} {}".format(gptfilename, gptfilename_new))

def run_filterbank(session, item, branch):
    program = 'filterbank'
    
    if branch == 'gptool':
        filterbank_in_file = output_file_name(session, item, branch, 'gpt.dat')
    else:
        filterbank_in_file = './' + os.path.basename(item.rawdatafile)
    
    fil_file = output_file_name(session, item, branch, 'fil')
    cmd = "filterbank {} -mjd {} -rf {} -nch {} -bw {} -ts {} -df {} > {}".format(filterbank_in_file, item.timestamp, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband_code, fil_file)
    
    print("[CMD]", cmd)
    
    if not session.test_mode:
        start_time = time.time()
        os.system(cmd)
        stop_time = time.time()
        
        print_exec_time(branch, program, stop_time-start_time)

def run_dspsr(session, item, branch):
    program = 'dspsr'
    exec_cmd(session, item, branch, program)
        
def run_pdmp(session, item, branch):
    program = 'pdmp'
    exec_cmd(session, item, branch, program)

def run_rficlean(session, item, branch):
    #print("[INFO] Trying to make the rficlean-gmhdr file ...")
    #rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
    #if not utils.make_rficlean_hdrfile(rfic_hdrfilename, item.jname, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband):
    #    print ("[ERROR] Could not make the rficlean-gmhdr file!")
    #    sys.exit(0)
        
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

def setup_input_ln(session, item):
    if not session.samedir:
        
        for infile in [item.rawdatafile, item.timestampfile]:
            
            ln_src = infile
            ln_dst = "./" + os.path.basename(infile)
    
            if os.path.exists(ln_dst) and os.path.islink(ln_dst):
                print("[INFO] Removing existing symlink {}".format(ln_dst))
                print("[CMD] rm {}".format(ln_dst))
                os.remove(ln_dst)
            elif os.path.exists(ln_dst) and not os.path.islink(ln_dst):
                print("[ERROR] Can't replace {}. Please check working directory.".format(ln_dst))
                raise OSError()
            
            print("[INFO] Creating symlink to {}".format(ln_src))
            print("[CMD] ln -s {} {}".format(ln_src, ln_dst))
            os.symlink(ln_src, ln_dst)
    
def remove_input_ln(session, item):
    if not session.samedir:
        
        for infile in [item.rawdatafile, item.timestampfile]:
            
            ln_dst = "./" + os.path.basename(infile)
    
            if os.path.exists(ln_dst) and os.path.islink(ln_dst):
                print("[INFO] Removing symlink {}".format(ln_dst))
                print("[CMD] rm {}".format(ln_dst))
                os.remove(ln_dst)
        


