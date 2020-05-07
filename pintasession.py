import getopt
import sys
import os
import yaml
import numpy as np
import pintatests as tests
import pintautils as utils

helpmsg = "Usage:\npinta.py [--help] [--test] [--no-gptool] [--no-rficlean] [--nodel] [--gptdir <...>] [--pardir <...>] <input_dir> <working_dir>"

class Session:
    def __init__(self):
        
        #= Parsing command line ========================================================================================
        cmdargs = sys.argv[1:]
        opts, args = getopt.gnu_getopt(cmdargs, "", ["gptdir=", "pardir=", "help", "test", "no-gptool", "no-rficlean", "nodel", "rficconf"])
        opts = dict(opts)
        
        #= Displaying help =============================================================================================
        if opts.get("--help") is not None:
            print(helpmsg)
            sys.exit(0)        
        
        #= Script directory and Currecnt Directory =====================================================================        
        self.script_dir = tests.test_read_dir( os.path.dirname(os.path.realpath(__file__)) )
        self.current_dir = tests.test_dir( os.getcwd() )
        
        #= Input and working directories ===============================================================================
        if len(args)<2:
            print("Input and working directories must be provided as command line arguments.")
            sys.exit(0)
            
        self.input_dir = tests.test_read_dir(args[0])
        self.working_dir= tests.test_dir(args[1])
        
        #= Getting lock on working directory============================================================================
        self.get_lock()
        
        #= Test Mode ===================================================================================================
        self.test_mode = opts.get("--test") is not None
        if self.test_mode:
            print("Running in test mode. Commands will only be displayed and not executed.")
        
        #= Reading config file =========================================================================================
        self.config_file = '{}/{}'.format(self.script_dir, 'pinta.yaml')
        try:
            print("Reading config from", self.config_file)
            config = yaml.load(open(self.config_file), Loader=yaml.FullLoader)
        except:
            print("Unable to read config file ", config_file)
            sys.exit(0)
        
        #= Which branches to run =======================================================================================
        self.run_gptool = opts.get("--no-gptool") is None
        if self.run_gptool:
            print("Will run gptool.")
        else:
            print("Will not run gptool.")

        self.run_rficlean = opts.get("--no-rficlean") is None
        if self.run_rficlean:
            print("Will run rficlean.")
        else:
            print("Will not run rficlean.")
        
        #= Pulsar ephemeris directory, gptool config directory and rfiClean config file ================================
        if opts.get("--pardir") is not None:
            print("*.par directory provided in command line.")
            self.par_dir = tests.test_read_dir( opts.get("--pardir") )
        else:
            self.par_dir = tests.test_read_dir( config['pinta']['pardir'] )

        if self.run_gptool:
            if opts.get("--gptdir") is not None:
                print("gptool.in directory provided in command line.")
                self.gptool_in_dir = tests.test_read_dir( opts.get("--gptdir") )
            else:
                self.gptool_in_dir = tests.test_read_dir( config['pinta']['gptdir'] )
        
        if self.run_rficlean:
            if opts.get("--rficconf") is not None:
                print("rfiClean configuration file profided in command line.")
                self.rfic_conf_file = tests.test_input_file( opts.get("--rficconf") )
            else:
                self.rfic_conf_file = tests.test_input_file( config['pinta']["rficconf"] )

        #= Whether to delete intermediate outputs ======================================================================
        self.delete_tmp_files = opts.get("--nodel") is None
        if self.delete_tmp_files:
            print("Will remove intermediate products.")
        else:
            print("Will not remove intermediate products.")
        
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
        
        print("Reading %s/pipeline.in..."%(self.working_dir), end=' ')
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
        
        self.auxdir = "{}/aux".format(self.working_dir)
        utils.check_mkdir(self.auxdir)
        
        self.logdir = "{}/log".format(self.working_dir)
        utils.check_mkdir(self.logdir)
        
        self.pipeline_items = []
        for idx, row in enumerate(self.pipeline_in_data):
            try:
                self.pipeline_items.append( PipelineItem(self, row) )
            except:
                print("Error processing row #{} of pipeline.in".format(idx+1))
                
                
    def get_lock(self):
        self.lockfile = "{}/{}".format(self.working_dir, 'pinta.lock')
        if os.access(self.lockfile, os.F_OK):
            print("Another instance of pinta seems to be running on this directory.")
            print("*IMPORTANT* If you are /sure/ this is a mistake, please remove pinta.lock manualy and try again. DOING THIS MAY CORRUPT THE DATA.")
            sys.exit(0)
        else:
            print("Creating lock file...")
            utils.touch_file(self.lockfile)
        
    def finish(self):
        print("Removing lock file...")
        os.remove(self.lockfile)
        sys.exit(0)
    
    def exec_cmd(self, cmd, logfile):
        lfname = '{}/aux/{}'.format(self.working_dir)
        lf = open(logfile, 'w')
    
    def __del__(self):
        if hasattr(self, 'lockfile') and os.access(self.lockfile, os.F_OK): 
            print("Removing lock file...")
            os.remove(self.lockfile)

class PipelineItem:
    def __init__(self, session, pipeline_in_row):
        
        self.jname = pipeline_in_row[0]
        
        self.rawdatafile = tests.test_input_file( "{}/{}".format(session.working_dir, pipeline_in_row[1]) )
        
        self.timestampfile = tests.test_input_file( "{}/{}".format(session.working_dir, pipeline_in_row[2]) )
        self.timestamp = utils.process_timestamp(self.timestampfile)
        
        self.parfile = tests.test_input_file( "{}/{}.par".format(session.pardir, self.jname) )
        
        self.freq_lo = float(pipeline_in_row[3])

        self.intfreq = utils.choose_int_freq(self.freq_lo)        
        utils.copy_gptool_in(session.gptdir, session.current_dir, self.intfreq)
        
        self.nbin = int(pipeline_in_row[4])
        
        self.nchan = int(pipeline_in_row[5])
        self.chanwidth = float(pipeline_in_row[6])
        if self.chanwidth >= 0:
            raise ValueError("ChannelWidth should be negative.")

        self.tsmpl = float(pipeline_in_row[7])
        
        self.sideband = float(pipeline_in_row[8])
        self.sideband_code = utils.process_sideband(self.sideband)
        
        self.npol = int(pipeline_in_row[9])
        if self.npol not in [1,2,4]:
            raise ValueError("The given npol = {} is invalid.".format(self.npol))
        
        self.tsubint = float(pipeline_in_row[10])

        self.cohded = bool(int(pipeline_in_row[11]))
        
        self.freq = utils.process_freq(self.freq_lo, self.nchan, self.chanwidth, self.cohded)

        self.auxdir = '{}/{}'.format(session.logdir, idx)
        self.logdir = '{}/{}'.format(session.auxdir, idx)
        utils.check_mkdir(self.logdir)
        utils.check_mkdir(self.auxdir)
    
session = Session()