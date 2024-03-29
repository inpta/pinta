import subprocess
import os
import time
import pintautils as utils
import sys

def exec_cmd(session, item, branch, program, xnbin=False):

    # xnbin option is valid for dspsr, pdmp and ps2pdf.

    outfile = log_file_name(session, item, branch, program, 'out', xnbin)
    errfile = log_file_name(session, item, branch, program, 'err', xnbin)
    
    print("[LOG] {}/{} stdout will be written to {}".format(branch, program, outfile))
    print("[LOG] {}/{} stderr will be written to {}".format(branch, program, errfile))
    
    if branch == 'gptool' and program == 'gptool':
        cmd = "gptool -f ./{} -nodedisp -o ./".format(os.path.basename(item.rawdatafile))
        #cmd = "gptool -f {} -nodedisp -o {}".format(item.rawdatafile, session.working_dir)
        #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
    elif program == 'dspsr':
        fil_file = output_file_name(session, item, branch, 'fil')
        if not xnbin:
            #fits_file_prefix = "{}/{}.{}".format(session.working_dir, item.output_root, branch)
            fits_file_prefix = "./{}.{}".format(item.output_root, branch)
            cmd = "dspsr -N {} -d {} -b {} -E {} -L {} -m {} -A {} -O {} -e fits".format(item.jname, item.npol, item.nbin, item.parfile, item.tsubint, item.timestamp, fil_file, fits_file_prefix)
            #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
        else:
            fits_file_prefix = "./{}.{}.{}xNBin".format(item.output_root, branch, session.xnbinfac)
            cmd = "dspsr -N {} -d {} -b {} -E {} -L {} -m {} -A {} -O {} -e fits".format(item.jname, item.npol, int(item.nbin*session.xnbinfac), item.parfile, item.tsubint, item.timestamp, fil_file, fits_file_prefix)
    elif program == 'psredit':
        if not xnbin:
            fits_file = output_file_name(session, item, branch, 'fits')
            cmd = "psredit -c name={},be:name=GWB,coord={},rcvr:name={},be:config='{}',be:delay={} -m {}".format(item.jname, item.coordstr, item.rcvr_name, item.gwb_config, -item.gwb_delay, fits_file)
        else:
            fits_file = output_file_name(session, item, branch, '{}xNBin.fits'.format(session.xnbinfac))
            cmd = "psredit -c name={},be:name=GWB,coord={},rcvr:name={},be:config='{}',be:delay={} -m {}".format(item.jname, item.coordstr, item.rcvr_name, item.gwb_config, -item.gwb_delay, fits_file)
    elif program == 'pam':
        if not xnbin:
            fits_file = output_file_name(session, item, branch, 'fits')
            cmd = "pam -a PSRFITS -m {}".format(fits_file)
        else:
            fits_file = output_file_name(session, item, branch, '{}xNBin.fits'.format(session.xnbinfac))
            cmd = "pam -a PSRFITS -m {}".format(fits_file)
    elif program == 'pdmp':
        if not xnbin:
            fits_file = output_file_name(session, item, branch, 'fits')
            summary_file = output_file_name(session, item, branch, 'summary.ps')
            cmd = "pdmp -mc 64 -ms 16 -g {}/cps {}".format(summary_file, fits_file)
            #cmd_split = filter(lambda x: len(x)>0, cmd.split(' '))
        else:
            fits_file = output_file_name(session, item, branch, '{}xNBin.fits'.format(session.xnbinfac))
            summary_file = output_file_name(session, item, branch, '{}xNBin.summary.ps'.format(session.xnbinfac))
            cmd = "pdmp -mc 64 -g {}/cps {}".format(summary_file, fits_file)
    elif branch == 'rfiClean' and program == 'rfiClean':
        fil_file = output_file_name(session, item, branch, 'fil')
        #rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
        Nprocess = 16
        ##cmd = 'crp_rficlean_gm.sh {} {} {} {} {} \"-psrf {} -psrfbins 32 -gmtstamp {}\"'.format(fil_file, session.rfic_conf_file, Nprocess, os.path.basename(item.rawdatafile), item.rfic_hdrfilename, item.f0psr, os.path.basename(item.timestampfile))
        ## now use absolute delta-freq. instead of Fourier-bins (whose width can change with tsamp,block-size)
        cmd = 'crp_rficlean_gm.sh {} {} {} {} {} \"-psrf {} -psrfdf 8.0 -gmtstamp {}\"'.format(fil_file, session.rfic_conf_file, Nprocess, os.path.basename(item.rawdatafile), item.rfic_hdrfilename, item.f0psr, os.path.basename(item.timestampfile))
        #cmd_split = ["crp_rficlean_gm.sh", fil_file, session.rfic_conf_file, str(Nprocess), item.rawdatafile, rfic_hdrfilename, rficlean_flags]
    elif program == 'ps2pdf':
        if not xnbin:
            summary_file = output_file_name(session, item, branch, 'summary.ps')
            cmd = "ps2pdf {}".format(summary_file)
        else:
            summary_file = output_file_name(session, item, branch, '{}xNBin.summary.ps'.format(session.xnbinfac))
            cmd = "ps2pdf {}".format(summary_file)
    
    print("[CMD]", cmd)
     
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

