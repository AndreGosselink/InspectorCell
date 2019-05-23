"""Implements contour class with all conversions
"""
import numpy as np


class ContourFormat():

    def __init__(self):
        self.value = None

    def get(self):
        return self.value


class StringFormat(ContourFormat):

    __doc__ = 'Contour as string format. Only has one path!'

    def fromContour(self, contour):
        point_strings = []
        for point in contour[0]:
            point = '{:.1f},{:.1f}'.format(*point.astype(float))
            point_strings.append(point)
        self.value = ' '.join(point_strings)

        return self.value

    def toContour(self, str_contour):
        if str_contour is None:
            self.value = None
            return None

        if not isinstance(str_contour, str):
            raise TypeError('Can only convert string to contour!')

        self.value = str_contour

        path = []
        for pt_string in str_contour.split(' '):
            pt_float = list(float(p) for p in pt_string.split(','))
            path.append(pt_float)

        return [np.array(path, float)]

 
class EntityContour():

    def __init__(self):
        #TODO add polygons and paths(?)
        # contours is a list of contour paths ndarrays. each ndarray is of
        # the shape (n, 2), where n is the number of points in a path
        # and each point consists of two component
        # contours is the central knowledg base. if any other property
        # is set, the contour must be set afterwards as well
        self._contour = None

        self._formats = {'string': StringFormat()}

    def __getattribute__(self, key):
        formats = super().__getattribute__('_formats')
        if not key in formats:
            return super().__getattribute__(key)

        fmt = self._formats[key]
        return fmt.get()

    def __setattr__(self, key, value):
        formats = getattr(self, '_formats', None)
        if formats is None or not key in formats:
            return super().__setattr__(key, value)
        
        # set all formats but the current one to None
        fmt = self._formats[key]
        newContour = fmt.toContour(value)
        for otherFmt in self._formats.values():
            if not fmt is otherFmt:
                otherFmt.fromContour(newContour)
        
        self._contour = newContour
    
    @property
    def contour(self):
        return self._contour

    @contour.setter
    def contour(self, value):
        """Generates all the other format values for contour
        """
        for fmt in self._formats.values():
            fmt.fromContour(value)
        self._contour = value
