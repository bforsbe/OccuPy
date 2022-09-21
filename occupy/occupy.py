import os
import numpy as np
import mrcfile as mf
from pathlib import Path
try:
    import map_tools, occupancy, vis, solvent, extras, args              # for pyCharm
except:
    from occupy import map_tools, occupancy, vis, solvent, extras, args   # for terminal use
from skimage.exposure import match_histograms

from typing import Optional
import typer


from pkg_resources import get_distribution
__version__ =  get_distribution("occupy").version


def version_callback(value: bool):
    if value:
        print(f"OccuPy: {__version__}")
        raise typer.Exit()


def parse(
        # Basic input --------------------------------------------------------------------------------------------------

        input_map: str = typer.Option(
            None,
            "--input-map", "-i",
            help="Map to estimate [.mrc NxNxN]"
        ),
        resolution: float = typer.Option(
            None,
            "--resolution", "-r",
            help="The lowest resolution of resolvable content input map.",
            min=0.0
        ),
        amplify: float = typer.Option(
            1.0,
            "--amplify", "-am",
            help="Alter partial occupancies, to make more or less equal to full occupancy?",
            min=1.0
        ),
        attenuate: float = typer.Option(
            1.0,
            "--attenuate", "-at",
            help="Attenuate partial occupancies, to weaken lower occupancies",
            min=1.0
        ),
        sigmoid: float = typer.Option(
            1.0,
            help="Power value for sigmoid scale modification [0,1]",
            min=1.0
        ),
        pivot: float = typer.Option(
            0.01,
            help="Threshold scale value for sigmoid scale modification [0,1]",
            min=0.01,
            max=0.99
        ),

        # Specific control ---------------------------------------------------------------------------------------------

        tau: float = typer.Option(
            None,
            "--tau", "-t",
            help="Percentile for scale-estimate normalization",
            min=0.0,
            max=1.0
        ),
        kernel_size: int = typer.Option(
            None,
            "--kernel",
            help="Size of the local occupancy estimation kernel [pixels]"
        ),
        tile_size: int = typer.Option(
            None,
            "--tile-size",
            help="Size of the local region used for scale normalization [pixels]"
        ),
        lowpass_input: float = typer.Option(
            None,
            "--lowpass", "-lp",
            help="Low-pass filter the input map to this resoution prior to scale estimation. Internal default is 6*pixel-size. [Å]"
        ),
        lowpass_output: float = typer.Option(
            None,
            "--lowpass-output",
            help="Optionally low-pass filter the amplified output to this resolution [Å]"
        ),
        exclude_solvent: bool = typer.Option(
            False,
            "--exclude-solvent/--retain-solvent",
            help="Should Estimated solvent be eliminated [flattened to 0]?"
        ),
        max_box: int = typer.Option(
            256,
            help="Input maps beyond this size will be down-sampled during estimation [pixels]"
        ),
        hedge_confidence: int = typer.Option(
            None,
            help="Exponent order for confidence estimation, such that values > 1 are more careful when amplifying low occupancies"
        ),
        solvent_def: str = typer.Option(
            None,
            help="Mask that defines non-solvent, used to aid solvent model fitting. [.mrc NxNxN]"
        ),
        scale_limit: float = typer.Option(
            0.05,
            "--scale-limit",
            help="Hard limit below which map scale/occupancy will be considered unreliable for amplification",
            min=0.0,
            max=1.0
        ),
        hist_match: bool = typer.Option(
            False,
            help="Histogram-match output (force equal greyscale as input)"
        ),

        # Output control -----------------------------------------------------------------------------------------------

        output_map: str = typer.Option(
            "out_<input_file_name>",
            "--output-map", "-o",
            help="Output map name"
        ),
        plot: bool = typer.Option(
            False,
            help="Plot a histogram showing solvent model fit and occupancy confidence?"
        ),
        save_all_maps: bool = typer.Option(
            False,
            help="Save all maps used internally"
        ),
        chimerax: bool = typer.Option(
            True,
            help="Write a .cxc file that starts an interactive chimeraX session with colored input/output maps"
        ),
        chimerax_silent: bool = typer.Option(
            False,
            help="Write a .cxc file that can be opened by chimeraX to show colored input/output maps"
        ),
        show_chimerax: bool = typer.Option(
            False,
            help="Open chimeraX when done. Implies --chimerax"
        ),
        min_vis_scale: float = typer.Option(
            0.2,
            help="Lower limit of map scale (occupancy) in chimeraX coloring & color-key",
            min=0.0,
            max=1.0
        ),

        # Extra  -------------------------------------------------------------------------------------------------------
        s0: bool = typer.Option(
            False,
            "--S0/--SW",
            help="Use simple kernel normalization S0 instead of tile-based percentile (SW)"
        ),
        lp_scale: bool = typer.Option(
            None,
            "--lp-scale/--raw-scale","--occupancy",
            help="Use the low-passed input for scale estimation, or use the raw input map"
        ),
        emdb_id: str = typer.Option(
            None,
            "--emdb","--emdb-id",
            help="Fetch the main map from an EMDB entry and use as input"
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose/--quiet",
            help="Let me know what's going on"
        ),
        #relion_classes: str = typer.Option(
        #    None,
        #    help="File of classes to diversify by occupancy amplification [_model.star]"
        #),
        help_all: Optional[bool] = typer.Option(
            None,
            "--help-all",
            is_eager=True,
            help="Print lots of help and exit"
        ),
        version: Optional[bool] = typer.Option(
            None,
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Print version info and exit"
        )
):
    options = args.occupy_options(
        input_map,
        resolution,
        amplify,
        attenuate,
        sigmoid,
        pivot,
        tau,
        kernel_size,
        tile_size,
        lowpass_input,
        lowpass_output,
        exclude_solvent,
        max_box,
        hedge_confidence,
        solvent_def,
        scale_limit,
        hist_match,
        output_map,
        plot,
        save_all_maps,
        chimerax,
        chimerax_silent,
        show_chimerax,
        min_vis_scale,
        s0,
        lp_scale,
        emdb_id,
        verbose,
        help_all,
        version
    )

    occupy_run(options)

