__all__ = ['gabor', 'GaborExtractor']

import numpy as np
import itertools as it

from ._feature_extractor import FeatureExtractorBase

_log2 = np.log(2)
_log2_sq = _log2 * _log2
sqrt_log2 = np.sqrt(_log2)
_2pi = 2 * np.pi

def gabor_kernel(p, q, L, sx, sy, u0, alpha, M):
    sx2 = sx * sx
    sy2 = sy * sy
    c = ( M + 1) / 2
    ap = alpha ** (-p)
    tq = np.pi * q / L
    cos_tq = np.cos(tq)
    sin_tq = np.sin(tq)
    f_exp = 2 * np.pi * 1j * u0

    X = ap * np.repeat(np.arange(M) - c, M).reshape(M, M)
    Y = X.T
    
    _X = X * cos_tq + Y * sin_tq
    _Y = Y * cos_tq - X * sin_tq
    
    f = np.exp(-.5 * (_X * _X / sx2 + _Y * _Y / sy2)) * np.exp(f_exp * _X)
    return f * ap / (2 * np.pi * sx * sy)

def gabor(image, region=None, *, rotations=8, dilations=8, freq_h=2, freq_l=.1, mask=21, show=False, labels=False):
    '''\
    gabor(image, region=None, *, rotations=8, dilations=8, freq_h=2, freq_l=.1, mask=21, show=False, labels=False)

    (TODO)

    Parameters
    ----------

    Returns
    -------

    See Also
    --------
    
    Examples
    --------
    '''

    if mask % 2 == 0:
        raise ValueError("`mask` value must be an odd positive integer, not '{mask}'")
    
    if region is None:
        region = np.ones_like(image)

    if show:
        print('--- extracting Gabor features...')
        
    alpha = (freq_h / freq_l) ** (1 / (dilations - 1))
    sx = sqrt_log2 * (alpha + 1) / (2 * np.pi * freq_h * (alpha-1))
    sy = sqrt_log2 - (2*_log2 / (_2pi * sx * freq_h))**2 /\
                     (_2pi * np.tan(np.pi / (2 * rotations)) *\
                      (freq_h - 2 * np.log( 1/4/np.pi**2/sx**2/freq_h)))
    u0 = freq_h
    
    k = np.where(region.astype(bool))
    N, M = image.shape
    
    g = np.zeros((dilations, rotations))
    size_out = image.shape + np.repeat(mask, 2) - 1
    Iw = np.fft.fft2(image, size_out)
    n1 = (mask + 1) // 2
    
    for p, q in it.product(range(dilations), range(rotations)):
        f = gabor_kernel(p, q, rotations, sx, sy, u0, alpha, mask)
        Ir = np.real(np.fft.ifft2(Iw * np.fft.fft2(np.real(f), size_out)))
        Ii = np.real(np.fft.ifft2(Iw * np.fft.fft2(np.imag(f), size_out)))
        Ir = Ir[n1:n1+N, n1:n1+M]
        Ii = Ii[n1:n1+N, n1:n1+M]
        Iout = np.sqrt(Ir*Ir + Ii*Ii)
        g[p, q] = Iout[k].mean()
    
    gmax = g.max()
    gmin = g.min()
    J = (gmax - gmin) / gmin
    features = np.hstack([g.ravel(), gmax, gmin, J])

    if labels:
        gabor_labels = np.hstack([
            [f'Gabor({p},{q})' for p, q in it.product(range(dilations), range(rotations))],
            ['Gabor-max', 'Gabor-min', 'Gabor-J']
        ])
        
        return gabor_labels, features
    
    return features

class GaborExtractor(FeatureExtractorBase):
    extractor_func = gabor