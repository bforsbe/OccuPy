import numpy as np
import pylab as plt
import mrcfile as mf
import os
from pathlib import Path

from typing import Optional
import typer

from . import map_tools, occupancy, vis, solvent

__version__ = "0.1.1"


def version_callback(value: bool):
    if value:
        print(f"OccuPy: {__version__}")
        raise typer.Exit()


def main(
        input_map: str = typer.Option(None, "--input-map", "-i", help="Map to estimate [.mrc NxNxN]"),
        output_map: str = typer.Option("out_<input_file_name>", "--output_map", "-o", help="Output map name"),
        resolution: str = typer.Option(None, "--resolution", "-r", help="Resolution of input map"),
        amplify: bool = typer.Option(False, "--amplify", "-a",
                                     help="Alter partial occupancies, to make more or less equal to full occupancy?"),
        amplify_amount: float = typer.Option(1.0, "--amplify_amount", "-am",
                                             help="How to alter confident partial occupancies [-1,1]"),
        amplify_limit: float = typer.Option(0.05, "--amplify_limit", "-al",
                                            help="Hard limit below which map scale/occupancy will be considered unreliable for amplification"),
        exclude_solvent: bool = typer.Option(False, "--exclude-solvent/--retain-solvent",
                                             help="Should Estimated solvent be eliminated [flattened to 0]?"),
        plot: bool = typer.Option(False, help="Plot a histogram showing solvent model fit and occupancy confidence?"),

        lowpass_input: float = typer.Option(None,
                                            help="Low-pass filter the input map to this resoution prior to scale estimation. Internal default is 6*pixel-size. [Å]"),
        lowpass_amplified: float = typer.Option(None,
                                                help="Optionally low-pass filter the amplified output to this resolution [Å]"),
        kernel_size: int = typer.Option(None, help="Size of the local occupancy estimation kernel [pixels]"),
        hedge_confidence: int = typer.Option(None,
                                             help="Exponent order for confidence estimation, such that values > 1 are more careful when amplifying low occupancies"),
        solvent_def: str = typer.Option(None,
                                        help="Mask that defines non-solvent, used to aid solvent model fitting. [.mrc NxNxN]"),

        save_all_maps: bool = typer.Option(False, help="Save all maps used internally"),
        save_chimerax: bool = typer.Option(True,
                                           help="Write a .cxc file that can be opened by chimeraX to show colored input/output maps"),
        min_vis_scale: float = typer.Option(0.2,
                                            help="Lower limit of map scale (occupancy) in chimeraX coloring & color-key"),
        verbose: bool = typer.Option(False, "--verbose/--quiet", help="Let me know what's going on"),

        relion_classes: str = typer.Option(None,
                                           help="File of classes to diversify by occupancy amplification [_model.star]"),
        version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True,
                                               help="Print version info and exit")
):
    """
    OccuPy takes a cryo-EM reconstruction produced by averaging and estimates a self-normative local map scaling.
    It can also locally alter confident partial occupancies.
    """

    if input_map is None:
        exit(1)  # TODO surely a better way to do nothing with no options. Invoke help?

    new_name = '_' + input_map

    if amplify or exclude_solvent:
        if output_map == 'out_<input_file_name>':
            output_map = 'out' + new_name
    else:
        output_map = None


    if relion_classes is not None:
        print('Input using a relion model.star to diversify classes is not yet implemented')
        exit(0)

    # --------------- READ INPUT ---------------------------------------------------------------
    f_open = mf.open(input_map)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size = f_open.voxel_size.x

    # --------------- SETTINGS -----------------------------------------------------------------
    # To make solvent more detectable, low-pass input.
    # If a lowpass is provided use it.
    # Otherwise, use double the provided resolution.
    # If a resolutions is not provided, use 3 times Nyquist.
    if lowpass_input is None:
        if resolution is not None:
            lowpass_input = int(2 * resolution)  # Å
        else:
            lowpass_input = int(2 * voxel_size * 3)  # Å

    # The size of the scale-estimation kernel.
    if kernel_size is None:
        # How many pixels do we fit into the significant highest frequency?
        kernel_size = int(np.ceil(lowpass_input / voxel_size))
        # Make it an odd size
        kernel_size = ((kernel_size // 2) * 2) + 1
        # It should be larger than 1, and never needs to be bigger than 7 (7^3 pixels as sample size)
        kernel_size = np.clip(kernel_size, 3, 7)

    # The radius of flattened solvent masking
    radius = int(0.95 * nd[0] / 2)  # TODO add flag?

    log_name = f'log_{Path(input_map).stem}.txt'
    f_log = open(log_name, 'w+')
    print(f'\n---------------I/O AND CALCULATED SETTINGS-------', file=f_log)
    print(f'Input   :\t\t {input_map}', file=f_log)
    print(f'Pixel   :\t\t {voxel_size:.2f}', file=f_log)
    print(f'Box     :\t\t {nd}', file=f_log)
    print(f'Radius  :\t\t {radius:.3f}', file=f_log)
    print(f'Kernel  :\t\t {kernel_size}', file=f_log)
    print(f'Filter  :\t\t {lowpass_input}', file=f_log)
    print(f'Amp. lim:\t\t {amplify_limit:.3f}', file=f_log)

    # ----- LOW-PASS SETTINGS ---------
    use_lp = False
    if lowpass_input > 2.5*voxel_size:
        use_lp = True
        lp_data = map_tools.lowpass_map(in_data, lowpass_input, f_open.voxel_size.x, keep_scale=False)
        sol_data = np.copy(lp_data)
    else:
        sol_data = np.copy(in_data)
    scale_data = np.copy(sol_data)
    out_data = np.copy(in_data)


    # --------------- PLOTTING STUFF--------------------------------------------------------
    if plot:
        interactive_plot = True  # TODO sort this in flags, or omit.
        global f, ax1, ax2
        f = plt.figure()

    # --------------- SOLVENT ESTIMATION -------------------------------------------------------

    # Make the spherical mask for masking flattened solvent in the input map
    mask = map_tools.create_circular_mask(
        nd[0],
        dim=3,
        radius=radius
    )

    # Apply the prided solvent definition as an additional mask
    if solvent_def is not None:
        s_open = mf.open(solvent_def)
        solvent_def_data = np.copy(s_open.data)
        mask = np.array(mask).astype(int) + 1 - solvent_def_data
        mask = mask > 1.5

    assert sol_data.shape == mask.shape
    h_data = sol_data[mask].flatten()

    # Estimate the solvent model
    levels=1000
    sol_limits, solvent_paramters = solvent.fit_solvent_to_histogram(
        h_data,
        plot=plot,
        n_lev=levels
    )

    # --------------- OCCUPANCY ESTIMATION ------------------------------------------------------

    scale_kernel = map_tools.create_circular_mask(kernel_size, dim=3, soft=False)
    scale_map = f'scale{new_name}'
    scale, max_val = occupancy.get_map_occupancy(
        scale_data,
        occ_kernel=scale_kernel,
        sol_threshold=None,
        save_occ_map=scale_map ,
        verbose=verbose
    )
    map_tools.change_voxel_size(scale_map , parent=input_map)

    # --------------- CONFIDENCE ESTIMATION ------------------------------------------------------


    confidence, mapping = occupancy.estimate_confidence(
        scale_data,
        solvent_paramters,
        hedge_confidence=hedge_confidence,
        n_lev=levels
)

    # --------------- MODIFY INPUT MAP IF AMPLIFYING AND/OR SUPPRESSING SOLVENT ------------------

    if amplify or exclude_solvent:

        if not amplify:
            amplify_amount = None

        # -- Amplify local scale --
        # The estimated scale is used to inverse-filter the data
        # The amplify_amount is the exponent of the scale.
        out_data = occupancy.amplify(
            out_data,
            scale,
            amplify_amount,
            occ_threshold=amplify_limit,
            save_amp_map=save_all_maps,
            verbose=verbose
        )

        # -- Supress solvent amplification --
        # Confidence-based mask of amplified content.
        # Solvent is added back unless excluded
        out_data = solvent.suppress(
            out_data,
            scale_data,
            confidence,
            exclude_solvent,
            verbose=verbose
        )

        # -- Low-pass filter output --
        out_data = map_tools.lowpass_map(
            out_data,
            lowpass_amplified,
            voxel_size,
            keep_scale=True
        )

        # -- Match output range --
        # inverse filtering can create a few spurious pixels that
        # ruin the dynamic range compared to the input. This is mostly
        # aesthetic.
        out_data = map_tools.clip_to_range(out_data, scale_data)

        # Save amplified and/or solvent-suppressed output.
        map_tools.new_mrc(
            out_data.astype(np.float32),
            output_map,
            parent=input_map,
            verbose=verbose
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

        if amplify:
            os.rename('amplification.mrc', f'amp{new_name}')
            print(f'Wrote amp{new_name}         \t: Local amplification applied', file=f_log)
            map_tools.change_voxel_size(f'amp{new_name}', parent=input_map)

    if save_chimerax:

        vis.chimx_viz(
            input_map,
            scale_map ,
            output_map,
            threshold_input=sol_limits[3],
            threshold_scale=sol_limits[3],
            threshold_output=sol_limits[3],
            min_scale=min_vis_scale,
        )

    f_open.close()

    if plot:
        f = plt.gcf()
        f.set_size_inches(20, 4)
        ax1 = f.axes[0]
        a, b = np.histogram(scale_data, bins=levels, density=True)

        ax1.plot(max_val * np.ones(2), ax1.get_ylim(), 'r--', label=f'{max_val:.2f}: full occupancy')
        if solvent_def is not None:
            ax1.plot(b[:-1], a, 'gray', label='unmasked data')
        ax1.plot(b[:-1], np.clip(mapping, ax1.get_ylim()[0], 1.0), 'r', label='confidence')
        if hedge_confidence is not None:
            ax1.plot(b[:-1], np.clip(mapping**hedge_confidence, ax1.get_ylim()[0], 1.0), ':r', label='hedged confidence')
        # for i in np.arange(5):
        #    ax1.plot(b[:-1], np.clip(content_conf, ax1.get_ylim()[0], 1.0)**(i+2), 'r', alpha=0.2)
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
    print(f'Solvent peak              : \t {solvent_paramters[1]:.3f}', file=f_log)
    print(f'Solvent full              : \t {max_val:.3f}', file=f_log)
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
