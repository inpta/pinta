This is a version of the `sigproc` package written by Duncan Lorimer customized for GMRT by B.C. Joshi.

`pinta` only uses the `filterbank` command in this package. 

I will clean up this distribution and remove code unnecessary for `pinta` later.

# Usage

    $ filterbank <raw_data_file> -mjd <starting_time> -rf <frequency> -nch {nchan} -bw {channelwidth} -ts {sampling_time} -df {sideband} > {output_file}

- `raw_data_file` is the path to the input file in GMRT raw data format.
- `starting_time` is the timestamp at the start of observation in MJD.
- `frequency` is the frequency label (in MHz) of the highest frequency channel in the observing band.
- `nchan` is the number of frequency channels.
- `channelwidth` is the bandwidth of a single channel.
- `sampling_time` is the sampling time at which the data is recorded.
- `sideband` is a code for the sideband used. "gmgwbf" represents upper sideband and "gmgwbr" represents lower sideband.
- `output_file` is the path to the output file in filterbank format.
