import numpy as np
import pylab as plt
from scipy.optimize import curve_fit


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
    assert components == 1 or components == 2
    tol = 0.001 #TODO make input?
    const_gauss = np.sqrt(2 * np.pi)

    vol = np.size(data)
    low = np.min(data)
    high = np.max(data)

    # Estimate solvent distribution initial parameters (to be refined by fitting)
    a, b = np.histogram(data, bins=n_lev, density=True)
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
        f = plt.gcf()
        ax1 = f.add_subplot(1, 1, 1)
        ax1.plot(b[:-1], a, 'k-', label='data')
        ax1.plot(domain, guess, 'b-', label='solvent guess', alpha=0.3)

        ax1.plot(domain, fit, 'g-', label='solvent fit')
        ax1.legend()
        low_lim = np.min(a[a > 0])
        ax1.set_ylim([low_lim * 0.5, solvent_scale * 1.1])
        plt.semilogy()

    solvent_vol = np.sum(solvent_model)
    solvent_fraction = solvent_vol / vol
    content_fraction = 1 - solvent_fraction

    solvent_model_peak_index = np.argmax(solvent_model)

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
    solvent_range = np.array([b[threshold_low], b[threshold_midlow], b[threshold_midhigh + 1], b[threshold_high]])

    if plot:
        # ax1.plot(solvent_range[0] * np.ones(2), ax1.get_ylim(), 'g--', label='solvent edge')
        ax1.plot(solvent_range[3] * np.ones(2), ax1.get_ylim(), 'g:', label=f'{solvent_range[3]:.2f}: solvent edge')
        ax1.plot(solvent_range[2] * np.ones(2), ax1.get_ylim(), 'g--', label=f'{solvent_range[2]:.2f}: content 1% of solvent')
        # ax1.plot(solvent_range[3] * np.ones(2), ax1.get_ylim(), 'g--', label='ugh')

    return solvent_range, popt
