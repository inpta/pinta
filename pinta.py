#!/usr/bin/python3
""" Generate and execute commands to reduce the raw uGMRT data into psrfits format.

    Original developer:  Abhimanyu Susobhanan

    Contributing developer: Yogesh Maan

    (included appropriate modules and commands to rfiClean the raw-gmrt-data and
     then generate a rfiCleaned fits file as well.  -- yogesh, July 28)
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
        pexec.gptool_branch(session, item)
    else:
        pexec.norfix_branch(session, item)
    
    if session.run_rficlean:
        pexec.rficlean_branch(session, item)

