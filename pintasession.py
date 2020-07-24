import getopt
import sys
import os
import yaml
import numpy as np
import traceback
import getpass
import datetime
import socket

import pintatests as tests
import pintautils as utils

helpmsg = "Usage:\npinta.py [--help] [--test] [--no-gptool] [--no-rficlean] [--nodel] [--retain-aux] [--log-to-file] [--gptdir <...>] [--pardir <...>] [--rficconf <...>] <input_dir> <working_dir>"

class Session:
    """  
        Contains information that is common to all items such as working_dir, input_dir etc.
    """

    def __init__(self):
        
        #= Parsing command line ========================================================================================
        cmdargs = sys.argv[1:]
        opts, args = getopt.gnu_getopt(cmdargs, "", ["gptdir=", "pardir=", "rficconf=", "help", "test", "no-gptool", "no-rficlean", "nodel", "retain-aux", "log-to-file"])
        opts = dict(opts)
        
        #= Displaying help =============================================================================================
        if opts.get("--help") is not None:
            print(helpmsg)
            sys.exit(0)
        
        #= Log to file =================================================================================================
        #if opts.get("--logfile") is not None:
        #    self.logfile = "{}/log/{}"
        
        #= User and time ===============================================================================================
        self.user = getpass.getuser()
        self.starttime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self.hostname = socket.gethostname()
        print("[INFO] pinta invoked by {} at {} on {}".format(self.user, self.starttime, self.hostname))
        
        #= Script directory and Currecnt Directory =====================================================================        
        self.script_dir = tests.test_read_dir( os.path.dirname(os.path.realpath(__file__)) )
        self.current_dir = tests.test_dir( os.getcwd() )
        
        #= Input and working directories ===============================================================================
        if len(args)<2:
            print("[ERROR] Input and working directories must be provided as command line arguments.")
            sys.exit(0)
            
        self.input_dir = tests.test_read_dir( os.path.realpath(args[0]) )
        self.working_dir = tests.test_dir( os.path.realpath(args[1]) )
        
        self.samedir = self.input_dir==self.working_dir
        if self.samedir:
            print("[INFO] Input dir and working dir are the same.")
        
        #= Getting lock on working directory ===========================================================================
        self.get_lock()
        
        #= Test Mode ===================================================================================================
        self.test_mode = opts.get("--test") is not None
        if self.test_mode:
            print("[CONFIG] Running in test mode. Commands will only be displayed and not executed.")
        
        #= Reading config file =========================================================================================
        self.config_file = '{}/{}'.format(self.script_dir, 'pinta.yaml')
        try:
            print("[CONFIG] Reading config from", self.config_file)
            config = yaml.load(open(self.config_file), Loader=yaml.FullLoader)
        except:
            print("[ERROR] Unable to read config file ", config_file)
            sys.exit(0)
        
        #= Which branches to run =======================================================================================
        self.run_gptool = opts.get("--no-gptool") is None
        if self.run_gptool:
            print("[CONFIG] Will run gptool.")
        else:
            print("[CONFIG] Will not run gptool.")

        self.run_rficlean = opts.get("--no-rficlean") is None
        if self.run_rficlean:
            print("[CONFIG] Will run rficlean.")
        else:
            print("[CONFIG] Will not run rficlean.")
        
        #= Pulsar ephemeris directory, gptool config directory and rfiClean config file ================================
        if opts.get("--pardir") is not None:
            print("[CONFIG] Pulsar ephemeris directory provided in command line.")
            self.par_dir = tests.test_read_dir( os.path.realpath( opts.get("--pardir") ) )
        else:
            self.par_dir = tests.test_read_dir( os.path.realpath( config['pinta']['pardir'] ) )

        if self.run_gptool:
            if opts.get("--gptdir") is not None:
                print("[CONFIG] gptool.in directory provided in command line.")
                self.gptool_in_dir = tests.test_read_dir( os.path.realpath( opts.get("--gptdir") ) )
            else:
                self.gptool_in_dir = tests.test_read_dir( os.path.realpath( config['pinta']['gptdir'] ) )
        
        if self.run_rficlean:
            if opts.get("--rficconf") is not None:
                print("[CONFIG] rfiClean configuration file profided in command line.")
                self.rfic_conf_file = tests.test_input_file( os.path.realpath( opts.get("--rficconf") ) )
            else:
                self.rfic_conf_file = tests.test_input_file( os.path.realpath( config['pinta']["rficconf"] ) )
        
        tests.check_current_group(config['pinta']["group"])
        
        #= Whether to delete intermediate outputs ======================================================================
        self.delete_tmp_files = opts.get("--nodel") is None
        if self.delete_tmp_files:
            print("[CONFIG] Will remove intermediate products.")
        else:
            print("[CONFIG] Will not remove intermediate products.")
        
        #= Checking if all required programs are present ===============================================================
        #program_list = ['gptool','dspsr','filterbank','tempo2','pdmp','crp_rficlean_gm.sh']
        program_list = ['dspsr','filterbank','tempo2','pdmp']
        if self.run_gptool:
            program_list += ['gptool']
        if self.run_rficlean:
            program_list += ['crp_rficlean_gm.sh']
        for program in program_list:
            if not tests.check_program(program):
                sys.exit(0)
        
        #= Checking gptool.in files for permissions ====================================================================
        if self.run_gptool:
            for freq in [499,749,1459]:
                tests.test_input_file("{}/gptool.in.{}".format(self.gptool_in_dir,freq))
        
        #= Checking and reading pipeline.in ============================================================================
        self.pipeline_in_file = tests.test_input_file("%s/pipeline.in"%(self.working_dir))
        
        print("[INPUT] Reading %s/pipeline.in..."%(self.working_dir), end=' ')
        try:
            self.pipeline_in_data = np.genfromtxt("%s/pipeline.in"%(self.working_dir), dtype=str, comments='#')
            if len(self.pipeline_in_data.shape)==1:
                self.pipeline_in_data = np.asarray([self.pipeline_in_data])
            
            no_of_cols_expected = 12
            if self.pipeline_in_data.shape[1] != no_of_cols_expected:
                raise ValueError()
            print("Done. %d item(s) to be processed."%(len(self.pipeline_in_data)))
        except ValueError:
            print("Invalid format... Quitting...")
            sys.exit(0)
        
        #= Checking --retain-aux option and creating aux/ directory ====================================================
        self.retain_aux = opts.get("--retain-aux") is not None
        if self.retain_aux:
            self.auxdir = "{}/aux".format(self.working_dir)
            utils.check_mkdir(self.auxdir)
            print("[CONFIG] Will move auxiliary files to", self.auxdir)
        else:
            print("[CONFIG] Will remove auxiliary files.")
        
        
        #= Creating log/ directory =====================================================================================
        self.logdir = "{}/log".format(self.working_dir)
        utils.check_mkdir(self.logdir)
        
        #= Creating PipelineItem objects from the pipeline.in file =====================================================
        self.pipeline_items = []
        for idx, row in enumerate(self.pipeline_in_data):
            try:
                self.pipeline_items.append( PipelineItem(self, row, idx) )
            except Exception as e:
                print("[ERROR] Error processing row #{} of pipeline.in".format(idx+1))
                traceback.print_exc()
        
        #= Enter working directory =====================================================================================
        print("[INFO] Enterting working directory.")
        print("[CMD] cd {}".format(self.working_dir))
        os.chdir(self.working_dir)       
                
    def get_lock(self):
        self.lockfile = "{}/{}".format(self.working_dir, 'pinta.lock')
        if os.access(self.lockfile, os.F_OK):
            print("[ERROR] Another instance of pinta seems to be running on this directory.")
            print("[ERROR] *IMPORTANT* If you are /sure/ this is a mistake, please remove pinta.lock manualy and try again. DOING THIS MAY CORRUPT THE DATA.")
            self.lockfail = True
            raise OSError()
        else:
            print("[LOCK] Creating lock file...")
            print("[CMD] touch {}".format(self.lockfile))
            utils.touch_file(self.lockfile)
            self.lockfail = False
    
    def exec_cmd(self, cmd, logfile):
        lfname = '{}/aux/{}'.format(self.working_dir)
        lf = open(logfile, 'w')
    
    def __del__(self):
        if hasattr(self, 'lockfile') and os.access(self.lockfile, os.F_OK): 
            if not self.lockfail:
                print("[LOCK] Removing lock file...")
                print("[CMD] rm {}".format(self.lockfile))
                os.remove(self.lockfile)
            
            print("[INFO] Changing back to current directory.")
            print("[CMD] cd {}".format(self.current_dir))
            os.chdir(self.current_dir)

