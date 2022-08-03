import numpy as np
import pylab as plt
from scipy import ndimage
import occupy.map as map


def occupancy_map(data, kernel, mask=None, verbose=True):
    occu_map, map_val_at_full_occupancy = occupancy_map_percentile(data, kernel, mask, with_max=True)
    return occu_map, map_val_at_full_occupancy


def percentile_filter_tiled(data, kernel, mask, n_tiles, tile_sz=None, per=0.4, with_max=False, verbose=False):
    nd = np.array(np.shape(data))
    dim = len(nd)

    if not all(nd % n_tiles == 0):
        if verbose:
            print(f'number of tiles ({n_tiles}) does not divide data array ({nd}) evenly;')
        t_low = n_tiles
        while t_low > 2:
            t_low -= 1
            if nd[0] % t_low == 0:
                break
        t_high = n_tiles
        while t_high < nd[0]:
            t_high += 1
            if nd[0] % t_high == 0:
                break
        n_tiles = np.min(np.array([t_low, t_high]) - n_tiles) + n_tiles
        if n_tiles == 1 or n_tiles == nd[0]:
            raise ValueError(f'Could not find a reasonable tile number (for data size {nd})')
        elif not all(nd % n_tiles == 0):
            raise ValueError(
                f'number of tiles ({n_tiles}) does not divide data array ({nd}), even after adjustment')
        else:
            if verbose:
                print(f' ---->  Adjusted percentile value scan to {n_tiles} tiles.')

    if tile_sz is None:
        tile_sz = (nd / n_tiles).astype(int)
    else:
        tile_sz = (tile_sz * np.ones(dim)).astype(int)

    tile_start = (nd / n_tiles).astype(int)
    npick = int(np.floor(per * np.product(tile_sz)))
    out_tiles = np.zeros(n_tiles * np.ones(dim).astype(int))
    if len(nd) == 2:
        for i in np.arange(tile_sz[0]):
            for j in np.arange(tile_sz[1]):
                r = np.copy(data[
                            i * tile_start[0]:i * tile_start[0] + tile_sz[0],
                            j * tile_start[1]:j * tile_start[1] + tile_sz[1]]).flatten()
                s = np.sort(r)
                out_tiles[i][j] = np.copy(s[npick])
    elif len(nd) == 3:
        if verbose:
            print(f'Percentile tile scan ', end='\r')
        c = 0
        for i in np.arange(n_tiles):
            for j in np.arange(n_tiles):
                for k in np.arange(n_tiles):
                    c += 1
                    if verbose:
                        print(f'Percentile tile scan {int(100 * c / (n_tiles ** 3))}% complete.', end='\r')
                    r = np.copy(data[
                                i * tile_start[0]:i * tile_start[0] + tile_sz[0],
                                j * tile_start[1]:j * tile_start[1] + tile_sz[1],
                                k * tile_start[2]:k * tile_start[2] + tile_sz[2]]).flatten()
                    s = np.sort(r)
                    out_tiles[i][j][k] = np.copy(s[npick])
    if verbose:
        print('Percentile tile scan completed.      \n')

    max_per = -1

    max_per = np.max(out_tiles)
    # divide by max percentile, so that all voxels where the max-value is higher than this are >1
    maxi = occupancy_map_maximum(data, kernel)
    if mask is not None:
        maxi = np.multiply(maxi, mask)

    '''
    maxi /= max_per
    if verbose:
        print(f'Map value defined to represent 100% occupancy is {max_per:.3f}')

    # Clip de occupancies>1 down to 1
    maxi = np.clip(maxi, 0.0, 1.0)
    '''

    return maxi, max_per


def occupancy_map_maximum(data, kernel):
    return ndimage.maximum_filter(data, footprint=kernel)


def occupancy_map_percentile(data, kernel, mask=None, per=0.95, tiles=12, tile_sz=5, with_max=False):
    return percentile_filter_tiled(data, kernel, mask, n_tiles=tiles, tile_sz=tile_sz, per=per, with_max=with_max)


def threshold_occu_map(occu_map, occ_threshold, mask=None):
    if mask is None:
        mask = occu_map
    # Occupancy higher than threshold should be boosted inversely to occupancy
    t_occu_map = np.multiply(occu_map, mask > occ_threshold)

    # Lower than threshold should be boosted as if full occupancy (do not touch),
    # but we set it to -1 for clarity and handle it during boosting
    t_occu_map -= mask <= occ_threshold

    return t_occu_map


def equalise_map(data, amplification):
    return np.multiply(data, np.abs(amplification))


def equalise_map_lambda(data, amplification, a=1, invert=False):
    occ = np.divide(1, amplification, where=amplification != 0)
    eff_occ = 1.0 - a + a * np.divide(1, occ, where=occ != 0)
    if invert:
        return np.divide(data, np.abs(eff_occ),where= np.abs(eff_occ)!=0 )
    else:
        return np.multiply(data, np.abs(eff_occ))


