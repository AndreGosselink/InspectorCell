"""Images used
"""
# built-ins
import random

# extern
import numpy as np

# GUI Stuff
import pyqtgraph as pg
from AnyQt import QtGui as qg, QtCore as qc


class OrientedImage(pg.ImageItem):

    def setImage(self, image=None, *args, **kwargs):
        # if not image is None:
        #     image = get_flipped(image)
        return super().setImage(image, *args, **kwargs)


class BackgroundImage(OrientedImage):

    def __init__(self, *args, **kwargs):
        super().__init__(
            parent=None, levels=np.array([0, 0xffff], np.uint16),
            autoLevels=False, autoDownsample=False)

        self.isRendered = False
        self.prevRender = None
        self.staticqimg = None
        self._bgpos = (0, 0)

    def setBGPos(self, x, y):
        self._bgpos = (x, y)

    def setImage(self, *args, **kwargs):
        """Monkeypatches setImages to set the
        is_rendered flag
        """
        self.is_rendered = False
        self.prevRender = None
        self.staticqimg = None
        return super().setImage(*args, **kwargs)

    def render(self, *args, **kwargs):
        """Monkeypatching the renderer. Keep the previous QImage
        and prevent re-rendering.
        """
        if not self.is_rendered:
            try:
                del self.prevRender
                self.prevRender = None
                super().render(*args, **kwargs)
            except MemoryError as err:
                return self.staticqimg
            #TODO maybe unessecary
            self.staticqimg = self.qimage
            if not self.staticqimg is None:
                self.isRendered = True
        else:
            self.qimage = self.staticqimg
            self.qimage.setPos(*self._bgpos)

    def paint(self, p, *args):
        if self.image is None:
            return
        if self.qimage is None:
            self.render()
            if self.qimage is None:
                return
        if self.paintMode is not None:
            p.setCompositionMode(self.paintMode)

        shape = self.image.shape[:2] if self.axisOrder == 'col-major' else self.image.shape[:2][::-1]
        coords = self._bgpos + (shape[0] + self._bgpos[0], shape[1] + self._bgpos[1])
        p.drawImage(qc.QRectF(*coords), self.qimage)
        if self.border is not None:
            p.setPen(self.border)
            p.drawRect(self.boundingRect())
