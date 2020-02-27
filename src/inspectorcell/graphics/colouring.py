"""Classes and function to controll coloring in the viewer
"""
from AnyQt.QtGui import QPen, QColor, QBrush
import AnyQt.QtCore as qc


class Style():

    def __init__(self, name='', pen=None, brush=None):
        self.name = name
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        self.pen = pen
        self.brush = brush


class Styles():
    """Styles for coloring of segments. For now hardcoded.

    Style, QBrush, QPen factory and compositor
    """

    def __init__(self):
        self._styles = {}
        self.addStyle(
            key='default',
            brushes=((69, 159, 255, 100), (69, 159, 255, 100)),
            pens=((69, 159, 255, 100), (4, 255, 255, 160)),
            widths=(1, 2),
        )

    def __getitem__(self, key):
        return self._styles[key]

    def get(self, key, default):
        return self._styles.get(key, default)

    def __iter__(self):
        def iterator():
            for (inactive, active) in self._styles.values():
                yield inactive
                yield active
        return iterator()

    def addStyle(self, key, brushes, pens, widths):
        """Makes a style

        key : str
            name of style
        brushes : tuple
            tuple of two RGBA tuples for brushes
        pens : tuple
            tuple of two RGBA tuples for pens
        width : tuple
            tuple of two floats pen widths
        """
        inactiveBrush, activeBrush = brushes
        inactivePen, activePen = pens
        inactiveW, activeW = widths

        inactive, active = Style(key + '_inactive'), Style(key + '_active')
        self._styles[key] = (inactive, active)
        inactive.brush.setColor(QColor(*inactiveBrush))
        inactive.brush.setStyle(qc.Qt.SolidPattern)
        inactive.pen.setColor(QColor(*inactivePen))
        inactive.pen.setWidth(inactiveW)

        active.brush.setColor(QColor(*activeBrush))
        active.brush.setStyle(qc.Qt.SolidPattern)
        active.pen.setColor(QColor(*activePen))
        active.pen.setWidth(activeW)


class ColorManager():
    """Keeps track of ViewContext and app state to calculate colouring
    """
    def __init__(self, styleTags=None):
        #TODO keep track of ViewContextState by refrerence or so
        #TODO parse initialization config

        if styleTags is None:
            styleTags = []

        self.styleTags = styleTags
        self.setDefaults()

    def setDefaults(self):
        """Sets default pen and brush with and color
        """
        self.styles = Styles()
        self.defaults = self.styles['default']

        mapping = dict(C1=(70, 190, 250), # (Fibroblasts)
                       C2=(237, 70, 47), # (Ki-67+ tumor)
                       C3=(170, 242, 43), # (Tumor)
                       C4=(245, 174, 50), # (Endothelium)
                       C5=(255, 255, 0), # (Plasma cells)
                       C6=(255, 0, 255), # (Myeloid cells)
                       C7=(0, 255, 255), # (NKs)
                       C8=(128, 0, 255), # (CD4+ T cells)
                       C9=(0, 128, 255), # (CD25+ CD4+ T cells)
                       C10=(255, 223, 128), # (CD8+ T cells)
        )

        for key, col in mapping.items():
            self.styles.addStyle(key,
                brushes=(col, col),
                pens=(col, col),
                widths=(1, 2))
            self.styleTags.append(key)

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
            styles = self.styles.get(tag, self.defaults)
        elif entity.tags:
            styles = self.defaults
            for cur_tag in entity.tags:
                # styles = self.tagstyles.get(cur_tag, self.defaults)
                if cur_tag in self.styleTags:
                    styles = self.styles.get(cur_tag, self.defaults)
                    break
        else:
            styles = self.defaults

        entity.GFX.defaultStyle, entity.GFX.selectedStyle = styles

    @property
    def allBrushes(self):
        """Iterator for all brushes managed
        """
        for style in self.styles:
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
