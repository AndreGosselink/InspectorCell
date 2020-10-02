""" Atomic representation of an Object with an shape found in MultiplexImages
"""
import copy
from uuid import UUID, uuid4
from enum import IntEnum, unique
from typing import Dict, Set, Type, List
from threading import Lock
from dataclasses import dataclass, field, fields

import numpy as np


@unique
class EntityType(IntEnum):
    """Defines possible Entity types

    Note
    ----
    Is sublcass of and can be treaded as int
    """
    Undefined = -1
    Cell = 0
    Artifact = 1
    Semantic = 2
    Historic = 3


@dataclass
class Entity:
    """Basic Class for everything that might be something found
    in multiplexed image stacks.
    """

    # NOTE
    # Using slots for performance and rigid class layout
    # However, using slots does not work with default values
    # and setting up a __init__ function is verbose. Or defaults
    # could be dropped. For now it is just an option if needed at some
    # point
    # __slots__ = ('eid', 'ref', 'etype', 'annotated', 'generic')

    # Only state representing field in entity.
    etype: int = EntityType.Cell

    # Reference which can be shared by several entities and should
    # point to the dataset/experiment to which the entity belongs to
    ref: UUID = None

    # Entity identifier, globally unique and unambigious identifier
    # for any Entity created.
    #TODO make unmutable after first time set
    eid: UUID = field(default_factory=uuid4)

    ### Annotation data
    # scalars are <str : float> mapping
    scalars: Dict[str, float] = field(default_factory=dict)
    # tags are str only
    tags: Set[str] = field(default_factory=set)

    ### Shape data
    #TODO make me property
    # generic data is <str : float|int|str|iterable-of-former> mapping
    contour: List[np.ndarray] = field(default_factory=list)

    ### Generic data
    # generic data is <str : numpy.ndarray> mapping
    # generic: Dict[str, np.ndarray] = field(default_factory=dict)
    generic: dict = field(default_factory=dict)

    @classmethod
    def get_field_names(cls):
        """Returns all valid fields in this dataclass
        """
        return [f.name for f in fields(cls)]


GenericEntityType = Type[Entity]