def log_file_name(session, item, branch, program, dev, xnbin=False):
    if not xnbin:
        return "{}/{}.{}.{}".format(item.logdir, program, branch, dev)
    else:
        return "{}/{}.{}.{}xNBin.{}".format(item.logdir, program, branch, session.xnbinfac, dev)

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
    #cmd = "filterbank {} -mjd {} -rf {} -nch {} -bw {} -ts {} -df {} > {}".format(filterbank_in_file, item.timestamp, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband_code, fil_file)
    sideband_opt = "-u" if item.sideband=='USB' else ''
    cmd = "ugmrt2fil -i {} -o {} -j {} -d {} -f {} -c {} -w {} -t {} {}".format(filterbank_in_file, fil_file, item.jname, item.timestamp, item.freq, item.nchan, item.chanwidth, item.tsmpl, sideband_opt)
    
    print("[CMD]", cmd)
    
    if not session.test_mode:
        start_time = time.time()
        os.system(cmd)
        stop_time = time.time()
        
        print_exec_time(branch, program, stop_time-start_time)

def run_dspsr(session, item, branch, xnbin=False):
    program = 'dspsr'
    exec_cmd(session, item, branch, program, xnbin=xnbin)
    
    # Checking if output file is created
    if not xnbin:
        fits_file = "./" + output_file_name(session, item, branch, 'fits')
    else:
        fits_file = "./" + output_file_name(session, item, branch, '{}xNBin.fits'.format(session.xnbinfac))
    
    if not os.access(fits_file, os.F_OK) and not session.test_mode:
        print("[ERROR] dspsr failed to create file {} ... Quitting...".format(fits_file))
        raise OSError


def run_psredit(session, item, branch, xnbin=False):
    program = 'psredit'
    exec_cmd(session, item, branch, program, xnbin=xnbin)

def run_pam(session, item, branch, xnbin=False):
    program = 'pam'
    exec_cmd(session, item, branch, program, xnbin=xnbin)

def run_pdmp(session, item, branch, xnbin=False):
    program = 'pdmp'
    exec_cmd(session, item, branch, program, xnbin=xnbin)
    
def run_ps2pdf(session, item, branch, xnbin=False):
    program = 'ps2pdf'
    exec_cmd(session, item, branch, program, xnbin=xnbin)

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
    run_pam(session, item, branch)
    run_psredit(session, item, branch)
    run_pdmp(session, item, branch)
    run_ps2pdf(session, item, branch)
    remove_tmp_file(session, item, branch, 'summary.ps')
    
    if session.fold_extra_nbin:
        run_dspsr(session, item, branch, xnbin=True)
        run_pam(session, item, branch, xnbin=True)
        run_psredit(session, item, branch, xnbin=True)
        run_pdmp(session, item, branch, xnbin=True)
        run_ps2pdf(session, item, branch, xnbin=True)
        remove_tmp_file(session, item, branch, '{}xNBin.summary.ps'.format(session.xnbinfac))
    
    remove_tmp_file(session, item, branch, 'fil')    

def gptool_branch(session, item):
    branch = 'gptool'
    run_gptool(session, item, branch)
    run_filterbank(session, item, branch)
    remove_tmp_file(session, item, branch, 'gpt.dat')
    run_dspsr(session, item, branch)
    run_pam(session, item, branch)
    run_psredit(session, item, branch)
    run_pdmp(session, item, branch)
    run_ps2pdf(session, item, branch)
    remove_tmp_file(session, item, branch, 'summary.ps')
    
    if session.fold_extra_nbin:
        run_dspsr(session, item, branch, xnbin=True)
        run_pam(session, item, branch, xnbin=True)
        run_psredit(session, item, branch, xnbin=True)
        run_pdmp(session, item, branch, xnbin=True)
        run_ps2pdf(session, item, branch, xnbin=True)
        remove_tmp_file(session, item, branch, '{}xNBin.summary.ps'.format(session.xnbinfac))
    
    remove_tmp_file(session, item, branch, 'fil')

def rficlean_branch(session, item):
    branch = 'rfiClean'
    run_rficlean(session, item, branch)
    run_dspsr(session, item, branch)
    run_pam(session, item, branch)
    run_psredit(session, item, branch)
    run_pdmp(session, item, branch)
    run_ps2pdf(session, item, branch)
    remove_tmp_file(session, item, branch, 'summary.ps')
    
    if session.fold_extra_nbin:
        run_dspsr(session, item, branch, xnbin=True)
        run_pam(session, item, branch, xnbin=True)
        run_psredit(session, item, branch, xnbin=True)
        run_pdmp(session, item, branch, xnbin=True)
        run_ps2pdf(session, item, branch, xnbin=True)
        remove_tmp_file(session, item, branch, '{}xNBin.summary.ps'.format(session.xnbinfac))
    
    remove_tmp_file(session, item, branch, 'fil')

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
        


