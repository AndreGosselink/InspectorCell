"""Generates and manages all the entity through their entire lifetime.
Uses EntityLoader and EntitySaver to ensure persistense during session
"""

class EntityManager():

    def __init__(self):
 
        # tracks all entities generated
        self._entities = {}
