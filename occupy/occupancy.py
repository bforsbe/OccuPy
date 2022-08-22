import numpy as np
from scipy import ndimage
from occupy import map_tools, solvent



def percentile_filter_tiled(
        data: np.ndarray,
        kernel: np.ndarray,
        n_tiles: int,
        tile_sz: int = None,
        tau: float = 0.95,
        verbose: bool = False
):
    assert 0 < tau <= 1

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
    npick = int(np.floor(tau * np.product(tile_sz)))
    out_tiles = np.zeros(n_tiles * np.ones(dim).astype(int), dtype=np.float32)
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
    maxi = max_filter(data, kernel)

    '''
    maxi /= max_per
    if verbose:
        print(f'Map value defined to represent 100% occupancy is {max_per:.3f}')

    # Clip de occupancies>1 down to 1
    maxi = np.clip(maxi, 0.0, 1.0)
    '''

    return maxi, max_per


def max_filter(
        data: np.ndarray,
        kernel: np.ndarray
):
    return ndimage.maximum_filter(data, footprint=kernel)


def percentile_filter(
        data: np.ndarray,
        kernel: np.ndarray,
        tau: float = None,
        tiles: int = 12,
        tile_sz: int = 5,
        verbose: bool = False
):
    assert 0 < tau <= 1
    return percentile_filter_tiled(
        data,
        kernel,
        n_tiles=tiles,
        tile_sz=tile_sz,
        tau=tau,
        verbose=verbose
    )


def threshold_scale_map(
        scale_map: np.ndarray,
        scale_threshold: float,
        mask: np.ndarray = None
):
    if mask is None:
        mask = scale_map
    # Occupancy higher than threshold should be boosted inversely to occupancy
    out_map = np.multiply(scale_map, mask > scale_threshold)

    # Lower than threshold should be boosted as if full occupancy (do not touch),
    # but we set it to -1 for clarity and handle it during boosting
    out_map -= mask <= scale_threshold

    return out_map


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
    '''
    This function amplifies by exponentiating the amplification by alpha
    alpha = 0 is identity
    alpha  = 1 is take everythin to 100%
    alpha = -inf is kill everything except when occ=100%
    '''

    assert a <= 1, "Amplifying with more than 1 does not make sense"
    assert a != 0, "Amplifying with 0 will not do anything"

    return np.multiply(data, np.abs(amplification) ** a)


def amplify_map_beta(
        data: np.ndarray,
        scale: np.ndarray,
        beta: float,
        amplify_beta: bool=None,
        attenuate_beta: bool=None
):
    '''
    Consider the input map to be 100% everywhere, but scaled down by the
    estimated scale 0<=S<=1:

    A_input = A_100% * S_est    (Ai = A1 * S)

    This function either

    1)  Amplifies by exponentiating the current scale 1/b-1:
        Ao = Ai * S ^ (1/b - 1) = ( A1 * S ) * S ^ (1/b -1) =  A1 * S ^ (1/b)
        So that:
            b = 0           not permitted
            0 < b < 1       attentuate, so not permitted
            b = 1           identity
            b > 0           amplify
            b = inf         amplify all occupancies to 100%

    2)  Attenuates by exponentiating the current scale b-1:
        Ao = Ai * S ^ (b - 1) = ( A1 * S ) * S ^ (b -1) =  A1 * S ^ b
        So that:
            b = 0           not permitted
            0 < b < 1       amplify, so not permitted
            b = 1           identity
            b > 0           attenuate
            b = inf         attenuate all occupancies to 0%, except those at 100%

    '''

    assert beta >= 1, "Beta-exponentiation of scale by less than 1 is not permitted"
    assert beta > 1,  "Beta-exponentiation by 1 is unity operation"
    assert amplify_beta is not None or attenuate_beta is not None, "Both amplify and attenuate are unset"
    assert not amplify_beta==attenuate_beta, "Cannot both amplify and attenuate"

    if amplify_beta or not attenuate_beta:
        beta = 1 / beta - 1
    else: #attenuate
        beta = beta - 1
    return np.abs(scale) ** beta

def amplify_map_lambda(
        data: np.ndarray,
        amplification: np.ndarray,
        l: float,
        invert: bool = False
):
    occ = np.divide(1, amplification, where=amplification != 0)
    eff_occ = 1.0 - l + l * np.divide(1, occ, where=occ != 0)
    if invert:
        return np.divide(data, np.abs(eff_occ), where=np.abs(eff_occ) != 0)
    else:
        return np.multiply(data, np.abs(eff_occ))

def get_map_scale(
        data: np.ndarray,
        scale_kernel: np.ndarray,
        tau: float = None,
        save_occ_map: str = None,
        verbose: bool = True
):
    """
        TODO
        :param data
        :param scale_kernel:
        :param sol_mask:
        :param sol_threshold:
        :param save_occ_map:
        :param verbose:
    """

    scale_map, map_val_at_full_scale = percentile_filter(
        data,
        scale_kernel,
        tau = tau,
        verbose=verbose)

    scale_map = np.clip(scale_map / map_val_at_full_scale, 0, 1)

    if save_occ_map is not None:
        map_tools.new_mrc(scale_map, save_occ_map, sz=1.0, verbose=verbose)
    return scale_map, map_val_at_full_scale


