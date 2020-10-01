# -*- coding: utf-8 -*-
"""Implements the main viewer element, to be used as a widget
generates views and manges them. implements interface to add and remove entities
and including background images.
"""

# built-ins
import warnings
from pathlib import Path
import os

# extern
import numpy as np

# GUI stuff
from AnyQt import QtCore as qc, QtWidgets as qw, QtGui as qg

# project
from ..graphics.scene import ViewContextScene
from ..graphics import InfoBox, CrossHair, HighlightFrame, ColorManager
from ..util import Enhancer, ViewContextManager
from ..util.image import getFlippedImagedata

from ..event import (ScalarAssignmentChanged, ActiveEntity, ResetZoomEvent,
                     ZoomEvent, EntityChangedEvent)
from .context import ContextMenu
from .dialog import ViewSetupDialog, TagEditDialog, EnhanceHistDialog
from .channel import Channel


class ViewContext(qw.QWidget):
    """Holds and generates the views, all manipulation of views and thus
    the view state over this class
    """

    ## mouse modes
    PanMode = 3
    RectMode = 1
    DrawMode = 4

    newDrawMode = qc.pyqtSignal(str)

    def __init__(self, parent=None, dataManager=None, entityManager=None):

        super().__init__(parent=parent)

        self.setMouseTracking(True)

        self.modeMap = {qc.Qt.Key_E: 'E',
                        qc.Qt.Key_D: 'D',
                        qc.Qt.Key_N: 'N'}

        # # build ui part
        # #TODO find proper parent
        # self.widget = qw.QWidget()

        self._colorManager = ColorManager()

        self.gridLayout = qw.QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.gridLayout)

        # Channel, Scene
        self.channels = {}
        self.entity_scn = ViewContextScene(parent=self)
        self.entity_scn.entityManager = entityManager
        self.empty_scn = ViewContextScene(isDisabled=True, parent=self)
        self._activeChannel = None
        self._clickedChannel = None
        self._lastActiveEntity = None
        self._lastClickedEntity = None

        # Context menu
        self.contextMenu = ContextMenu()
        self.contextBtn = qc.Qt.RightButton

        # Mouse mode by default
        self.mouseMode = ViewContext.PanMode
        self._zoom = 250

        self.contextStoreKeys = (
            qc.Qt.Key_1, qc.Qt.Key_2, qc.Qt.Key_3, qc.Qt.Key_4)

        # the infobox for readouts
        self._infoBox = InfoBox(parent=self)
        #TODO remove me if infobox works fine
        # as then it seems no explicit adding is needed
        # self._infoBox._content.setVisible(True)
        # self.entity_scn.addItem(self._infoBox._content)

        # corshair, syncing the views
        self._crossHair = CrossHair(parent=self)

        # highlighting frame
        self._highlightFrame = HighlightFrame(parent=self)

        # register calls to function to save viewstate
        # later on
        # self.state = CallTracker()

        self.enhancer = Enhancer()

        #TODO better names for keys
        self.viewSetup = ViewContextManager()
        self.viewSession = Path(os.getcwd(), 'session.json')

        self._dataManager = dataManager
        self.imageRepository = {'background': {'None': None}}

        # the dialogs
        self.dialogs = {}
        self.addDialogs()

        self._connect()

        #Initialize state
        self.setDrawMode('N')

    def setDataManager(self, dataManagerRef):
        self._dataManager = dataManagerRef

    def addDialogs(self):
        """populates Controller.dialogs
        viewer and entityManager must be already set!
        """
        ### Layout
        viewSetupDialog = ViewSetupDialog(
            parent=self,
            viewSetup=self.viewSetup,
            callback=self.updateLayout)

        ### TAGS
        if self._dataManager is None:
            currentTags = set()
        else:
            currentTags = self._dataManager.tags

        tagEditDialog = TagEditDialog(
            parent=self,
            currentTags=currentTags,
            callback=self.setTagSelection)

        ### Enhancments
        enhanceHistDialog = EnhanceHistDialog(
            parent=self,
            callback=self.enhanceContrastClicked)

        self.dialogs = {
            'viewSetup': viewSetupDialog,
            'tagEdit': tagEditDialog,
            'enhanceHist': enhanceHistDialog}

    def enhanceContrastClicked(self, minVal, maxVal):
        """convenience wrapper that calles enhanceContrast
        for last clicked channel
        """
        index = self._clickedChannel.channelIndex
        bgName = self.viewSetup['backgrounds'].get(index, 'None')
        self.enhanceImageContrast(minVal, maxVal, bgName)

    def enhanceImageContrast(self, minVal, maxVal, bgName, update=True):
        self.viewSetup['enhancments'][bgName] = (minVal, maxVal)
        for index, showsBG in self.viewSetup['backgrounds'].items():
            if showsBG != bgName:
                continue
            self.enhanceChannelContrast(minVal, maxVal, index, update)

    def enhanceChannelContrast(self, minVal, maxVal, index, update=True):
        self.enhancer.adjustFrom = (minVal, maxVal)
        lut = self.enhancer.getScalingLUT()
        chan = self.channels[index]
        chan.background.setLookupTable(lut, update=update)
        if update:
            chan.updateBackground()

    def showViewSetupDialog(self):
        """shows the ViewSetup dialog and updated view after it is accepted
        or closed. syncs the view and dialog values
        """
        diag = self.dialogs['viewSetup']
        diag.viewSetup.update(self.viewSetup)
        diag.updateGui()
        diag.show()

    def showTagEditDialog(self):
        """shows the tag edit dialog and updated view after it is accepted
        or closed. syncs the view and dialog values
        """
        diag = self.dialogs['tagEdit']
        diag.updateGui()
        diag.show()

    def showEnhanceDialog(self):
        """shows the ViewSetup dialog and updated view after it is accepted
        or closed. syncs the view and dialog values
        """
        self._updateEnhanceDialog()
        self.dialogs['enhanceHist'].show()

    def _updateEnhanceDialog(self):
        idx = self._clickedChannel.channelIndex
        bgname = self.viewSetup['backgrounds'].get(idx, 'None')
        enh = self.viewSetup['enhancments']
        minVal, maxVal = enh.setdefault(bgname, (0, 0xffff))
        diag = self.dialogs['enhanceHist']
        diag.updateGui(minVal, maxVal, bgname)

    def _connect(self):
        """connects
        """
        # proxy signal through
        self.contextMenu.sigSelected.connect(
            self._processSelection)
        self.contextMenu.sigShowItems.connect(
            self.changeItemVisibility)
        self.contextMenu.sigEnhanceSelected.connect(
            self.showEnhanceDialog)

    def resetZoom(self, autorange=False):
        """
        Resets all channels in viewer to initial zoom/scale settings
        """
        for curChan in self.channels.values():
            resetZoom = ResetZoomEvent(autorange)
            qc.QCoreApplication.postEvent(curChan, resetZoom)
            break

    def zoomOut(self):
        for curChan in self.channels.values():
            zoom_out = ZoomEvent(zoomIn=False)
            qc.QCoreApplication.postEvent(curChan, zoom_out)
            break

    def zoomIn(self):
        for curChan in self.channels.values():
            zoom_in = ZoomEvent(zoomIn=True)
            qc.QCoreApplication.postEvent(curChan, zoom_in)
            break

    def setGridlayout(self, rows, cols):
        """Modify grid layout directly
        """
        self.viewSetup['cols'] = cols
        self.viewSetup['rows'] = rows
        self.updateLayout()

    def updateLayout(self, newViewSetup=None):
        """view layout, crosshair and other from
        self.viewSetup. also checks all shared resources
        should handel alle layout options
        """
        if not newViewSetup is None:
            for key in ('rows', 'cols', 'cross'):
                self.viewSetup[key] = newViewSetup[key]

        self._spawn_views(cols=self.viewSetup['cols'],
                          rows=self.viewSetup['rows'])

        if self.viewSetup['cross']:
            crh = self._crossHair
        else:
            crh = None

        for chan in self.channels.values():
            chan._crossHair = crh

    def _restoreViewSetup(self):
        """Restores view as defined by viewSetup
        """
        #TODO ultimatively only make changes to view
        # setup upon events. then call this func, check
        # for diff and act acordingly
        # IS: change -> tracked by viewSetup
        # OUGHT: viewSetup changes -> propageted to components
        # maybe even synced flag <- only during actual change
        # reloading the global layout
        self.updateLayout()
        self.setGlobalOpacity(self.viewSetup['globalAlpha'])
        
        restoredBackgrounds = set([])
        for row in range(self.viewSetup['rows']):
            for col in range(self.viewSetup['cols']):
                curIndex = row, col
                showEnt = self.viewSetup['foregrounds'].get(curIndex, False)
                bgName = self.viewSetup['backgrounds'].get(curIndex, 'None')
                self.show_entities(showEnt, curIndex)
                self.loadImage(curIndex, bgName)
                restoredBackgrounds.add(bgName)

        for bgName in restoredBackgrounds:
            bgEnh = self.viewSetup['enhancments'].setdefault(
                    bgName, (0, 0xffff))
            self.enhanceImageContrast(*bgEnh, bgName, update=True)

    def setBackgroundSelection(self, imageSelection):
        """view layout, crosshair and other from
        self.viewSetup
        """
        rep = self.imageRepository['background'] = dict(imageSelection)
        rep['None'] = None
        self.contextMenu.updateSelection(rep.keys(), 'channelBg')

    def addEntity(self, entity):
        if not entity.GFX is None:
            self._colorManager.setColor(entity)
            self.entity_scn.addGFX(entity.GFX)

    def setTagSelection(self):
        tags = self._dataManager.tags
        self.contextMenu.updateSelection(tags, 'tags')
        self._colorManager.taglist = list(tags)
        self._colorManager.taglist.sort()

    def _spawn_views(self, rows, cols):
        """ generates row * cols viewboxes with label, background and
        foreground/overlay images
        """
        #TODO improve me by ierating only once
        for chan in self.channels.values():
            self.gridLayout.removeWidget(chan)
            chan.setVisible(False)

        # will be always there
        refChan = self.channels.get((0, 0), None)
        if not refChan is None:
            matrix = refChan.transform()
        else:
            matrix = qg.QTransform()
        for row in range(rows):
            for col in range(cols):
                curIndex = row, col
                curChan = self.channels.get(curIndex, None)
                if curChan is None:
                    #TODO find proper parent
                    curChan = Channel(self, useOpenGL=False)
                    curChan.sigDeviceRangeChanged.connect(self.syncRanges)
                    curChan.setScene(self.empty_scn)
                    curChan.channelIndex = curIndex
                    curChan.background.setBGPos(-0.5, -0.5)

                self.channels[curIndex] = curChan
                curChan.setVisible(True)
                curChan.setTransform(matrix)
                curChan._crossHair = self._crossHair
                curChan.update()
                self.gridLayout.addWidget(curChan, row, col)

        self.gridLayout.update()

    @qc.pyqtSlot(object, object)
    def syncRanges(self, src_chan, new_range):
        """ Syncronizes the individual views
        """
        for curChan in self.channels.values():
            curChan.blockSignals(True)

        for curChan in self.channels.values():
            if not curChan is src_chan:
                curChan.setRange(new_range, padding=0)

        for curChan in self.channels.values():
            curChan.blockSignals(False)

    def mousePressEvent(self, event):
        self.setActiveChannel()
        self._clickedChannel = self._activeChannel
        self._lastClickedEntity = self._lastActiveEntity

        if event.button() == self.contextBtn:
            self.syncContextMenu()
            self.contextMenu.popup(event.screenPos().toPoint())
            #XXX Quirky. If not accepted, two cotext menus appear
            event.accept()
            return

        self._updateEnhanceDialog()
        event.ignore()
        # super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        #TODO directly set ref in frame and infobox..
        self.setActiveChannel()

        # pointPos = event.screenPos().toPoint()
        # # pointPos = event.pos()
        # pointPos = self._crossHair.setPos(pointPos)
        for chan in self.channels.values():
            chan.updateForeground()

        event.ignore()
        # super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        # viewcontext storing and fetching
        if event.modifiers() == qc.Qt.AltModifier:
            if event.key() in self.contextStoreKeys:
                self.viewSetup.activeViewKey = event.key()
                self._restoreViewSetup()
                for chan in self.channels.values():
                    chan.chanLabel.set(2, text='VC{}'.format(event.key()))
                event.accept()
            elif event.key() == qc.Qt.Key_L:
                try:
                    self.viewSetup.load(self.viewSession)
                    self._restoreViewSetup()
                    event.accept()
                except:
                    warnings.warn('Could not load the last Session')
            elif event.key() == qc.Qt.Key_S:
                self.viewSetup.save(self.viewSession)
                event.accept()
            else:
                event.ignore()

        # viewcontext storing and fetching
        elif qc.Qt.Key_0 <= event.key() <= qc.Qt.Key_9:
            idx = event.key() - 0x31
            if idx < 0:
                idx = 10
            taglist = list(self._dataManager.tags)
            taglist.sort()
            try:
                useTag = taglist[idx]
                self._lastClickedEntity = self._lastActiveEntity
                self._processSelection(useTag, 'tags')
                event.accept()
            except IndexError:
                event.ignore()

        elif event.key() in (qc.Qt.Key_Plus, qc.Qt.Key_Minus):
            if event.key() == qc.Qt.Key_Minus:
                changeRad = self.entity_scn.decreaseRadius
            else:
                changeRad = self.entity_scn.increaseRadius

            changeRad()

            self.setActiveChannel()
            self._crossHair.setProperties(
                radius=self.entity_scn.drawingRadius)

            self._activeChannel.updateForeground()
            event.accept()

        elif event.key() in (qc.Qt.Key_E, qc.Qt.Key_D, qc.Qt.Key_N):
            newMode = self.modeMap[event.key()]
            if self.entity_scn.mode == newMode:
                newMode = 'N'
            self.setDrawMode(newMode)
            self.newDrawMode.emit(newMode)

        elif event.key() == qc.Qt.Key_P:
            chan = self._activeChannel
            if chan is None:
                return
            chan.chanLabel.setVisible(False)
            chan.updateForeground()
            chan.setHighlightFrame(None)

            viewName = chan.chanLabel.elements[0].text[:10] + '.png'
            
            #TODO make me a function
            rect = qc.QRect(0, 0, chan.width(), chan.height())
            pixMap = chan.grab(rect)
            pixMap.save(viewName)

            # import IPython as ip
            # ip.embed()
            
            #FIXME
            # fullRect = chan.scene().itemsBoundingRect()
            # chan.setRange(fullRect, padding=0)
            # pixMap = chan.grab(fullRect.toRect())
            # fullName = chan.chanLabel.elements[0].text[:10] + '_full.png'
            # pixMap.save(fullName)

            # chan.setRange(rect, padding=0)

            chan.chanLabel.setVisible(True)
            chan.setHighlightFrame(self._highlightFrame)
            chan.updateForeground()
            event.accept()
        elif event.key() == qc.Qt.Key_Y:
            self._lastClickedEntity = self._lastActiveEntity
            self._processSelection('done', 'tags')
            event.accept()
        else:
            event.ignore()

    def syncContextMenu(self):
        if self._activeChannel is None:
            return

        shows = self._activeChannel.scene() is self.entity_scn
        self.contextMenu.updateVisible(shows)

    def setActiveChannel(self):
        """sets the _activeChannel propertie
        never updates
        """
        # iterating over all channels, to test if they are
        # under the mouse and set properties accordingly
        # self._activeChannel = None

        activeChannel = None
        for curIndex, curChan in self.channels.items():
            if curChan.underMouse():
                activeChannel = curChan
                break

        if activeChannel is None:
            return None

        # TODO other way round. set ref, in paint then just check if ref is the
        # painting channel...
        if not activeChannel is self._activeChannel:
            if not self._activeChannel is None:
                self._activeChannel.setHighlightFrame(None)
            self._activeChannel = activeChannel
        self._activeChannel.setHighlightFrame(self._highlightFrame)

    def setBackground(self, imagedata, name, index=None):
        """Sets the background of channel at index to imagedata
        will silently fail if there is no channel at index

        if index is none, use the _activeChannel
        if imagedata is None, make black background
        """
        chan, index = self.getChan(index)

        chan.background.setImage(imagedata)
        chan.chanLabel.set(0, text=name)

        # if it was already enhanced, load the enhancment
        minVal, maxVal = self.viewSetup['enhancments'].setdefault(
            name, (0, 0xffff))
        
        self.enhanceChannelContrast(
            minVal, maxVal, index=index, update=False)

        chan.updateBackground()

    def loadImage(self, idx, name):
        """Loads an image from rpository and set it as background
        of channel with index idx
        """
        # not get, as this state should be never reached. thus
        # should throw an error as this means data got inconsistent
        path = self.imageRepository['background'][name]

        # 'None' image selected
        if path is None:
            img = np.ones((1, 1), dtype=np.uint16) * 0xffff
        else:
            # try to load image at path. If fails, return with warning
            img = getFlippedImagedata(path)
            if img is None:
                warnings.warn('Could not load {} @ {}'.format(name, path))
                return

        self.setBackground(img, index=idx, name=name)
        self.viewSetup['backgrounds'][idx] = name

    @qc.pyqtSlot(str, str)
    def _processSelection(self, aName, selector):
        """load image to selector
        """
        if selector == 'channelBg':
            idx = self._clickedChannel.channelIndex
            self.loadImage(idx, aName)

        elif selector == 'tags':
            if self._lastClickedEntity is None:
                return
            if aName == 'None':
                self._lastClickedEntity.tags = set([])
                colorString = None
            elif aName in self._lastClickedEntity.tags:
                self._lastClickedEntity.tags.remove(aName)
                colorString = None
            else:
                self._lastClickedEntity.tags.add(aName)
                colorString = aName
            self._updateInfoBox(self._lastClickedEntity)

            # do the color stuff
            self._colorManager.setColor(self._lastClickedEntity, colorString)
            self._lastClickedEntity.GFX.update()

    def _updateInfoBox(self, entity):
        #TODO to function...
        chanIdx = self._activeChannel.channelIndex
        chanName = self.viewSetup['backgrounds'].get(chanIdx, 'None')
        self._infoBox.setValues(
            eid=entity.eid,
            tags=entity.tags,
            scalars=entity.scalars,
            chanName=chanName)
        self._activeChannel.updateForeground()

    def getChan(self, index=None):
        """looks up the channel to operate on. If the index is none, the
        active channel is returned. if no channel is active, None is returned
        """
        #TODO remove me?

        if index is None:
            chan = self._activeChannel
        else:
            chan = self.channels.get(index, None)

        return chan, chan.channelIndex

    @qc.pyqtSlot(bool)
    def changeItemVisibility(self, visible):
        """change visivility of items in last active channel
        """
        self.show_entities(visible)

    def show_entities(self, show=True, index=None):
        """Sets channel at index to show entities
        will silently fail if there is no channel at index
        """
        chan, index = self.getChan(index)
        if chan is None:
            return

        self.viewSetup['foregrounds'][index] = show

        if show:
            chan.setScene(self.entity_scn)
        else:
            chan.setScene(self.empty_scn)

    def customEvent(self, event):
        self.setActiveChannel()

        if event == ActiveEntity:
            event.accept()
            if event.isActive:
                self.setActiveEntity(event.entity)
                self.contextMenu.allowTagSelection = True
                self._activeChannel.setInfoBox(self._infoBox, ref=event.rect)
                self._updateInfoBox(event.entity)
            else:
                self._activeChannel.setInfoBox(None)
                self.contextMenu.allowTagSelection = False
                self.setActiveEntity(None)
        elif event == ScalarAssignmentChanged:
            event.accept()
            if self._lastActiveEntity is None or self._activeChannel is None:
                return
            index = self._activeChannel.channelIndex
            chanName = self.viewSetup['backgrounds'].get(index, 'None')
            scalarKey = (chanName, 0) #0 is manual
            val = self._lastActiveEntity.scalars.get(scalarKey, 0)
            val += event.change
            self._lastActiveEntity.scalars[scalarKey] = val
            self._updateInfoBox(self._lastActiveEntity)
            self.setActiveEntity(self._lastActiveEntity)
        elif event == EntityChangedEvent:
            event.entity.makeGFX()
            self.addEntity(event.entity)

        try:
            self._activeChannel.updateForeground()
        except AttributeError as err:
            if self._activeChannel is None:
                warnings.warn('No active channel!')
            else:
                raise err

    def setActiveEntity(self, entity=None):
        """Track last active entity, allows to change layout based on entity
        properties, yadda yadda here should be a callback"""
        #TODO remove knowledge about entity?
        self._lastActiveEntity = entity

        if entity is None:
            scalarNames = []

        else:
            scalarNames = list(entity.scalars.keys())

        for curChan in self.channels.values():
            bgName = self.viewSetup['backgrounds'].get(curChan.channelIndex,
                                                       'None')
            if bgName is None:
                continue
            if bgName in scalarNames:
                scValue = entity.scalars[(bgName, 0)]
                curChan.chanLabel.set(0, fgColor='#E62B38')
                curChan.chanLabel.set(1, text='{}'.format(scValue),
                                      fgColor='#E62B38')
            else:
                curChan.chanLabel.set(0, fgColor='#10AA00')
                curChan.chanLabel.set(1, text='', fgColor='#10AA00')

            curChan.updateForeground()

    def setDrawMode(self, drawMode):
        """ Similar functionality to ViewBox in pyqtgraph

            Set the mouse interaction mode. *mode* must be either ViewContext.PanMode
            or ViewContext.RectMode. In PanMode, the left mouse button pans the view
            and the right button scales. In RectMode, the left button draws a
            rectangle which updates the visible region
        """
        if drawMode in 'DE':
            self._crossHair.setProperties(
                radius=self.entity_scn.drawingRadius)
        elif drawMode == 'N':
            self._crossHair.setProperties(radius=0)
        self.entity_scn.setDrawingMode(drawMode)

    def setGlobalOpacity(self, alpha):
        """Sets opacity of all items in ViewContext scene

        Parameters
        ----------
        alpha : float
            Alphavalue to be set as opacity for all items in the scene
        """
        self._colorManager.changeOpacity(alpha)
        self.viewSetup['globalAlpha'] = alpha
        for item in self.entity_scn.items():
            item.update()
