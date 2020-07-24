#!/usr/bin/python3.6

from pintautils import process_timestamp
import sys

if len(sys.argv)>1:
    tstmpfile = sys.argv[1]
    print(process_timestamp(tstmpfile))