def amplify(
        data: np.ndarray,
        occ_map: np.ndarray,
        amplify_amount: float = None,
        fake_solvent: np.ndarray = None,
        sol_mask: np.ndarray = None,
        scale_threshold: float = None,
        save_amp_map: bool = False,
        verbose: bool = True
):
    if amplify_amount is None or amplify_amount == 0:
        return data

    if scale_threshold is None:
        scale_threshold = 0.05
        if verbose:
            print(f'No occupancy threshold set, using {100 * scale_threshold:.1f}% to limit spurious over-amplification.')
    elif verbose:
        print(f'Applying provided strict occupancy threshold of {100 * scale_threshold:.1f}%.')
    thresholded_scale_map = threshold_scale_map(occ_map, scale_threshold)
    amplification = np.divide(1, thresholded_scale_map, where=thresholded_scale_map != 0)

    if sol_mask is not None:
        if verbose:
            print('Using solvent mask when equalising occupancy.')
        amplification = (1 - sol_mask) + np.multiply(sol_mask, amplification)

    # Amplify or attenuate map
    amplified_map = amplify_map_alpha(data, amplification, amplify_amount)

    if save_amp_map:
        map_tools.new_mrc(
            np.multiply(data, np.abs(amplification) ** amplify_amount).astype(np.float32),
            'amplification.mrc',
            sz=1)

    if fake_solvent is not None:
        # This is only active if attenuating, in which case the amplification is on [0,1]
        amplified_map += np.multiply(fake_solvent, 1 - np.abs(amplification)**amplify_amount)

    return amplified_map

def amplify_beta(
        data: np.ndarray,
        scale: np.ndarray,
        beta: float = None,
        fake_solvent: np.ndarray = None,
        sol_mask: np.ndarray = None,
        scale_threshold: float = None,
        attenuate: bool = False,
        save_amp_map: bool = False,
        verbose: bool = True
):
    if beta is None or beta==1:
        return data

    if scale_threshold is None:
        scale_threshold = 0.05
        if verbose:
            print(f'No occupancy threshold set, using {100 * scale_threshold:.1f}% to limit spurious over-amplification.')
    elif verbose:
        print(f'Applying provided strict occupancy threshold of {100 * scale_threshold:.1f}%.')
    thresholded_scale_map = threshold_scale_map(scale, scale_threshold)

    if sol_mask is not None:
        if verbose:
            print('Using solvent mask when equalising occupancy.')
        thresholded_scale_map = (1 - sol_mask) + np.multiply(sol_mask, thresholded_scale_map)

    # Construct modification as dependent on scaling and beta-coeff
    amplification = amplify_map_beta(
        scale,
        thresholded_scale_map,
        beta,
        attenuate_beta=attenuate
        )

    # Amplify or attenuate map
    amplified_map = np.multiply(data, amplification)

    if save_amp_map:
        map_tools.new_mrc(amplification.astype(np.float32), 'amplification.mrc',sz=1)

    if fake_solvent is not None:
        # This is only active if attenuating, in which case the amplification is on [0,1]
        amplified_map += np.multiply(fake_solvent, 1 - amplification)

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

    # Enforce monotonically decreasing confidence with decreasing map scale
    out = np.copy(content_fraction_all)
    dt = 0
    for i in np.flip(np.arange(np.size(out)-1)):

        # The out[i+1]-dt teem enforces monotonically decreasing *derivative* of confidence with decreasing map scale
        a = [out[i],out[i+1],out[i+1]-dt]

        out[i] = np.min(a)

        # The current derivative
        dt = out[i+1]-out[i]

        # Lower map values should be left 0
        if out[i-1] <= 0:
            out[:i-1]=0
            break

    indx = (map_tools.uniscale_map(np.copy(scale_data), norm=True) * n_lev - 1).astype(int)

    if hedge_confidence is not None:
        out = out ** hedge_confidence

    confidence = (out[indx]).astype(np.float32)

    confidence = np.clip(confidence,0.0,1.0)

    return confidence, out

def set_tau(kernel=None, n_v=None):

    if kernel is not None and n_v is not None:
        raise ValueError("Specify kernel OR n_v, not both")
    if kernel is None and n_v is None:
        raise ValueError("Specify kernel OR n_v, not both")

    if kernel is not None:
        n_v = np.sum(kernel)

    # Solve for the only real and positive root of x^n = 1 - x
    # which is the same as x^n + x -1 = 0
    v=np.zeros(n_v+1)
    v[0]  +=1
    v[-2] +=1
    v[-1] =-1
    rt = np.roots(v)
    rt = rt[rt.real>0]

    #Select the root with the smallest imaginaryvalue, in case there's issues in precision
    r = np.argsort(np.abs(rt.imag))

    #Make sure it's real
    tau = rt[r[0]].real

    return tau

def spherical_kernel(size, radius=None):

    assert size % 2 == 1, f'Please make odd-sizes kernels, not size={size}'
    assert radius <= (size+2)/2.0, f'This radius ({radius}) requires a bigger odd-size kernel than {size}'

    kernel = map_tools.create_circular_mask(
        size,
        dim=3,
        radius=radius,  # pixels
        soft=False
    )

    tau = set_tau(kernel)

    return kernel, tau