class PipelineItem:
    """  
        Contains information that is specific to each item.
        Each object corresponds to one line in pipeline.in file/.
    """

    def __init__(self, session, pipeline_in_row, idx):
        
        self.jname = pipeline_in_row[0]
        
        self.rawdatafile = tests.test_input_file( "{}/{}".format(session.input_dir, pipeline_in_row[1]) )
        self.input_size = os.stat(self.rawdatafile).st_size//(1024**2)
        
        self.timestampfile = tests.test_input_file( "{}/{}".format(session.input_dir, pipeline_in_row[2]) )
        self.timestamp = utils.process_timestamp(self.timestampfile)
        print("[INPUT] The timestamp is MJD", self.timestamp)
                
        self.parfile = tests.test_input_file( "{}/{}.par".format(session.par_dir, self.jname) )
        
        self.freq_lo = float(pipeline_in_row[3])

        self.intfreq = utils.choose_int_freq(self.freq_lo)
        
        self.nbin = int(pipeline_in_row[4])
        
        self.nchan = int(pipeline_in_row[5])
        self.bandwidth = float(pipeline_in_row[6])
        self.chanwidth = -self.bandwidth/self.nchan
        
        self.tsmpl = float(pipeline_in_row[7])
        
        self.sideband = pipeline_in_row[8]
        self.sideband_code = utils.process_sideband(self.sideband)
        
        self.npol = int(pipeline_in_row[9])
        if self.npol not in [1,2,4]:
            raise ValueError("The given npol = {} is invalid.".format(self.npol))
        
        self.tsubint = float(pipeline_in_row[10])

        self.cohded = bool(int(pipeline_in_row[11]))
        
        self.freq = utils.process_freq(self.freq_lo, self.nchan, self.bandwidth, self.sideband, self.cohded)

        self.idx = idx

        self.output_root = "{:s}_{:0.6f}_{:d}".format(self.jname, float(self.timestamp), int(self.freq_lo))

        self.logdir = '{}/{}'.format(session.logdir, self.output_root)
        utils.check_mkdir(self.logdir)

        if session.retain_aux:
            self.auxdir = '{}/{}'.format(session.auxdir, self.output_root)
            utils.check_mkdir(self.auxdir)
        
        if session.run_rficlean:
            self.rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, self.jname, self.idx)
        
        self.f0psr = utils.fetch_f0(self.parfile)
        if self.f0psr <= 0:
            raise OSError("Could not read pulsar frequency from par file {}.".format(self.parfile))
    
    def desc(self):
        return '{}, MJD {}, {} MHz, {}'.format(self.jname, int(self.timestamp), self.intfreq, "CDP" if self.cohded else "PA")
    
session = Session()
