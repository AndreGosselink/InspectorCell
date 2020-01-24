"""Controller, bridges between data and view
"""
# built-in
import warnings

# extern
import numpy as np

# project
from .viewer import ViewContext
from .entities import EntityManager, EntityFile, read_into_manager
from .datamanager import DataManager
from .util.image import getFlippedImagedata


class Controller():
    """Cotrols the app, including data and gui. Every feature should be
    in principle triggerable by this class

    controlls view and entities
    """
    #TODO terminally remove uncommented code

    def __init__(self):
        """Implements all functions to manipulate the view and the entities
        """
        # shoudl be in some kind of data structure?
        self.dataManager = DataManager()
        self.entityManager = EntityManager()

        self.viewer = ViewContext(dataManager=self.dataManager,
                                  entityManager=self.entityManager)

        # self._connect()

    # def _connect(self):
    #     """Connects elements
    #     """
    #     # self.viewer.
    #     pass

    def initViewContext(self):
        """Initializes the GUI/ViewContext
        """
        self.viewer.setGridlayout(2, 2)
        self.viewer.setTagSelection()

    def clearEntities(self):
        """Clears all entities generated including the graphic
        representations for the entities. with highest level of
        contorl/abstraction this function has to ensure that all
        steps are done to free memory
        """
        self.entityManager.clear()

    def _loadFromJson(self, jsonFile):
        """Loading from json file, setting the tags accordingly

        Parameters
        ----------
        jsonFile : Path
            path to a jsonfile where entity data is written to as json
        """
        # load data from file
        read_into_manager(jsonFile, self.entityManager)

        # update view and tags
        self.dataManager.addTags(self.entityManager.allTags)
        #TODO should be synced automatically, when dialog is brought up
        self.viewer.setTagSelection()

    def storeEntities(self, jsonFile=None):
        """Unified interface for storing the entity space
        to an file format or other source

        Parameters
        ----------
        jsonFile : Path
            path to a jsonfile where entity data is written to as json
        """

        with EntityFile.open(jsonFile, 'w') as trgt:
            trgt.writeEntities(self.getEntities())

    def generateEntities(self, entityMask=None, entityContours=None,
                         jsonFile=None, entityMaskPath=None):
        """Unified interface for populating the entity space
        converts both inputs into a entity format
        Either entityMask OR entityContours

        Parameters
        ----------
        entityMask : ndarray
            ndarray encoding the entity id per pixel

        entityMaskPath : Path to image file
            Points to an image, that will be interpreted as entityMask

        entityContours : tuple
            tuple (Id, path) where Id is the entity id and path, a list of
            points, where each point is a float tuple

        jsonFile : Path
            path to jsonFile containing entity data. Will set tag selection
            accordingly

        Raises
        ------
        ValueError
            Raises ValueError if an entry is mailformed
        """
        # no source available, raise en error as it was called without
        # any attributes but needs one
        opts = sum([1 for _ in (entityMask, entityMaskPath, entityContours, jsonFile)\
                   if not _ is None]) 
        if opts != 1:
            msg = 'Only one sorce can be given at a time'
            raise ValueError(msg)

        # contours are given. transform them into the contourData format
        elif not entityContours is None:
            self.entityManager.generateFromContours(entityContours)

        # transform masks into the contour format
        elif not entityMask is None:
            self.entityManager.generateFromPixelmap(entityMask)

        # load from a json file
        elif not jsonFile is None:
            self._loadFromJson(jsonFile)

        # load from a entity mask path file
        elif not entityMaskPath is None:
            # entityMask = getFlippedImagedata(entityMaskPath)
            EVERYTHING BAD HAPPENS HERE!!!!!
            entityMask = getFlippedImagedata(entityMaskPath)
            self.entityManager.generateFromPixelmap(entityMask)

        # conflicting data sources are given. could be handled but for now
        # just raise an error
        else:
            raise RuntimeError('How did we get here?')

        # add all entities to the scene
        for entity in self.entityManager:
            if not entity.historical:
                self.viewer.addEntity(entity)

    #TODO remove this section
    # def sync(self, *args, **kwargs):
    #     """Syncs the viewer and the entityManager
    #     so that the viewer know what data is there to
    #     show.

    #     can set callbacks and do dependency injection to
    #     some statefull object, or manipulate directly
    #     """
    #     pass

    def setImages(self, imageSelection):
        """sets image selection viable to display in all kinds of
        layers

        Parameters
        ----------
        imageSelection : list of tuples
            each item in the list is an image represented by an tuple. the tuple
            constist of an string and a path. the string is the display name and
            the path points to the respective image file
        """
        self.viewer.setBackgroundSelection(imageSelection)

    def getEntities(self):
        """Returns a list of all Entity instances

        Returns
        -------
        entities : list of Entity
            list of all Entity instances in self.EntityManager
        """
        return [ent for ent in self.entityManager]

    def getEntityData(self):
        """Generates a list of all data about entities 

        Returns
        -------
        entityData : list of dicts
            lost of dicts, each dict is a entity entry with the tags
            Id, tags, scalars and contour
        """
        entity_data = []
        for entity in self.entityManager:
            entry = {
                'id': entity.eid,
                'tags': entity.tags,
                'scalars': entity.scalars,
                'contour': entity.contours,
                #TODO handling of ancestors and historical
                # 'active': entity.isActive,
                'historical': entity.historical,
                'ancestors': [],
            }
            entity_data.append(entry)
        return entity_data

    @property
    def widget(self):
        return self.viewer
