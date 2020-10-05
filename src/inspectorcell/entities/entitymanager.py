"""Generates and manages all the entity through their entire lifetime.
Uses EntityLoader and EntitySaver to ensure persistense during session
"""
# built-in
import warnings

# extern
from sortedcontainers import SortedList
import numpy as np
import cv2

# buddy
from miscmics.entities import EntityFactory

# this
from .entity import Entity
from .entityfile import EntityFile
from .misc import get_sliced_mask, mask_to_contour as to_contour


class EntityManager:

    def __init__(self):
        self._factory = EntityFactory()
        self.clear()
        self._used_eids = set([0])

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

    def _is_valid(self, objectid):
        not_zero = objectid > 0
        not_used = objectid not in self._used_eids
        is_int = isinstance(objectid, int)
        return not_zero and not_used and is_int

    def make_entity(self, entity_id: int = None):

        if entity_id is None:
            entity_id = self.getObjectId()
        elif not self._is_valid(entity_id):
            raise ValueError(f'Invalid eid {entity_id}')

        new_ent = Entity(entity_id)
        
        self.addEntity(new_ent)

        return new_ent

    def popEntity(self, eid):
        """Looks up entity by id and pops it.

        Looks up an entity form the manager by it's id. The entity is returned
        and removed from the manager. Analog to Dict.pop(key)

        Parameters
        ----------
        eid : int
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

        popee = self.getEntity(eid)
        self._used_eids.remove(eid)

        # translate the eid to uniqueid...
        popee.eid = popee.unique_eid
        self._factory.ledger.remove_entity(popee)

        # ...and back
        popee.eid = eid

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
            eid = entry.get('id', None)
            contour = entry['contour']

            entity = self.make_entity(eid)

            entity.tags = set(entry['tags'])
            entity.scalars = dict(entry['scalars'])
            entity.generic['historical'] = bool(entry['historical'])

            if not entity.historical:
                try:
                    entity.from_contours(contour)
                    entity.makeGFX()
                except ValueError as e:
                    if not 'polygons' in str(e):
                        raise e
                    msg = 'Entity {} has no segment/contour. Will be' +\
                          ' marked historic'
                    warnings.warn(msg.format(eid))
                    entity.historical = True
                    entity.contours = []

    def clear(self):
        """reset the whole entity manager, mainly for testabiliy
        """
        self._factory.ledger.clear()
        self._used_eids = set([0])

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

    def getEntity(self, eid):
        for ent in self.getEntities():
            if ent.eid == eid:
                return ent
        return None

    def getObjectId(self, objectId=None):
        if objectId is None:
            return max(self._used_eids) + 1

        if self._is_valid(objectId):
            return objectId
        else:
            return max(self._used_eids) + 1
    
    def addEntity(self, entity):
        object_id = entity.eid
        
        # already added?
        other = self.getEntity(object_id)
        if other is entity:
            return

        if self._is_valid(object_id):
            # use unique id in ledger
            entity.eid = entity.unique_eid
            self._factory.ledger.add_entity(entity)
            
            # set eid to object id
            self._used_eids.add(object_id)
            entity.eid = object_id
        else:
            raise ValueError(f'Invalid entity to add: {entity}')
