import numpy as np
import pylab as plt
from scipy import ndimage
from scipy.optimize import curve_fit
import mrcfile as mf
from pathlib import Path


# -------------------------------------------BASIC STUFF-----------------
def new_mrc(data, file_name, parent=None, verbose=False):
    pix_size = 1.0
    if parent is not None:
        p = mf.open(parent)
        pix_size = p.voxel_size
        p.close()
    o_file = mf.new(file_name, overwrite=True)
    o_file.set_data(data.astype(np.float32))
    o_file.voxel_size = pix_size
    o_file.flush()
    o_file.close()
    if verbose:
        print(f'Wrote new file {file_name}')


def change_voxel_size(file, sz=None, parent=None):
    if (parent is None) and (sz is None):
        raise ValueError('Change to pixel size to what? (No parent or value provided)')

    f_mod = mf.open(file, 'r+')
    if parent is not None:
        try:
            f_ref = mf.open(parent)
            f_mod.voxel_size = f_ref.voxel_size
            f_ref.close()
        except ValueError:
            print('Could not open parent file for reading pixel size')
    elif sz is not None:
        f_mod.voxel_size = sz
    f_mod.flush()
    f_mod.close()


def unity_map(data):
    param = [np.min(data), np.max(data)]
    data /= param[1] - param[0]
    data -= param[0]
    return data, param


def rescale_map(data, param):
    data += param[0]
    data *= param[1] - param[0]
    return data


def match_to_range(change, reference):
    rp = np.array([np.min(reference), np.max(reference)])
    cp = np.array([np.min(change), np.max(change)])

    change -= cp[0]
    change /= cp[1] - cp[0]

    change *= rp[1] - rp[0]
    change += rp[0]

    return change


def uniscale_map(data):
    param = [np.min(data), np.max(data)]
    data /= param[1] - param[0]
    return data


def lowpass_map_square(data, cutoff, voxel_size, resample=False, keep_scale=False):
    n = np.shape(data)[0]
    ndim = len(np.shape(data))
    ref_scale = np.max(data)
    assert ndim == 3
    f_data = np.fft.rfftn(data)
    f_data = np.fft.fftshift(f_data, axes=(0, 1))
    cutoff /= voxel_size
    cutoff_level = int(np.floor(2 * (n / cutoff)))  # Keep this many of the lower frequencies
    mid = int(n / 2)
    if resample:
        t = f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
    else:
        t = np.zeros(np.shape(f_data)).astype(np.complex)
        t[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1] = \
            f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
    f_data = np.fft.ifftshift(t, axes=(0, 1))
    r_data = np.fft.irfftn(f_data)
    if keep_scale:
        m = np.mean(r_data)
        r_data = (r_data - m) * (ref_scale / np.max(r_data)) + m
    return r_data


def lowpass_map(data, cutoff, voxel_size, resample=False, keep_scale=False):
    n = np.shape(data)[0]
    ndim = len(np.shape(data))
    ref_scale = np.max(data)
    assert ndim == 3  # TODO make work for 2D just in case

    f_data = np.fft.rfftn(data)
    f_data = np.fft.fftshift(f_data, axes=(0, 1))

    cutoff /= voxel_size
    cutoff_level = int(np.floor(2 * (n / cutoff)))  # Keep this many of the lower frequencies
    mid = int(n / 2)

    if resample:  # TODO test/fix
        mid_resample = cutoff_level // 2
        mask = create_circular_mask(cutoff_level, ndim)[:, :, mid_resample:]
        t = f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
        # print(t.shape,mask.shape)
        t = np.multiply(t, mask)
    else:
        mask = create_circular_mask(n, ndim, radius=cutoff_level)[:, :, mid - 1:]
        # print(f_data.shape,mask.shape,mask.sum(),mask.size,n,cutoff_level)
        t = np.multiply(f_data, mask)

    f_data = np.fft.ifftshift(t, axes=(0, 1))
    r_data = np.fft.irfftn(f_data)
    if keep_scale:
        m = np.mean(r_data)
        r_data = (r_data - m) * (ref_scale / np.max(r_data)) + m
    return r_data


