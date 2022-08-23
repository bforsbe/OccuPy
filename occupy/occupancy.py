import numpy as np
from scipy import ndimage
from occupy import map_tools, solvent


def adjust_tiles(
        array_size,
        n_tiles,
        verbose=False
):
    """
    Adjust the number of tiles and with respect to the map dimension

    :param array_size:
    :param n_tiles:
    :param verbose:
    :return:    tile_number, tile_size
    """
    array_size = array_size[0]
    if not array_size % n_tiles == 0:
        if verbose:
            print(f'number of tiles ({n_tiles}) does not divide data array ({array_size}) evenly;')
        t_low = n_tiles
        while t_low > 2:
            t_low -= 1
            if array_size % t_low == 0:
                break
        t_high = n_tiles
        while t_high < array_size:
            t_high += 1
            if array_size % t_high == 0:
                break
        n_tiles = np.min(np.array([t_low, t_high]) - n_tiles) + n_tiles
        if n_tiles == 1 or n_tiles == array_size:
            raise ValueError(f'Could not find a reasonable tile number (for data size {array_size})')
        elif not array_size % n_tiles == 0:
            raise ValueError(
                f'number of tiles ({n_tiles}) does not divide data array ({array_size}), even after adjustment')
        else:
            if verbose:
                print(f' ---->  Adjusted percentile value scan to {n_tiles} tiles.')

    return n_tiles


def percentile_filter_tiled(
        data: np.ndarray,
        kernel: np.ndarray,
        n_tiles: int,
        tile_sz: int = None,
        tau: float = 0.95,
        verbose: bool = False
):
    """
    Penerate the components of a normalized max-filter on the input data

    A conventional max-filter utilizing the provided kernel established each pixel value s_i
    A tiled (non-exhaustive) search across the input array establishes a normalization constant s_max

    The output is

        s_i, s_max

    The normalized max-filter can be computed as

       clip(s_i/s_max, 0, 1)

    :param data:        input data array
    :param kernel:      kernel for max-value filtration
    :param n_tiles:     number of tiles across each dimension
    :param tile_sz:     number of pixels along each dimension of the tile/input array
    :param tau:         the percentile of the max-vlue distribution to use to establish s_max
    :param verbose:     be verbose
    :return:   s_i   and    s_max
    """

    # Tau is a percentile, it does not make sense to use it outside the range [0,1]
    assert 0 < tau <= 1

    # Sizes
    nd = np.array(np.shape(data))
    dim = len(nd)

    # Establish / adjust default tile sizes
    n_tiles = adjust_tiles(
        nd,
        n_tiles,
        verbose=verbose
    )

    # Set the tile size as an array
    if tile_sz is None:
        tile_sz = (nd / n_tiles).astype(int)
    else:
        tile_sz = (tile_sz * np.ones(dim)).astype(int)

    # Index for the first tile element
    tile_start = (nd / n_tiles).astype(int)

    # Index of the smallest element in the percentile Tau
    n_tau = int(np.floor(tau * np.product(tile_sz)))

    # Prepare the output array
    s_tau_tiles = np.zeros(n_tiles * np.ones(dim).astype(int), dtype=np.float32)

    # SCipy.ndimage has a percentile filter, but we only need non-exhaustive sampling and this is faster
    # despite using a for-loop structure.
    # There's probably a faster/better way of doing it, but at the moment this is negligible in execution time
    if dim == 2:
        for i in np.arange(tile_sz[0]):
            for j in np.arange(tile_sz[1]):
                r = np.copy(data[
                            i * tile_start[0]:i * tile_start[0] + tile_sz[0],
                            j * tile_start[1]:j * tile_start[1] + tile_sz[1]]).flatten()
                s = np.sort(r)
                s_tau_tiles[i][j] = np.copy(s[n_tau])
    else:
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
                    s_tau_tiles[i][j][k] = np.copy(s[n_tau])
    if verbose:
        print('Percentile tile scan completed.      \n')

    # Establish s_max
    max_per = np.max(s_tau_tiles)

    # Establish s_i
    maxi = ndimage.maximum_filter(data, footprint=kernel)

    return maxi, max_per


