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
            entity_id = max(self._used_eids) + 1
        elif not self._is_valid(entity_id):
            raise ValueError(f'Invalid eid {entity_id}')

        new_ent = self._factory.create_entity(cls=Entity)
        # newstyle factory creates a thread safe uuid.
        # but it does not do shadowing
        new_ent.eid = entity_id

        self._used_eids.add(entity_id)

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

    def getEntity(self, eid):
        for ent in self._factory.ledger.entities.values():
            if ent.eid == eid:
                return ent
        return None
    
    def addEntity(self, entity):
        if self._is_valid(entity.eid):
            self._factory.ledger.add_entity(entity)
            self._used_eids.add(entity.eid)
        else:
            raise ValueError(f'Invalid entity to add: {entity}')


class EntityManagerLEGACY:

    def __init__(self, *args, **kwargs):
        # tracks all entities generated and some stats
        # about them
        self._entity_dat = None
        self.clear()

    def __len__(self):
        """Number of entities in manager
        """
        return len(self._entity_dat['id_list'])

    def iter_active(self):
        """Convinience iterator over all entities that are active
        """
        def _filtered():
            for ent in self.iter_all():
                if ent.isActive: yield ent
                else: continue
        return _filtered()

    def iter_all(self):
        """Convinience iterator over all entities that are active
        """
        def _iter():
            for entity in self._entity_dat['entities'].values():
                yield entity
        return _iter()

    def __iter__(self):
        """Defaults to iter_active
        """
        return self.iter_active()

    def _add_entity(self, new_ent):
        """actuall adding of entity, updating stats
        will add w/o any checking for valid id or dat consistency
        Raises
        ------
        RuntimeError:
            if anything went wrong
        """
        entity_dict = self._entity_dat['entities']
        id_list = self._entity_dat['id_list']
        new_id = new_ent.eid

        # modify entity dict
        entity_dict[new_id] = new_ent

        # modify id_list
        try:
            if new_id > id_list[-1]:
                id_list.add(new_id)
            elif new_id < id_list[0]:
                id_list.add(new_id)
            else:
                # index in list is id - 1 as the list is always sorted
                id_list.add(new_id)
        except IndexError:
            id_list.add(new_id)

        if len(id_list) != len(entity_dict):
            raise RuntimeError('Inserting new id failed!')

    def make_entity(self, entity_id=None):
        """Create new entity. if entity_id is none, a new unused id is used
        if entity_id is an integer it will be tested for validity. If not valid
        or already used, an integer error is raised

        Returns
        -------
        new_entity : Entity
            newly created entety, alreaddy added and managed

        Raises
        ------
        ValueError:
            If a given entity_id is invalid

        RuntimeError:
            If the entity_id generation went wrong (e.g. due to racing
            conditions)
        """
        entities_dict = self._entity_dat['entities']

        if entity_id is None:
            entity_id = self.get_eid()
            if not entities_dict.get(entity_id, None) is None:
                raise RuntimeError('Entity ID found already in use!')

        elif not self.valid_eid(entity_id):
            msg = 'Can not create entity with invalid ID {}'
            raise ValueError(msg.format(entity_id))

        # create new entity
        new_entity = Entity(entity_id)
        # add it to _entity_dat
        self._add_entity(new_entity)

        return new_entity

    def getEntity(self, eid):
        """Looks up entity by id. If eid is not found, None is returned

        Parameters
        ----------
        eid : int
            entity id to look up

        Returns
        -------
        entity : Entity or None
            if Entity with eid is found, it is returned. Otherwise None
            is returned
        """
        entities_dict = self._entity_dat['entities']

        return entities_dict.get(eid, None)


    def addEntity(self, entity):
        """add an externally generated entity

        Raises
        ------
        ValueError:
            If entity.eid is invalid

        RuntimeError:
            If the entity generation went wrong (e.g. due to racing
            conditions)
        """
        entities_dict = self._entity_dat['entities']

        if entity.eid is None:
            entity.eid = self.get_eid()
            if not entities_dict.get(entity.eid, None) is None:
                raise RuntimeError('Entity ID found already in use!')

        elif not self.valid_eid(entity.eid):
            msg = 'Can not create entity with invalid ID {}'
            raise ValueError(msg.format(entity.eid))

        # add it to _entity_dat
        self._add_entity(entity)

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
        entities_dict = self._entity_dat['entities']
        used_ids = self._entity_dat['id_list']
        ent = entities_dict.pop(eid, None)

        if not ent is None:
            used_ids.remove(eid)

        return ent

    def _find_unused_eid(self):
        """finds smalles unused entity id.

        Returns
        -------
        ID:
            Unused ID
        """
        used_ids = self._entity_dat['id_list']

        if len(used_ids) == 0:
            return 1

        left = 0
        right = len(used_ids) - 1

        if used_ids[right] == len(used_ids):
            return len(used_ids) + 1

        if used_ids[left] != 1:
            return 1

        while True:
            mid = left + (right - left) // 2
            val = used_ids[mid] - 1
            if val != mid:
                right = mid
            else:
                left = mid
            if right - left == 1:
                break

        lval = used_ids[left]
        rval = used_ids[right]

        if rval - lval > 1:
            return lval + 1
        # else:
        return len(used_ids) + 1

    def valid_eid(self, entity_id):
        """Checks if entity_id is valid
        """
        valid = isinstance(entity_id, int) and entity_id > 0
        other = self._entity_dat['entities'].get(entity_id, None)
        return other is None and valid

    def get_eid(self):
        """Gets an eid that is free based on all entities managed
        finds the smalles possible free id
        """
        new_id = self._find_unused_eid()
        return new_id

    #TODO Make an generator to process pixmaps and then use the generateEntities
    #interface as well
    def generateFromPixelmap(self, pixelmap):
        """Encapsulate the usage of the entity generator
        to aid in concurrency later on

        Parameters
        ----------
        pixelmap : int ndarray
            map that assigns each pixel i, j to background pixelmap[i, j] == 0
            or to an entity with an id pixelmap[i, j] == id
        """
        gen = EntityGenerator()
        gen.fromGreyscaleImage(pixelmap)
        for entity in gen.entities:
            entity.makeGFX()
            self.addEntity(entity)

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
            entity.scalars = entry['scalars']
            entity.historical = entry['historical']

            #TODO handel ancestors
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
        self._entity_dat = _entity_dat = {
            'entities': {},
            'id_list': SortedList([]),
        }

    def isEmpty(self):
        if len(self) > 0:
            return False
        else:
            return True

    @property
    def allTags(self):
        """set of all tags from Entities owned by the EntityManager 
        """
        allTags = set([])
        for entity in self._entity_dat['entities'].values():
            allTags.update(entity.tags)
        return allTags

    @property
    def allUserScalars(self):
        """set of all user scalars from Entities owned by the EntityManager 
        """
        allScalars = set([])
        for entity in self._entity_dat['entities'].values():
            curScalars = set(key for key, _ in entity.scalars.keys())
            allScalars.update(curScalars)
        return allScalars
