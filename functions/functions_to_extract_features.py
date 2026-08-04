###############################################################################
# functions_to_extract_features.py
#
# Shared functions for the extraction of stabilometric features.
#
# Sections
#   1. Trajectory preprocessing
#   2. Data augmentation
#   3. Machine learning
###############################################################################

from config import *
import DAML_functions as f


import numpy as np

from scipy.integrate import cumulative_trapezoid
from scipy.signal import welch, detrend


def extract_features(ap, ml, fs):
    """
    Compute stabilometric features from AP and ML acceleration trajectories.

    Parameters
    ----------
    ap : array-like
        AP acceleration.
    ml : array-like
        ML acceleration.
    fs : float
        Sampling frequency [Hz].

    Returns
    -------
    dict
        Stabilometric features.
    """
    ap = np.asarray(ap)
    ml = np.asarray(ml)
    
    # ==============================================================
    # TIME DOMAIN
    # ==============================================================

    area_cop = ellipse95(ap, ml)

    duration = len(ap) / fs

    dist = np.mean(np.sqrt((ap - np.mean(ap)) ** 2 + (ml - np.mean(ml)) ** 2))
    path = np.sum(np.sqrt(np.diff(ap) ** 2 + np.diff(ml) ** 2))
    mean_freq = path / (2 * np.pi * dist * duration)

    rms = np.sqrt(np.mean(ap ** 2 + ml ** 2))

    coeff_var_ap = np.std(ap) / np.mean(ap)
    coeff_var_ml = np.std(ml) / np.mean(ml)

    max_dev_ap = np.max(ap) - np.min(ap)
    max_dev_ml = np.max(ml) - np.min(ml)

    t = np.arange(len(ap)) / fs
    vx = cumulative_trapezoid(ap, t, initial=0)
    vy = cumulative_trapezoid(ml, t, initial=0)

    avg_vel = np.mean(np.sqrt(vx ** 2 + vy ** 2))
    
    # ==============================================================
    # FREQUENCY DOMAIN
    # ==============================================================
    resultant = np.sqrt(ap ** 2 + ml ** 2)

    window = int(4 * fs)

    f, pxx = welch(detrend(resultant), fs=fs, window="hann", nperseg=window, noverlap=window // 2, nfft=window)

    df = np.mean(np.diff(f))
    total_power = np.sum(pxx) * df
    cumulative_power = np.cumsum(pxx) * df

    median_freq = f[np.where(cumulative_power >= 0.50 * total_power)[0][0]]
    f95 = f[np.where(cumulative_power >= 0.95 * total_power)[0][0]]

    centroid_freq = np.sum(f * pxx) / np.sum(pxx)
    freq_dispersion = np.sqrt(np.sum(((f - centroid_freq) ** 2) * pxx) / np.sum(pxx)) / centroid_freq

    return {
        "area_cop": area_cop,
        "Coeff_var_AP": coeff_var_ap,
        "Coeff_var_ML": coeff_var_ml,
        "Max_dev_AP": max_dev_ap,
        "Max_dev_ML": max_dev_ml,
        "PATH": path,
        "T": duration,
        "MF": mean_freq,
        "DIST": dist,
        "RMS": rms,
        "avg_vel": avg_vel,
        "totalPower": total_power,
        "medianFreq": median_freq,
        "F95": f95,
        "centroidFreq": centroid_freq,
        "freqDispersion": freq_dispersion
    }