def volume_limit_amplification(occu_map, n_lev=30, plot=False, cutoff=False):
    global f, ax1, ax2

    mask = map.create_circular_mask(np.shape(occu_map)[0], dim=3)

    print('Stepping through occupancy thresholds...')
    m_min = np.min(occu_map)
    m_max = np.max(occu_map)
    levels = np.linspace(m_max, m_min, n_lev + 1)
    occ = np.copy(occu_map) * 0.0
    vtot = float(np.sum(mask))  # float(np.size(occu_map))
    vcs = 0
    occ_lim = np.zeros((n_lev, 2))
    occ_lim[:, 0] = levels[1:]
    occ_lim[:, 1] = levels[1:]
    reset = False
    clip_low = 0.0
    clip_high = 1.0
    if plot:
        f = plt.gcf()
        ax1 = f.add_subplot(2, 1, 1)
        ax2 = f.add_subplot(2, 1, 2)
        ax1.plot(levels[1:], occ_lim[:, 0], '--', label='estimated occu')
        ax2.hist(occu_map.flatten(), bins=levels[::-1], label='estimated occu', histtype='step')

    for i in np.arange(n_lev):
        print('done ' + str(int(100 * (i + 1) / n_lev)) + '%', end='\r')
        sel = np.logical_and(occu_map <= levels[i], occu_map > levels[i + 1])
        v = float(np.sum(np.multiply(sel, mask)))
        if v == 0:
            # print('no elements in this occupancy range')
            if reset:
                # set new occupancy limit to the same value as previous occupancy range
                occ_lim[i, 1] = occ_lim[i - 1, 1]
        else:
            #
            vcs += v
            min_occu = vcs / vtot
            if min_occu > levels[i + 1]:
                if reset:
                    clip_low = min_occu
                    clip_high = min_occu
                    if cutoff:
                        clip_low = 1.0
                        clip_high = 1.0
                    print(f'resetting occupancy level {levels[i + 1]:.2f} to {clip_low:.2f} ')
                else:
                    reset = True
                    clip_low = np.max([levels[i + 1], min_occu])
                    clip_high = np.max([levels[i], min_occu])
                    print(f'resetting occupancy level {levels[i + 1]:.2f} to {clip_low:.2f} ')
                occ_lim[i, 1] = clip_low
            # print(levels[i+1],levels[i],min_occu,clip_low,clip_high)
            occ_eff = np.multiply(sel, np.clip(occu_map, clip_low, clip_high))
            # print(np.min(occ_eff),np.max(occ_eff))
            occ += occ_eff

    # Set all lover values to effectively 100% occupancy (don't boost)
    occ += occ <= levels[-1]

    if plot:
        ax1.plot(levels[1:], occ_lim[:, 1], 'ro', label='vol-limited  occu')
        ax2.hist(occ.flatten(), bins=levels[::-1], label='vol-limited occu', histtype='step', density=True)
        ax1.set_xlim([1, 0])
        ax2.set_xlim([1, 0])
        ax1.legend()
        ax2.legend()

    # Hedge by restrict
    # occ+=(1-occ)*restrict

    # print(vtot,vcs,np.min(occ),np.max(occ))
    return np.divide(1, occ, where=occ > 0)


# -------------------------------------------OCCUPANCY WRAPPER-----------------

def get_map_occupancy(
        data,
        occ_kernel,
        sol_mask=None,
        sol_threshold=None,
        save_occ_map=False,
        verbose=True
):
    '''
    We have to limit the boosting somehow, by regulating areas of low occupancy (like solvent)
    Either we
    A) Use a solvent mask

    B) use a boost threshold, so that occupancies<threshold are set to 1 (i.e. not boosted).
       This works fine if you have a good threshold.

    C) limit the occupancy by volume, so that the occupancy can never be lower than the
       relative volume that has this occupancy. That is, if 20% of the box has 10% occupancy,
       these regions are assigned an effective occupancy of 20% (boosted less).
       :param sol_threshold:
    '''

    occ_map, map_val_at_full_occupancy = occupancy_map(
        data,
        occ_kernel,
        mask=sol_mask,
        verbose=verbose)

    if sol_threshold is not None:
        occ_map = np.clip(occ_map / map_val_at_full_occupancy, sol_threshold / map_val_at_full_occupancy, 1)
    else:
        occ_map = np.clip(occ_map / map_val_at_full_occupancy, 0, 1)
    # occ_map, _ = unity_map(occ_map)

    if save_occ_map:
        map.new_mrc(np.clip(occ_map, 0, 1), 'occupancy.mrc', verbose=False)
    return occ_map, map_val_at_full_occupancy


def equalise_map_occupancy(
        data,
        occ_map,
        confidence=None,
        retain_solvent=True,
        sol_mask=None,
        occ_threshold=None,
        save_bst_map=False,
        invert=False,
        verbose=True
):
    if confidence is not None:
        thr_occu_map = threshold_occu_map(occ_map, 0)
        amplification = np.divide(1, thr_occu_map, where=thr_occu_map != 0)

    elif occ_threshold is not None:
        # Use the supplied threshold hard
        if verbose:
            print(f'Applying strict occupancy threshold of {100 * occ_threshold:.1f}%.')
        thr_occu_map = threshold_occu_map(occ_map, occ_threshold)
        amplification = np.divide(1, thr_occu_map, where=thr_occu_map != 0)

    if sol_mask is not None:  # TODO make possible to use on top of occ_threshold
        if verbose:
            print('Using solvent mask when estimating occupancy.')
        amplification = (1 - sol_mask) + np.multiply(sol_mask, amplification)

    # TODO make use of volume-limiting thresholding?
    ''' 
        # Estimate the occupancy threshold
        if verbose:
            print('Using volume-limited occupancy.')
        boosting = volume_limit_boost(occ_map, plot=False, cutoff=True)
    '''

    # Boost map
    equalised_map = equalise_map_lambda(data, amplification, 1, invert)

    if confidence is not None:
        equalised_map = np.multiply(equalised_map,confidence)
        if retain_solvent:
            equalised_map += np.multiply(data,1-confidence)

    if save_bst_map:
        map.new_mrc(amplification.astype(np.float32), 'amplification.mrc')
    return equalised_map
