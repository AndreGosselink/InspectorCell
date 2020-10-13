"""Normalizing channels in an imagestack
"""
import copy
from typing import Any

import numpy as np
from scipy.special import expit

from ..multiplex.multiplex import ImageStack


def mode_value(hist: np.ndarray, bins: np.ndarray) -> float:
    """Find mode in histogram of array
    """
    mode_idx = np.argmax(hist == hist.max())
    mode_bin_cent = ((bins[1:] + bins[:-1]) / 2)[mode_idx]
    return float(mode_bin_cent)


def normalize_channel(channel: np.ndarray, transform: str = 'log2',
                      center: str = 'mode', scale: str = 'std',
                      bincount: int = 100, squeeze: str = None):
    """Normalize imagestack by centralizing and scaling and transform

    Parameter
    ---------
    channel: np.ndarray
        raw data to preprocess in channel
    transform: str (default='log2')
        log transform. if -1 no log transform, else base 2
    center: str (default='mode')
        Definiton of center for centering after transform
    scale: str (default='std')
        Scaling of the data after centering
    squeeze : Union[str, callable]
        Squeezing function after scaling
    """

    # to bits
    if transform == 'log2':
        pixels = np.log2(channel.ravel() + 1)
    elif transform == 'log10':
        pixels = np.log10(channel.ravel() + 1)
    elif transform is None:
        pixels = channel.ravel()

    hist, bins = np.histogram(pixels, bins=bincount)

     # centering
    if center == 'mode':
        pixels = pixels - mode_value(hist, bins)
    else:
        try:
            pixels = center(pixels)
        except TypeError:
            pass

    # scaling
    if scale == 'std':
        pixels = pixels / pixels.std()
    elif scale == '2std':
        pixels = pixels / (2 * pixels.std())
    elif scale == 'max':
        pixels = pixels / pixels.max()
    else:
        try:
            pixels = scale(pixels)
        except TypeError:
            pass

    # squeezing
    if squeeze == 'tanh':
        pixels = np.tanh(pixels)
    elif squeeze == 'sigmoid':
        pixels = expit(pixels)
    else:
        try:
            pixels = squeeze(pixels)
        except TypeError:
            pass

    return pixels.reshape(channel.shape)


def normalize_stack(image_stack: ImageStack, **kwargs):
    """Channelwise normalization

    Parameters
    ----------
    image_stack: ImageStack
        ImageStack instance to normalize
    **kwargs: Dict[str, Any]
        Parameter passed to `miscmics.processing.normalize_channel`
    """
    normalized = ImageStack()
    normalized.meta = copy.deepcopy(image_stack)

    for chan in normalized.data:
        kwargs['channel'] = chan
        norm_chan = normalize_channel(**kwargs)
        normalized.add_image(norm_chan, norm_chan.meta)

    return normalized
