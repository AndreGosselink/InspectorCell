"""Controller, bridges between 
"""
import warnings

from .viewer import Viewer
from .viewer.dialog import ViewSetupDialog
from .entities import EntityManager


class Controller():
    """Cotrols the app, including data and gui. Every feature should be
    in principle triggerable by this class

    controlls view and entities
    """

    def __init__(self):
        """Implements all functions to manipulate the view and the entities
        """
        self.viewer = Viewer()
        self.entityManager = EntityManager()

        self.dialogs = {}
        self.addDialogs()

    def addDialogs(self):
        """populates Controller.dialogs
        viewer and entityManager must be already set!
        """
        viewSetupDialog = ViewSetupDialog(
            parent=self.viewer,
            viewSetup=self.viewer.viewSetup,
            callback=self.viewer.update)

        self.dialogs = {
            'viewSetup': viewSetupDialog }

    def initViewer(self):
        """Initializes the GUI/Viewer
        """
        self.viewer.setGridlayout(2, 2)

    def clearEntities(self):
        """Clears all entities generated including the graphic
        representations for the entities. with highest level of
        contorl/abstraction this function has to ensure that all
        steps are done to free memory
        """
        #TODO implement me
        msg = '<Controller.clearEntities()> no entitie was cleared!'
        class NotImplementedWarning(UserWarning):
            pass
        warnings.warn(NotImplementedWarning(msg))

    def generateEntities(self, entityMask=None, entityContours=None):
        """Unified interface for populating the entity space
        converts both inputs into a entity format
        Either entityMask OR entityContours

        Parameter
        ---------
        entityMask : ndarray
            ndarray encoding the entity id per pixel

        entityContours : tuple
            tuple (Id, path) where Id is the entity id and path, a list of
            points, where each point is a float tuple

        Raises
        ------
        ValueError
            Raises ValueError if an entry is mailformed, see Notes
        """
        # no source available, raise en error as it was called without
        # any attributes but needs one
        if not entityMask is None and not entityContours is None:
            msg = 'Only entityContours or entityMask must be given, not both'
            raise ValueError(msg)
        
        # contours are given. transform them into the contourData format
        elif not entityContours is None:
            self.entityManager.generateFromContours(entityContours)

        # transform masks into the contour format
        elif not entityMask is None:
            pass
        
        # conflicting data sources are given. could be handled but for now
        # just raise an error
        else:
            msg = 'At least entityContours or entityMask must be given!'
            raise ValueError(msg)

    def sync(self, *args, **kwargs):
        """Syncs the viewer and the entityManager
        so that the viewer know what data is there to
        show.

        can set callbacks and do dependency injection to
        some statefull object, or manipulate directly
        """
        pass
    
    def showViewSetupDialog(self):
        """shows the ViewSetup dialog and updated view after it is accepted
        or closed. syncs the view and dialog values
        """
        diag = self.dialogs['viewSetup']
        diag.updateGui()
        diag.show()

    @property
    def widget(self):
        return self.viewer
