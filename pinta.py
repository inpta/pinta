#!/usr/bin/python3
""" Generate and execute commands to reduce the raw uGMRT data into TIMER format.

    Developers: Abhimanyu Susobhanan, Yogesh Maan
"""

import shutil
import sys
import os
import numpy as np
import parse
import getopt
import time
import glob
import yaml
import datetime
#import multiprocessing as mproc

if '--log-to-file' in sys.argv:
    now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    logfile = 'pinta.{}.log'.format(now)
    print('Output will be written to', logfile)
    sys.stdout = open(logfile, 'w')

import pintautils as utils
import pintaexec as pexec
from pintasession import session

for idx, item in enumerate(session.pipeline_items):
    
    if session.run_gptool:
        utils.copy_gptool_in(session.gptool_in_dir, session.current_dir, item.intfreq)
        pexec.gptool_branch(session, item)
    else:
        pexec.norfix_branch(session, item)
    
    if session.run_rficlean:
        rfic_hdrfilename = "{}/{}-{}-ttemp-gm.info".format(session.working_dir, item.jname, item.idx)
        utils.make_rficlean_hdrfile(rfic_hdrfilename, item.jname, item.freq, item.nchan, item.chanwidth, item.tsmpl, item.sideband)
        os.system('ls -l *.info')
        pexec.rficlean_branch(session, item)

    if session.retain_aux:
        utils.move_aux_files(session, item)
    else:
        utils.remove_aux_files(session, item)

session.finish() 
