import numpy as np
import mrcfile as mf
from pathlib import Path
#import map_tools, occupancy, vis, solvent
from occupy import map_tools, occupancy, vis, solvent
from skimage.exposure import match_histograms

from typing import Optional
import typer


from pkg_resources import get_distribution
__version__ =  get_distribution("occupy").version


def version_callback(value: bool):
    if value:
        print(f"OccuPy: {__version__}")
        raise typer.Exit()


def main(
        # Basic input --------------------------------------------------------------------------------------------------

        input_map: str = typer.Option(
            None,
            "--input-map", "-i",
            help="Map to estimate [.mrc NxNxN]"
        ),
        resolution: float = typer.Option(
            None,
            "--resolution", "-r",
            help="Resolution of input map"
        ),
        amplify: bool = typer.Option(
            False,
            "--amplify", "-ap",
            help="Alter partial occupancies, to make more or less equal to full occupancy?"
        ),
        attenuate: bool = typer.Option(
            False,
            "--attenuate", "-at",
            help="Attenuate partial occupancies, to weaken lower occupancies"
        ),
        beta: float = typer.Option(
            None,
            "--beta", "-b",
            help="How to alter confident partial occupancies >1"
        ),

        # Specific control ---------------------------------------------------------------------------------------------

        tau: float = typer.Option(
            None,
            "--tau", "-t",
            help="Percentile for scale-estimate normalization"
        ),
        kernel_size: int = typer.Option(
            None,
            "--kernel", "-k",
            help="Size of the local occupancy estimation kernel [pixels]"
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
        max_box_dim: int = typer.Option(
            200,
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
            help="Hard limit below which map scale/occupancy will be considered unreliable for amplification"
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
        min_vis_scale: float = typer.Option(
            0.2,
            help="Lower limit of map scale (occupancy) in chimeraX coloring & color-key"
        ),

        # Extra  -------------------------------------------------------------------------------------------------------

        verbose: bool = typer.Option(
            False,
            "--verbose/--quiet",
            help="Let me know what's going on"
        ),
        relion_classes: str = typer.Option(
            None,
            help="File of classes to diversify by occupancy amplification [_model.star]"
        ),
        version: Optional[bool] = typer.Option(
            None,
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Print version info and exit"
        )
):
    """
    OccuPy takes a cryo-EM reconstruction produced by averaging and estimates a self-normative local map scaling.
    It can also locally alter confident partial occupancies.
    """

    if input_map is None:
        exit(1)  # TODO surely a better way to do nothing with no options. Invoke help?

    if plot:
        import pylab as plt

    new_name = '_' + input_map
    doc = ''

    modify = amplify or attenuate or exclude_solvent
    if modify:
        if output_map == 'out_<input_file_name>':
            output_map = 'out' + new_name
    else:
        output_map = None

    if amplify or attenuate:
        if beta is None:
            raise ValueError("--beta must be specified if attenuating or amplifying")
    else:
        beta = None  # We might still do solvent exclusion

    if relion_classes is not None:
        print('Input using a relion model.star to diversify classes is not yet implemented')
        exit(0)

    # --------------- READ INPUT ---------------------------------------------------------------

    f_open = mf.open(input_map)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size = np.copy(f_open.voxel_size.x)
    assert nd[0] % 2 == 0
    assert max_box_dim % 2 == 0
    # --------------- LIMIT PROCESSING SIZE ----------------------------------------------------

    downscale_processing = nd[0] > max_box_dim
    if downscale_processing:
        factor = max_box_dim / nd[0]

        in_data, voxel_size = map_tools.lowpass(
            in_data,
            output_size=max_box_dim,
            voxel_size=f_open.voxel_size.x,
            square=True,
            resample=True
        )

        if save_all_maps:
            # Save downscaled processing map
            map_tools.new_mrc(
                in_data.astype(np.float32),
                "downscaled.mrc",
                parent=input_map,
                verbose=verbose,
            )
    nd_processing = np.shape(in_data)[0]

    # The radius of flattened solvent masking
    radius = int(nd_processing // 2)

    # Use raw (but downscaled) data for scale estimation
    scale_data = np.copy(in_data)

    # --------------- SETTINGS -----------------------------------------------------------------

    # To make solvent more detectable, low-pass input.
    # If a lowpass is provided use it.
    # Otherwise, use double the provided resolution.
    # If a resolutions is not provided, use 3 times Nyquist.
    if lowpass_input is None:
        if resolution is not None:
            lowpass_input = 2 * resolution  # Å
        else:
            lowpass_input = (2 * voxel_size * 3).astype(np.float32)  # Å

    # The size of the scale-estimation kernel.
    if kernel_size is None:
        # How many pixels do we fit into the significant highest frequency?
        kernel_size = int(np.floor(lowpass_input / voxel_size))
        # Make it an odd size
        kernel_size = ((kernel_size // 2) * 2) + 1
        # It should be larger than 1, and never needs to be bigger than 9.
        kernel_size = np.clip(kernel_size, 3, 9)

    # Make a kernel (morphological structuring element) for max-filter (greyscale dilation).
    kernel_radius = lowpass_input / (2 * voxel_size)
    scale_kernel, tau_ana = occupancy.spherical_kernel(
        kernel_size,
        radius=kernel_radius
    )

    own_tau = False
    n_v = int(np.sum(scale_kernel))
    tau_ana = occupancy.set_tau(n_v=n_v)
    if tau is None:
        tau = tau_ana
    elif verbose:
        own_tau = True
        print(f'Using provided tau value of {tau} instead of recommended {tau_ana} for kernel size {kernel_size}')
    assert 0 < tau <= 1

    log_name = f'log_{Path(input_map).stem}.txt'
    f_log = open(log_name, 'w+')
    print(f'\n---------------I/O AND CALCULATED SETTINGS-------', file=f_log)
    print(f'Input    :\t     \t {input_map}', file=f_log)
    print(f'Pixel    :\t[A]  \t {voxel_size:.2f}', file=f_log)
    print(f'Box in   :\t[pix]\t {nd}', file=f_log)
    print(f'Box proc :\t[pix]\t {np.shape(in_data)}', file=f_log)
    print(f'Box radi :\t[pix]\t {radius:.3f}', file=f_log)
    print(f'Kernel s :\t[pix]\t {kernel_size}', file=f_log)
    print(f'Kernel r :\t[pix]\t {kernel_radius:.2f}', file=f_log)
    print(f'Kernel nv:\t[pix]\t {n_v}', file=f_log)
    print(f'Tau      :\t[0,1]\t {tau:.3f}', file=f_log)
    if own_tau:
        print(f'Tau(rec).:\t[0,1]\t {tau_ana:.3f}', file=f_log)
    print(f'LP Filt. :\t[A]  \t {lowpass_input:.2f}', file=f_log)
    print(f'Scale lim:\t[0,1]\t {scale_limit:.3f}', file=f_log)

    # ----- LOW-PASS SETTINGS ---------

    use_lp = False
    if lowpass_input > 2 * voxel_size:
        use_lp = True

        lp_data, _ = map_tools.lowpass(
            in_data,
            lowpass_input,
            voxel_size=voxel_size,
            square=False,
            resample=False
        )

        sol_data = np.copy(lp_data)
    else:
        sol_data = np.copy(in_data)

    # We apply any estimations or solvent operation on the raw input (possibly down-sized)
    if modify:
        out_data = np.copy(in_data)

    # --------------- PLOTTING STUFF------------------------------------------------------------

    if plot:
        interactive_plot = False  # TODO sort this in flags, or omit.
        global f, ax1, ax2
        f = plt.figure()

    # --------------- SOLVENT ESTIMATION -------------------------------------------------------

    mask = map_tools.create_radial_mask(nd_processing, dim=3, radius=radius)
    if solvent_def is not None:
        s_open = mf.open(solvent_def)
        assert s_open.data.shape == mask.shape

        mask_def = np.array(mask).astype(int) + 1 - s_open.data
        mask_def = mask_def > 1.5
        h_data = sol_data[mask_def].flatten()
    else:
        assert sol_data.shape == mask.shape
        h_data = sol_data[mask].flatten()

    # Estimate the solvent model
    levels = 1000
    sol_limits, solvent_parameters = solvent.fit_solvent_to_histogram(
        h_data,
        plot=plot,
        n_lev=levels
    )

    # --------------- OCCUPANCY ESTIMATION ------------------------------------------------------

    scale_map = f'scale{new_name}'
    scale, max_val = occupancy.get_map_scale(
        scale_data,
        scale_kernel=scale_kernel,
        tau=tau,
        save_occ_map=scale_map,
        verbose=verbose
    )
    map_tools.adjust_to_parent(file_name=scale_map, parent=input_map)

    # --------------- CONFIDENCE ESTIMATION ------------------------------------------------------

    confidence, mapping = occupancy.estimate_confidence(
        sol_data,
        solvent_parameters,
        hedge_confidence=hedge_confidence,
        n_lev=levels
    )

    # --------------- MODIFY INPUT MAP IF AMPLIFYING AND/OR SUPPRESSING SOLVENT ------------------
    if exclude_solvent:
        output_map = 'solExcl_' + Path(output_map).stem + '.mrc'
        doc = 'Solvent exclusion '

    fake_solvent = None  # Will not  add fake solvent during amplify

    attn_map = None
    ampl_map = None

    if amplify or exclude_solvent:
        ampl = occupancy.modify_beta(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            beta=beta,  # The exponent for amplification / attenuation
            attenuate=False,  # False is amplifying or not doing anything
            fake_solvent=fake_solvent,
            scale_threshold=scale_limit,
            save_amp_map=save_all_maps,
            verbose=verbose
        )

        if save_all_maps:
            map_tools.adjust_to_parent(file_name='amplification.mrc', parent=input_map)

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        ampl = solvent.suppress(
            ampl,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            exclude_solvent,  # Only add back if not excluding solvent
            verbose=verbose
        )

        # -- Low-pass filter output --
        ampl = map_tools.lowpass_map(
            ampl,
            lowpass_output,
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
        if hist_match:
            ampl = match_histograms(ampl,
                                    f_open.data)  # Output is no longer input + stuff, i.e. good part is now something else.
        else:
            ampl = map_tools.clip_to_range(ampl, f_open.data)

        # TODO  -  Test histogram-matching of low-occupancy regions with high-occupancy as reference?

        # Save amplified and/or solvent-suppressed output.
        if amplify:
            ampl_map = f'ampl_{beta:.1f}_' + Path(output_map).stem + '.mrc'
            ampl_doc = f'{doc} attenuation beta={beta:.2f}'
        else:
            ampl_map = output_map
            ampl_doc = f'{doc}'

        map_tools.new_mrc(
            ampl.astype(np.float32),
            ampl_map,
            parent=input_map,
            verbose=verbose,
            extra_header=ampl_doc
        )

    if attenuate:
        if not exclude_solvent:
            # If we are not excluding solvent, then we will add some back when we attenuate
            fake_solvent = np.random.randn(nd_processing, nd_processing, nd_processing)
            fake_solvent = solvent_parameters[1] + solvent_parameters[2] * fake_solvent
            # TODO:
            # what is the correct scaling factor of the variance here????
            # also spectral properties

        attn = occupancy.modify_beta(
            out_data,  # Amplify raw input data (no low-pass apart from down-scaling, if that)
            scale,  # The estimated scale to use for amplification
            beta=beta,  # The exponent for amplification / attenuation
            attenuate=True,  # False is amplifying or not doing anything
            fake_solvent=fake_solvent,
            scale_threshold=scale_limit,
            save_amp_map=save_all_maps,
            verbose=verbose
        )

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        attn = solvent.suppress(
            attn,  # Supress the amplified output data
            in_data,  # Add back solvent from raw input (full res)
            confidence,  # The confidence mask to supress amplification
            exclude_solvent,  # Only add back if not excluding solvent
            verbose=verbose
        )

        # -- Low-pass filter output --
        attn = map_tools.lowpass_map(
            attn,
            lowpass_output,
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
        if hist_match:
            attn = match_histograms(attn,
                                    f_open.data)  # Output is no longer input + stuff, i.e. good part is now something else.
        else:
            attn = map_tools.clip_to_range(attn, f_open.data)

        # TODO  -  Test histogram-matching of low-occupancy regions with high-occupancy as reference?

        # Save amplified and/or solvent-suppressed output.
        attn_map = f'attn_{beta:.1f}_' + Path(output_map).stem + '.mrc'
        attn_doc = f'{doc} attenuation beta={beta:.2f}'
        map_tools.new_mrc(
            attn.astype(np.float32),
            attn_map,
            parent=input_map,
            verbose=verbose,
            extra_header=attn_doc
        )

    # ----------------OUTPUT FILES AND PLOTTING -------------------------------------------------
    if save_all_maps:

        map_tools.new_mrc(
            confidence.astype(np.float32),
            f'conf{new_name}',
            parent=input_map,
            verbose=verbose,
            log=f_log
        )

        if use_lp:
            map_tools.new_mrc(
                lp_data,
                f'lowpass{new_name}',
                parent=input_map,
                verbose=verbose,
                log=f_log
            )

    if chimerax:
        vis.chimx_viz(
            input_map,
            scale_map,
            ampl_map=ampl_map,
            attn_map=attn_map,
            threshold_input=(max_val+sol_limits[3])/2.0,
            threshold_scale=0.5,
            threshold_ampl=(max_val + sol_limits[3]) / 2.0,
            threshold_attn=(max_val + sol_limits[3]) / 2.0,
            min_scale=min_vis_scale
        )

    if chimerax_silent:
        vis.chimx_viz(
            input_map,
            scale_map,
            ampl_map=ampl_map,
            attn_map=attn_map,
            threshold_input=None,  # sol_limits[3],
            threshold_scale=0.5,
            min_scale=min_vis_scale,
            silent=True
        )

    f_open.close()

    if plot:
        f = plt.gcf()
        f.set_size_inches(20, 4)
        ax1 = f.axes[0]
        a, b = np.histogram(sol_data, bins=levels, density=True)

        if solvent_def is not None:
            ax1.plot(b[:-1], a, 'gray', label='unmasked data')
        ax1.plot(b[:-1], np.clip(mapping, ax1.get_ylim()[0], 1.0), 'r', label='confidence')
        if hedge_confidence is not None:
            ax1.plot(b[:-1], np.clip(mapping ** hedge_confidence, ax1.get_ylim()[0], 1.0), ':r',
                     label='hedged confidence')

        ax1.legend()

        save_name = input_map
        has_solvent_def = None
        if solvent_def is not None:
            has_solvent_def = Path(solvent_def).stem

        vis.save_fig(
            save_name,
            extra_specifier=has_solvent_def
        )

        if interactive_plot:
            plt.show()

    print(f'\n------------------------------------Detected thresholds-------', file=f_log)
    print(f'Content at 1% of solvent  : \t {sol_limits[2]:.3f}', file=f_log)
    print(f'Solvent drop to 0% (edge) : \t {sol_limits[3]:.3f}', file=f_log)
    print(f'Solvent peak              : \t {solvent_parameters[1]:.3f}', file=f_log)
    print(f'Occupancy full            : \t {max_val:.3f}', file=f_log)

    f_log.close()
    if verbose:
        f_log = open(log_name, 'r')
        print(f_log.read())
        f_log.close()

    return 0


if __name__ == '__main__':
    typer.run(main)


def app():
    typer.run(main)
