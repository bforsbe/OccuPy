import numpy as np
import pylab as plt
from scipy.optimize import curve_fit


def cauchy(
        x: np.ndarray,
        c: float,
        mu: float,
        gamma: float
):
    if gamma == 0:
        gamma += 0.001  # TODO
    res = (1/(np.pi*gamma))*(gamma**2/((x-mu)**2 + gamma**2))
    return res


def onecomponent_solvent(
        x: np.ndarray,
        c: float,
        mu: float,
        sigma: float
):
    if sigma == 0:
        sigma += 0.001  # TODO
    res = c * np.exp(- (x - mu) ** 2.0 / (2.0 * sigma ** 2.0))
    return res


def onecomponent_solvent_zeropeak(
        x: np.ndarray,
        c: float,
        mu: float,
        sigma: float
):
    if sigma == 0:
        sigma += 0.001  # TODO
    res = c * np.exp(- (x - mu) ** 2.0 / (2.0 * sigma ** 2.0))
    penalty = mu * 1000
    return res + penalty


def twocomponent_solvent(
        x: np.ndarray,
        c1: float,
        mu1: float,
        sigma1: float,
        c2: float,
        mu2: float,
        sigma2: float
):
    if sigma1 == 0:
        sigma1 += 0.001  # TODO
    if sigma2 == 0:
        sigma2 += 0.001
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0)) \
          + c2 * np.exp(- (x - mu2) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return res


def log_nonzero_solvent_and_content(
        x: np.ndarray,
        c1: float,
        mu1: float,
        sigma1: float,
        c2: float,
        mu2: float,
        sigma2: float
):
    if sigma1 == 0:
        sigma1 += 0.001
    if sigma2 == 0:
        sigma2 += 0.001
    res = c1 * np.exp(- (x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0)) \
          + c2 * np.exp(- (x - mu2) ** 2.0 / (2.0 * sigma2 ** 2.0))
    return np.log(res, where=res > 0)


def fit_solvent_to_histogram(
        data: np.ndarray,
        verbose: bool = False,
        plot: bool = False,
        components: int = 1,
        n_lev: int = 1000
):
    """
    Fit a single gaussian to the main peak of the array histogram

    :param data:        input data
    :param verbose:     be verbose
    :param plot:        plot output
    :param n_lev:       number of bins for histogram
    :return:
    """

    assert components == 1 or components == 2

    # Set a tolerance for numerical stability
    tol = 0.001 #TODO make input?

    # Some constants
    vol = np.size(data)
    low = np.min(data)
    high = np.max(data)

    # Estimate solvent distribution initial parameters (to be refined by fitting)
    a, b = np.histogram(data, bins=n_lev, density=True)

    # step
    d_domain = b[1] - b[0]

    # guess peak as most common bin
    solvent_peak_index = np.argmax(a)
    solvent_peak = b[solvent_peak_index]

    # guess scale as height at peak
    solvent_scale = a[solvent_peak_index]
    c = solvent_peak_index

    # estimate width as 1/e drop in bin height
    while a[c] >= solvent_scale * 1 / np.exp(1):
        c += 1
    solvent_width = (c - solvent_peak_index) * d_domain

    # Estimate content distribution initial parameters (to be refined by fitting)
    n_sigma = 20.0
    content_width = (high - low)
    content_width /= n_sigma

    # Set the domain
    domain = np.linspace(low, high, n_lev)

    # Define the guess and optimize fit
    p_guess = [solvent_scale, solvent_peak, solvent_width]
    popt, pcov = curve_fit(onecomponent_solvent, domain, a, p0=p_guess)

    # calculate the guess and fitted model at each domain point
    guess = onecomponent_solvent(domain, p_guess[0], p_guess[1], p_guess[2])
    solvent_model = onecomponent_solvent(domain, popt[0], popt[1], popt[2])

    # clip very low values of the model
    fit = np.clip(solvent_model, tol ** 2, np.max(solvent_model))

    # calculate the fraction of solvent and content at each bin value
    content_fraction_all = np.divide((a + tol - fit), a + tol)
    solvent_fraction_all = 1 - content_fraction_all


    if plot:
        f = plt.gcf()
        ax1 = f.add_subplot(1, 1, 1)
        ax1.plot(b[:-1], a, 'k-', label='data')
        ax1.plot(domain, guess, 'b-', label='solvent guess', alpha=0.3)

        ax1.plot(domain, fit, 'g-', label='solvent fit')
        ax1.legend()
        low_lim = np.min(a[a > 0])
        ax1.set_ylim([low_lim * 0.5, solvent_scale * 1.1])
        plt.semilogy()

    # Estimate some cutoffs that might be interesting, but which we do not use at the moment
    # TODO reevaluate these search methods
    threshold_high = n_lev - 1
    while solvent_model[threshold_high] < tol ** 3 and threshold_high > 0:
        threshold_high -= 1
    if threshold_high == 0:
        plt.savefig('Incomplete.png')
        raise ValueError('high threshold limit not found, solvent fitted as larger than data domain?')

    threshold_midhigh = n_lev - 1
    while content_fraction_all[threshold_midhigh] > 0.01 and threshold_midhigh > 0:
        threshold_midhigh -= 1
    if threshold_midhigh == 0:
        raise ValueError('midhigh threshold limit not found, solvent fitted as larger than data domain?')

    threshold_midlow = 0
    while solvent_fraction_all[threshold_midlow] > 0.01 and threshold_midlow < n_lev - 1:
        threshold_midlow += 1
    if threshold_midlow == n_lev:
        raise ValueError('midlow threshold limit not found, solvent fitted as larger than data domain?')

    threshold_low = 0
    while solvent_model[threshold_low] < 1 and threshold_low < n_lev - 1:
        threshold_low += 1
    if threshold_low == n_lev:
        raise ValueError('low threshold limit not found, solvent fitted as larger than data domain?')

    solvent_range = np.array([b[threshold_low], b[threshold_midlow], b[threshold_midhigh + 1], b[threshold_high]])

    if plot:
        ax1.plot(solvent_range[3] * np.ones(2), ax1.get_ylim(), 'g:', label=f'{solvent_range[3]:.2f}: solvent edge')
        ax1.plot(solvent_range[2] * np.ones(2), ax1.get_ylim(), 'g--', label=f'{solvent_range[2]:.2f}: content 1% of solvent')

    return solvent_range, popt

def suppress(
        modified_data,
        unmodified_data,
        confidence,
        exclude_solvent=False,
        verbose=False
):
    """
    Supress modification of data outside the confidence, and re-introduce original solvent unless explicitly excluded

    :param modified_data:
    :param unmodified_data:
    :param confidence:
    :param exclude_solvent:
    :param verbose:
    :return:
    """
    if verbose:
        print('Using confidence based on solvent model to suppress modified solvent.')

    # Apply confidence to supress solvent modification
    out_data = np.multiply(modified_data, confidence)

    if exclude_solvent:
        if verbose:
            print('Not retaining input solvent.')
    else:
        if verbose:
            print('Retaining solvent from input.')

        # Add back the unmodified solvent
        out_data += np.multiply(unmodified_data, 1 - confidence)

    return out_data