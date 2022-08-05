import numpy as np
import pylab as plt
import mrcfile as mf
import os
from pathlib import Path
from . import map_tools, occupancy, solvent, vis

import typer


def main(
        input_map: str = typer.Option(..., "--input-map", "-i", help="Map to estimate [.mrc NxNxN]"),
        output_map: str = typer.Option('out_<input_file_name>', "--output_map", "-o", help="Output map name"),
        amplify: bool = typer.Option(False,
                                     help="Alter partial occupancies, to make more or less equal to full occupancy?"),
        amplify_amount: float = typer.Option(1.0, help="How to alter confident partial occupancies [-1,1]"),
        amplify_limit: float = typer.Option(0.05,
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
        save_chimeraX: bool = typer.Option(True,
                                           help="Write a .cxc file that can be opened by chimeraX to show colored input/output maps"),
        verbose: bool = typer.Option(False, "--verbose/--quiet", help="Let me know what's going on"),

        relion_classes: str = typer.Option(None,
                                           help="File of classes to diversify by occupancy amplification [_model.star]")
):
    """
    OccuPy takes a cryo-EM reconstruction produced by averaging and estimates a self-normative local map scaling.
    It can also locally alter confident partial occupancies.
    """

    if input_map is None:
        exit(1)  # TODO surely a better way to do nothing with no options. Invoke help?

    new_name = '_' + input_map
    if output_map == 'out_<input_file_name>':
        output_map = 'out' + new_name

    if relion_classes is not None:
        print('Input using a relion model.star to diversiy classes is not yet implemented')
        exit(0)

    # --------------- READ INPUT ---------------------------------------------------------------
    f_open = mf.open(input_map)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size = f_open.voxel_size.x

    # --------------- SETTINGS -----------------------------------------------------------------
    if lowpass_input is None:
        lowpass_input = int(3 * 2 * voxel_size)  # Å

    if kernel_size is None:
        kernel_size = ((int(np.ceil(lowpass_input / voxel_size)) // 2) * 2) + 1
        kernel_size = np.clip(kernel_size, 3, 7)

    levels = 1000
    log_name = f'log_{Path(input_map).stem}.txt'
    f_log = open(log_name, 'w+')
    print(f'\n-------------------------------------------------------I/O-------', file=f_log)
    print(f'Input   :\t\t {input_map}', file=f_log)
    print(f'Pixel   :\t\t {voxel_size:.2f}', file=f_log)
    print(f'Box     :\t\t {nd}', file=f_log)
    print(f'Kernel  :\t\t {kernel_size}', file=f_log)
    print(f'Filter  :\t\t {lowpass_input}', file=f_log)
    print(f'Amp. lim:\t\t {amplify_limit:.3f}', file=f_log)

    # ----- THRESHOLD SETTINGS ---------
    invert = False  # True #TODO inverting the equalization, to anti-boost? (Different from neg lambda, I think)

    # ----- LOW-PASS SETTINGS ---------
    use_lp_for_solvent = True
    use_lp_for_occupancy = True  # TODO use the same for solvent estimation and confidence filter
    use_lp_for_amplification = False

    if use_lp_for_solvent or use_lp_for_occupancy or use_lp_for_amplification:
        lp_data = map_tools.lowpass_map(in_data, lowpass_input, f_open.voxel_size.x, keep_scale=False)

    # --------------- DIAGNOSTIC OUTPUT --------------------------------------------------------
    if plot:
        interactive_plot = True  # TODO sort this in flags, or omit.
        global f, ax1, ax2
        f = plt.figure()

    # --------------- SOLVENT ESTIMATION -------------------------------------------------------
    if use_lp_for_solvent:
        sol_data = np.copy(lp_data)
    else:
        sol_data = np.copy(in_data)

    # ----- ESTIMATE THRESHOLD ------
    # Estimate solvent paramters for mask
    radius = int(0.95 * nd[0] / 2)  # TODO add flag?
    # print(radius)
    mask = map_tools.create_circular_mask(nd[0], dim=3, radius=radius)  # TODO use mask radius in Å/nm
    if solvent_def is not None:
        s_open = mf.open(solvent_def)
        solvent_def_data = np.copy(s_open.data)
        mask = np.array(mask).astype(int) + 1 - solvent_def_data
        mask = mask > 1.5

    assert sol_data.shape == mask.shape
    h_data = sol_data[mask].flatten()
    sol_limits, sol_param = solvent.fit_solvent_to_histogram(
        h_data,
        plot=plot,
        n_lev=levels
    )

    # --------------- OCCUPANCY AMPLIFICATION ------------------------------------------------------

    if use_lp_for_occupancy:
        occ_data = np.copy(lp_data)
    else:
        occ_data = np.copy(in_data)

    if use_lp_for_amplification:
        amp_data = np.copy(lp_data)
    else:
        amp_data = np.copy(in_data)

    occ_kernel = map_tools.create_circular_mask(kernel_size, dim=3, soft=False)

    occ, full_occ = occupancy.get_map_occupancy(
        occ_data,
        occ_kernel=occ_kernel,
        sol_threshold=None,  # sol_limits[2],
        save_occ_map=True,
        verbose=verbose
    )

    a, b = np.histogram(occ_data, bins=levels, density=True)

    # Find intersection of solvent model and content
    solvent_model = solvent.onecomponent_solvent(b, sol_param[0], sol_param[1], sol_param[2])
    fit = np.clip(solvent_model, 0.0, np.max(solvent_model))

    c = len(b) - 2
    while c > 0:
        c -= 1
        if a[c] <= fit[c] and fit[c] > 0.1:
            break

    content_fraction_all = np.divide((a + 0.01 - fit[:-1]), a + 0.01)
    # solvent_fraction_all = 1 - content_fraction_all

    content_conf = np.copy(content_fraction_all)
    for i in np.arange(np.size(content_conf) - 2) + 1:
        content_conf[-i - 2] = np.min(content_conf[-i - 2:-i])
        if content_conf[-i - 3] < 0:
            content_conf[:-i - 2] = 0
            break
    if plot:
        f = plt.gcf()
        f.set_size_inches(20, 4)
        ax1 = f.axes[0]
        ax1.plot(full_occ * np.ones(2), ax1.get_ylim(), 'r--', label=f'{full_occ:.2f}: full occupancy')
        if solvent_def is not None:
            ax1.plot(b[:-1], a, 'gray', label='unmasked data')
        ax1.plot(b[:-1], np.clip(content_conf, ax1.get_ylim()[0], 1.0), 'r', label='confidence')
        # for i in np.arange(5):
        #    ax1.plot(b[:-1], np.clip(content_conf, ax1.get_ylim()[0], 1.0)**(i+2), 'r', alpha=0.2)
        ax1.legend()

    # indx = (occ * np.sum(b>0) + np.sum(b<0) - 2 ).astype(int)
    indx = (map_tools.uniscale_map(np.copy(occ_data), norm=True) * levels - 1).astype(int)
    if hedge_confidence is not None:
        content_conf = content_conf ** hedge_confidence
    confidence = content_conf[indx]

    print(f'\n------------------------------------Detected thresholds-------', file=f_log)
    # if c is not None:
    #    print(f'Sol/Content intersection : \t {b[c]:.3f}', file=f_log)
    print(f'Content at 1% of solvent  : \t {sol_limits[2]:.3f}', file=f_log)
    print(f'Solvent drop to 0% (edge) : \t {sol_limits[3]:.3f}', file=f_log)
    print(f'Solvent peak              : \t {sol_param[1]:.3f}', file=f_log)
    print(f'Solvent full              : \t {full_occ:.3f}', file=f_log)

    print(f'\n------------------------------------Output files--------------', file=f_log)
    logstring = ""
    if amplify or exclude_solvent:

        out_data = np.copy(amp_data)

        if amplify:
            logstring = 'Amplified partial scale & '
            out_data = occupancy.equalise_map_occupancy(
                amp_data,
                occ,
                amplify_amount,
                occ_threshold=amplify_limit,
                save_amp_map=save_all_maps,
                verbose=verbose,
                invert=invert
            )

            if lowpass_amplified is not None:
                out_data = map_tools.lowpass_map(out_data, lowpass_amplified, voxel_size, keep_scale=True)

            out_data = map_tools.clip_to_range(out_data, occ_data)

        if verbose:
            print('Using confidence based on solvent model to limit amplification when amplifying partial occupancy.')
        out_data = np.multiply(out_data, confidence)

        if exclude_solvent:
            logstring = f'{logstring}Excluded solvent'
            if verbose:
                print('Not retaining solvent, eliminating based on confidence')
        else:
            logstring = f'{logstring}Retained solvent'
            if verbose:
                print('Retaining solvent by inverse confidence')
            out_data += np.multiply(occ_data, 1 - confidence)

        map_tools.new_mrc(out_data.astype(np.float32), output_map, parent=input_map, verbose=False)
        print(f'Wrote {output_map}        \t: {logstring} ', file=f_log)

    os.rename('occupancy.mrc', 'scale' + new_name)
    print(f'Wrote scale{new_name}     \t: Local estimated scale (occupancy)', file=f_log)
    map_tools.change_voxel_size('occ' + new_name, parent=input_map)

    if save_all_maps:

        map_tools.new_mrc(lp_data, 'lowpass' + new_name, parent=input_map, verbose=False)
        print(f'Wrote lowpass{new_name} \t: Low-pass filtered input map', file=f_log)

        map_tools.new_mrc(confidence.astype(np.float32), 'conf' + new_name, parent=input_map, verbose=False)
        print(f'Wrote conf{new_name}     \t: Local confidence of non-solvent content', file=f_log)

        if amplify:
            os.rename('amplification.mrc', 'amp' + new_name)
            print(f'Wrote amp{new_name}         \t: Local amplification applied', file=f_log)
            map_tools.change_voxel_size('amp' + new_name, parent=input_map)

    if save_chimeraX:

        full_name = None
        if amplify:
            full_name = 'full' + new_name

        vis.chimx_viz(
            input_map,
            'occ' + new_name,
            full_name,
            threshold_ori=sol_limits[3],
            # threshold_full=sol_limits[3],
            threshold_occ=amplify_limit
        )

    f_open.close()

    if plot:
        save_nem = input_map
        if solvent_def is not None:
            vis.save_fig(
                input_map,
                extra_specifier=Path(solvent_def).stem)
        else:
            vis.save_fig(
                input_map)
        if interactive_plot:
            plt.show()

    f_log.close()
    if verbose:
        f_log = open(log_name, 'r')
        print(f_log.read())
        f_log.close()


if __name__ == '__main__':
    typer.run(main)


def app():
    typer.run(main)
