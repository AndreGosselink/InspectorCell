from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ChildGroup
import pyqtgraph as pg


# class ScopeView(ViewBox):
# 
#     def __init__(self, *args, **kwargs, globalChildGroup=None,
#                  globalItems=None):
#         super(*args, **kwargs).__init__()
# 
#         if globalChildGroup is None:
#             raise TypeError('globalChildGroup must be given!')
#         if globalItems is None:
#             raise TypeError('globalItems must be given!')
# 
#         self.globalChildGroup = globalChildGroup
#         self.globalItems = globalChildGroup
# 
#     def addItemGlobal(self, item, ignoreBounds=False):
#         """
#         Add a QGraphicsItem to this the global view. All ScopeViews with the
#         same globalChildGroup will include this item when determining how to set
#         its range automatically unless *ignoreBounds* is True.
#         """
#         if item.zValue() < self.zValue():
#             item.setZValue(self.zValue()+1)
#         scene = self.scene()
#         if scene is not None and scene is not item.scene():
#             scene.addItem(item)  ## Necessary due to Qt bug: https://bugreports.qt-project.org/browse/QTBUG-18616
#         item.setParentItem(self.childGroup)
#         if not ignoreBounds:
#             self.addedItems.append(item)
#         self.updateAutoRange()
# 
#     def removeItemGlobal(self, item):
#         pass

class GlobalItemContainer():
    pass

class GlobalView(ViewBox):
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    
    Can register and unregister viewboxes. Draws all global items for each
    view registered
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
