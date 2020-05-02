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
import astropy.time as astrotime
import getopt
import time
import pintautils as utils

#= Parsing command line ============
cmdargs = sys.argv[1:]

opts, args = getopt.gnu_getopt(cmdargs, "", ["gptdir=", "pardir=", "help", "test", "no-gptool", "no-rficlean", "nodel"])
opts = dict(opts)

#= Displaying help =================
if opts.get("--help") is not None:
	print("Usage : ")
	print("uGMRT_pipeline.py [--help] [--test] [--no-gptool] [--no-rficlean] [--nodel] [--gptdir <...>] [--pardir <...>] <input_dir> <working_dir>")
	sys.exit(0)

if len(args)<2:
	print("Input and working directories must be provided as command line arguments.")
	sys.exit(0)
else:
	input_dir = args[0]
	working_dir= args[1]

#= Testing Lock ===================
lockfile = "{}/{}".format(working_dir, 'pinta.lock')
if os.access(lockfile, os.F_OK):
	print("Another instance of pinta seems to be running on this directory.")
	print("*IMPORTANT* If you are /sure/ this is a mistake, please remove pinta.lock manualy and try again. DOING THIS MAY CORRUPT THE DATA.")
	sys.exit(0)
else:
	print("Creating lock file...")
	utils.touch_file(lockfile)


test_run = opts.get("--test") is not None
if test_run:
	print("Running in test mode. Commands will only be displayed and not executed.")

if opts.get("--pardir") is not None:
	print("*.par directory provided in command line.")
	par_dir = opts.get("--pardir")
else:
	par_dir = "/Data/bcj/INPTA/30june2018/gwbh7/parfilesinpta/"

if opts.get("--gptdir") is not None:
	print("gptool.in directory provided in command line.")
	gptool_in_dir = opts.get("--gptdir")
else:
	gptool_in_dir = "/misc/home/asusobhanan/Work/gptool_files"

run_gptool = opts.get("--no-gptool") is None
if run_gptool:
	print("Will run gptool.")
else:
	print("Will not run gptool.")

run_rficlean = opts.get("--no-rficlean") is None
if run_rficlean:
	print("Will run rficlean.")
else:
	print("Will not run rficlean.")

delete_tmp_files = opts.get("--nodel") is None
if delete_tmp_files:
	print("Will remove intermediate products.")
else:
	print("Will not remove intermediate products.")

#===================================

# Checking if all required programs are present
for program in ['gptool','dspsr','filterbank','tempo2','pdmp']:
	if not utils.check_program(program):
		sys.exit(0)

##################################################################

# Checking directories for permissions
print("The working directory is %s"%working_dir)
if not utils.check_dir(working_dir):
	sys.exit(0)

print("The input directory is %s"%input_dir)
for folder in [input_dir,par_dir]:
	if not utils.check_read_dir(folder):
		sys.exit(0)
if run_gptool:
	if not utils.check_read_dir(gptool_in_dir):
		sys.exit(0)

##################################################################


# Checking gptool.in files for permissions
if run_gptool:
	for freq in [499,749,1459]:
		if not utils.check_input_file("%s/gptool.in.%d"%(gptool_in_dir,freq)):
			sys.exit(0)

##################################################################

# Checking and reading pipeline.in
if not utils.check_input_file("%s/pipeline.in"%(working_dir)):
	sys.exit(0)
print("Reading %s/pipeline.in..."%(working_dir), end=' ')
try:
	pipeline_in_data = np.genfromtxt("%s/pipeline.in"%(working_dir), dtype=str, comments='#')
	if len(pipeline_in_data.shape)==1:
		pipeline_in_data = np.asarray([pipeline_in_data])
	
	no_of_cols_expected = 11
	if pipeline_in_data.shape[1] != no_of_cols_expected:
		print("Invalid format... Quitting...")
		sys.exit(0)
	print("Done. %d item(s) to be processed."%(len(pipeline_in_data)))
except ValueError:
	print("Invalid format... Quitting...")
	sys.exit(0)

##################################################################

