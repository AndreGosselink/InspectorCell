"""Controller, bridges between data and view
"""
# std
import json
import warnings
from pathlib import Path
import copy

# extern
import numpy as np
from miscmics.entities.legacyjson.factory import LegacyEntityJSON
from miscmics.entities.jsonfile import EntityJSONDecoder, save as saveEnt
from miscmics.entities import EntityFactory

# project
from .viewer import ViewContext
from .entities import EntityManager, EntityFile, read_into_manager, Entity
from .entities.entity import dilatedEntity
from .datamanager import DataManager
from .util.image import getImagedata


class Controller():
    """Controls the app, including data and gui. Every feature should be
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
        self.viewer.clearEntities()

    def _loadFromJson(self, jsonFile):
        """Loading from json file, setting the tags accordingly

        Parameters
        ----------
        jsonFile : Path
            path to a jsonfile where entity data is written to as json
        """

        # # load data from file
        # read_into_manager(jsonFile, self.entityManager)
        jsonFile = Path(jsonFile)
        if jsonFile.suffix == '.json':
            loader_fac = LegacyEntityJSON()
            loader_fac.load(jsonFile, cls=Entity)
        elif jsonFile.suffix == '.ent':
            with jsonFile.open('r') as src:
                entityData = json.load(src)
            loader_fac = EntityFactory()
            decoder = EntityJSONDecoder(factory=loader_fac)
            for entDat in entityData:
                newEnt = decoder.from_dict(
                    copy.deepcopy(entDat), cls=Entity)

        assert not (loader_fac.ledger is self.entityManager._factory.ledger)

        for ent in loader_fac.ledger.entities.values():
            validId = self.entityManager.getObjectId(ent.objectId)
            if ent.objectId != validId:
                print(f'Changed {ent.objectId} to {validId}')
                ent.objectId = validId
            # add to manager
            self.entityManager.addEntity(ent)
        
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
        
        # with Path(jsonFile).open('w') as trgt:
        #     json.dump(list(self.entityManager.iter_all()),
        #               trgt, cls=EntityJSONEncoder)
        saveEnt(jsonFile, self.entityManager._factory.ledger, mode='w')

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
            pixelMap = getImagedata(entityMaskPath)
            self.entityManager.generateFromPixelmap(pixelMap)
            for ent in self.entityManager:
                dilatedEntity(ent, 1)

        # conflicting data sources are given. could be handled but for now
        # just raise an error
        else:
            raise RuntimeError('How did we get here?')

        # add all entities to the scene
        for entity in self.entityManager.iter_active():
            try:
                self._initRenderEntity(entity)
            except ValueError:
                if entity.int_contour == []:
                    entity.historical = True
                    msg = f'Entity {entity.eid} has no contour.' + \
                           'It will be set historical!'
                    warnings.warn(msg)

    def _initRenderEntity(self, entity):
        """ Check of entity has GFX, create one if needed and add to
        viewer
        """
        if entity.GFX is None:
            entity.makeGFX()
            self.viewer.addEntity(entity)

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
