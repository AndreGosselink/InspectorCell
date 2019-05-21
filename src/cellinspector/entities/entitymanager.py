"""Generates and manages all the entity through their entire lifetime.
Uses EntityLoader and EntitySaver to ensure persistense during session
"""
from sortedcontainers import SortedList
import numpy as np

from .entity import Entity
from .misc import get_sliced_mask

from ..util import depreciated


#TODO generator factory -> data into unified job format return generators
class EntityGenerator:
    """Divide the process of generation and management of entities
    does not enforce any rules, just is set of entities based on some input
    might be usefull in context of multithreading
    """

    def __init__(self):
        self.entities = None

    def fromGreyscaleImage(self, image, offset=(0, 0)):
        """populates the entities list from a greyscale map

        Parameters
        ----------
        image : ndarray
            greyscalmap encoding entities ID by pixel.
        offset : tuple
            offset added to each slice for entities.

        Notes
        -----
        Populates EntityGenerator.entities w/o any asking, has an offset to allow
        multiple generators on map slices. Rules enforced on entity generation
        id > 0
        """
        entities = []
        valid_values = set(image[image > 0])
        for cur_value in valid_values:
            mask_slice, mask = get_sliced_mask(image, cur_value)
            new_entity = Entity(cur_value)
            new_entity.from_mask(mask_slice, mask, offset)
            entities.append(new_entity)

        self.entities = entities

    @depreciated(fromGreyscaleImage)
    def from_greyscale_image(self, image, offset=(0, 0)):
        pass


class EntityManager:
    __instance = None

    # tracks all entities generated and some stats
    # about them
    _entity_dat = {
        'entities': {},
        'id_list': SortedList([]),
    }

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __len__(self):
        """Number of entities in manager
        """
        return len(self._entity_dat['id_list'])
    
    def __iter__(self, filterActive=True):
        """Convinience iterator over all entities that are active
        """
        def _iter():
            for entity in self._entity_dat['entities'].values():
                if entity.isActive:
                    yield entity

        return _iter()
    
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
            entry = {'id': eid, 'contour': contours}
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
        """
        for entry in entityData:
            eid = entry.get('id', None)
            contour = entry['contour']
            entity = self.make_entity(eid)
            entity.from_contours(contour)
            entity.makeGFX()
    
    @depreciated(generateFromPixelmap)
    def generate_from_pixelmap(self, pixelmap):
        pass

    @depreciated(addEntity)
    def add_entity(self, entity):
        pass
    
    @classmethod
    def clear(cls):
        """reset the whole entity manager, mainly for testabiliy
        """
        cls._entity_dat = _entity_dat = {
            'entities': {},
            'id_list': SortedList([]),
        }


