"""Generates and manages all the entity through their entire lifetime.
Uses EntityLoader and EntitySaver to ensure persistense during session
"""
from entity import Entity


class EntityManager():

    def __init__(self):
        # tracks all entities generated
        self._entities = {}

    def make_entity(self, entity_id=None):
        if entity_id is None:
            entity_id = self.get_eid()
        elif not self.valid_eid(entity_id):
            msg = 'Can not create entity with invalid ID {}'
            raise ValueError(msg.format(entity_id))

        new_entity = Entity(entity_id)
        self._entities[new_entity.eid] = new_entity
        
        return new_entity

    def valid_eid(self, eid):
        valid = isinstance(eid, int) and eid > 0
        other = self._entities.get(eid, None)
        return other is None and valid

    def get_eid(self):
        """Gets an eid that is free
        """
        left = 0
        right = len(self._entities) - 1

        used_ids = list(self._entities.keys())
        used_ids.sort()

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
        else:
            return len(used_ids) + 1

