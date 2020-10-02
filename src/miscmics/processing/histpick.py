""" Picking images from image stack by histogram
"""
from copy import deepcopy
from numbers import Number

import numpy as np

from ..multiplex import ImageStack


def calc_dynamic_range(ref: Number, sig: Number) -> float:
    """Calculate dynamic range in dB

    Parameter
    ---------
    ref : Number
        Reference value, lower end of the used dynamic range
    sig : Number
        Signal value, upper end of the used dynamic range

    Returns
    -------
    bits : float
        Used dynamic range in bits
    """
    # power-root
    # return 20.0 * float(np.log10(val) - np.log10(ref))
    return np.log2(sig) - np.log2(ref)


def calc_saturation(nonzeros: np.ndarray, limit: Number) -> float:
    """Calculate the percentage of saturated pixels

    Parameter
    ---------
    nonezeros : np.ndarray
        Non-zero pixel values as ndarray
    limit : Number
        Saturation limit. All pixel values above/equal to
        limit are considered saturated

    Note
    ----
    Saturated pixels are pixels with an value above the
    limit. The returned fraction is then the ratio between
    the number of saturated pixels and the number of pixels
    above the mean pixel value.
    """
    saturated = np.sum(nonzeros >= limit)
    overaverage = np.sum(nonzeros > nonzeros.mean())
    if overaverage == 0:
        return 0
    ret = saturated / overaverage

    if np.isnan(ret) or np.isinf(ret):
        raise ValueError('Can not compute saturation')

    return ret


def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.

    (stolen from:
    https://stackoverflow.com/questions/16856788/slice-2d-array-into-smaller-2d-arrays)
    """
    h, w = arr.shape
    if h % nrows != 0:
        raise ValueError(f'{h} rows is not evenly divisble by {nrows}')
    if w % ncols != 0:
        raise ValueError(f'{h} cols is not evenly divisble by {ncols}')
    return (arr.reshape(h // nrows, nrows, -1, ncols)
               .swapaxes(1, 2)
               .reshape(-1, nrows, ncols))


def field_vals(img, maxval, splits=4):
    """Calculates the dynamic range and saturation for
    """
    dyns = []
    sats = []
    if img.ndim == 3 and img.shape[-1] != 1:
        raise ValueError(f'Only one channel per channel, please got: {img.shape}')

    for block in np.array_split(img.squeeze(), splits):
        nonz = block[block > 0]
        # only evaluate actuall values
        if nonz.size >= 10:
            dyns.append(calc_dynamic_range(nonz.min(), nonz.max()))
            sats.append(calc_saturation(nonz, maxval))
    if not dyns or not sats:
        raise ValueError('Ill formed image input')
    return dyns, sats


def select_by_hist(imstack: ImageStack, groupkey: str, maxval: Number = 0xfff,
                   satlim: Number = 5e-4, annotate: bool = True) -> ImageStack:
    """Return best exposed channels in a new ImageStack

    Groups images by matching values for an meta key in the channel metadata.
    From each group the best image wrt saturation and dynamic range are
    choosen. These images are then returned in a new image stack.

    Parameter
    ---------
    imstack : ImageStack
        ImageStack, from which the image data is taken
    groupkey : str
        Key oused to group the channels by.
    maxval : Number
        Maximum value that can occure in images
    satlim : Number (default=5e-4)
        Number of pixels that can be in saturation. Parameter
        for `calc_saturation`
    annotate : bool (default=True)
        If `True` annotate all images in imstac

    Returns
    -------
    selected : ImageStack
        ImageStack with selected channels
    """
    selected = ImageStack(meta=deepcopy(imstack.meta))

    for unique_key in imstack.unique()[groupkey]:

        cands = []
        for img in imstack.find({groupkey: unique_key}, single=False):
            dyns, sats = field_vals(img, maxval)
            cands.append((img, np.mean(dyns), np.mean(sats)))
            if annotate:
                img.meta['dyns'] = np.max(dyns)
                img.meta['sats'] = np.sum(sats)

        # sort by dynamic range
        cands.sort(key=lambda i: i[1])
        # keep track of min dyn
        min_dyn = cands[0]
        # filter oversaturated
        cands = [(i, d, s) for i, d, s in cands if s < satlim]

        if cands:
            # if any left, take best dyn
            img, _, _ = cands[-1]
        else:
            # take smallest dyn ~ exposure
            img, _, _ = min_dyn

        selected.add_image(img, img.meta)

    return selected
