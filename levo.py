import numpy as np
import pylab as plt
import mrcfile as mf
import os
import sys

import levo_utilities as levo

if __name__ == '__main__':

    # --------------- INPUT --------------------------------------------------------------------
    plt.ion()
    file_name = sys.argv[1]
    f_open = mf.open(file_name)
    in_data = np.copy(f_open.data)
    nd = np.shape(in_data)
    voxel_size = f_open.voxel_size.x

    # --------------- SETTINGS -----------------------------------------------------------------
    resol = int(3 * 2 * voxel_size)  # Å
    filter_output = None  # Å

    kernel_size = ((int(np.ceil(resol / voxel_size)) // 2) * 2) + 1
    kernel_size = np.clip(kernel_size, 3, 7)
    method = 'percentile_max'
    verbose = False  # True
    levels = 1000
    f_log = open('log.txt', 'w+')
    print(f'Input :\t\t {file_name}', file=f_log)
    print(f'Pixel :\t\t {voxel_size:.2f}', file=f_log)
    print(f'Box   :\t\t {nd}', file=f_log)
    print(f'Kernel:\t\t {kernel_size}', file=f_log)
    print(f'Filter:\t\t {resol}', file=f_log)
    print(f'--------------------------------------------------------------\n', file=f_log)

    # ----- THRESHOLD SETTINGS ---------
    solvent_threshold = None  # Set to None to estimate using solvent fitting
    occupancy_threshold = None  # Set to None to estimate using volume-limits
    estimate_occ_threshold = True  # This seems to be a better way than solvent masking to limit solvent boosting

    # ----- MASK SETTINGS ---------
    solvent_mask = None
    use_solvent_mask = False  # This does not seem to be a good ides to limit solvent boosting

    # ----- LOW-PASS SETTINGS ---------
    use_lp_for_solvent = False
    use_lp_for_occupancy = True
    use_lp_for_boosting = False

    if use_lp_for_solvent or use_lp_for_occupancy or use_lp_for_boosting:
        lp_data = levo.lowpass_map(in_data, resol, f_open.voxel_size.x, keep_scale=False)
        # print(f'Using low-passed map for some processing, saving file lowpass.mrc.\n',file=f_log)
        levo.new_mrc(lp_data, 'lowpass.mrc', parent=file_name, verbose=False)

    # --------------- DIAGNOSTIC OUTPUT --------------------------------------------------------
    plot = True  # False
    save_occ_file = True
    save_sol_file = True
    save_bst_map = False

    # --------------- SOLVENT ESTIMATION -------------------------------------------------------
    if use_lp_for_solvent:
        sol_data = np.copy(lp_data)
    else:
        sol_data = np.copy(in_data)

    # ----- ESTIMATE THRESHOLD ------
    if solvent_threshold is None:
        # Estimate solvent paramters for mask
        radius = int(0.95 * nd[0] / 2)
        # print(radius)
        mask = levo.create_circular_mask(nd[0], dim=3, radius=radius)  # TODO use mask radius in Å/nm
        h_data = sol_data[mask].flatten()
        sol_limits, sol_param = levo.fit_solvent_to_histogram(
            h_data,
            plot=plot,
            n_lev=levels
        )

        if verbose:
            print(f'--------------------------------------------------------------', file=f_log)
            print(f'Detected data limits for solvent:', file=f_log)
    else:
        # Use provided solvent threshold to create a solvent mask
        sol_limits = np.array([np.min(sol_data), -solvent_threshold, solvent_threshold, np.max(sol_data)])
        if verbose:
            print(f'Supplied (and assumed) data limits for solvent:', file=f_log)
    if verbose:
        print(f'{sol_limits[0]:.4f} : {sol_limits[1]:.4f} : {sol_limits[2]:.4f} : {sol_limits[3]:.4f}', file=f_log)
        print(f'--------------------------------------------------------------', file=f_log)

    '''
    # ----- CREATE MASK ------
    if use_solvent_mask and solvent_mask is None:
        # content_region = (lp_data < sol_limits[1]) + (lp_data > sol_limits[2])

        content_region = (lp_data > sol_limits[2])

        # TODO: this is heuristic
        n_heurisitc = 2
        for i in np.arange(n_heurisitc):
            if verbose:
                print(f' Heuristic solvent expansion round {i + 1} of {n_heurisitc}', end=' \r')
            solvent_kernel = create_circular_mask(kernel_size, dim=3, soft=False)
            content_region = ndimage.median_filter(content_region, footprint=solvent_kernel)
            content_region = ndimage.maximum_filter(content_region, footprint=solvent_kernel)
        if verbose:
            print('\n Done heuristic solvent expansion')

        solvent_mask = content_region
        if (save_sol_file):
            new_mrc(content_region.astype(np.float32), 'solvent_mask.mrc')
    '''

    if not use_solvent_mask:
        solvent_mask = None

    global f, ax1, ax2

    # --------------- OCCUPANCY BOOSTING ------------------------------------------------------

    if use_lp_for_occupancy:
        occ_data = np.copy(lp_data)
    else:
        occ_data = np.copy(in_data)

    if use_lp_for_boosting:
        bst_data = np.copy(lp_data)
    else:
        bst_data = np.copy(in_data)

    boost_kernel = levo.create_circular_mask(kernel_size, dim=3, soft=False)

    occ, full_occ = levo.get_map_occupancy(
        occ_data,
        occ_kernel=boost_kernel,
        sol_mask=solvent_mask,
        sol_threshold=None,  # sol_limits[2],
        save_occ_map=save_occ_file,
        verbose=verbose
    )

    a, b = np.histogram(sol_data[occ > 0.9], bins=levels)
    if plot:
        f = plt.gcf()
        ax1 = f.axes[0]
        ax1.plot(b[:-1], a, 'r', label='high occ')

    # Find intersection of solvent model and content
    solvent_model = levo.onecomponent_solvent(b, sol_param[0], sol_param[1], sol_param[2])
    fit = np.clip(solvent_model, 0.0, np.max(solvent_model))
    cond = fit[:-1] > a
    c = len(b) - 2
    while c > 0:
        c -= 1
        if a[c] <= fit[c] and fit[c] > 0.1:
            break

    if estimate_occ_threshold and occupancy_threshold is None:
        # occupancy_threshold = (sol_limits[2]+sol_limits[3])/2 / full_occ
        occupancy_threshold = b[c] / full_occ

    print(f'Detected thresholds:', file=f_log)
    print(f'Solvent low : \t {b[c]:.3f}', file=f_log)
    print(f'Solvent full: \t {full_occ:.3f}', file=f_log)
    print(f'Occupancy   : \t {occupancy_threshold:.3f}', file=f_log)

    boosted = levo.boost_map_occupancy(
        bst_data,
        occ,
        sol_mask=solvent_mask,
        occ_threshold=occupancy_threshold,
        save_bst_map=save_bst_map,
        verbose=verbose
    )
    if plot:
        ax1.legend()

    if filter_output is not None:
        rescaled = levo.lowpass_map(boosted, filter_output, voxel_size, keep_scale=True)
    else:
        rescaled = boosted

    newName = '_' + file_name
    levo.new_mrc(rescaled.astype(np.float32), 'full' + newName, parent=file_name, verbose=False)
    # print(f'A file with boosted components was written tp full{newName}',file=f_log)

    if save_occ_file or save_sol_file or save_bst_map:
        if verbose:
            print(f'-------------------------------------------------------------- \nAdditional files:', file=f_log)
    if save_occ_file:
        os.rename('occupancy.mrc', 'occ' + newName)
        if verbose:
            print(f'The occupancy was written to occ{newName}', file=f_log)
        levo.change_voxel_size('occ' + newName, parent=file_name)

    if save_sol_file and solvent_mask is None and use_solvent_mask:
        os.rename('solvent_mask.mrc', 'sol' + newName)
        if verbose:
            print(f'The estimated solvent mask was written to sol{newName}', file=f_log)
        levo.change_voxel_size('sol' + newName, parent=file_name)

    if save_bst_map:
        os.rename('boosting.mrc', 'bst' + newName)
        if verbose:
            print(f'The estimated boosting was written to bst{newName}', file=f_log)
        levo.change_voxel_size('bst' + newName, parent=file_name)

    levo.chimX_viz(
        file_name,
        'full' + newName,
        'occ' + newName,
        threshold_ori=sol_limits[3],
        threshold_full=sol_limits[3],
        threshold_occ=occupancy_threshold
    )

    f_open.close()
    f_log.close()