no_of_observations = len(pipeline_in_data)
for i,pipeline_input in enumerate(pipeline_in_data):
	
	psr_start_time = time.time()	

	psrj, rawdatafile, timestamp_file, frequency, nbins, nchannels, bandwidth, samplingtime, sideband_, pol_opt, integ_durn = pipeline_input
	print("\nProcessing %s (%d of %d)..."%(psrj,i+1,no_of_observations))

	for infile in [rawdatafile, timestamp_file]:
		if not utils.check_input_file("%s/%s"%(input_dir, infile)):
			sys.exit(0)
	
	# Checking the par file for permissions
	parfile = "%s/%s.par"%(par_dir,psrj)
	if not utils.check_input_file(parfile):
		sys.exit(0)

	#### for rficlean ...
	if run_rficlean:
		
		print("Trying to get the pulsar's spin frequency...\n")
		try:
			f0psr = utils.fetch_f0(parfile)
		except:
			print("Could not fetch F0 from the parfile. Quitting...")
			sys.exit(0)
		if f0psr<0.0:
			print("could not fetch F0 from the parfile. Quitting...")
			sys.exit(0)
		
		####	
		print("Trying to make the rficlean-gmhdr file ...\n")
		if not utils.make_rficlean_hdrfile(("%s/%s-ttemp-gm.info"%(working_dir,psrj)), psrj,frequency,nchannels,bandwidth,samplingtime,sideband_):
			print ("Could not make the rficlean-gmhdr file!")
			sys.exit(0)
	####	

	print("Processing timestamp file...", end=' ')
	try:
		timestamp_mjd = utils.process_timestamp(input_dir+'/'+timestamp_file)
	except Exception as e:
		print("Could not process timestamp file. Quitting...")
		sys.exit(0)
	print("Done.   Timestamp = ", timestamp_mjd)
	
	if sideband_ == 'USB':
		sideband = 'gmgwbf'
	elif sideband_ == 'LSB':
		sideband = 'gmgwbr'
	else:
		print("The given sideband is invalid. Quitting...")
		sys.exit(0)

	if run_gptool:
		gpt_start_time = time.time()
		freq_int = utils.choose_int_freq(float(frequency))
		print("Creating %s/gptool.in for frequency %d..."%(working_dir,freq_int),end=' ')
		try:
			gptool_in_src = "%s/gptool.in.%d"%(gptool_in_dir,freq_int)
			gptool_in_dst = "%s/gptool.in"%(working_dir)
			shutil.copy(gptool_in_src,gptool_in_dst)
		except Exception:
			print("Could not create. Quitting...")
			sys.exit(0)
		print("Done.")

		print("Running gptool...")
		cmd = "gptool -f %s/%s -nodedisp -o %s"%(input_dir,rawdatafile,  working_dir)
		print("cmd :: %s"%(cmd))
		# Run gptool here.
		if not test_run:
			os.system(cmd)
		gpt_file = rawdatafile+".gpt"
		filterbank_in_file = gpt_file
		filterbank_in_dir = working_dir
		gpt_stop_time = time.time()
		print("[TIME] Execution time for gptool = ",gpt_stop_time-gpt_start_time)
	else:
		filterbank_in_file = rawdatafile
		filterbank_in_dir = input_dir

	fil_start_time = time.time()
	print("Creating filterbank file...")
	#rawdata_size = os.stat(rawdatafile).st_size//(1024**2)
	rawdata_size = os.stat("%s/%s"%(input_dir,rawdatafile)).st_size//(1024**2)
	out_file_root = psrj+"."+str(timestamp_mjd)+"."+str(frequency)+"."+str(rawdata_size)+"M"
	fil_file = out_file_root+'.fil' 
	cmd = ("filterbank %s/%s -mjd %0.15f -rf %s -nch %s -bw %s -ts %s -df %s > %s/%s"%(filterbank_in_dir,filterbank_in_file,timestamp_mjd,frequency,nchannels,bandwidth,samplingtime,sideband, working_dir, fil_file))
	print("cmd :: %s"%(cmd))
	# Run filterbank here.
	if not test_run:
		os.system(cmd)
	fil_stop_time = time.time()
	print("[TIME] Execution time for filterbank = ",fil_stop_time-fil_start_time)	

	if run_gptool and delete_tmp_files:
		# Now delete gpt file
		print('Removing %s/%s...'%(working_dir,gpt_file), end=' ')
		if not test_run:
			try:
				os.remove("%s/%s"%(working_dir,gpt_file))
				print("Done.")
			except:
				print("Could not delete gpt file.")
		else:
			print('Done.')	

	dspsr_start_time = time.time()
	print("Running dspsr...")	
	# This command produces output in the "TIMER" format and "PSRFITS" format.
	# For PSRFITS format use "-a PSRFITS" option. For some reason this fails with a segfault.
	# So we are stuck with the TIMER format for the time being. Need to debug this.
	cmd = "dspsr -N %s -d %s -b %s -E %s -L %s   -A %s/%s -O %s/%s -e fits "%(psrj,pol_opt,nbins,parfile, integ_durn, working_dir, fil_file, working_dir,out_file_root)
	print("cmd :: %s"%cmd)
	# Run dspsr here
	if not test_run:
		os.system(cmd)
	dspsr_stop_time = time.time()
	print("[TIME] Execution time for dspsr = ", dspsr_stop_time-dspsr_start_time)
	
	# Now delete fil files
	if delete_tmp_files:
		print("Removing %s/%s ..."%(working_dir, fil_file), end=' ')
		if not test_run:
			try:
				os.remove("%s/%s"%(working_dir, fil_file))
				print("Done.")
			except:
				print("Could not delete fil file.")
		else:
			print('Done.')

	if run_rficlean:
		# #################################################################################
		# =================================================================================
		# Now get a rfiCleaned filterbank file
		rficlean_start_time = time.time()
		cleanfil_file = out_file_root+'.rfiClean.fil' 
		Nprocess = 16
		#cmd = ("/home/ymaan/bin/rficlean -t 16384  -ft 6  -st 10  -rt 4  -white  -pcl  -psrf %f  -psrfbins 32  -o %s/%s  -ps %s.rfiClean.ps -gm %s/ttemp-gm.info  -gmtstamp %s/%s   %s/%s"%(f0psr, working_dir,cleanfil_file, out_file_root, working_dir,psrj, input_dir,timestamp_file,  input_dir,rawdatafile))
		cmd = ('/home/ymaan/bin/crp_rficlean_gm.sh  %s/%s  /home/ymaan/inpta_pipeline/inpta_rficlean.flags  %d  %s/%s  %s/%s-ttemp-gm.info  "-psrf %f  -psrfbins 32  -gmtstamp %s/%s"'%(working_dir,cleanfil_file,  Nprocess,  input_dir,rawdatafile,   working_dir,psrj,  f0psr,  input_dir,timestamp_file))
		print("cmd :: %s"%(cmd))
		# run the command to generate rfiCleaned filterbank file...
		if not test_run:
			os.system(cmd)
		rficlean_stop_time = time.time()
		print("[TIME] Execution time for rfiClean = ", rficlean_stop_time-rficlean_start_time)
		
		# Now generate the rfiClean-ed fits file using dspsr
		dspsr_rc_start_time = time.time()
		print("Running dspsr on rfiCleaned filterbankd file...")	
		cmd = "dspsr -N %s -d %s -b %s -E %s -L %s   -A %s/%s -O %s/%s.rfiClean -e fits "%(psrj,pol_opt,nbins,parfile, integ_durn, working_dir, cleanfil_file, working_dir,out_file_root)
		print("cmd :: %s"%cmd)
		# Run dspsr here
		if not test_run:
			os.system(cmd)
		dspsr_rc_stop_time = time.time()
		print("[TIME] Execution time for dspsr (rfiClean) = ", dspsr_rc_stop_time-dspsr_rc_start_time)
		# =================================================================================

		if delete_tmp_files:
			# Now delete rfiCleaned filterbank file
			print("Removing %s/%s ..."%(working_dir, cleanfil_file), end=' ')
			if not test_run:
				try:
					os.remove("%s/%s"%(working_dir, cleanfil_file))
					print("Done.")
				except:
					print("Could not delete rfiCleaned filterbank-file.")
			else:
				print('Done.')


	print("Creating summary plots...")
	cmd = "pdmp -mc 64 -g %s/%s_summary.ps/cps %s.fits"%(working_dir, out_file_root, out_file_root)
	print("cmd :: ",cmd)
	if not test_run:
		os.system(cmd)	
	
	if run_rficlean:	
		cmd = "pdmp -mc 64 -g %s/%s.rfiClean_summary.ps/cps %s.rfiClean.fits"%(working_dir, out_file_root, out_file_root)
		print("cmd :: ",cmd)
		if not test_run:
			os.system(cmd)
        # #################################################################################

	print("Processing %s (%d of %d) successful."%(psrj,i+1,no_of_observations))
	
	psr_stop_time = time.time()
	print("[TIME] Total processing time = ", psr_stop_time-psr_start_time)


print("Process finished.")
print("Removing lock file...")
os.remove(lockfile)
