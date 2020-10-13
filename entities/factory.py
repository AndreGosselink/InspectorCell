"""Base class to generate and organize tracking of everything Entity
"""
import copy
import warnings
from uuid import UUID

from .entity import GenericEntityType as GenericEntity, Entity
from .ledger import EntityLedger


class EntityFactory:
    """Generates Entities

    Enforces registration of Entities, uniqness of uudis
    Base class for generators from file, generic ones etc
    """

    valid_fields = frozenset(Entity.get_field_names())

    def __init__(self, ledger: EntityLedger = None):
        """Entity derived class to create

        Parameters
        ----------
        ledger : EntityLedger (default=None)
            EntityLedger to use. If 'None' an new one will be
            created
        """
        if ledger is None:
            ledger = EntityLedger.instance()

        self.ledger = ledger

        if self.ledger.entities != {}:
            warnings.warn(
                'Might re-add entities, as the eids are freshly' + \
                ' created! Consider `LegacyEntityJSON.ledger.clear()`')

    def create_entity(self, eid: UUID = None, raise_eid: bool = True,
                      cls: GenericEntity = None, **kwargs) -> GenericEntity:
        """Creates a new Entity and returns it

        Parameters
        ----------
        eid : UUID
            Requested unique entity id for entity to create
            If `eid` is `None` (default) a new uuid4 is created
            If an `eid` is provided, which already exists, `None`
            is returned

        raise_eid : bool
            Raise an error, if the an provided `eid` is not unique (default)
            else just return None

        cls : GenericEntity
            Entity derived sublcass that will be instanciated and returned
            if not provided, Entity will be used.

        **kwargs : dict
            Other keywords are directly interpreted as Entity dataclass
            field values. If they none are provided, (empty) default values
            are used.

        Returns
        -------
        ent : [Entity|None]
           Returns the created entity, if a valid `eid` was provided.
           There will be always a Entity returned, if `eid` is `None`.
           Otherwise the provided `eid` parameter must be unique. If it
           is already used within the curretn runtime, `None` is returned.

        Raises
        -------
        TypeError
            If any of the provided keyword arguments does is not a valid
            field in the `Entity` dataclass

        ValueError
            If a provided `eid` is invalid (already in EntityLedger) and
            `raise_eid` is `True` (default)
        """
        if eid is None:
            eid = self.ledger.get_eid()

        if cls is None:
            cls = Entity
        else:
            if not issubclass(cls, Entity):
                raise ValueError(f"'{cls}' is not an Entity subclass")

        # create new EntityType
        ent = cls(eid=eid)
        try:
            self.ledger.add_entity(ent)
        except ValueError:
            if raise_eid:
                raise ValueError(f'Eid {eid} is already in ledger!')
            return None

        for key, val in kwargs.items():
            if not key in self.valid_fields:
                raise TypeError(f"Invalid Entity field: '{key}'")
            setattr(ent, key, copy.deepcopy(val))
        
        return ent

    def pop_entity(self, entity: GenericEntity) -> GenericEntity:
        """Removes a new Entity and returns it

        Parameters
        ----------
        entity : Entity
            Entity toe be removed
        """
        if entity.eid in self.ledger:
            self.ledger.remove_entity(entity)
        return entity
