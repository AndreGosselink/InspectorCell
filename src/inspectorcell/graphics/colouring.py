"""Classes and function to controll coloring in the viewer
"""
from AnyQt.QtGui import QPen, QColor, QBrush
import AnyQt.QtCore as qc


class Style():

    def __init__(self, pen=None, brush=None):
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        self.pen = pen
        self.brush = brush


class ColorManager():
    """Keeps track of ViewContext and app state to calculate colouring
    """
    def __init__(self, taglist=None):
        #TODO keep track of ViewContextState by refrerence or so
        #TODO parse initialization config

        if taglist is None:
            taglist = []

        self.taglist = taglist

        self.setDefaults()

    def setDefaults(self):
        """Sets default pen and brush with and color
        """
        # initial color for all segments
        self.defaultStyle = Style()
        self.defaultStyle.brush.setColor(QColor(69, 159, 255, 100))
        self.defaultStyle.brush.setStyle(qc.Qt.SolidPattern)
        self.defaultStyle.pen.setColor(QColor(69, 159, 255, 100))
        self.defaultStyle.pen.setWidth(1)

        self.selectedStyle = Style()
        self.selectedStyle.brush.setColor(QColor(69, 159, 255, 100))
        self.selectedStyle.brush.setStyle(qc.Qt.SolidPattern)
        self.selectedStyle.pen.setColor(QColor(4, 255, 255, 160))
        self.selectedStyle.pen.setWidth(2)

        self.redDefaultStyle = Style()
        self.redDefaultStyle.brush.setColor(QColor(255, 159, 69, 100))
        self.redDefaultStyle.brush.setStyle(qc.Qt.SolidPattern)
        self.redDefaultStyle.pen.setColor(QColor(255, 255, 4, 160))
        self.redDefaultStyle.pen.setWidth(2)

        self.redSelectedStyle = Style()
        self.redSelectedStyle.brush.setColor(QColor(255, 159, 69, 100))
        self.redSelectedStyle.brush.setStyle(qc.Qt.SolidPattern)
        self.redSelectedStyle.pen.setColor(QColor(255, 255, 4, 160))
        self.redSelectedStyle.pen.setWidth(2)

        self.defaults = self.defaultStyle, self.selectedStyle
        reds = self.redDefaultStyle, self.redSelectedStyle

        self.tagstyles = {
            'RED': reds,
        }

    def setColor(self, entity, tag=None):
        """Calculate Polygon color for Entity

        Takes into account the Entity properties and states
        of the ViewContext, the ColorManager tracks, to calculate
        the color for the Entity polygon. Inspects Entity and
        ViewContext to come to an conclusion

        Parameters
        ----------
        entity : Entity
            Entity instance for which the colour should be changed

        tag : str
            tag used to decide for highlighting and color selection.
            If `None`, all tags in entity are tested
        """
        if not tag is None:
            styles = self.tagstyles.get(tag, self.defaults)
        elif entity.tags:
            for cur_tag in entity.tags:
                styles = self.tagstyles.get(cur_tag, self.defaults)
                if not styles is self.defaults:
                    break
        else:
            styles = self.defaults

        entity.GFX.defaultStyle, entity.GFX.selectedStyle = styles

    @property
    def allBrushes(self):
        """Iterator for all brushes managed
        """
        for style in (self.defaultStyle, self.selectedStyle):
            yield style.brush

    def changeOpacity(self, alpha):
        """Changes the opacity of all brushes

        Parameters
        ----------
        alpha : float
            Alphavalue used to set for each brush
        """
        for brush in self.allBrushes:
            color = brush.color()
            color.setAlpha(alpha)
            brush.setColor(color)
