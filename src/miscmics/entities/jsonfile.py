import json
import copy
from uuid import UUID
from typing import Callable, Union
from collections import OrderedDict
import warnings

from pathlib import Path
import numpy as np

from .entity import Entity, GenericEntityType, EntityType
from .factory import EntityFactory
from .ledger import EntityLedger


def to_dict(entity):
    """Converts entity to dict for serializaton

    Tries to convert alle fields in an entity to a dict
    This dict can be used for serializaiotns

    Parameter
    ---------
    entity : Entity
        Entity dataclass which should be convertet into an dict

    Raises
    ------
    TypeError
        TypError is raised, if any conversion fails
    """

    ser_dict = OrderedDict()
    ser_dict['eid'] = entity.eid.hex
    ser_dict['etype'] = int(entity.etype)

    ser_dict['tags'] = [str(tag) for tag in entity.tags]

    scalar = ser_dict['scalars'] = []
    for key, val in entity.scalars.items():
        scalar.append([str(key), float(val)])

    gen = ser_dict['generic'] = []
    for key, val in entity.generic.items():
        gen.append([str(key), np.asarray(val).tolist()])

    if entity.ref is None:
        ser_dict['ref'] = ''
    elif isinstance(entity.ref, UUID):
        ser_dict['ref'] = entity.ref.hex
    else:
        ser_dict['ref'] = str(entity.ref)

    contour = ser_dict['contour'] = []
    for cont in entity.contour:
        new_cont = []
        for (pt0, pt1) in cont:
            new_cont.append([float(pt0), float(pt1)])
        contour.append(new_cont)

    return ser_dict


class EntityJSONEncoder(json.JSONEncoder):
    """Class to serialize Entities to JSON
    """

    def default(self, entity):  # pylint: disable=E0202
        """Reimplemtantion of default

        Entity to dict for JSON encoding. Is called if other
        encoders failed.

        Parameter
        ---------
        entity : [Entity|Ans]
            Entity dataclass instance to be serialized
        """

        if not isinstance(entity, Entity):
            raise TypeError(f'Invalid object {repr(entity)}.')

        as_dict = to_dict(entity)
        return as_dict
    

class EntityJSONDecoder(json.JSONDecoder):

    def __init__(self, factory: EntityFactory, *args, **kwargs):
        """Decodes JSON to and creates Entity instance

        Combines creation of Entity from JSON by providing
        decoding of raw JSON objects to Entity instances created
        with factory

        Parameter
        ---------
        factory : EntityFactory
            Factory used to create entities from the JSON objects
        """
        self.fac = factory
        super().__init__(*args, **kwargs)

    def from_dict(self, enity_dict: dict,
                  cls: GenericEntityType = None) -> GenericEntityType:

        missing = set(enity_dict.keys()).symmetric_difference(
            EntityFactory.valid_fields)

        if missing:
            misses = ', '.join(f"'{dif}'" for dif in missing)
            raise TypeError(f"Missing or unknown key(s) {misses}")


        enity_dict['eid'] = UUID(hex=enity_dict['eid'])

        enity_dict['etype'] = EntityType(enity_dict['etype'])

        if enity_dict['ref'] == '':
            enity_dict['ref'] = None
        else:
            try:
                enity_dict['ref'] = UUID(hex=enity_dict['ref'])
            except ValueError:
                enity_dict['ref'] = str(enity_dict['ref'])

        enity_dict['tags'] = set(enity_dict['tags'])

        scalars = {}
        for key, val in enity_dict['scalars']:
            scalars[key] = float(val)
        enity_dict['scalars'] = scalars

        generic = {}
        for key, val in enity_dict['generic']:
            generic[key] = np.asarray(val)
        enity_dict['generic'] = generic

        enity_dict['contour'] = [np.asarray(shape) for shape in \
                                 enity_dict['contour']]

        try:
            return self.fac.create_entity(**enity_dict, cls=cls)
        except ValueError as err:
            raise ValueError(
                f"Could not create entity with eid '{enity_dict['eid']}'" +\
                f"\n->'{err}'")


    def decode(self, s):
        """Decodes JSON to Entity

        Decodes JSON serialized Entity to dict accepted by
        `EntityFactory.create_from_dict()` and then calls it

        Parameter
        ---------
        s : str
            JSON serialized entity

        Raises
        ------
        TypeError
            If JSON serialized data misses the `eid` field or not
            all serialized data is used during decoding
        """
        return self.from_dict(super().decode(s))


def save(filename: Union[str, Path], ledger: EntityLedger = None,
         mode: str = 'w'):
    """Stores the ledger as JSON

    Each entity is stored in a separate line. the entities
    get sorted by their eid

    Parameter
    ---------
    filename : Union[str|Path]
        Path to file, where Entities in Ledger will be stored
    ledger : EntitLedger (default=`None`)
        Ledger with Entity instances to be stored. If none is provided,
        a new is instanciated
    mode : str (default='w')
        Filemode used to open and write file. Should be 'a' or 'w'

    Returns
    -------
    ledger : EntityLedger
        Used EntityLedger instance, containing all the enties loaded
        from filename
    """
    # sort entities by eid
    entities = list(ledger.entities.values())
    entities.sort(key=lambda ent: ent.eid.bytes)

    as_strings = []
    to_dump = []

    ent_enc = EntityJSONEncoder()
    for ent in entities:
        try:
            as_strings.append(ent_enc.encode(ent))
        except TypeError:
            to_dump.append(ent)
            import IPython as ip
            ip.embed()
    
    if len(to_dump):
        dump_file = Path(filename).with_name('dump.txt')
        warnings.warn(f'dumped {len(to_dump)} entities to {dump_file}!')
        with dump_file.open('w') as dmp:
            for dumpee in to_dump:
                dmp.write(str(ent) + '\n')

    # make iterencoder
    with Path(filename).open(mode) as fp:
        fp.write('[\n')
        fp.write(',\n'.join(as_strings))
        fp.write('\n]')

    return ledger


def load(filename: Union[str, Path],
         factory: EntityFactory = None,
         cls: GenericEntityType = Entity) -> EntityFactory:
    """loades entities from JSON to ledger

    Parameter
    ---------
    filename : Union[str|Path]
        Path to file, where Entities in Ledger are loaded from
    factory : EntityFactory (default=None)
        EntityFactory to use for adding entities. If `None` a new one is created
    cls : GenericEntityType
        Entityclass to use

    Returns
    ------
    factory : EntityFactory
        If a factory is passed as parameter, it is returned. If `factory` was `None`
        the new `EntityFactory` instance with the loaded entities is returned
    """
    if factory is None:
        factory = EntityFactory()

    # setup decoder
    ent_dec = EntityJSONDecoder(factory=factory)

    # load from file into leadger
    with Path(filename).open('r') as fp:
        for ent_dict in json.load(fp):
            ent_dec.from_dict(ent_dict, cls=cls)

    return factory

