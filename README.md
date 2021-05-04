# pinta
`pinta` is a data analysis pipeline for upgraded GMRT pulsar data. It RFI mitigates and folds uGMRT data to form Timer archives. 

A detailed description of `pinta` is given in 
Susobhanan et al., 2020 (https://doi.org/10.1017/pasa.2021.12).
If you use this pipeline in your research, please cite this paper,
along with those for the two RFI excision tools that `pinta` heavily
make use of (`RFIClean`: https://doi.org/10.1051/0004-6361/202040164, `gptool`:to be updated).

## Installing

### Installing Dependencies

Install the following pulsar packages by following the installation instructions given in their respective websites/repositories.
- tempo2 (https://bitbucket.org/psrsoft/tempo2/src/master/)
- dspsr (http://dspsr.sourceforge.net/)
- psrchive (http://psrchive.sourceforge.net/)
- RFIClean (https://github.com/ymaan4/RFIClean)
- gptool (https://github.com/chowdhuryaditya/gptool)

Install the python dependencies.

    $ pip3 install parse astropy pyyaml --user

### Installing `filterbank-gmrt`

    $ cd filterbank-gmrt
    $ ./configure

This script will ask for a directory where the executable will be created. Enter an appropriate path.
Note that the `filterbank` executable must be in `$PATH` for `pinta` to work. 
 
    $ make filterbank
    $ cd ..

### Permissions

One persistent issue that arises while analyzing data using a pipeline is maintaining correct permissions for the data files. 
The way we deal with this is to use one user group for all analysis using `pinta`. 
For example, we will use the `pulsar` group name in this guide. The following command should be run at the start of every session before running `pinta`.
(Make sure that this group is created and you are added to it.)

    $ newgrp pulsar

### Installing `pinta`

Say you want to install `pinta` in `/pinta/install/path/`. 

    $ git clone https://github.com/abhisrkckl/pinta.git
    $ cp pinta/pinta pinta/pinta*.py pinta/pinta.yaml /pinta/install/path/
    $ chgrp pulsar /pinta/inst/path/*
    $ chmod ug+r /pinta/inst/path/*
    $ chmod ug+x /pinta/inst/path/pinta

Now add this line to your `.bashrc` file.

    $ export PATH=$PATH:/pinta/install/path/pinta

### Configuring `pinta`

The `pinta` configuration is stored in `pinta.yaml`. This file should be saved in the same directory as the `pinta` executable script. `pinta.yaml` looks like this:
    
        pinta:
            pardir: /pinta/par/dir/
            gptdir: /pinta/gpt/dir/
            rficconf: /pinta/rfic/dir/inpta_rficlean.flags
            group: pulsar

- `pardir` is the directory where the pulsar ephemeris (par) files (named like J1234+5678.par) are stored. These files are needed for folding.
- `gptdir` is the directory where the gptool configuration files (`gptool.in.*`) are stored. See `examples` directory for examples.
- `rficconf` contains the flags to be passed to `RFIClean`. See `examples` directory for example.
- `group` is the user group which has permissions to run `pinta`.

### Running `pinta`

#### Input files

For each observation uGMRT produces two files - a binary raw data file and a timestamp file. Both are required for analysis.

#### Usage

`pinta` is invoked from the command line with the following syntax.

    $ pinta [--help] [--test] [--no-gptool] [--no-rficlean] [--nodel] [--retain-aux] [--log-to-file] [--gptdir <...>] [--pardir <...>] [--rficconf <...>] <input_dir> <working_dir>

- `<input_dir>` is the directory where the input (raw data and timestamp) files are saved.
- `<working_dir>` is the directory where the output files will be created. For `pinta` to run, this directory should contain a file called `pipeline.in` containing the metadata required to do the analysis.

- `--help` prints this syntax on the screen.
- `--test` performs the input validation steps and prints out the commands without executing them. Used for debugging.
- `--no-gptool` runs `pinta` without `gptool`.
- `--no-rficlean` runs `pinta` without `RFIClean`.
- `--nodel` keeps the intermediate data products.
- `--retain-aux` keeps the auxiliary putput files produced by component programs.
- `--log-to-file` writes the `stdout` to a log file.
- `--gptdir` specifies a custom directory for `gptool.in` files. This is recommended.
- `--pardir` specifies a custom directory for par files. 
- `--rficconf` specifies a custom `RFIClean` configuration file. 

#### `pipeline.in` file

The uGMRT raw data file does not contain any metadata required to analyze it. So we provide it through an ASCII file named `pipeline.in`.
Each row in `pipeline.in` represents a raw data file. The columns are as follows:
    
1. JNAME - The J2000 of the pulsar (eg. J2124-3358)
2. RawData - The raw data file name (not the full path)
3. Timestamp - The timestamp file name (not the full path)
4. Freq - The local oscillator frequency (MHz)
5. Nbin - The number of phase bins for folding
6. Nchan - Number of frequency channels
7. BandWidth - Observation bandwidth (MHz)
8. TSmpl - Sampling time of observation (s)
9. SB - Sideband (USB - Upper sideband / LSB - Lower sideband)
10. Npol - Number of polarization products (1 - Total intensity / 4 - Stokes IQUV). Only total intensity is implemented at present.
11. TSubint - Subintegration duration for folding (s)
12. Cohded - Whether the data has been coherently dedispersed (1 - Yes / 0 - No)

An example is given in the `examples` directory.
