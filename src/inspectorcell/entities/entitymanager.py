"""Generates and manages all the entity through their entire lifetime.
Uses EntityLoader and EntitySaver to ensure persistense during session
"""
# built-in
import warnings
from uuid import UUID

# extern
from sortedcontainers import SortedList
import numpy as np
import cv2

# buddy
from miscmics.entities import EntityFactory
from miscmics.entities.util import mask_to_contour as to_contour, get_sliced_mask

# this
from .entity import Entity
from .entityfile import EntityFile
# from .misc import get_sliced_mask, mask_to_contour as to_contour


class EntityManager:

    def __init__(self):
        self._factory = EntityFactory()
        self._usedObjIds = set([])
        self.clear()

    def __len__(self):
        """Number of entities in manager
        """
        return len(self._factory.ledger.entities)

    @property
    def allTags(self):
        tags = set()
        for ent in self.iter_all():
            tags = tags.union(ent.tags)
        return tags

    def iter_active(self):
        """Convinience iterator over all entities that are active
        """
        def _filtered():
            for ent in self.iter_all():
                if ent.isActive:
                    yield ent
                else: continue
        return _filtered()

    def iter_all(self):
        """Convinience iterator over all entities that are active
        """
        def _iter():
            for entity in self._factory.ledger.entities.values():
                yield entity
        return _iter()

    def __iter__(self):
        """Defaults to iter_all
        """
        return self.iter_all()

    def _is_valid(self, objectId):
        try:
            is_num = (float(objectId) - int(objectId)) == 0
            not_zero = objectId > 0
            not_used = objectId not in self._usedObjIds
            return not_zero and not_used and is_num
        except (TypeError, ValueError):
            return False

    def make_entity(self, objectId: int = None):
        
        # get objjectId if none is provided
        if objectId is None:
            objectId = self.getObjectId()
        elif not self._is_valid(objectId):
            raise ValueError(f'Invalid objectId: {objectId}')

        new_ent = Entity(objectId=objectId)
        self.addEntity(new_ent)

        assert new_ent.objectId == objectId

        return new_ent

    def popEntity(self, eid):
        """Looks up entity by id and pops it.

        Looks up an entity form the manager by it's id. The entity is returned
        and removed from the manager. Analog to Dict.pop(key)

        Parameters
        ----------
        eid : uuid
            entity id to pop

        Returns
        -------
        entity : Entity or None
            if Entity with eid is found, it is returned. Otherwise None
            is returned

        Note
        ----
        If the return value is not None, then the entity with the id eid is
        removed form the manager afterwards. The popped eid is also freed and
        can be reused
        """

        popee = self.lookupEntity(objectId=eid)
        self._usedObjIds.remove(popee.objectId)

        # translate the eid to uniqueid...
        self._factory.ledger.remove_entity(popee)

        return popee

    def generateEntities(self, entityData):
        """Add entities based on the entityData representation
        will always use contours for generation of spatial information

        common entity data structure here!

        Parameters
        ----------
        entityData : list of entityEntries
            entityEntries are dicts

        Notes
        -----
        If an entity has no contour, it will be automaticaly considered as
        deleted and thus hisorical
        """
        for entry in entityData:
            objectId = entry.get('id', None)
            contour = entry['contour']

            entity = self.make_entity(objectId=objectId)
            assert entity.objectId == objectId

            entity.tags.update(set(entry['tags']))
            entity.scalars.update(dict(entry['scalars']))
            entity.historical = bool(entry['historical'])

            if not entity.historical:
                try:
                    entity.from_contours(contour)
                    entity.makeGFX()
                except ValueError as e:
                    if not 'polygons' in str(e):
                        raise e
                    msg = 'Entity {} has no segment/contour. Will be' +\
                          ' marked historic'
                    warnings.warn(msg.format(objectId))
                    entity.historical = True
                    entity.contours = []

    def clear(self):
        """reset the whole entity manager, mainly for testabiliy
        """
        self._factory.ledger.clear()
        self._usedObjIds = set([0])

    def generateFromContours(self, contourData):
        """Encapsulate the usage of the entity generator
        to aid in concurrency later on

        Parameters
        ----------
        contourData : tuple iterable
            iterable containing entityId and list of paths
            where everey path is a list of float tuples
        """

        entityData = []

        for eid, contours in contourData:
            contours = [np.round(np.array(cont)) for cont in contours]
            contours = [cont.astype(int) for cont in contours]
            entry = {'id': eid, 'contour': contours, 'tags': [], 'scalars': {},
                     'historical': False}
            entityData.append(entry)

        self.generateEntities(entityData)


    def generateFromPixelmap(self, pixelmap):
        """Encapsulate the usage of the entity generator
        to aid in concurrency later on

        Parameters
        ----------
        pixelmap : int ndarray
            map that assigns each pixel i, j to background pixelmap[i, j] == 0
            or to an entity with an id pixelmap[i, j] == id
        """
        valid_values = np.unique(pixelmap.ravel())
        valid_values = valid_values[valid_values > 0]
        
        entities_dat = []
        for cur_value in valid_values:
            mask_slice, mask = get_sliced_mask(pixelmap, cur_value)

            contour = to_contour(mask_slice, mask)

            entry = {'id': int(cur_value), 'contour': contour, 'tags': [],
                     'scalars': {}, 'historical': False}

            entities_dat.append(entry)

        self.generateEntities(entities_dat)

    def getEntities(self):
        """Return iterator over all entities
        """
        return iter(self._factory.ledger.entities.values())

    def lookupEntity(self, eid=None, objectId=None):
        # return self._factory.ledger.entities.get(eid)
        hasEid, hasObjId = eid is not None, objectId is not None

        if not ((hasEid or hasObjId) and (not (hasEid and hasObjId))):
            msg = 'Exactly one parameter must be given: eid or hasObjId'
            raise ValueError(msg)
        elif hasEid:
            if not isinstance(eid, UUID):
                raise ValueError(f'eid must be an UUID instance!')
            return self._factory.ledger.entities.get(eid)
        elif hasObjId:
            ents = self._factory.ledger.entities.values()
            ents = [ent for ent in ents if ent.objectId == objectId]
            if not ents:
                return None
            elif len(ents) == 1:
                return ents[0]
            else:
                msg = f'Multiple entities with objectId {objectId} found!'
                warnings.warn(msg)
                return ents[0]

    def getObjectId(self, objectId=None):
        if self._is_valid(objectId):
            return objectId
        else:
            return max(self._usedObjIds) + 1
    
    def addEntity(self, entity):

        # already added?
        inLedger = entity.eid in self._factory.ledger.entities
        inUse = entity.objectId in self._usedObjIds
        if inLedger or inUse:
            err = ValueError(f'Can not add entity {entity.eid}, entity.objectId')
            byEid = self.lookupEntity(eid=entity.eid)
            byObjId = self.lookupEntity(objectId=entity.objectId)
            if byEid is entity:
                if byObjId is None and self._is_valid(entity.objectId):
                    self._usedObjIds.add(entity.objectId)
                elif not (byObjId is entity):
                    raise err
            elif byEid is not None:
                raise err

        if self._is_valid(entity.objectId):
            # use unique id in ledger
            self._factory.ledger.add_entity(entity)
            # set eid to object id
            self._usedObjIds.add(entity.objectId)
        else:
            raise ValueError(f'Invalid entity to add: {entity}')
