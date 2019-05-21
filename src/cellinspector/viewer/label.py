import pyqtgraph as pg
# import AnyQt.QtCore as qc
from AnyQt import QtGui as qg, QtCore as qc, QtWidgets as qw


class LabelElement():

    def __init__(self, text='', fgColor='#10AA00', bgColor='#000000'):
        
        self.html = None

        self.fgColor = fgColor
        self.bgColor = bgColor
        self.text = text
        
        self._style = """background-color:{bg:};color:{fg:}"""
        self._html = """<span style="{style:}">{txt:}</span>"""
        
        self.update()

    def update(self):
        style = self._style.format(bg=self.bgColor,
                                   fg=self.fgColor)
        self.html = self._html.format(style=style, txt=self.text)

    def __str__(self):
        return self.html

    # @property
    # def fgColor(self, fgColor='#10AA00'):
    #     self._fgColor = fgColor

    # @property
    # def bgColor(self, bgColor='#000000'):
    #     self._bgColor = bgColor

    # @property
    # def text(self, text=''):
    #     self._text = text

class ChannelLabel(qw.QGraphicsTextItem):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.elements = [LabelElement() for i in range(3)]
        # self.options = qw.QStyleOptionGraphicsItem
        # self.options = qw.QStyleOptionGraphicsItem.SO_GraphicsItem

        self._html = """<body><b>{:}</b> <em>{:}</em> <em>{:}</em></body>"""

    def update(self):
        strings = (str(em) for em in self.elements)
        html = self._html.format(*strings)
        self.setHtml(html)

    def set(self, index, fgColor=None, bgColor=None, text=None):
        element = self.elements[index]
        if not fgColor is None:
            element.fgColor = fgColor

        if not bgColor is None:
            element.bgColor = bgColor

        if not text is None:
            element.text = text

        element.update()
        self.update()
