"""Contains graphic Elements for used by the viewer
"""

#TODO move labels here as well

from AnyQt.QtGui import QPen
from AnyQt import QtCore as qc
from AnyQt.QtWidgets import QGraphicsItem

import pyqtgraph as pg
import pyqtgraph.functions as fn

from ..viewer.label import InfoBoxContent


class InfoBox(pg.GraphicsObject):
    """Infobox shown in the channel view
    """

    def __init__(self, *args, parent=None, **kwargs):
        # self._parent = kwargs.get('parent', None)
        super().__init__(*args, **kwargs)

        self.view = None

        self.setFlag(QGraphicsItem.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)

        self._content = None
        self._canvas = None
        self._bgbrush = None
        self.width = None
        self.height = None

        # reference to which the infocpx belongs to
        self.ref = None

        self.setProperties()

    def setProperties(self, bgcolor=(255, 0, 40, 125), width=30, height=30):
        """set the properties of the infobox
        """
        self._canvas = qc.QRectF(0, 0, width, height)
        self._bgbrush = fn.mkBrush(*bgcolor)

        self._content = InfoBoxContent(parent=self)
        self._content.set(0, text='ObjectId')
        self._content.set(1, text='TAGs')
        self._content.set(2, text='SCALARs')

    def setPos(self, pos):
        super().setPos(qc.QPointF(pos))
        self._canvas.moveTo(self.pos())
        self._content.setPos(self.pos())

    def getXPos(self):
        return self.pos[0]

    def getYPos(self):
        return self.pos[1]

    def getPos(self):
        return self.pos

    def boundingRect(self):
        return self._canvas

    def paint(self, painter, rect):
        painter.setBrush(self._bgbrush)
        painter.drawRect(self._canvas)
        self._content.paint(painter, rect, target=None)

    def setValues(self, eid=None, tags=None, scalars=None, chanName=None):
        #TODO some formatting
        if not eid is None:
            self._content.set(0, text='ObjID: {}'.format(eid))
        if not tags is None:
            tagString = ', '.join(aTag for aTag in tags)
            self._content.set(1, text='Tags: {}'.format(tagString))
        if not chanName is None and not scalars is None:
            # for key in scalars.keys():
            #     scalarName = 
            scalarFmt = """Scalar:<br />{}"""
            scalarLines = ''
            for scalarName, value in scalars.items():
                scalarLines += '<em>{}</em>: {}<br />'.format(
                    scalarName[:12], value)
            scalarString = scalarFmt.format(scalarLines)
            self._content.set(2, text=scalarString)
