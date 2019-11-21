import AnyQt.QtCore as qc
import numpy as np


class Enhancer(qc.QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.adjustFrom = (0x0, 0x0ffff)
        self.adjustTo = (0x0, 0x0ff)
        self.imgDesc = (0xffff, np.uint8)

        self.auto_bins = 255
        self.auto_thresh_factor = 1e-4
        self.auto_limit_factor = 0.1

    def getScalingLUT(self):
        # lower * m - b = to_lower
        # upper * m - b = to_upper
        if self.adjustFrom == self.adjustTo:
            return None

        low0, up0 = self.adjustFrom
        low1, up1 = self.adjustTo
        maxInVal, dtype = self.imgDesc

        if (low0 - up0) == 0:
            return None

        m = (low1 - up1) / (low0 - up0)
        b0 = low0 * m - low1
        b1 = up0 * m - up1

        low0, up0 = int(low0), int(up0)
        if int(low0) >= int(up0):
            return None

        lut = np.zeros(maxInVal, dtype=dtype)
        lut[low0:up0] = np.linspace(low1, up1, up0-low0)
        lut[up0:] = up1

        return lut

#     def get_autobounds(self, img, bincount=0xfff, sat_trgt=1e-6,
#                        under_trgt=0.002):
#         if img is None:
#             return 0, 0xff
# 
#         counts, bins = np.histogram(img.ravel(), bins=bincount)
#         bins = bins[1:]
# 
#         # sat_trgt = sat_trgt * img.size
#         sat_trgt = 1
#         under_trgt = under_trgt * img.size
#         sat_px = 0
#         under_px = counts[0]
#         sat_edge = None
#         under_edge = None
# 
#         for i in range(1, len(bins)):
# 
#             if sat_px <= sat_trgt:
#                 sat_px += counts[-i]
#                 sat_edge = bins[-i]
# 
#             if under_px <= under_trgt:
#                 under_px += counts[i]
#                 under_edge = bins[i]
# 
#         if sat_edge is None:
#             sat_edge = 0xfff
# 
#         if under_edge is None:
#             under_edge = 0
# 
#         if under_edge > sat_edge:
#             under_edge = 0
# 
#         if under_edge > sat_edge:
#             sat_edge = 0xfff
#         
#         print(under_edge, sat_edge)
#         print(under_px, sat_px)
#         return under_edge, sat_edge
