# -*- coding: utf-8 -*-
import numpy as np

import AnyQt.QtCore as qc
import AnyQt.QtGui as qg
import AnyQt.QtWidgets as qw

import pyqtgraph as pg

from templates import get_viewbox_label_html


class GridViewBoxLabel(pg.TextItem):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.cur_text = {'fg': None, 'bg': None, 'misc': None}

    def set_label_text(self, bg_txt=None, fg_txt=None, misc=None,
                       bgcolor='#000000', fgcolor='#10AA00'):

        for new, key in zip((bg_txt, fg_txt, misc), ('bg', 'fg', 'misc')):
            cur = self.cur_text[key]
            if not new is None:
                self.cur_text[key] = new

        bg_txt, fg_txt = self.cur_text['bg'], self.cur_text['fg']
        misc_txt = self.cur_text['misc']
        html_text = get_viewbox_label_html(bg_txt, fg_txt, misc,
                                           bgcolor, fgcolor)
        self.setHtml(html_text)


class GridViewBox(pg.ViewBox):

    def __init__(self, parent=None):
        """ Class implementing the drawing handling
        """
        super().__init__(invertY=True, parent=parent, lockAspect=True)

        self.disableAutoRange()

        self.paning_btn = qc.Qt.RightButton
        self.draw_btn = qc.Qt.LeftButton
        self.context_btn = qc.Qt.RightButton

        #TODO just a general description, what it shows like names
        #TODO as objects are real objects now, they will handel events themselve
        #TODO as objects are real objects now, they will handel events themselve

        # image label
        self.imagelabel = GridViewBoxLabel()
        self.addItem(self.imagelabel)
        self.imagelabel.setZValue(10)

    def set_label(self, bg=None, fg=None, bgcolor='#000000',
                  fgcolor='#10AA00'):
        """Sets the label
        """
        self.imagelabel.set_label_text(bg, fg, bgcolor=bgcolor, fgcolor=fgcolor)

    def setRange(self, *args, **kwargs):
        super().setRange(*args, **kwargs)
        (new_x, _), (new_y, _) = self.state['viewRange']
        self.imagelabel.setPos(new_x, new_y)

    def mouseDragEvent(self, event):
        # paning and scaling, pass the drawing button
        if event.button() & self.paning_btn:
            self._pan_view(event)
            event.accept()

    def _pan_view(self, ev):
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        ## Ignore axes if mouse is disabled
        mask = np.array([1.0, 1.0], dtype=float)

        # paning
        if self.state['mouseMode'] == pg.ViewBox.RectMode:
            # This is the final move in the drag; changethe view scale now
            if ev.isFinish():
                # print "finish"
                self.rbScaleBox.hide()
                p0, p1 = pg.Point(ev.buttonDownPos(ev.button())), pg.Point(pos)
                ax = qc.QRectF(p0, p1)
                ax = self.childGroup.mapRectFromParent(ax)
                self.showAxRect(ax)
                self.axHistoryPointer += 1
                self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
            else:
                ## update shape of scale box
                self.updateScaleBox(ev.buttonDownPos(), ev.pos())
        else:
            tr = dif * mask
            tr = self.mapToView(tr) - self.mapToView(pg.Point(0,0))
            x = tr.x() if mask[0] == 1 else None
            y = tr.y() if mask[1] == 1 else None

            self._resetTarget()
            if x is not None or y is not None:
                self.translateBy(x=x, y=y)
            self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