# create circular mask
def create_circular_mask(s, dim, soft=False, center=None, radius=None):
    if center is None:  # use the middle of the image
        center = int(s / 2)

    if radius is None:
        radius = center

    if s % 2 == 0:
        center -= 0.5
        radius -= 0.5

    if dim == 2:
        x, y = np.ogrid[:s, :s]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    elif dim == 3:
        x, y, z = np.ogrid[:s, :s, :s]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2)
    else:
        raise ValueError('Mask dimension is not 2 or 3 ')

    if soft:  # TODO fix
        dist_from_center = np.divide(dist_from_center <= radius, dist_from_center, where=dist_from_center != 0)

    mask = (dist_from_center <= radius)
    return mask


def component(x, c, mu, sigma):
    res = c * np.exp(- (x - mu) ** 2.0 / (2.0 * sigma ** 2.0))
    return res


def onecomponent_solvent(x, c1, mu1, sigma1):
    if sigma1 == 0:
        sigma1 += 0.001
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0))
    return res


def twocomponent_solvent(x, c1, mu1, sigma1, c2, mu2, sigma2):
    if sigma1 == 0:
        sigma1 += 0.001
    if sigma2 == 0:
        sigma2 += 0.001
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0)) \
          + c2 * np.exp(- (x - mu2) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return res


def log_nonzero_solvent_and_content(x, c1, mu1, sigma1, c2, mu2, sigma2):
    if sigma1 == 0:
        sigma1 += 0.001
    if sigma2 == 0:
        sigma2 += 0.001
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0)) \
          + c2 * np.exp(- (x - mu2) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return np.log(res, where=res > 0)


def log_nonzero_solvent_and_unicontent(x, c1, mu1, sigma1, c2, mu2, sigma2, width2):
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0))
    res += c1 / 10 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 * 0.4 ** 2.0))
    n = 11
    nh = (n - 1) / 2
    for i in width2 * (np.arange(n) - nh) / nh:
        res += c2 * np.exp(- (x - mu2 + i) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return np.log(res, where=res > 0)


def nonzero_solvent_and_unicontent(x, c1, mu1, sigma1, c2, mu2, sigma2, width2):
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0))
    n = 11
    nh = (n - 1) / 2
    for i in width2 * (np.arange(n) - nh) / nh:
        res += c2 * np.exp(- (x - mu2 + i) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return res


def fit_solvent_to_histogram(data, verbose=False, plot=False, components=1, n_lev=1000):
    tol = 0.001
    const_gauss = np.sqrt(2 * np.pi)

    vol = np.size(data)
    low = np.min(data)
    high = np.max(data)

    # Estimate solvent distribution initial parameters (to be refined by fitting)
    a, b = np.histogram(data, bins=n_lev)
    d_domain = b[1] - b[0]
    solvent_peak_index = np.argmax(a)
    solvent_peak = b[solvent_peak_index]
    solvent_scale = a[solvent_peak_index]
    c = solvent_peak_index
    while a[c] >= solvent_scale * 1 / np.exp(1):
        c += 1
    solvent_width = (c - solvent_peak_index) * d_domain
    solvent_vol = solvent_scale * (solvent_width / d_domain) * const_gauss  # area under initial guess
    solvent_fraction = solvent_vol / vol

    # Gaussian = 1/ (sigma * sqrt(2pi)) * exp ()

    # Estimate content distribution initial parameters (to be refined by fitting)
    n_sigma = 20.0
    content_width = (high - low)
    content_peak = solvent_peak  # low + (content_width / 2)
    content_width /= n_sigma
    content_peak_index = int(np.floor((content_peak - low) / d_domain))
    content_scale = a[content_peak_index]
    content_vol = content_scale * (content_width / d_domain) * const_gauss  # area under curve
    content_fraction = content_vol / vol

    domain = np.linspace(low, high, n_lev)
    if components == 1:
        p_guess = [solvent_scale, solvent_peak, solvent_width]
        popt, pcov = curve_fit(onecomponent_solvent, domain, a, p0=p_guess)
    else:
        p_guess = [solvent_scale, solvent_peak, solvent_width, content_scale, content_peak, content_width]
        popt, pcov = curve_fit(twocomponent_solvent, domain, a, p0=p_guess)

    if components == 1:
        guess = onecomponent_solvent(domain, p_guess[0], p_guess[1], p_guess[2])
        solvent_model = onecomponent_solvent(domain, popt[0], popt[1], popt[2])
    else:
        guess = twocomponent_solvent(domain, p_guess[0], p_guess[1], p_guess[2], p_guess[3], p_guess[4], p_guess[5])
        solvent_model = twocomponent_solvent(domain, popt[0], popt[1], popt[2], popt[3], popt[4], popt[5])

    fit = np.clip(solvent_model, tol ** 2, np.max(solvent_model))
    content_fraction_all = np.divide((a + tol - fit), a + tol)
    solvent_fraction_all = 1 - content_fraction_all

    if plot:
        f = plt.figure()
        ax1 = f.add_subplot(2, 1, 1)
        ax1.plot(b[:-1], a, 'k-', label='data')
        ax1.plot(domain, guess, 'b-', label='solvent guess', alpha=0.3)

        ax1.plot(domain, fit, 'g-', label='solvent fit')
        ax1.legend()
        ax1.set_ylim([1, solvent_scale * 1.1])
        plt.semilogy()

        ax2 = f.add_subplot(2, 1, 2)

        ax2.plot(domain, 100 * solvent_fraction_all, 'g-', label='solvent_fraction')
        ax2.set_ylim([0.1, 110])
        ax2.legend()

        plt.show()

    solvent_vol = np.sum(solvent_model)
    solvent_fraction = solvent_vol / vol
    content_fraction = 1 - solvent_fraction

    solvent_model_peak_index = np.argmax(solvent_model)

    threshold_high = n_lev - 1
    while solvent_model[threshold_high] < 1 and threshold_high > 0:
        threshold_high -= 1
    if threshold_high == 0:
        raise ValueError('high threshold limit not found, solvent fitted as larger than data domain?')

    threshold_midhigh = n_lev - 1
    while content_fraction_all[threshold_midhigh] > 0.01 and threshold_midhigh > 0:
        threshold_midhigh -= 1
    if threshold_midhigh == 0:
        raise ValueError('midhigh threshold limit not found, solvent fitted as larger than data domain?')

    threshold_midlow = 0
    while solvent_fraction_all[threshold_midlow] > 0 and threshold_midlow < n_lev - 1:
        threshold_midlow += 1
    if threshold_midlow == n_lev:
        raise ValueError('midlow threshold limit not found, solvent fitted as larger than data domain?')

    threshold_low = 0
    while solvent_model[threshold_low] < 1 and threshold_low < n_lev - 1:
        threshold_low += 1
    if threshold_low == n_lev:
        raise ValueError('low threshold limit not found, solvent fitted as larger than data domain?')

    if verbose:
        print(f'Revised estimate is {100 * solvent_fraction:.1f}% solvent and {100 * content_fraction:.1f}% content')
        '''
        print(f'Solvent limits are {b[threshold_low]:.4f} to {b[threshold_high]:.4f}. The latter is a recommended threshold. ')

        print('--SOLVENT--------------------------------------------')
        print(f' Peak:   {popt[1]:.4f}')
        print(f' Width:  {popt[2]:.4f} ({popt[2] / d_domain:.4f} bins)')
        print(f' Scale:  {popt[0]:.4f}')
        print(f' Volume: {solvent_vol:.2f}')
        print('--CONTENT--------------------------------------------')
        print(f' Peak:   {popt[4]:.4f}')
        print(f' Width:  {popt[5]:.4f} ({popt[5] / d_domain:.4f} bins)')
        print(f' Scale:  {popt[3]:.4f}')
        print(f' Volume: {content_vol:.2f}')
        '''
    solvent_range = np.array([b[threshold_low], b[threshold_midlow], b[threshold_midhigh], b[threshold_high]])

    if plot:
        for i in np.arange(4):
            ax1.plot(solvent_range[i] * np.ones(2), ax1.get_ylim(), 'k--')
            ax2.plot(solvent_range[i] * np.ones(2), ax2.get_ylim(), 'k--')

    return solvent_range, popt


# -------------------------------------------OCCUPANCY RELATED-----------------
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


def boost_map(data, boosting):
    return np.multiply(data, np.abs(boosting))


def boost_map_lambda(data, boosting, a=1):
    occ = np.divide(1, boosting, where=boosting != 0)
    eff_occ = 1.0 - a + a * np.divide(1, occ, where=boosting != 0)
    return np.multiply(data, np.abs(eff_occ))


def volume_limit_boost(occu_map, n_lev=30, plot=False, cutoff=False):
    global f, ax1, ax2

    mask = create_circular_mask(np.shape(occu_map)[0], dim=3)

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
        ax2.hist(occ.flatten(), bins=levels[::-1], label='vol-limited occu', histtype='step')
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
        new_mrc(np.clip(occ_map, 0, 1), 'occupancy.mrc', verbose=False)
    return occ_map, map_val_at_full_occupancy


def boost_map_occupancy(
        data,
        occ_map,
        sol_mask=None,
        occ_threshold=None,
        save_bst_map=False,
        verbose=True
):
    if occ_threshold is not None:
        # Use the supplied threshold hard
        if verbose:
            print(f'Applying strict occupancy threshold of {100 * occ_threshold:.1f}%.')
        boosting = 1 / threshold_occu_map(occ_map, occ_threshold)

    if sol_mask is not None:  # TODO make possible to use on top of occ_threshold
        if verbose:
            print('Using solvent mask when estimating occupancy.')
        boosting = (1 - sol_mask) + np.multiply(sol_mask, boosting)

    # TODO make use of volume-limiting thresholding?
    ''' 
        # Estimate the occupancy threshold
        if verbose:
            print('Using volume-limited occupancy.')
        boosting = volume_limit_boost(occ_map, plot=False, cutoff=True)
    '''

    # Boost map
    boosted_map = boost_map_lambda(data, boosting, 1)

    if save_bst_map:
        new_mrc(boosting.astype(np.float32), 'boosting.mrc')
    return boosted_map


def chimX_viz(
        ori,
        full,
        occ,
        threshold_ori=None,
        threshold_full=None,
        threshold_occ=None,
        extra_files=None):
    file_name = 'chimX_' + Path(ori).stem + '.cxc'

    pLDDT_unity = '0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue'
    rainbow = 'rainbow'

    with open(file_name, 'w') as f_open:
        # -----MODELS --------------------------------------
        print(f'open {ori} ', file=f_open)
        if threshold_ori is not None:
            print(f'vol #1 level {threshold_ori}', file=f_open)
        print(f'open {full} ', file=f_open)
        if threshold_full is not None:
            print(f'vol #2 level {threshold_full}', file=f_open)
        print(f'open {occ} ', file=f_open)
        if threshold_occ is None:
            print(f'hide #3 ', file=f_open)
        else:
            print(f'vol #3 level {threshold_occ}', file=f_open)

        # -----COLOR-----------------------------------------
        print(f'volume #1 color #d3d7cf \n', file=f_open)
        print(f'color sample #2 map #3 palette {rainbow} range 0,1 \n', file=f_open)
        print(f'volume  #3 color #4077bf40 \n', file=f_open)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=f_open)
        print(f'set bgColor white', file=f_open)
        print(f'camera ortho', file=f_open)

    f_open.close()
