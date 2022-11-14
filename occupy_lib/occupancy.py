import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as ndi
import warnings

from occupy_lib import map_tools, solvent


def sigmoid_effective_mu(
        mu0: float,
        order: float
):
    """
    Use a sigmoid defined on the [0,1]-interval to attenuate low and reinforce high scale:

    f(x)  =  ( 1 + ((x*(1-mu)) / (mu*(1-x))) ^ -m ) ^ -1

    Where m is an order paramter >=1, and x takes values on [0,1].

    But this ia defined to have f(mu) = 0.5.  We want to specify a scale-value that should be unchenged, i.e.

    f(mu0) = mu0

    Solving that equation finds a value mu_eff that results in f(mu0) = mu0

    mu_eff = ( (1/mu0 + 1)^(-1/m) * (1-mu0) / mu0  + 1 ) ^ -1

    :param mu:
    :param order:
    :return:
    """
    k = (1 / mu0 - 1) ** (-1 / order)
    k *= (1 - mu0) / mu0
    return 1 / (1 + k)


def sigmoid_scale(x, mu, order):
    """
    Use a sigmoid defined on the [0,1]-interval to attenuate low and reinforce high scale:

    f(x)  =  ( 1 + ((x*(1-mu)) / (mu*(1-x))) ^ -m ) ^ -1

    Where m is an order paramter >=1, and x takes values on [0,1]. Defined to have f(mu) = 0.5.

    :param x:
    :param mu:
    :param order:
    :return:
    """
    out = np.divide(mu * (1 - x), x * (1 - mu), where= x != 0)
    #out = np.divide(1, out, where=out != 0)
    if order != 1:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = np.power(out,order)
    out = out + 1
    out = np.divide(1, out, where=out != 0)
    out = np.clip(out, 0, 1)

    #To make sure
    for i in np.arange(len(x)):
        if x[i] == 0:
            out[i] = 0
        if x[i] == 1:
            out[i] == 1

    for i in np.arange(len(x)-1):
        if out[i+1]<out[i]:
            out[i+1]=out[i]



    return out


def scale_mapping_sigmoid(value_cutoff, order, n=1000, save_plot=False):
    # Determine the sigmoid mean (i.e. sigmoid(mean)=0.5) that results in f(value_cutoff) = value_cutoff for this order
    mu = sigmoid_effective_mu(value_cutoff, order=order)

    # Generate domain and mapping
    x = np.linspace(0, 1, n).astype(np.float32)
    s = sigmoid_scale(x, mu, order)

    if save_plot:
        plt.plot(x, s, label=f'{mu},order={order}')
        plt.legend()
        plt.savefig('sigmoid_mapping.png')

    return x, s