def percentile_filter(
        data: np.ndarray,
        kernel: np.ndarray,
        tau: float = None,
        tiles: int = 12,
        tile_sz: int = 5,
        verbose: bool = False
):
    # Tau is a percentile, it does not make sense to use it outside the range [0,1]
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
    """
    Apply a threshold to a map representing estimated scale, WHERE VALUES BELOW ARE SET TO 1.

    if mask is None:
        mask = input_array

    S_out(i) = S_in(i)  if  mask(i) > scale_threshold
    S_out(i) = 1        if  mask(i) > scale_threshold

    :param scale_map:
    :param scale_threshold:
    :param mask:
    :return:
    """
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
    """
    Amplify a in input array by the local scale. At the moment simple element-wise multiplication

    :param data:
    :param amplification:
    :return:

    """
    return np.multiply(data, np.abs(amplification))


def amplify_map_beta(
        data: np.ndarray,
        scale: np.ndarray,
        beta: float,
        amplify_beta: bool = None,
        attenuate_beta: bool = None
):
    """
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

    :param data:
    :param scale:
    :param beta:
    :param amplify_beta:
    :param attenuate_beta:
    :return:

    """

    assert beta >= 1, "Beta-exponentiation of scale by less than 1 is not permitted"
    assert beta > 1, "Beta-exponentiation by 1 is unity operation"
    assert amplify_beta is not None or attenuate_beta is not None, "Both amplify and attenuate are unset"
    assert not amplify_beta == attenuate_beta, "Cannot both amplify and attenuate"

    if amplify_beta or not attenuate_beta:
        beta = 1 / beta - 1
    else:  # attenuate
        beta = beta - 1
    return np.abs(scale) ** beta


def get_map_scale(
        data: np.ndarray,
        scale_kernel: np.ndarray,
        tau: float = None,
        save_occ_map: str = None,
        verbose: bool = True
):
    """
    Estimate the local scale of each array element with respect to the global gray scale (distribution)

        :param data
        :param scale_kernel:
        :param tau:
        :param sol_mask:
        :param sol_threshold:
        :param save_occ_map:
        :param verbose:
    """

    # Calculate the local scale and normalisation constant based on desired percentile confidence
    scale_map, map_val_at_full_scale = percentile_filter(
        data,
        scale_kernel,
        tau=tau,
        verbose=verbose)

    # Perform max-filter normalisation
    scale_map = np.clip(scale_map / map_val_at_full_scale, 0, 1)

    # Save the scale
    if save_occ_map is not None:
        map_tools.new_mrc(scale_map, save_occ_map, vox_sz=1.0, verbose=verbose)
    return scale_map, map_val_at_full_scale


