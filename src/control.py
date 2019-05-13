"""Controller, bridges between 
"""
from .viewer import Viewer
from .entities import EntityManager


class Control():
    """Cotrols the app, including data and gui. Every feature should be
    in principle triggerable by this class

    controlls view and entities
    """

    def __init__(self):
        """Implements all functions to manipulate the view and the entities
        """
        self.viewer = Viewer()
        self.entityManager = EntityManager()

    def loadEntities(self, *args, **kwargs):
        """loads the entities by triggering the 
        the entityManager functions applicable 
        """
        pass

    def sync(self, *args, **kwargs):
        """Syncs the viewer and the entityManager
        so that the viewer know what data is there to
        show.

        can set callbacks and do dependency injection to
        some statefull object, or manipulate directly
        """
        pass


