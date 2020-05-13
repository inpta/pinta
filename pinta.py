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
#import multiprocessing as mproc

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
        pexec.rficlean_branch(session, item)

    if session.retain_aux:
        utils.move_aux_files(session, item)
    else:
        utils.remove_aux_files(session, item)
            
