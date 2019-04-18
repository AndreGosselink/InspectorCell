import PyQt5.QtCore as qc
import numpy as np


class Enhancer(qc.QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.adjust_from = (0x0, 0x0ffff)
        self.adjust_to = (0x0, 0x0ff)
        self.img_desc = (0xffff, np.uint8)

        self.auto_bins = 255
        self.auto_thresh_factor = 1e-4
        self.auto_limit_factor = 0.1

    def get_scaling_lut(self):
        # lower * m - b = to_lower
        # upper * m - b = to_upper
        if self.adjust_from == self.adjust_to:
            return None

        low0, up0 = self.adjust_from
        low1, up1 = self.adjust_to
        max_in_val, dtype = self.img_desc

        if (low0 - up0) == 0:
            return None

        m = (low1 - up1) / (low0 - up0)
        b0 = low0 * m - low1
        b1 = up0 * m - up1

        low0, up0 = int(low0), int(up0)
        if int(low0) >= int(up0):
            return None

        lut = np.zeros(max_in_val, dtype=dtype)
        lut[low0:up0] = np.linspace(low1, up1, up0-low0)
        lut[up0:] = up1

        return lut

    def get_autobounds(self, img):
        if img is None:
            return 0, 1
        limit = img.size * self.auto_limit_factor
        threshold = img.size * self.auto_thresh_factor
        hist, bins = np.histogram(img.flatten(), self.auto_bins)

        hmin = hist.size
        hmax = 0
        for i, count in enumerate(hist):
            if count > limit:
                count = 0
            if count > threshold:
                hmin = i
                break

        for i, count in enumerate(hist[::-1], 1):
            if count > limit:
                count = 0
            if count > threshold:
                hmax = hist.size - i
                break

        return bins[int(hmin)], bins[int(hmax)]