def compute_tiling(
        nd,
        tile_sz,
        n_tiles,
        verbose=False
):
    dim = len(nd)

    # Set the tile size as an array
    if tile_sz is None:
        tile_sz = (nd / n_tiles).astype(int)
    else:
        tile_sz = (tile_sz * np.ones(dim)).astype(int)

    # The maximum number of tiles. Overlap is ok.
    max_tiles = nd - tile_sz + 1

    if all(n_tiles > max_tiles):
        if verbose:
            print(
                f'{n_tiles} tiles is bigger than the largest number of {tile_sz[0]}-pixel tiles possible ({max_tiles[0]}). Reducing.')
        n_tiles = max_tiles[0]

    # number of voxels not used for tiles
    non_tile = nd - n_tiles * tile_sz
    non_tile_0 = np.clip(non_tile, 0, nd[0])

    # Space in-between n_tiles number of tiles
    space = np.floor(non_tile_0 // (n_tiles - 1)).astype(int)
    space_0 = np.clip(space, 0, nd[0]).astype(int)

    # Tile step (can be smaller than tile_sz)
    tile_step = (tile_sz + np.floor(non_tile // (n_tiles - 1))).astype(int)

    # Space around tiles
    edge = ((nd - ((n_tiles - 1) * tile_step + tile_sz)) // 2).astype(int)
    # ((non_tile_0 - space_0 * (n_tiles - 1)) / 2).astype(int)

    if verbose:
        print(
            f'Using {n_tiles} {tile_sz[0]}-voxel tiles, spaced by {space[0]}/{tile_step[0]} voxels and starting {edge[0]} voxels from the edge')

    return tile_sz, tile_step, edge


def percentile_filter_tiled(
        data: np.ndarray,
        kernel: np.ndarray,
        n_tiles: int,
        tile_sz: int = None,
        tau: float = 0.95,
        s0: bool = False,
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
    norm_val = 1.0
    extremum_idx_pix = None
    if s0:
        # Simpler normalization
        if verbose:
            print("Using simple kernel normalization, no tiled search")
        norm_val = tau * np.max(data)
    else:
        # Distribution-aware normalization

        # Tau is a percentile, it does not make sense to use it outside the range [0,1]
        assert 0 < tau <= 1

        # Sizes
        nd = np.array(np.shape(data))
        dim = len(nd)

        tile_sz, tile_step, edge = compute_tiling(
            nd,
            tile_sz,
            n_tiles,
            verbose=verbose
        )

        # Index of the smallest element in the percentile Tau
        n_tau = int(np.floor(tau * np.product(tile_sz)))

        # Prepare the output array
        # s_tau_tiles = np.zeros(n_tiles * np.ones(dim).astype(int), dtype=np.float32)

        # SCipy.ndimage has a percentile filter, but we only need non-exhaustive sampling and this is faster
        # despite using a for-loop structure.
        # There's probably a faster/better way of doing it, but at the moment this is negligible in execution time
        extremum = np.max(data) * np.array([-1, 1])
        extremum_idx = np.zeros((2, 3)).astype(int)

        if dim == 2:
            for i in np.arange(n_tiles):
                for j in np.arange(n_tiles):
                    low_edge = edge + np.multiply(tile_step, [i, j])
                    high_edge = low_edge + tile_sz
                    r = np.copy(data[
                                low_edge[0]: high_edge[0],
                                low_edge[1]: high_edge[1]]).flatten()
                    s = np.sort(r)
                    s_tau_tiles[i][j] = np.copy(s[n_tau])
        else:
            if verbose:
                print(f'Percentile tile scan... ', end='\r')
            c = 0
            for i in np.arange(n_tiles):
                for j in np.arange(n_tiles):
                    for k in np.arange(n_tiles):
                        c += 1
                        #if verbose:
                        #    print(f'Percentile tile scan {int(100 * c / (n_tiles ** 3))}% complete.', end='\r')
                        tile_r = np.sqrt((i - n_tiles / 2) ** 2 + (j - n_tiles / 2) ** 2 + (k - n_tiles / 2) ** 2)
                        if tile_r < n_tiles / 2 - 1:
                            low_edge = edge + np.multiply(tile_step, [i, j, k])
                            high_edge = low_edge + tile_sz
                            r = np.copy(data[
                                        low_edge[0]: high_edge[0],
                                        low_edge[1]: high_edge[1],
                                        low_edge[2]: high_edge[2]]).flatten()
                            s = np.sort(r)
                            v = s[n_tau]
                            # s_tau_tiles[i][j][k] = np.copy(v)

                            # Largest value
                            if v > extremum[0]:
                                extremum[0] = v
                                extremum_idx[0, :] = np.array([i, j, k])

                            # Smallest value
                            if v < extremum[1]:
                                extremum[1] = v
                                extremum_idx[1, :] = np.array([i, j, k])

        extremum_idx_pix = edge + tile_step[0] * extremum_idx + tile_sz / 2
        if verbose:
            print(f'Percentile tile scan completed.      \n')
            print(
                f'The largest value in percentile tile was {extremum[0]:.3f} in region {extremum_idx[0, :]} (pixel center {extremum_idx_pix[0, :]})')
            # print(f'The smallest value in percentile tile was {extremum[1]} in region {extremum_idx[1, :]} (pixel center {extremum_idx_pix[1,:]})')

        extremum_idx_pix = np.vstack((extremum_idx_pix, tile_sz / 2))
        # Establish s_max
        norm_val = extremum[0]  # np.max(s_tau_tiles)

    # Establish s_i
    maxi = ndi.maximum_filter(data, footprint=kernel)

    return maxi, norm_val, extremum_idx_pix


def percentile_filter(
        data: np.ndarray,
        kernel: np.ndarray,
        tau: float = None,
        tiles: int = 20,
        tile_sz: int = 12,
        s0: bool = False,
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
        s0=s0,
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


def modify_scale_gamma(
        scale: np.ndarray,
        gamma: float,
        amplify_gamma: bool = None,
        attenuate_gamma: bool = None
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
            b > 1           amplify
            b = inf         amplify all occupancies to 100%

    2)  Attenuates by exponentiating the current scale b-1:
        Ao = Ai * S ^ (b - 1) = ( A1 * S ) * S ^ (b -1) =  A1 * S ^ b
        So that:
            b = 0           not permitted
            0 < b < 1       amplify, so not permitted
            b = 1           identity
            b > 1           attenuate
            b = inf         attenuate all occupancies to 0%, except those at 100%

    :param data:
    :param scale:
    :param gamma:
    :param amplify_gamma:
    :param attenuate_gamma:
    :return:

    """

    assert gamma >= 1, "gamma-exponentiation of scale by less than 1 is not permitted"
    assert gamma > 1, "gamma-exponentiation by 1 is unity operation"
    assert amplify_gamma is not None or attenuate_gamma is not None, "Both amplify and attenuate are unset"
    assert not amplify_gamma == attenuate_gamma, "Cannot both amplify and attenuate"

    if amplify_gamma or not attenuate_gamma:
        gamma = 1 / gamma - 1
    else:  # attenuate
        gamma = gamma - 1
    return np.abs(scale) ** gamma


def modify_scale_sigmoid(
        scale: np.ndarray,
        nu: float,
        mu: float
):
    n = 100

    domain, mapping = scale_mapping_sigmoid(mu, nu, n)

    scale_idx = (np.abs(scale) * n - 1).astype(int)

    modification = np.divide(mapping[scale_idx], scale, where=scale > 0)

    return modification


def get_map_scale(
        data: np.ndarray,
        scale_kernel: np.ndarray,
        tau: float = None,
        save_occ_map: str = None,
        s0: bool = False,
        tile_size: int = 12,
        scale_mode: str = None,
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
    scale_map, map_val_at_full_scale, extr_tiles = percentile_filter(
        data,
        scale_kernel,
        tau=tau,
        s0=s0,
        tile_sz=tile_size,
        verbose=verbose)

    # Perform max-filter normalisation
    scale_map = np.clip(scale_map / map_val_at_full_scale, 0, 1)

    if s0:
        scale_mode = f'naive_{scale_mode}'
    # Save the scale
    if save_occ_map is not None:
        map_tools.new_mrc(
            scale_map,
            save_occ_map,
            vox_sz=1.0,
            verbose=verbose,
            extra_header=f'occupy scale: {scale_mode}'
        )
    return scale_map, map_val_at_full_scale, extr_tiles


def modify(
        data: np.ndarray,
        scale: np.ndarray,
        amplify_gamma: float = None,
        attenuate_gamma: float = None,
        sigmoid_gamma: float = None,
        sigmoid_pivot: float = None,
        fake_solvent: np.ndarray = None,
        sol_mask: np.ndarray = None,
        scale_threshold: float = None,
        save_modified_map: bool = False,
        verbose: bool = True
):
    """
    Modify an input array by applying a power-scaled scale-estimate


    :param data:
    :param scale:
    :param gamma:
    :param fake_solvent:
    :param sol_mask:
    :param scale_threshold:
    :param attenuate:
    :param save_modified_map:
    :param verbose:
    :return:
    """

    do_amplify = amplify_gamma is not None
    do_attenuate = attenuate_gamma is not None
    do_sigmoid = sigmoid_gamma is not None and sigmoid_pivot is not None

    # Expect separate calls, so that we dont do more than one thing
    actions = do_amplify + do_attenuate + do_sigmoid
    assert actions == 1, f'A modify call should only perform one action: ampl={do_amplify}, attn={do_attenuate}, sigm={do_sigmoid}'

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

    # Construct modification as dependent on scaling and gamma-coefficient
    modification = []
    if do_amplify:
        modification = modify_scale_gamma(
            thresholded_scale_map,
            amplify_gamma,
            attenuate_gamma=do_attenuate)

    if do_attenuate:
        modification = modify_scale_gamma(
            thresholded_scale_map,
            attenuate_gamma,
            attenuate_gamma=do_attenuate)

    if do_sigmoid:
        # Construct modification as dependent on scaling and gamma-coefficient
        modification = modify_scale_sigmoid(
            scale,
            sigmoid_gamma,
            sigmoid_pivot)

    # Amplify or attenuate map
    modified_map = np.multiply(data, modification)

    # Optional output with --save-all-maps
    if save_modified_map:
        map_tools.new_mrc(modification.astype(np.float32), 'modification.mrc', vox_sz=1)

    # Fake solvent is drawn from solvent model distribution
    # Fake solvent is None if amplifying
    if fake_solvent is not None:
        # CURRENT METHOD:  This is only active if attenuating, in which case the modification is on [0,1]
        modified_map += np.multiply(fake_solvent, np.clip(1 - modification,0,1))

        '''
        # OPTIONAL METHOD, make an attenuation mask (1-mod).clip(0,1), and combine with confidence. Add solvent there.
        region = np.multiply(confidence, np.clip(1 - modification,0,1))

        # Option to blend the added noise into the noise background by low-pass. 
        # Not as good as expected in tests - inactive
        blended_sol = modified_map + np.multiply(fake_solvent, region)
        blended_sol, _ = map_tools.lowpass(
            blended_sol,
            resolution=5.0,
            voxel_size=1.0
        )

        modified_map = np.multiply(modified_map, 1-region) + np.multiply(blended_sol, region)
        '''

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
        if hedge_confidence > 1:
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

    # Solving is too slow for the GUI responsiveness.
    """
    # Solve for the only real and positive root of x^n = 1 - x
    # which is the same as x^n + x -1 = 0
    v = np.zeros(n_v + 1)  # n_v + 1 degree polynomial with coefficients
    v[0] += 1  # x^n_v
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
    """
    tau = None
    if n_v <= 1000:
        tau_presolved = \
            [0.5000, 0.6180, 0.6823, 0.7245, 0.7549, 0.7781, 0.7965, 0.8117, 0.8243, 0.8351,
             0.8444, 0.8526, 0.8598, 0.8662, 0.8720, 0.8772, 0.8819, 0.8862, 0.8902, 0.8939,
             0.8973, 0.9004, 0.9034, 0.9061, 0.9087, 0.9111, 0.9134, 0.9155, 0.9175, 0.9195,
             0.9213, 0.9230, 0.9246, 0.9262, 0.9277, 0.9291, 0.9305, 0.9318, 0.9330, 0.9342,
             0.9354, 0.9365, 0.9375, 0.9386, 0.9396, 0.9405, 0.9414, 0.9423, 0.9432, 0.9440,
             0.9448, 0.9456, 0.9463, 0.9470, 0.9477, 0.9484, 0.9491, 0.9497, 0.9504, 0.9510,
             0.9516, 0.9522, 0.9527, 0.9533, 0.9538, 0.9543, 0.9548, 0.9553, 0.9558, 0.9563,
             0.9567, 0.9572, 0.9576, 0.9581, 0.9585, 0.9589, 0.9593, 0.9597, 0.9601, 0.9604,
             0.9608, 0.9612, 0.9615, 0.9619, 0.9622, 0.9625, 0.9629, 0.9632, 0.9635, 0.9638,
             0.9641, 0.9644, 0.9647, 0.9650, 0.9653, 0.9655, 0.9658, 0.9661, 0.9663, 0.9666,
             0.9668, 0.9671, 0.9673, 0.9676, 0.9678, 0.9680, 0.9683, 0.9685, 0.9687, 0.9689,
             0.9691, 0.9694, 0.9696, 0.9698, 0.9700, 0.9702, 0.9704, 0.9706, 0.9708, 0.9709,
             0.9711, 0.9713, 0.9715, 0.9717, 0.9718, 0.9720, 0.9722, 0.9724, 0.9725, 0.9727,
             0.9728, 0.9730, 0.9732, 0.9733, 0.9735, 0.9736, 0.9738, 0.9739, 0.9741, 0.9742,
             0.9744, 0.9745, 0.9746, 0.9748, 0.9749, 0.9750, 0.9752, 0.9753, 0.9754, 0.9756,
             0.9757, 0.9758, 0.9759, 0.9761, 0.9762, 0.9763, 0.9764, 0.9765, 0.9766, 0.9768,
             0.9769, 0.9770, 0.9771, 0.9772, 0.9773, 0.9774, 0.9775, 0.9776, 0.9777, 0.9778,
             0.9779, 0.9780, 0.9781, 0.9782, 0.9783, 0.9784, 0.9785, 0.9786, 0.9787, 0.9788,
             0.9789, 0.9790, 0.9791, 0.9792, 0.9793, 0.9794, 0.9794, 0.9795, 0.9796, 0.9797,
             0.9798, 0.9799, 0.9799, 0.9800, 0.9801, 0.9802, 0.9803, 0.9803, 0.9804, 0.9805,
             0.9806, 0.9807, 0.9807, 0.9808, 0.9809, 0.9810, 0.9810, 0.9811, 0.9812, 0.9812,
             0.9813, 0.9814, 0.9815, 0.9815, 0.9816, 0.9817, 0.9817, 0.9818, 0.9819, 0.9819,
             0.9820, 0.9821, 0.9821, 0.9822, 0.9822, 0.9823, 0.9824, 0.9824, 0.9825, 0.9826,
             0.9826, 0.9827, 0.9827, 0.9828, 0.9828, 0.9829, 0.9830, 0.9830, 0.9831, 0.9831,
             0.9832, 0.9832, 0.9833, 0.9834, 0.9834, 0.9835, 0.9835, 0.9836, 0.9836, 0.9837,
             0.9837, 0.9838, 0.9838, 0.9839, 0.9839, 0.9840, 0.9840, 0.9841, 0.9841, 0.9842,
             0.9842, 0.9843, 0.9843, 0.9844, 0.9844, 0.9845, 0.9845, 0.9846, 0.9846, 0.9846,
             0.9847, 0.9847, 0.9848, 0.9848, 0.9849, 0.9849, 0.9850, 0.9850, 0.9850, 0.9851,
             0.9851, 0.9852, 0.9852, 0.9853, 0.9853, 0.9853, 0.9854, 0.9854, 0.9855, 0.9855,
             0.9855, 0.9856, 0.9856, 0.9857, 0.9857, 0.9857, 0.9858, 0.9858, 0.9859, 0.9859,
             0.9859, 0.9860, 0.9860, 0.9860, 0.9861, 0.9861, 0.9862, 0.9862, 0.9862, 0.9863,
             0.9863, 0.9863, 0.9864, 0.9864, 0.9864, 0.9865, 0.9865, 0.9865, 0.9866, 0.9866,
             0.9866, 0.9867, 0.9867, 0.9867, 0.9868, 0.9868, 0.9868, 0.9869, 0.9869, 0.9869,
             0.9870, 0.9870, 0.9870, 0.9871, 0.9871, 0.9871, 0.9872, 0.9872, 0.9872, 0.9873,
             0.9873, 0.9873, 0.9873, 0.9874, 0.9874, 0.9874, 0.9875, 0.9875, 0.9875, 0.9875,
             0.9876, 0.9876, 0.9876, 0.9877, 0.9877, 0.9877, 0.9877, 0.9878, 0.9878, 0.9878,
             0.9879, 0.9879, 0.9879, 0.9879, 0.9880, 0.9880, 0.9880, 0.9880, 0.9881, 0.9881,
             0.9881, 0.9881, 0.9882, 0.9882, 0.9882, 0.9883, 0.9883, 0.9883, 0.9883, 0.9884,
             0.9884, 0.9884, 0.9884, 0.9884, 0.9885, 0.9885, 0.9885, 0.9885, 0.9886, 0.9886,
             0.9886, 0.9886, 0.9887, 0.9887, 0.9887, 0.9887, 0.9888, 0.9888, 0.9888, 0.9888,
             0.9888, 0.9889, 0.9889, 0.9889, 0.9889, 0.9890, 0.9890, 0.9890, 0.9890, 0.9890,
             0.9891, 0.9891, 0.9891, 0.9891, 0.9892, 0.9892, 0.9892, 0.9892, 0.9892, 0.9893,
             0.9893, 0.9893, 0.9893, 0.9893, 0.9894, 0.9894, 0.9894, 0.9894, 0.9894, 0.9895,
             0.9895, 0.9895, 0.9895, 0.9895, 0.9896, 0.9896, 0.9896, 0.9896, 0.9896, 0.9897,
             0.9897, 0.9897, 0.9897, 0.9897, 0.9898, 0.9898, 0.9898, 0.9898, 0.9898, 0.9899,
             0.9899, 0.9899, 0.9899, 0.9899, 0.9899, 0.9900, 0.9900, 0.9900, 0.9900, 0.9900,
             0.9900, 0.9901, 0.9901, 0.9901, 0.9901, 0.9901, 0.9902, 0.9902, 0.9902, 0.9902,
             0.9902, 0.9902, 0.9903, 0.9903, 0.9903, 0.9903, 0.9903, 0.9903, 0.9904, 0.9904,
             0.9904, 0.9904, 0.9904, 0.9904, 0.9905, 0.9905, 0.9905, 0.9905, 0.9905, 0.9905,
             0.9906, 0.9906, 0.9906, 0.9906, 0.9906, 0.9906, 0.9906, 0.9907, 0.9907, 0.9907,
             0.9907, 0.9907, 0.9907, 0.9908, 0.9908, 0.9908, 0.9908, 0.9908, 0.9908, 0.9908,
             0.9909, 0.9909, 0.9909, 0.9909, 0.9909, 0.9909, 0.9909, 0.9910, 0.9910, 0.9910,
             0.9910, 0.9910, 0.9910, 0.9910, 0.9911, 0.9911, 0.9911, 0.9911, 0.9911, 0.9911,
             0.9911, 0.9912, 0.9912, 0.9912, 0.9912, 0.9912, 0.9912, 0.9912, 0.9912, 0.9913,
             0.9913, 0.9913, 0.9913, 0.9913, 0.9913, 0.9913, 0.9914, 0.9914, 0.9914, 0.9914,
             0.9914, 0.9914, 0.9914, 0.9914, 0.9915, 0.9915, 0.9915, 0.9915, 0.9915, 0.9915,
             0.9915, 0.9915, 0.9916, 0.9916, 0.9916, 0.9916, 0.9916, 0.9916, 0.9916, 0.9916,
             0.9917, 0.9917, 0.9917, 0.9917, 0.9917, 0.9917, 0.9917, 0.9917, 0.9917, 0.9918,
             0.9918, 0.9918, 0.9918, 0.9918, 0.9918, 0.9918, 0.9918, 0.9919, 0.9919, 0.9919,
             0.9919, 0.9919, 0.9919, 0.9919, 0.9919, 0.9919, 0.9920, 0.9920, 0.9920, 0.9920,
             0.9920, 0.9920, 0.9920, 0.9920, 0.9920, 0.9921, 0.9921, 0.9921, 0.9921, 0.9921,
             0.9921, 0.9921, 0.9921, 0.9921, 0.9921, 0.9922, 0.9922, 0.9922, 0.9922, 0.9922,
             0.9922, 0.9922, 0.9922, 0.9922, 0.9923, 0.9923, 0.9923, 0.9923, 0.9923, 0.9923,
             0.9923, 0.9923, 0.9923, 0.9923, 0.9924, 0.9924, 0.9924, 0.9924, 0.9924, 0.9924,
             0.9924, 0.9924, 0.9924, 0.9924, 0.9925, 0.9925, 0.9925, 0.9925, 0.9925, 0.9925,
             0.9925, 0.9925, 0.9925, 0.9925, 0.9925, 0.9926, 0.9926, 0.9926, 0.9926, 0.9926,
             0.9926, 0.9926, 0.9926, 0.9926, 0.9926, 0.9927, 0.9927, 0.9927, 0.9927, 0.9927,
             0.9927, 0.9927, 0.9927, 0.9927, 0.9927, 0.9927, 0.9927, 0.9928, 0.9928, 0.9928,
             0.9928, 0.9928, 0.9928, 0.9928, 0.9928, 0.9928, 0.9928, 0.9928, 0.9929, 0.9929,
             0.9929, 0.9929, 0.9929, 0.9929, 0.9929, 0.9929, 0.9929, 0.9929, 0.9929, 0.9929,
             0.9930, 0.9930, 0.9930, 0.9930, 0.9930, 0.9930, 0.9930, 0.9930, 0.9930, 0.9930,
             0.9930, 0.9930, 0.9931, 0.9931, 0.9931, 0.9931, 0.9931, 0.9931, 0.9931, 0.9931,
             0.9931, 0.9931, 0.9931, 0.9931, 0.9931, 0.9932, 0.9932, 0.9932, 0.9932, 0.9932,
             0.9932, 0.9932, 0.9932, 0.9932, 0.9932, 0.9932, 0.9932, 0.9933, 0.9933, 0.9933,
             0.9933, 0.9933, 0.9933, 0.9933, 0.9933, 0.9933, 0.9933, 0.9933, 0.9933, 0.9933,
             0.9933, 0.9934, 0.9934, 0.9934, 0.9934, 0.9934, 0.9934, 0.9934, 0.9934, 0.9934,
             0.9934, 0.9934, 0.9934, 0.9934, 0.9934, 0.9935, 0.9935, 0.9935, 0.9935, 0.9935,
             0.9935, 0.9935, 0.9935, 0.9935, 0.9935, 0.9935, 0.9935, 0.9935, 0.9935, 0.9936,
             0.9936, 0.9936, 0.9936, 0.9936, 0.9936, 0.9936, 0.9936, 0.9936, 0.9936, 0.9936,
             0.9936, 0.9936, 0.9936, 0.9936, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937,
             0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9937, 0.9938,
             0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9938,
             0.9938, 0.9938, 0.9938, 0.9938, 0.9938, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939,
             0.9939, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939, 0.9939,
             0.9939, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940,
             0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9940, 0.9941, 0.9941,
             0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941,
             0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9941, 0.9942, 0.9942, 0.9942, 0.9942,
             0.9942, 0.9942, 0.9942, 0.9942, 0.9942, 0.9942, 0.9942, 0.9942, 0.9942, 0.9942,
             0.9942, 0.9942, 0.9942, 0.9942, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943,
             0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943, 0.9943,
             0.9943, 0.9943, 0.9943, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944,
             0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944, 0.9944,
             0.9944, 0.9944, 0.9944, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945,
             0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945, 0.9945,
             0.9945, 0.9945, 0.9945, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946,
             0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9946,
             0.9946, 0.9946, 0.9946, 0.9946, 0.9946, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947,
             0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947,
             0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9947, 0.9948, 0.9948, 0.9948
        ]
        tau = tau_presolved[n_v-1]
    elif n_v <= 7000:
        tau_presolved_from1100_incr100_to7000 = [
            0.99516, 0.99551, 0.99580, 0.99605, 0.99628, 0.99648, 0.99665, 0.99681, 0.99696, 0.99709,
            0.99720, 0.99731, 0.99741, 0.99751, 0.99759, 0.99767, 0.99775, 0.99781, 0.99788, 0.99794,
            0.99800, 0.99805, 0.99810, 0.99815, 0.99820, 0.99824, 0.99828, 0.99832, 0.99836, 0.99839,
            0.99843, 0.99846, 0.99849, 0.99852, 0.99855, 0.99858, 0.99860, 0.99863, 0.99865, 0.99868,
            0.99870, 0.99872, 0.99874, 0.99876, 0.99878, 0.99880, 0.99882, 0.99884, 0.99885, 0.99887,
            0.99889, 0.99890, 0.99892, 0.99893, 0.99895, 0.99896, 0.99897, 0.99899, 0.99900, 0.99901
        ]
        idx = (n_v-1000)//100
        tau = tau_presolved_from1100_incr100_to7000[idx]
    else: # n_v > 7000
        tau = 0.999
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
    # assert radius <= (size + 2) / 2.0, f'This radius ({radius}) requires a bigger odd-size kernel than {size}'

    # Construct the kernel
    kernel = map_tools.create_radial_mask(
        size,
        dim=3,
        radius=radius  # pixels
    )

    # Calculate optimal tau
    tau = set_tau(kernel)

    return kernel, tau
