


def help_all():
	help_text="""
--------------------- BASIC INPUT --------------------

--input-map/-i
An input map in .mrc format. Currently, this needs to be cubic, i.e. with equal sides.  Occupy expects this to contain solvent noise, but sometimes solvent-flattening and AI-guided map modifications are ok. The input map is automatically masked with a radius equal to half the box-size, so that its corners are not considered.

--resolution/-r
The estimated resolution [Å] of the input map, which is best set to the largest value of relevant content. If amplifying/attenuating (modifying) by scale, this is the worst resolution of components that are to be modified. This is to assure that the resolution-dependent contribution to local scale estimate is minimized. If the local scale of components expected to be of full occupancy are estimated at lower scale, it is possible to compensate this by reducing the --tile size, or --tau/-t value.  The chosen resolution is also used to determine parameters that can be set explicitly if so desired: a reasonable low-pass filter to apply to the map initially (--lowpass/-lp), which dictates the kernel size (--kernel-size/-k) and tau value (--tau/-t).

--amplify/-am
If set, confident partial occupancies will be amplified by applying a gamma-factor (power-scaling) to the estimated local scale of the input map, equal to 1/gamma. This option requires that one also specifies --gamma. This option can be used along --attenuate/-at, which will do the opposite and produce a separate output file. This option can be used in combination with --exclude-solvent.

	gamma = 0		not permitted
	0 < gamma < 1	attenuate, so not permitted
	gamma = 1		do nothing
	gamma > 1		amplify by applying S^(1/gamma)
	gamma = inf		amplify all occupancies to 100%

Theory:			input = full * S   <=>   full  =  input  * S^-1
Implemented:	amplified = full * S^(1/gamma) = input * S^((1/gamma) - 1)

NOTE: the amplified output is an amplified version of the input, but the implementation reflects that S is the local scale of the input. Hence, S is always going to act as an attenuation, but of the theoretical full-scale map.


--attenuate/-at
If set, confident partial occupancies will be attenuated by applying a gamma-factor (power-scaling) to the estimated local scale of the input map. This option requires that one also specifies --gamma. This option can be used along --amplify/-am,which will do the opposite and produce a separate output file. This option can be used in combination with --exclude-solvent.

	gamma = 0		not permitted
	0 < gamma < 1	amplify, so not permitted
	gamma = 1		do nothing
	gamma > 1		attenuate by applying S^(gamma)
	gamma = inf		attenuate all occupancies to 0%, except those at 100%

Theory:			input = full * S   <=>   full  =  input  * S^-1
Implemented:	attenuated = full * S^(gamma) = input * S^((gamma) - 1)


--gamma/-g
The power [1<] of scale modification. Any number larger than 1. This is used for Either or both of the options --amplify/-am and/or --attenuate/at. At each voxel the local scale S is estimated. The theoretical full-scale map is calculated by dividing by S (multiplying by S^-1). This map is then further modified by the estimated partial scale S of the input map:

--------------------- CONTROL OPTIONS --------------------

--tau/-t   (OPTIONAL, dep on )
The percentile [0<tau<1] for scale-map normalization. The scale is essentially estimated as the range of pixel-values in a small region. Instead of using the full range, a percentile is used to make it robust to outlier values and to act as a grey-scale dilation filter (as in morphological image processing). This percentile is chosen optimally based on the size of the region considered, which depeneds on the resolution, lowpass and pizel size.

Lower values will consider lower values as "high", and tend to make more regions of the input map estimated at full occupancy. The uncertainty of the estimated scale can naively be considered as 1-tau, so a lower setting will lead to larger uncertainty.

--kernel/-k
The size [pixels] of the region considered when estimating the local scale, i.e. it's 'locality'. A larger egion will achieve better significance by sampling more voxels, but suffer decreased resolution. It is *not* recommended to change this setting.

--tile-size
The size of the regions used to define the scale normalization. Choosing a smaller value means that you permit a smaller region to be used to define "full" scale. If you have heavy atoms, then these will tend to dominate a small region, and define "full" scale. If you set it too big, no "full scale" region will be found, and the normalization is too small, leading to over-estimated scale. The default is big neough to not account for single atoms like mteal ions, but look for protein or nucleic acid regions as "full" scale refrence volumes. 

--lowpass/-lp
The maximal resolution [Å] consider in the input map. Low-pass filtering the input tends to allow better estimation of solvent, which can lead to better confidence of low-scale components.

--lowpass-output
The maximal resolution [Å] consider in the output map.

--exclude-solvent/--retain-solvent
Solvent is included by default, i.e. the amplified or attenuated output maps(s) retain the noise around them that is estimated as solvent. Using this option, the output omits this noise. This is useful for visualization, but is not recommended in outher contexts.

NOTE: This option does *not* require amplifiaction or attentiuation. If used without any of these options, the outout is simply a solvent-masked input map.

--max-box
The box-size [pixels] than is used internally to perform any estimation or modification. The output maps will always be the same size as the input, but internally the map may be down-scale if larger than this value. This will limit the resolution of the output, as reported in the output log.

--hedge-confidence
The solvent model leads to a confidence of the estimated local scale, which tends to decrease along with the scale. Integer value larger than 1 supplied through this option will be used as a power-scaling of the confidence, such that values > 1 results to less modification of low-scale regions. 

--solvent-def
An .mrc-format map of the same size as the input, that delinetes content from solvent. This only affects scale-based modification, not the scale estimation itself, and so is only useful along with either amplifaction and/or attenuation.

It does not matter if the mask covers solvent or content, the program will invert it if necessary by comparing it against the input map. This can be a conventional solvent mask, but it is not used as such. Instead, it is used to limit the content of the input map that is used to estiamte a solvent model.

--scale-limit
The lower limit [<1] that is considered  when amplifying or attenuating. The default value of 0.05 means that any scale estimated below 5% will not be amplified or further attenuated.

--hist_match
If set, the output map will be subject to histogram-matching against the input map. This will force an equal gray-scale, which is typically good even wihtout this option.

--------------------- OUTPUT OPTIONS --------------------

--output-map/-o
Name of the output

--plot
Save a figure of the input histogram, solvent model, confidence, and scale parameters. If using a solvent-definition, this will show a histogram of the voxels included.

--save_all_maps
If set, a number of intermediate stages of the processing will be written to  allow analysis of what is applied to the input
	- low-passed input
	- confidence of points as non-solvent
	- the modification applied

--chimerax/--no-chimerax
If set, a .cxc command script is written that will allow the output to be easily visualized. This is on by default

--chimerax_silent
If set, a .cxc command script is written that will allow thumbnails to be generated. Typical useage is
	[linux] chimerax --offscreen chimX_file_silent.cxc

--min_vis_scale
The lower limit [<1] of the estimated scale that is used for visualization in the chimeraX command-scripts. The default value of 0.2 means that all estiamted scales below this value are colored as the minimum occupancy.

--------------------- EXTRA OPTIONS --------------------  
--S0/--SW
Two modes of scale normalization are implemented. By default, SW is used, which considers the distribution of the data within local regions when determining the edfinintion of "full" scale. S0 is a simpler normalization that tends to make the estimated scale be more sensitive to intense points in the input map.

--lp-scale/--raw-scale, --occupancy
The low-pass frequency is determined from the --lowpass/-lp and --resolution/-r flags. By default, the 

--verbose/--quiet
Print information during use

--version
Print the version

--help
Get brief help on input options

--help-all
Get extensive help on input options
"""
	print(help_text)
	exit