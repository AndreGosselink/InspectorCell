"""Implements threadsave and UUID consistency enforcing EntityLedger

For now this is more a dummy as an fully featuer fledged register for
all entity instances. It's current main function is to allow for flexibility
down the road.
"""

from typing import Generic, Type, Any, T, List
from threading import Lock
from uuid import uuid4

from .entity import GenericEntityType as GenericEntity
from ..util import SingletonMixin


class EntityLedger():
    """Global Registry of Entities

    Lookup of all generated entities, checking if Entity is valid
    in current ledger
    """
    # non-reentrant as any call to locked functions should be 'atomic'
    # and not call another locked function
    _ledger_lock = Lock()

    def __init__(self):
        self.entities = {}

    def __iter__(self):
        return self.entities.__iter__()

    def clear(self):
        """Clears all entities
        """
        self.entities = {}

    @classmethod
    def instance(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Get *an* instance of the class, constructed when  using (kw)args.
        """
        return cls(*args, **kwargs)

    #TODO if creation of uuid4 is enforced
    # no locks are needed in add
    def get_eid(self):
        """Returns safe uuid
        """
        with self._ledger_lock:
            new_eid = uuid4()
            while new_eid in self.entities:
                new_eid = uuid4()
            return new_eid

    def add_entity(self, ent: GenericEntity):
        """Adds an entity to the ledger

        Parameters
        ----------
        ent : Entity instace
            Instance to add to the Ledger. If the uuid `ent.eid` if the
            entity is already registered, an ValueErro is raised

        Raises
        -------
        ValueError
            If an entity with uuid `ent.eid` is already added to the ledger and
            `reassign_eid` is `False`
        """

        # will always be released, even if Exception is raised
        with self._ledger_lock:
            if ent.eid not in self.entities:
                self.entities[ent.eid] = ent
            else:
                raise ValueError(f'Entity with {ent.eid} already added')

    def remove_entity(self, ent: GenericEntity) -> GenericEntity:
        """Removes an entity from the ledger

        Parameters
        ----------
        ent : Entity instace
            Instance to remove from the ledger. If there is no entity with
            corresponding `ent.eid` is not in the ledger a ValueErro is raised

        Raises
        -------
        ValueError
            If an entity with uuid `ent.eid` is not in the ledger
        """

        # will always be released, even if Exception is raised
        with self._ledger_lock:
            if ent.eid in self.entities:
                return self.entities.pop(ent.eid)
            raise ValueError(f'Entity with {ent.eid} not in ledger')
