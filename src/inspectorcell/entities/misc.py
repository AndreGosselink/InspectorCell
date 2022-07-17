"""Helperfunctions needed at several points in entitiy generation
"""
import numpy as np
import cv2


def get_kernel(k):
    """Simple circular kernel
    """
    if k <= 0:
        raise ValueError('kernel radius must be >= 1')
    linrange = np.linspace(-k+0.5, k-0.5, 2*k)
    x, y = np.meshgrid(linrange, linrange)
    return ((np.sqrt(x**2 + y**2) <= k)).astype(np.uint8)