def occupy_run(options: args.occupy_options):

    """
    OccuPy takes a cryo-EM reconstruction produced by averaging and estimates a self-normative local map scaling.
    It can also locally alter confident partial occupancies.
    """
    
    if options.help_all:
        extras.help_all()

    if options.input_map is None:
        if options.emdb_id is None:
            exit(1)  # TODO surely a better way to do nothing with no options. Invoke help?
        else:
            input_map = map_tools.fetch_EMDB(options.emdb_id)

    if options.plot:
        import matplotlib.pyplot as plt

    # Remove path for output
    new_name = Path(options.input_map).name
    # Force .mrc for output
    new_name = f'_{Path(new_name).stem}.mrc'

    doc = ''

    do_amplify = options.amplify is not None
    do_attenuate = options.attenuate is not None
    do_sigmoid = options.sigmoid is not None

    if do_sigmoid and options.pivot is None:
        raise ValueError("You have to provide --pivot to do sigmoid modification using --sigmoid ")

    if do_amplify and options.amplify==1:
        print(f'\033[93mSetting --amplify to 1 means to not modify at all, which is pointless.\033[0m')
        do_amplify = False
    if options.attenuate and options.attenuate == 1:
        print(f'\033[93mSetting --attenuate to 1 means to not modify at all, which is pointless.\033[0m')
        attenuate = False
    if do_sigmoid and options.sigmoid == 1:
        print(f'\033[93mSetting --sigmoid to 1 means to not modify at all, which is pointless.\033[0m')
        do_sigmoid = False

    modify = do_amplify or do_attenuate or options.exclude_solvent
    if modify:
        if options.output_map == 'out_<input_file_name>':
            output_map = 'out' + new_name
    else:
        output_map = None

    if do_amplify or do_attenuate or do_sigmoid:
        # If modifying, then occupancy is probably desired, in which case it makes sense to use low-passed
        # input for scale estimation. But if --raw-scale (which sets lp_scale to false) is set, we don't override it
        if options.lp_scale is None:
            options.lp_scale = True
    else:
        # If not modifying, then scale might as well reflect resolutio-dependent scale as well, in which low-passed
        # input should NOT be used for scale estimation. But if --lp-scale is set, we don't override it
        if options.lp_scale is None:
            options.lp_scale = False

    assert options.lp_scale is not None # Temp check


    # --------------- READ INPUT ---------------------------------------------------------------

    f_open = mf.open(options.input_map)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size_ori = voxel_size = np.copy(f_open.voxel_size.x)
    range_ori = np.array([f_open.header['dmin'],f_open.header['dmax']])
    axis_order = np.array([f_open.header['mapc'],f_open.header['mapr'],f_open.header['maps']])
    offset_ori = np.array([f_open.header['nxstart'],f_open.header['nystart'],f_open.header['nzstart']])
    f_open.close()

    if not len(np.unique(in_data.shape)) == 1:
        raise ValueError(f'\033[91m input map is not cubic (pixel-extents: {nd})\033[0m')
    if not (nd[0] % 2)==0:
        raise ValueError(f'\033[91m input map is not even-sized. (pixel-extents: {nd})\033[0m')
    if not (options.max_box % 2 == 0) and (options.max_box < nd[0]):
        raise ValueError(f'\033[91m You specified an odd (not even) --max-box value ({options.max_box})\033[0m')


    print(f'Estimating local scale of {options.input_map}...')
    # --------------- LIMIT PROCESSING SIZE ----------------------------------------------------

    downscale_processing = nd[0] > options.max_box
    factor = 1
    if downscale_processing:
        factor = options.max_box / nd[0]

        in_data, voxel_size = map_tools.lowpass(
            in_data,
            output_size=options.max_box,
            voxel_size=voxel_size_ori,
            square=True,
            resample=True
        )

        if options.save_all_maps:
            # Save downscaled processing map
            map_tools.new_mrc(
                in_data.astype(np.float32),
                "downscaled.mrc",
                parent=options.input_map,
                verbose=options.verbose,
            )
    nd_processing = np.shape(in_data)[0]

    # The radius of flattened solvent masking
    radius = int(nd_processing // 2)

    # Use raw (but downscaled) data for scale estimation
    scale_data = np.copy(in_data)

    # --------------- SETTINGS -----------------------------------------------------------------

    # Use low-pass filter to
    # - improve solvent estimation significance
    # - eliminate reslution-dependent scale factors
    # If a lowpass or resolution is provided, use it. Otherwise default to 8.0Å
    if options.lowpass_input is None:
        if options.resolution is None:
            lower_limit_default = 3 * voxel_size # 3 pixels
            lowpass_input = np.max([lower_limit_default,8.0]) # 8 Å default unless large pixel size
        else:
            lowpass_input = options.resolution  # Å
    elif options.resolution is not None:
        if options.resolution < options.lowpass_input:
            print(f'Warning: provided --resolution/-r value ({options.resolution}) is not used, since --lowpass/-lp ({options.lowpass_input}) is greater')
        lowpass_input = np.float32(np.max([options.lowpass_input,options.resolution]))
    lowpass_input = np.float32(lowpass_input)

    # The size of the scale-estimation kernel.
    if options.kernel_size is None:
        # How many pixels do we fit into the significant highest frequency?
        kernel_size = int(np.floor(lowpass_input / voxel_size))
        # Make it an odd size
        kernel_size = ((kernel_size // 2) * 2) + 1
        # It should be larger than 1, and never needs to be bigger than 9.
        kernel_size = np.clip(kernel_size, 3, 9)

    # Make a kernel (morphological structuring element) for max-filter (greyscale dilation).
    kernel_radius = lowpass_input / (2 * voxel_size)

    kernel_warn=False
    if kernel_size < 5:
        kernel_warn=True
        print(f'\033[93m \nAuto-calculated a very small kernel-size ({kernel_size} pixels). \nThis may lead to a bad solvent model \nSuggest --kernel 5 or more, and/or --lowpass {int(lowpass_input*2)} or more \n \033[0m')

    if kernel_radius < kernel_size/(2*2):
        print(f'\033[93m \nAuto-calculated a very small kernel radius ({kernel_radius:.2f} pixels). \nThis may lead to a bad solvent model \nSuggest --lowpass {int(lowpass_input*2)} or more \n \033[0m')
        kernel_warn = True

    scale_kernel, tau_ana = occupancy.spherical_kernel(
        kernel_size,
        radius=kernel_radius
    )

    own_tau = False
    n_v = int(np.sum(scale_kernel))
    tau_ana = occupancy.set_tau(n_v=n_v)
    if options.tau is None:
        tau = tau_ana
    else:
        own_tau = True
        if options.verbose:
            print(f'Using provided tau value of {options.tau} instead of recommended {tau_ana} for kernel size {kernel_size}')




    log_name = f'log_{Path(options.input_map).stem}.txt'
    f_log = open(log_name, 'w+')
    print(f'\n---------------I/O AND CALCULATED SETTINGS-------', file=f_log)
    print(f'Input    :\t     \t {options.input_map}', file=f_log)
    print(f'Pix      :\t[A]  \t {voxel_size_ori:.2f}', file=f_log)
    print(f'Box in   :\t[pix]\t {nd}', file=f_log)
    print(f'Box proc :\t[pix]\t {np.shape(in_data)}', file=f_log)
    if downscale_processing:
        print(f'Pix proc :\t[A]  \t {voxel_size:.2f}', file=f_log)
    print(f'Box radi :\t[pix]\t {radius:.3f}', file=f_log)
    print(f'Kernel s :\t[pix]\t {kernel_size}', file=f_log)
    print(f'Kernel r :\t[pix]\t {kernel_radius:.2f}', file=f_log)
    print(f'Kernel nv:\t[pix]\t {n_v}', file=f_log)
    print(f'Tau      :\t[0,1]\t {tau:.3f}', file=f_log)
    if own_tau:
        print(f'Tau(rec).:\t[0,1]\t {tau_ana:.3f}', file=f_log)
    print(f'LP Filt. :\t[A]  \t {lowpass_input:.2f}', file=f_log)
    if options.lp_scale:
        print(f'LP scale :\t     \t {options.lp_scale} (Try to ignore res)', file=f_log)
    else:
        print(f'LP scale :\t     \t {options.lp_scale} (Include res-dep)', file=f_log)
    print(f'Scale lim:\t[0,1]\t {options.scale_limit:.3f}', file=f_log)

    # ----- LOW-PASS SETTINGS ---------

    use_lp = False
    scale_mode = 'res'
    if lowpass_input > 2 * voxel_size:
        use_lp = True

        lp_data, _ = map_tools.lowpass(
            in_data,
            lowpass_input,
            voxel_size=voxel_size,
            square=False,
            resample=False
        )
        if options.save_all_maps:
            map_tools.new_mrc(
                lp_data,
                f'lowpass{new_name}',
                parent=input_map,
                verbose=options.verbose,
                log=f_log
            )
        if options.lp_scale:
            scale_data = np.copy(lp_data)
            scale_mode = 'occ'
            if options.verbose:
                print('Using low-passed input to estimate scale')
        else:
            if options.verbose:
                print('Using raw input to estimate scale')

        sol_data = np.copy(lp_data)
        del lp_data

    else:

        sol_data = np.copy(in_data)


    # We apply any estimations or solvent operation on the raw input (possibly down-sized)
    if modify:
        out_data = np.copy(in_data)

    # --------------- PLOTTING STUFF------------------------------------------------------------

    if options.plot:
        interactive_plot = False  # TODO sort this in flags, or omit.
        global f, ax1, ax2
        f = plt.figure()

    # --------------- SOLVENT ESTIMATION -------------------------------------------------------

    mask = map_tools.create_radial_mask(nd_processing, dim=3, radius=radius)
    if options.solvent_def is not None:
        s_open = mf.open(options.solvent_def)
        sol_mask  = np.copy(s_open.data)
        s_open.close()

        # Check same size as ori inout map (can be relaxed later)
        if not sol_mask.shape[0] == nd:
            raise ValueError(f'\033[91m input solvent definition map  size ({sol_mask.shape}) is not the same size as input map: {nd}\033[0m')

        if downscale_processing:
            sol_mask, _ = map_tools.lowpass(
                sol_mask,
                output_size=options.max_box,
                voxel_size=voxel_size_ori,
                square=True,
                resample=True
            )

        assert sol_mask.shape == sol_data.shape

        # Make a mask from the solvent definition.
        # People might provide a mask that covers the solvent or content, we will use it as makes most sense
        solvent_region = solvent.smallest_variance_region(
            sol_data,       # data
            sol_mask,    # solvent def
            mask            # radial mask
        )

        h_data = sol_data[solvent_region].flatten()
    else:
        assert sol_data.shape == mask.shape
        h_data = sol_data[mask].flatten()

    # Estimate the solvent model
    levels = 1000
    sol_limits, solvent_parameters = solvent.fit_solvent_to_histogram(
        h_data,
        plot=options.plot,
        n_lev=levels
    )

    # --------------- SCALE ESTIMATION ------------------------------------------------------

    scale_map = f'scale_{scale_mode}{new_name}'
    scale, max_val, tiles_raw = occupancy.get_map_scale(
        scale_data,
        scale_kernel=scale_kernel,
        tau=tau,
        save_occ_map=scale_map,
        s0=options.s0,
        tile_size=options.tile_size,
        verbose=options.verbose
    )
    map_tools.adjust_to_parent(file_name=scale_map, parent=options.input_map)

    # Fix the tile coordinates found during percentiel serach, for plotting
    tiles=np.copy(tiles_raw)

    #Set tile coordinates according to axis order in input file
    for i in np.arange(3):
        tiles[:,2-i] = tiles_raw[:,axis_order[i]-1]

    # Add any offset in the input file coords (but not radius),  and make in original non-pix length.
    tiles[:-1,:] = voxel_size_ori*(tiles[:-1,:] / factor + offset_ori)

    # Set radius to original non-pix length as well
    tiles[-1,:] = voxel_size_ori * tiles[-1,:] / factor

    if options.verbose:
        print(f'Corrected tile max: {tiles[0,:]}')

    # Get the average pixel value across all regions with full scale
    # This is an estimate of the density, which we can convert back to a scale,
    # which in turn signifies the expected scale at full occupancy and full variability/flex
    variability_limit = np.mean(scale_data[scale==1]) / max_val
    del scale_data

    # --------------- CONFIDENCE ESTIMATION ------------------------------------------------------

    confidence, mapping = occupancy.estimate_confidence(
        sol_data,
        solvent_parameters,
        hedge_confidence=options.hedge_confidence,
        n_lev=levels
    )

    # clean sol_data asap
    if options.plot:
        a, b = np.histogram(sol_data, bins=levels, density=True)
    del sol_data

    warnings=None

    # A high value of lowest confident scale means a wide solvent model compared to the overall histogram
    lowest_confident_scale = sol_limits[3] / max_val
    if options.verbose:
        print(f'Min c.sc :\t[0,1]\t {lowest_confident_scale:.3f}', file=f_log)

    # Dirty check on the solvent model, could be more rigorous
    if modify:

        if lowest_confident_scale > 0.5:
            warnings = "Solvent model fit is likely bad. Check terminal output and"
            if not options.plot:
                warnings = f'{warnings} run with --plot and check solModel*.png'
            else:
                warnings = f'{warnings} check the output solModel*.png '
            solvent.warn_bad(lowest_confident_scale,file=f_log,verbose=options.verbose,kernel_warn=kernel_warn)


    # --------------- MODIFY INPUT MAP IF AMPLIFYING AND/OR SUPPRESSING SOLVENT ------------------
    if options.exclude_solvent:
        output_map = 'solExcl_' + Path(options.output_map).stem + '.mrc'
        doc = 'Solvent exclusion '

    fake_solvent = None  # Will not  add fake solvent during amplify

    attn_map = None
    ampl_map = None

    if do_amplify or options.exclude_solvent:
        ampl = occupancy.modify(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            gamma=options.amplify,  # The exponent for amplification / attenuation
            sigmoid_mu=options.pivot,  # The scale value for sigmoid modificaiton
            attenuate=False,  # False is amplifying or not doing anything
            fake_solvent=fake_solvent,
            scale_threshold=options.scale_limit,
            save_amp_map=options.save_all_maps,
            verbose=options.verbose
        )

        if options.save_all_maps:
            map_tools.adjust_to_parent(file_name='modification.mrc', parent=input_map)

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        ampl = solvent.suppress(
            ampl,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            options.exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        ampl = map_tools.lowpass_map(
            ampl,
            options.lowpass_output,
            voxel_size,
            keep_scale=True
        )

        # If the input map was larger than the maximum processing size, we need to get back the bigger size as output
        if downscale_processing:
            ampl, _ = map_tools.lowpass(
                ampl,
                output_size=nd[0],
                square=True,
                resample=True
            )

        # -- Match output range --
        # inverse filtering can create a few spurious pixels that
        # ruin the dynamic range compared to the input. This is mostly
        # aesthetic.
        # TODO Compare power spectrum of input out put to examine spectral effect
        # TODO also check the average change in pixel value, anf how it relates to power spectral change
        if options.hist_match:
            f_open = mf.open(input_map)
            ampl = match_histograms(
                ampl,
                reference=f_open.data
            )  # Output is no longer input + stuff, i.e. good part is now something else.
            f_open.close()
        else:
            ampl = map_tools.clip_to_range(
                ampl,
                range=range_ori
            )

        # TODO  -  Test histogram-matching of low-occupancy regions with high-occupancy as reference?

        # Save amplified and/or solvent-suppressed output.
        if options.amplify:
            if options.pivot is not None:
                ampl_map = f'sigmoid_{options.amplify:.1f}_{options.pivot:.1f}_' + Path(output_map).stem + '.mrc'
            else:
                ampl_map = f'ampl_{options.amplify:.1f}_' + Path(output_map).stem + '.mrc'
            ampl_doc = f'{doc} attenuation gamma={options.amplify:.2f}'
        else:
            ampl_map = output_map
            ampl_doc = f'{doc}'

        map_tools.new_mrc(
            ampl.astype(np.float32),
            ampl_map,
            parent=options.input_map,
            verbose=options.verbose,
            extra_header=ampl_doc
        )

        del ampl

    if do_attenuate:
        if not options.exclude_solvent:
            # If we are not excluding solvent, then we will add some back when we attenuate
            fake_solvent = np.random.randn(nd_processing, nd_processing, nd_processing)
            fake_solvent = solvent_parameters[1] + solvent_parameters[2] * fake_solvent
            # TODO:
            # what is the correct scaling factor of the variance here????
            # also spectral properties

        attn = occupancy.modify(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            gamma=options.attenuate,  # The exponent for amplification / attenuation
            attenuate=True,  # False is amplifying or not doing anything
            fake_solvent=fake_solvent,
            scale_threshold=options.scale_limit,
            save_amp_map=options.save_all_maps,
            verbose=options.verbose
        )

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        attn = solvent.suppress(
            attn,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            options.exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        attn = map_tools.lowpass_map(
            attn,
            options.lowpass_output,
            voxel_size,
            keep_scale=True
        )

        # If the input map was larger than the maximum processing size, we need to get back the bigger size as output
        if downscale_processing:
            attn, _ = map_tools.lowpass(
                attn,
                output_size=nd[0],
                square=True,
                resample=True
            )

        # -- Match output range --
        # inverse filtering can create a few spurious pixels that
        # ruin the dynamic range compared to the input. This is mostly
        # aesthetic.
        # TODO Compare power spectrum of input out put to examine spectral effect
        # TODO also check the average change in pixel value, anf how it relates to power spectral change
        if options.hist_match:
            f_open = mf.open(input_map)
            attn = match_histograms(
                attn,
                reference=f_open.data
            )  # Output is no longer input + stuff, i.e. good part is now something else.
            f_open.close()
        else:
            attn = map_tools.clip_to_range(
                attn,
                range=range_ori
            )
        # TODO  -  Test histogram-matching of low-occupancy regions with high-occupancy as reference?

        # Save amplified and/or solvent-suppressed output.
        attn_map = f'attn_{options.attenuate:.1f}_' + Path(output_map).stem + '.mrc'
        attn_doc = f'{doc} attenuation gamma={options.attenuate:.2f}'
        map_tools.new_mrc(
            attn.astype(np.float32),
            attn_map,
            parent=options.input_map,
            verbose=options.verbose,
            extra_header=attn_doc
        )

        del attn

    # ----------------OUTPUT FILES AND PLOTTING -------------------------------------------------
    if options.save_all_maps:

        map_tools.new_mrc(
            confidence.astype(np.float32),
            f'conf{new_name}',
            parent=input_map,
            verbose=options.verbose,
            log=f_log
        )

    if options.show_chimerax:
        chimerax=True

    if options.chimerax:
        chimx_file =vis.chimx_viz(
            options.input_map,
            scale_map,
            ampl_map=ampl_map,
            attn_map=attn_map,
            threshold_input=(max_val+sol_limits[3]) / 2.0,
            threshold_scale=variability_limit,
            threshold_ampl=(max_val + sol_limits[3]) / 2.0,
            threshold_attn=(max_val + sol_limits[3]) / 2.0,
            min_scale=options.min_vis_scale,
            tiles=tiles,
            warnings=warnings
        )

    if options.chimerax_silent:
        chimx_file_silent = vis.chimx_viz(
            options.input_map,
            scale_map,
            ampl_map=ampl_map,
            attn_map=attn_map,
            threshold_input=(max_val+sol_limits[3]) / 2.0,
            threshold_scale=variability_limit,
            threshold_ampl=(max_val + sol_limits[3]) / 2.0,
            threshold_attn=(max_val + sol_limits[3]) / 2.0,
            min_scale=options.min_vis_scale,
            silent=True,
            warnings=warnings
        )


    if options.plot:
        f = plt.gcf()
        f.set_size_inches(20, 4)
        ax1 = f.axes[0]

        if options.solvent_def is not None:
            ax1.plot(b[:-1], a, 'gray', label='unmasked data')
        ax1.plot(b[:-1], np.clip(mapping, ax1.get_ylim()[0], 1.0), 'r', label='confidence')
        if options.hedge_confidence is not None:
            ax1.plot(b[:-1], np.clip(mapping ** options.hedge_confidence, ax1.get_ylim()[0], 1.0), ':r',
                     label='hedged confidence')

        ax1.legend()

        save_name = options.input_map
        has_solvent_def = None
        if options.solvent_def is not None:
            has_solvent_def = Path(options.solvent_def).stem

        vis.save_fig(
            save_name,
            extra_specifier=has_solvent_def
        )

        if interactive_plot:
            plt.show()

        n_lines = 5
        n_elements = 1000
        col = plt.cm.binary(np.linspace(0.3,0.7,n_lines+1))

        if options.pivot is not None:
            f2 = plt.figure()
            x = np.linspace(0,1,n_elements)
            plt.plot(x, x, color=col[0], label=f'gamma=1')
            for i in np.arange(n_lines):
                t = options.pivot
                val = 1+np.sqrt(t)*2**i # just values that shows some range depending on mu.
                _, y=occupancy.scale_mapping_sigmoid(options.pivot,val,n_elements)
                plt.plot(x,y,color=col[i+1],label=f'gamma={val:.2f}')
            # The actual value used
            _, y=occupancy.scale_mapping_sigmoid(options.pivot,options.amplify,n_elements)
            plt.plot(x,y,'--',color='green',label=f'gamma={options.amplify}')
            plt.legend()
            plt.savefig("sigmoid_modification.png")
        elif modify:
            f3 = plt.figure()
            x = np.linspace(0,1,n_elements)
            col_ampl = plt.cm.Blues(np.linspace(0.3,0.7,n_lines))
            col_attn = plt.cm.Reds(np.linspace(0.3, 0.7, n_lines))
            for i in np.arange(n_lines):
                k = 2**i
                if do_amplify:
                    plt.plot(x,x**(1/k), color=col_ampl[i], label=f'ampl gamma={int(k)}')
                if do_attenuate:
                    plt.plot(x,x**k,color=col_attn[i],label=f'attn gamma={int(k)}')
            if do_amplify:
                plt.plot(x, x ** (1 / options.amplify), color='green', label=f'ampl gamma={options.amplify}')
            if do_attenuate:
                plt.plot(x, x ** options.attenuate, color='blue', label=f'attn gamma={options.amplify}')

            plt.legend()
            plt.savefig("gamma_modification.png")

        if interactive_plot:
            plt.show()



    print(f'\n------------------------------------Detected limits-------', file=f_log)
    print(f'Content at 1% of solvent  : \t {sol_limits[2]:.3f}', file=f_log)
    print(f'Solvent drop to 0% (edge) : \t {sol_limits[3]:.3f}', file=f_log)
    print(f'Solvent peak              : \t {solvent_parameters[1]:.3f}', file=f_log)
    print(f'Occupancy full            : \t {max_val:.3f}', file=f_log)
    print(f'Variability_limit         : \t {variability_limit:.3f}', file=f_log)
    print(f'Scale confidence limit    : \t {lowest_confident_scale:.3f}', file=f_log)

    f_log.close()
    if options.verbose:
        f_log = open(log_name, 'r')
        print(f_log.read())
        f_log.close()


    if modify:
        print(f'\033[92mDone\033[0m estimating local scale and modifying input by local scale. ')
    else:
        print(f'\033[92mDone\033[0m estimating local scale')
        print(f'You \033[96mcould\033[0m also modify according to estimated occupancy by using either --amplify, --attenutate, or both')

    if not options.exclude_solvent:
        print(
            f'You \033[96mcould\033[0m also exclude solvent by adding --exclude-solvent')

    if options.chimerax:
        if options.show_chimerax:
            print(f'\033[92m \nOpening {chimx_file} in chimeraX, this may take a moment. Please be patient. \033[0m \n')
            os.system(f'chimerax {chimx_file} & ')
        else:
            print(f'\nYou should run chimeraX to visualize the output, using this command: ')
            print(f'\033[92m \nchimerax {chimx_file} \033[0m \n')
            print(f'HINT: you could also auto-start chimeraX by using --show-chimerax')

    if options.chimerax_silent:
        if options.show_chimerax:
             os.system(f'chimerax {chimx_file}')
        else:
            print(f'\nTo generate thumbnails of your output, run: ')
            print(f'\033[94m \nchimerax --offscreen {chimx_file_silent} \033[0m \n')

    return 0

if __name__ == '__main__':
    typer.run(parse)


def app():
    typer.run(parse)
