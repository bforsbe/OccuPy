import os
import numpy as np
import mrcfile as mf
from pathlib import Path

from occupy_lib import map_tools, occupancy, vis, solvent, extras, args   # for terminal use

from skimage.exposure import match_histograms


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
            options.input_map = map_tools.fetch_EMDB(options.emdb_id)
            if options.scale_mode is None:
                options.scale_mode = 'res'

    if options.plot:
        import matplotlib.pyplot as plt



    # Remove path for output
    new_name = Path(options.input_map).name
    # Force .mrc for output
    new_name = f'{Path(new_name).stem}.mrc'
    doc = ''


    do_amplify = options.amplify > 1
    do_attenuate = options.attenuate > 1
    do_sigmoid = options.sigmoid > 1
    do_exclude_solvent = options.exclude_solvent
    do_modify = do_amplify or do_attenuate or do_sigmoid

    # Save amplified and/or solvent-suppressed output.'
    base_out_name = f'{new_name}'
    if do_exclude_solvent:
        base_out_name = f'solExcl_{new_name}'
        doc = f'solvent exclusion, {doc}'

    if do_sigmoid and options.pivot is None:
        raise ValueError("You have to provide --pivot to do sigmoid modification using --sigmoid ")


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

    assert options.lp_scale is not None  # Temp check

    # --------------- READ INPUT ---------------------------------------------------------------

    f_open = mf.open(options.input_map)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size_ori = voxel_size = np.copy(f_open.voxel_size.x)
    range_ori = np.array([np.min(f_open.data),np.max(f_open.data)]) # header info is unreliable from e.g. relion_postprocess_localfiltered
    axis_order = np.array([f_open.header['mapc'], f_open.header['mapr'], f_open.header['maps']])
    offset_ori = np.array([f_open.header['nxstart'], f_open.header['nystart'], f_open.header['nzstart']])
    f_open.close()

    if not len(np.unique(in_data.shape)) == 1:
        raise ValueError(f'** fail ** input map is not cubic (pixel-extents: {nd})')
    if not (nd[0] % 2) == 0:
        raise ValueError(f'** fail **  input map is not even-sized. (pixel-extents: {nd})')
    if not (options.max_box % 2 == 0) and (options.max_box < nd[0]):
        raise ValueError(f'** fail **  You specified an odd (not even) --max-box value ({options.max_box})')

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

    # --------------- SETTINGS -----------------------------------------------------------------

    # Use low-pass filter to
    # - improve solvent estimation significance
    # - eliminate reslution-dependent scale factors
    # If a lowpass or resolution is provided, use it. Otherwise default to 8.0Å
    if options.lowpass_input is None:
        if options.resolution is None:
            lower_limit_default = 3 * voxel_size  # 3 pixels
            options.lowpass_input = np.max([lower_limit_default, 8.0])  # 8 Å default unless large pixel size
        else:
            lowpass_input = options.resolution  # Å
    elif options.resolution is not None:
        if options.resolution < options.lowpass_input and options.resolution > 0 :
            print(
                f'Warning: provided --resolution/-r value ({options.resolution}) is not used, since --lowpass/-lp ({options.lowpass_input}) is greater')
        options.lowpass_input = np.float32(np.max([options.lowpass_input, options.resolution]))
    options.lowpass_input = np.float32(options.lowpass_input)

    # The size of the scale-estimation kernel.
    if options.kernel_size is None:
        # How many pixels do we fit into the significant highest frequency?
        options.kernel_size = int(np.floor(options.lowpass_input / voxel_size))
        # Make it an odd size
        options.kernel_size = ((options.kernel_size // 2) * 2) + 1
        # It should be larger than 1, and never needs to be bigger than 9.
        options.kernel_size = np.clip(options.kernel_size, 3, 9)

    # Make a kernel (morphological structuring element) for max-filter (greyscale dilation).
    if options.kernel_radius is None:
        options.kernel_radius = options.lowpass_input / (2 * voxel_size)

    kernel_warn = False
    if options.kernel_size < 5:
        kernel_warn = True
        print(
            f'** warn ** Auto-calculated a very small kernel-size ({options.kernel_size} pixels). \n** warn ** This may lead to a bad solvent model \n** warn ** Suggest --kernel 5 or more, and/or --lowpass {int(options.lowpass_input * 2)} or more\n')

    if options.kernel_radius < options.kernel_size / (2 * 2):
        print(
            f'** warn ** Auto-calculated a very small kernel radius ({options.kernel_radius:.2f} pixels). \n** warn ** This may lead to a bad solvent model \n** warn ** Suggest --lowpass {int(options.lowpass_input * 2)} or more\n')
        kernel_warn = True

    scale_kernel, tau_ana = occupancy.spherical_kernel(
        options.kernel_size,
        radius=options.kernel_radius
    )

    own_tau = False
    n_v = int(np.sum(scale_kernel))
    tau_ana = occupancy.set_tau(n_v=n_v)
    if options.tau is None:
        options.tau = tau_ana
    else:
        own_tau = True
        if options.verbose:
            print(
                f'Using provided tau value of {options.tau:.4f} (recommend {tau_ana:.4f})')

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
    print(f'Kernel s :\t[pix]\t {options.kernel_size}', file=f_log)
    print(f'Kernel r :\t[pix]\t {options.kernel_radius:.2f}', file=f_log)
    print(f'Kernel nv:\t[pix]\t {n_v}', file=f_log)
    print(f'Tau      :\t[0,1]\t {options.tau:.3f}', file=f_log)
    if own_tau:
        print(f'Tau(rec).:\t[0,1]\t {tau_ana:.3f}', file=f_log)
    print(f'LP Filt. :\t[A]  \t {options.lowpass_input:.2f}', file=f_log)
    if options.lp_scale:
        print(f'LP scale :\t     \t {options.lp_scale} (Try to ignore res)', file=f_log)
    else:
        print(f'LP scale :\t     \t {options.lp_scale} (Include res-dep)', file=f_log)
    print(f'Scale lim:\t[0,1]\t {options.scale_limit:.3f}', file=f_log)
    if options.lowpass_output is not None:
        print(f'LP output:\t     \t {options.lowpass_output} (Include res-dep)', file=f_log)
    #else:
    #    options.lowpass_output = None

    # ----- LOW-PASS SETTINGS ---------

    use_lp = False
    if options.scale_mode=='occ':
        use_lp=True

    scale_data = np.copy(in_data)
    if options.lowpass_input > 2 * voxel_size:

        lp_data, _ = map_tools.lowpass(
            in_data,
            options.lowpass_input,
            voxel_size=voxel_size,
            square=False,
            resample=False
        )
        if options.save_all_maps:
            map_tools.new_mrc(
                lp_data,
                f'lowpass_{new_name}',
                parent=options.input_map,
                verbose=options.verbose,
                log=f_log
            )
        if use_lp:
            scale_data = np.copy(lp_data)
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
    if do_modify or do_exclude_solvent:
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
        sol_mask = np.copy(s_open.data)
        s_open.close()

        # Check same size as ori inout map (can be relaxed later)
        if not sol_mask.shape == nd:
            raise ValueError(
                f'** fail ** input solvent definition map  size {sol_mask.shape} is not the same size as input map: {nd}')

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
            sol_data,  # data
            sol_mask,  # solvent def
            mask  # radial mask
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

    scale_map = f'scale_{options.scale_mode}_{new_name}'
    if options.s0:
        scale_map = f'scale_naive_{options.scale_mode}_{new_name}'
    scale, max_val, tiles_raw = occupancy.get_map_scale(
        scale_data,
        scale_kernel=scale_kernel,
        tau=options.tau,
        save_occ_map=scale_map,
        s0=options.s0,
        tile_size=options.tile_size,
        scale_mode=options.scale_mode,
        verbose=options.verbose
    )
    map_tools.adjust_to_parent(file_name=scale_map, parent=options.input_map)

    tiles = None
    if tiles_raw is not None:
        # Fix the tile coordinates found during percentiel serach, for plotting
        tiles = np.copy(tiles_raw)

        # Set tile coordinates according to axis order in input file
        for i in np.arange(3):
            tiles[:, 2 - i] = tiles_raw[:, axis_order[i] - 1]

        # Add any offset in the input file coords (but not radius),  and make in original non-pix length.
        tiles[:-1, :] = voxel_size_ori * (tiles[:-1, :] / factor + offset_ori)

        # Set radius to original non-pix length as well
        tiles[-1, :] = voxel_size_ori * tiles[-1, :] / factor

        if options.verbose:
            print(f'Corrected tile max: {tiles[0, :]}')

    # Get the average pixel value across all regions with full scale
    # This is an estimate of the density, which we can convert back to a scale,
    # which in turn signifies the expected scale at full occupancy and full variability/flex
    variability_limit = np.mean(scale_data[scale == 1]) / max_val
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

    warnings = None

    # A high value of lowest confident scale means a wide solvent model compared to the overall histogram
    lowest_confident_scale = sol_limits[3] / max_val
    if options.verbose:
        print(f'Min c.sc :\t[0,1]\t {lowest_confident_scale:.3f}', file=f_log)

    # Dirty check on the solvent model, could be more rigorous
    if lowest_confident_scale > 0.5:
        warnings = "Solvent model fit is likely bad. Check output log for warnings and"
        if not options.plot:
            warnings = f'{warnings} run with --plot and check solModel*.png'
        else:
            warnings = f'{warnings} check the solvent model'
        solvent.warn_bad(lowest_confident_scale, file=f_log, verbose=options.verbose, kernel_warn=kernel_warn)



    fake_solvent = None  # Will not  add fake solvent during amplify

    ampl_name = None
    attn_name = None
    sigm_name = None

    if do_amplify:
        ampl = occupancy.modify(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            amplify_gamma=options.amplify,  # The exponent for amplification / attenuation
            scale_threshold=options.scale_limit,
            save_modified_map=options.save_all_maps,
            verbose=options.verbose
        )

        if options.save_all_maps:
            map_tools.adjust_to_parent(file_name='modification_ampl.mrc', parent=options.input_map)

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        ampl = solvent.suppress(
            ampl,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            do_exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        if options.lowpass_output is not None:
            ampl, _ = map_tools.lowpass(
                ampl,
                options.lowpass_output,
                voxel_size
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
            f_open = mf.open(options.input_map)
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

        ampl_name = f'ampl_{options.amplify:.1f}_{base_out_name}'
        ampl_doc = f'ampl {options.amplify:.1f}, {doc}'

        map_tools.new_mrc(
            ampl.astype(np.float32),
            ampl_name,
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
            attenuate_gamma=options.attenuate,  # The exponent for amplification / attenuation
            fake_solvent=fake_solvent,
            scale_threshold=options.scale_limit,
            save_modified_map=options.save_all_maps,
            verbose=options.verbose
        )

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        attn = solvent.suppress(
            attn,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            do_exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        if options.lowpass_output is not None:
            attn, _ = map_tools.lowpass(
                attn,
                options.lowpass_output,
                voxel_size
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
        attn_name = f'attn_{options.attenuate:.1f}_{base_out_name}'
        attn_doc = f'attn {options.attenuate:.1f}, {doc}'

        map_tools.new_mrc(
            attn.astype(np.float32),
            attn_name,
            parent=options.input_map,
            verbose=options.verbose,
            extra_header=attn_doc
        )

        del attn

    if do_sigmoid:
        #if not options.exclude_solvent:
        # TODO: sigmoid noise comp

        if not options.exclude_solvent:
            # If we are not excluding solvent, then we will add some back when we attenuate
            fake_solvent = np.random.randn(nd_processing, nd_processing, nd_processing)
            fake_solvent = solvent_parameters[1] + solvent_parameters[2] * fake_solvent

            # TODO:
            # what is the correct scaling factor of the variance here????
            # also spectral properties

        sigm = occupancy.modify(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            sigmoid_gamma=options.sigmoid,  # The exponent for sigmoid
            sigmoid_pivot=options.pivot,
            fake_solvent=fake_solvent,
            scale_threshold=options.scale_limit,
            save_modified_map=options.save_all_maps,
            verbose=options.verbose
        )

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        sigm = solvent.suppress(
            sigm,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            do_exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        if options.lowpass_output is not None:
            sigm, _ = map_tools.lowpass(
                sigm,
                options.lowpass_output,
                voxel_size
            )

        # If the input map was larger than the maximum processing size, we need to get back the bigger size as output
        if downscale_processing:
            sigm, _ = map_tools.lowpass(
                sigm,
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
            f_open = mf.open(options.input_map)
            sigm = match_histograms(
                sigm,
                reference=f_open.data
            )  # Output is no longer input + stuff, i.e. good part is now something else.
            f_open.close()
        else:
            sigm = map_tools.clip_to_range(
                sigm,
                range=range_ori
            )
        # TODO  -  Test histogram-matching of low-occupancy regions with high-occupancy as reference?

        # Save amplified and/or solvent-suppressed output.
        sigm_name = f'sigm_{options.sigmoid:.1f}-{options.pivot:.2f}_{base_out_name}'
        sigm_doc = f'sigm {options.sigmoid:.1f} {options.pivot:.2f}, {doc}'

        map_tools.new_mrc(
            sigm.astype(np.float32),
            sigm_name,
            parent=options.input_map,
            verbose=options.verbose,
            extra_header=sigm_doc
        )

        del sigm

    solExcl_only_name = None
    if not do_modify and do_exclude_solvent:
        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        solExcl_only = solvent.suppress(
            out_data,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            do_exclude_solvent,  # Only add back if not excluding solvent
            verbose=options.verbose
        )

        # -- Low-pass filter output --
        solExcl_only = map_tools.lowpass_map(
            solExcl_only,
            options.lowpass_output,
            voxel_size,
            keep_scale=True
        )

        # If the input map was larger than the maximum processing size, we need to get back the bigger size as output
        if downscale_processing:
            solExcl_only, _ = map_tools.lowpass(
                solExcl_only,
                output_size=nd[0],
                square=True,
                resample=True
            )

        # Save solvent-suppressed output.
        solExcl_only_name = f'{base_out_name}'
        solExcl_only_doc = f'{doc}'

        map_tools.new_mrc(
            solExcl_only.astype(np.float32),
            solExcl_only_name,
            parent=options.input_map,
            verbose=options.verbose,
            extra_header=solExcl_only_doc
        )

        del solExcl_only

    # ----------------OUTPUT FILES AND PLOTTING -------------------------------------------------
    #if options.save_all_maps:
    map_tools.new_mrc(
        confidence.astype(np.float32),
        f'conf_{new_name}',
        parent=options.input_map,
        verbose=options.verbose,
        log=f_log
    )

    # If auto-opening, must write the file for it
    if options.show_chimerax:
        options.chimerax = True

    if options.chimerax:
        chimx_file = vis.chimx_viz(
            options.input_map,
            scale_map,
            ampl_map=ampl_name,
            attn_map=attn_name,
            sigm_map=sigm_name,
            solExcl_only_map=solExcl_only_name,
            threshold_maps=(max_val + sol_limits[3]) / 2.0,
            threshold_scale=variability_limit,
            min_scale=options.min_vis_scale,
            tiles=tiles,
            warnings=warnings
        )

    if options.chimerax_silent:
        chimx_file_silent = vis.chimx_viz(
            options.input_map,
            scale_map,
            ampl_map=ampl_name,
            attn_map=attn_name,
            sigm_map=sigm_name,
            threshold_map=(max_val + sol_limits[3]) / 2.0,
            threshold_scale=variability_limit,
            min_scale=options.min_vis_scale,
            silent=True,
            warnings=warnings
        )

    if options.plot:
        f = plt.gcf()
        f.set_size_inches(12, 2.52)
        ax1 = f.axes[0]

        if options.solvent_def is not None:
            ax1.plot(b[:-1], a, 'gray', label='unmasked data')
        ax1.plot(b[:-1], np.clip(mapping, ax1.get_ylim()[0], 1.0), 'r', label='confidence')
        if options.hedge_confidence is not None:
            ax1.plot(b[:-1], np.clip(mapping ** options.hedge_confidence, ax1.get_ylim()[0], 1.0), ':r',
                                  label='hedged confidence')

        # It would be nice to plot this, but this is on the lp (sol_data) hist
        # plt.plot([max_val,max_val],ax1.get_ylim(),'k-',label='full scale')

        ax1.legend(bbox_to_anchor=(1, 1), loc="upper left",prop={'size': 11})
        plt.subplots_adjust(
            top=0.94,
            bottom=0.154,
            left=0.062,
            right=0.688)
        #f.tight_layout(rect=[0, 0, 1.05, 1.05])

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
        col = plt.cm.binary(np.linspace(0.3, 0.7, n_lines + 1))

        if options.pivot is not None:
            f2 = plt.figure()
            x = np.linspace(0, 1, n_elements)
            plt.plot(x, x, color=col[0], label=f'gamma=1')
            for i in np.arange(n_lines):
                t = options.pivot
                val = 1 + np.sqrt(t) * 2 ** i  # just values that shows some range depending on mu.
                _, y = occupancy.scale_mapping_sigmoid(options.pivot, val, n_elements)
                plt.plot(x, y, color=col[i + 1], label=f'gamma={val:.2f}')
            # The actual value used
            _, y = occupancy.scale_mapping_sigmoid(options.pivot, options.amplify, n_elements)
            plt.plot(x, y, '--', color='green', label=f'gamma={options.amplify}')
            plt.legend()
            plt.savefig("sigmoid_modification.png")
        elif do_modify:
            f3 = plt.figure()
            x = np.linspace(0, 1, n_elements)
            col_ampl = plt.cm.Blues(np.linspace(0.3, 0.7, n_lines))
            col_attn = plt.cm.Reds(np.linspace(0.3, 0.7, n_lines))
            for i in np.arange(n_lines):
                k = 2 ** i
                if do_amplify:
                    plt.plot(x, x ** (1 / k), color=col_ampl[i], label=f'ampl gamma={int(k)}')
                if do_attenuate:
                    plt.plot(x, x ** k, color=col_attn[i], label=f'attn gamma={int(k)}')
            if do_amplify:
                plt.plot(x, x ** (1 / options.amplify), color='green', label=f'ampl gamma={options.amplify}')
            if do_attenuate:
                plt.plot(x, x ** options.attenuate, color='blue', label=f'attn gamma={options.amplify}')

            plt.legend()
            plt.savefig("gamma_modification.png")

        if interactive_plot:
            plt.show()

    print(f'\n------------------------------------Detected limits-------', file=f_log)
    print(f'Content at 1% of solvent  \t: \t {sol_limits[2]:.3f}', file=f_log)
    print(f'Solvent drop to 0% (edge) \t: \t {sol_limits[3]:.3f}', file=f_log)
    print(f'Solvent peak        \t    \t: \t {solvent_parameters[1]:.3f}', file=f_log)
    print(f'Full scale          \t    \t: \t {max_val:.3f}', file=f_log)
    print(f'Variability_limit   \t    \t: \t {variability_limit:.3f}', file=f_log)
    print(f'Scale confidence limit    \t: \t {lowest_confident_scale:.3f}', file=f_log)

    f_log.close()
    if options.verbose:
        f_log = open(log_name, 'r')
        print(f_log.read())
        f_log.close()

    if options.gui:
        print(f'\n  -*- Use chimeraX to view output -*- \n')
    else:
        if do_modify:
            print(f'Done estimating local scale and modifying input by local scale. ')
        else:
            print(f'Done estimating local scale')
            print(
                f'You *could* also modify according to estimated occupancy by using either amplify, attenuate, and/or sigmoid')

        if not options.exclude_solvent:
            print(
                f'You *could* also exclude solvent ')

        if options.chimerax and not options.gui:
            if options.show_chimerax:
                print(f'Opening {chimx_file} in chimeraX, this may take a moment. Please be patient.\n')
                os.system(f'chimerax {chimx_file} & ')
            else:
                print(f'\nYou should run chimeraX to visualize the output, using this command: ')
                print(f'chimerax {chimx_file}\n')
                print(f'HINT: you could also auto-start chimeraX by using --show-chimerax')

        if options.chimerax_silent:
            if options.show_chimerax:
                os.system(f'chimerax {chimx_file}')
            else:

                print(f'\nTo generate thumbnails of your output, run: ')
                print(f'\nchimerax --offscreen {chimx_file_silent}\n')

    return 0