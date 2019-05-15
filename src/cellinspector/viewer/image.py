"""silly cirles to play around with and other util stuff
"""

import random

import pyqtgraph as pg
from AnyQt import QtGui as qg, QtCore as qc

import numpy as np


class OrientedImage(pg.ImageItem):

    def setImage(self, image=None, *args, **kwargs):
        if not image is None:
            image = get_flipped(image)
        return super().setImage(image, *args, **kwargs)


class BackgroundImage(OrientedImage):

    def __init__(self, *args, **kwargs):
        super().__init__(
            parent=None, levels=np.array([0, 0xffff], np.uint16),
            autoLevels=False, autoDownsample=False)

        self.is_rendered = False
        self.prev_render = None
        self.staticqimg = None
        self.cur_view = None

    def setImage(self, *args, **kwargs):
        """Monkeypatches setImages to set the
        is_rendered flag
        """
        self.is_rendered = False
        self.prev_render = None
        self.staticqimg = None
        self.cur_view = None
        return super().setImage(*args, **kwargs)

    def render(self, *args, **kwargs):
        """Monkeypatching the renderer. Keep the previous QImage
        and prevent re-rendering.
        """
        if not self.is_rendered:
            try:
                del self.prev_render
                self.prev_render = None
                super().render(*args, **kwargs)
            except MemoryError as err:
                return self.staticqimg
            #TODO maybe unessecary
            self.staticqimg = self.qimage
            if not self.staticqimg is None:
                self.is_rendered = True
        else:
            self.qimage = self.staticqimg


def get_flipped(image):
    return np.flipud(np.rot90(image))
