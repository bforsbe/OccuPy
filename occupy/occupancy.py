import numpy as np
from scipy import ndimage
from occupy import map_tools, solvent


def occupancy_map(
        data: np.ndarray,
        kernel: np.ndarray,
        mask: np.ndarray = None,
        verbose: bool = True
):
    occu_map, map_val_at_full_occupancy = occupancy_map_percentile(data, kernel, mask)
    return occu_map, map_val_at_full_occupancy


def percentile_filter_tiled(
        data: np.ndarray,
        kernel: np.ndarray,
        mask: np.ndarray,
        n_tiles: int,
        tile_sz: int = None,
        per:float = 0.4,
        verbose: bool = False
):
    assert (per>0 and per <=1)

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


def occupancy_map_maximum(
        data: np.ndarray,
        kernel: np.ndarray
):
    return ndimage.maximum_filter(data, footprint=kernel)


def occupancy_map_percentile(
        data: np.ndarray,
        kernel: np.ndarray,
        mask: np.ndarray = None,
        per:float = 0.95,
        tiles: int = 12,
        tile_sz: int = 5
):
    assert (per > 0 and per <= 1)
    return percentile_filter_tiled(data, kernel, mask, n_tiles=tiles, tile_sz=tile_sz, per=per)


def threshold_occu_map(
        occu_map: np.ndarray,
        occ_threshold: float,
        mask: np.ndarray = None
):
    if mask is None:
        mask = occu_map
    # Occupancy higher than threshold should be boosted inversely to occupancy
    t_occu_map = np.multiply(occu_map, mask > occ_threshold)

    # Lower than threshold should be boosted as if full occupancy (do not touch),
    # but we set it to -1 for clarity and handle it during boosting
    t_occu_map -= mask <= occ_threshold

    return t_occu_map


def amplify_map(
        data: np.ndarray,
        amplification: np.ndarray
):
    return np.multiply(data, np.abs(amplification))


def amplify_map_alpha(
        data: np.ndarray,
        amplification: np.ndarray,
        a: float,
):
    assert a <= 1, "Amplifying with more than 1 does not make sense"
    assert a != 0, "Amplifying with 0 will not do anything"

    return np.multiply(data, np.abs(amplification)**a)


def amplify_map_lambda(
        data: np.ndarray,
        amplification: np.ndarray,
        l: float,
        invert: bool = False
):
    occ = np.divide(1, amplification, where=amplification != 0)
    eff_occ = 1.0 - l + l * np.divide(1, occ, where=occ != 0)
    if invert:
        return np.divide(data, np.abs(eff_occ),where= np.abs(eff_occ)!=0 )
    else:
        return np.multiply(data, np.abs(eff_occ))


def get_map_occupancy(
        data: np.ndarray,
        occ_kernel: np.ndarray,
        sol_mask: np.ndarray = None,
        sol_threshold: float = None,
        save_occ_map: str = None,
        verbose: bool = True
):
    """
        TODO
        :param data
        :param occ_kernel:
        :param sol_mask:
        :param sol_threshold:
        :param save_occ_map:
        :param verbose:
    """

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

    if save_occ_map is not None:
        map_tools.new_mrc(np.clip(occ_map, 0, 1), save_occ_map, verbose=False)
    return occ_map, map_val_at_full_occupancy


def amplify(
        data: np.ndarray,
        occ_map: np.ndarray,
        amplify_amount: float = None,
        sol_mask: np.ndarray = None,
        occ_threshold: float = None,
        save_amp_map: bool = False,
        verbose: bool = True
):

    if amplify_amount is None or amplify_amount == 0:
        return data

    if occ_threshold is None:
        occ_threshold = 0.05
        if verbose:
            print(f'No occupancy threshold set, using {100 * occ_threshold:.1f}% to limit spurious over-amplification.')
    elif verbose:
        print(f'Applying provided strict occupancy threshold of {100 * occ_threshold:.1f}%.')
    thr_occu_map = threshold_occu_map(occ_map, occ_threshold)
    amplification = np.divide(1, thr_occu_map, where=thr_occu_map != 0)

    if sol_mask is not None:
        if verbose:
            print('Using solvent mask when equalising occupancy.')
        amplification = (1 - sol_mask) + np.multiply(sol_mask, amplification)

    if save_amp_map:
        map_tools.new_mrc(amplification.astype(np.float32), 'amplification.mrc')

    # Equalise map
    amplified_map = amplify_map_alpha(data, amplification, amplify_amount)

    return amplified_map

def estimate_confidence(
        scale_data,
        solvent_paramters,
        hedge_confidence=None,
        n_lev=1000
):
    # Establish histogram for the data without solvent masked
    a, b = np.histogram(
        scale_data,
        bins=n_lev,
        density=True
    )

    # Find intersection of solvent model and content
    solvent_model = solvent.onecomponent_solvent(
        b,
        solvent_paramters[0],
        solvent_paramters[1],
        solvent_paramters[2]
    )
    fit = np.clip(solvent_model, 0.0, np.max(solvent_model))

    c = len(b) - 2
    while c > 0:
        c -= 1
        if a[c] <= fit[c] and fit[c] > 0.1:
            break

    content_fraction_all = np.divide((a + 0.01 - fit[:-1]), a + 0.01)

    content_conf = np.copy(content_fraction_all)
    for i in np.arange(np.size(content_conf) - 2) + 1:
        content_conf[-i - 2] = np.min(content_conf[-i - 2:-i])
        if content_conf[-i - 3] < 0:
            content_conf[:-i - 2] = 0
            break

    indx = (map_tools.uniscale_map(np.copy(scale_data), norm=True) * n_lev - 1).astype(int)

    if hedge_confidence is not None:
        content_conf = content_conf ** hedge_confidence

    confidence = content_conf[indx]

    return confidence, content_conf