def modify_beta(
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
    """
    Modify an input array by applying a power-scaled scale-estimate


    :param data:
    :param scale:
    :param beta:
    :param fake_solvent:
    :param sol_mask:
    :param scale_threshold:
    :param attenuate:
    :param save_amp_map:
    :param verbose:
    :return:
    """

    # Exit without doing anything
    if beta is None or beta == 1:
        return data

    # Scale threshold stops very small estimated scales from being modified.
    if scale_threshold is None:
        scale_threshold = 0.05
        if verbose:
            print(
                f'No occupancy threshold set, using {100 * scale_threshold:.1f}% to limit spurious over-modification.')
    elif verbose:
        print(f'Applying provided strict occupancy threshold of {100 * scale_threshold:.1f}%.')

    # Supply threshold (set scale below threshold to 1, i.e. don't modify)
    thresholded_scale_map = threshold_scale_map(scale, scale_threshold)

    # Solvent mask option that isn't really used at the moment
    if sol_mask is not None:
        if verbose:
            print('Using solvent mask when equalising occupancy.')
        thresholded_scale_map = (1 - sol_mask) + np.multiply(sol_mask, thresholded_scale_map)

    # Construct modification as dependent on scaling and beta-coefficient
    modification = amplify_map_beta(
        scale,
        thresholded_scale_map,
        beta,
        attenuate_beta=attenuate
    )

    # Amplify or attenuate map
    modified_map = np.multiply(data, modification)

    # Optional output with --save-all-maps
    if save_amp_map:
        map_tools.new_mrc(modification.astype(np.float32), 'modification.mrc', vox_sz=1)

    # Fake solvent is drawn from solvent model distribution
    # Fake solvent is None if amplifying
    if fake_solvent is not None:

        # This is only active if attenuating, in which case the modification is on [0,1]
        modified_map += np.multiply(fake_solvent, 1 - modification)

    return modified_map


def estimate_confidence(
        data,
        solvent_paramters,
        hedge_confidence=None,
        n_lev=1000
):
    """
    Estimate the confidence of each voxel, given the data and the solvent model

    The estiamte is based on the relative probability of each voxel value pertaining to non-solvent or solvenr model

    :param data:                input array
    :param solvent_paramters:   solvent model parameters, gaussian (scale, mean, var)
    :param hedge_confidence:    take the estimated confidence to this power to hedge
    :param n_lev:               how many levels to use for the histogram
    :return:

    """
    # Establish histogram for the data without solvent masked
    a, b = np.histogram(
        data,
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

    # Solvent model to compare against histogram
    fit = np.clip(solvent_model, 0.0, np.max(solvent_model))

    # Raw confidence estimate
    content_fraction_all = np.divide((a + 0.01 - fit[:-1]), a + 0.01)

    # Enforce monotonically decreasing confidence with decreasing map scale
    out = np.copy(content_fraction_all)
    dt = 0
    for i in np.flip(np.arange(np.size(out) - 1)):

        # The out[i+1]-dt teem enforces monotonically decreasing *derivative* of confidence with decreasing map scale
        a = [out[i], out[i + 1], out[i + 1] - dt]

        out[i] = np.min(a)

        # The current derivative
        dt = out[i + 1] - out[i]

        # Lower map values should be left 0
        if out[i - 1] <= 0:
            out[:i - 1] = 0
            break

    # generate the mapping of data to confidence
    indx = (map_tools.uniscale_map(np.copy(data), move=True) * n_lev - 1).astype(int)

    # Hedge if requested
    if hedge_confidence is not None:
        assert hedge_confidence > 1
        out = out ** hedge_confidence

    # Generate ouput from mapping
    confidence = (out[indx]).astype(np.float32)

    # Clip output to [0,1]  (This should not be necessary, but is legacy and untested)
    confidence = np.clip(confidence, 0.0, 1.0)

    return confidence, out


def set_tau(
        kernel=None,
        n_v=None
):
    """
    Set the percentile of a random variable X which equals the confidence in it's max-value distribution max(x_i,..,x_n)

    This crucially depends no the number of values n. One can provide either a boolean kernel or a number of samples n_v

    The function the finds the only positive real root of the equation

    x**n + x - 1 == 0

    :param kernel:
    :param n_v:
    :return: percentile
    """

    if kernel is not None and n_v is not None:
        raise ValueError("Specify kernel OR n_v, not both")
    if kernel is None and n_v is None:
        raise ValueError("Specify kernel OR n_v, not both")

    # A kernel tends to be a multi-dimensional array with equal sides, where 1 = True
    if kernel is not None:
        n_v = np.sum(kernel)

    # Solve for the only real and positive root of x^n = 1 - x
    # which is the same as x^n + x -1 = 0
    v = np.zeros(n_v + 1)   # n_v + 1 degree polynomial wiht coefficients
    v[0] += 1   # x^n_v
    v[-2] += 1  # x^1
    v[-1] = -1  # x^0
    rt = np.roots(v)

    # Select positive
    rt = rt[rt.real > 0]

    # SElect the real root, as the root with the smallest imaginary value, in case there's issues in precision
    r = np.argsort(np.abs(rt.imag))

    # Make sure it's real
    tau = rt[r[0]].real

    return tau


def spherical_kernel(
        size,
        radius=None
):
    """
    Create spherical kernel and return the optimal percentile tau as well

    :param size:    [pix]       Odd-size kernel length
    :param radius:  [pix]       Non-integer radius
    :return:
    """
    assert size % 2 == 1, f'Please make odd-sizes kernels, not size={size}'
    assert radius <= (size + 2) / 2.0, f'This radius ({radius}) requires a bigger odd-size kernel than {size}'

    # Construct the kernel
    kernel = map_tools.create_radial_mask(
        size,
        dim=3,
        radius=radius  # pixels
    )

    # Calculate optimal tau
    tau = set_tau(kernel)

    return kernel, tau
