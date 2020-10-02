"""Helperfunction to convert old style entity jsons to new dataformat
"""
import json
from pathlib import Path

from .factory import LegacyEntityJSON
from ..jsonfile import EntityJSONEncoder
from .. import ImageEntity


def convert(jsonfile, strip=True, cls=ImageEntity, outfile=None):
    """ Converts .json to .ent

    Parameter
    ---------
    jsonfile : [pathlib.Path|str]
        Path to JSON file containing the legacy Entity data

    strip : bool (default=True)
        If true, all historic elements are striped from the
        dataset

    cls : Type[Entity] (default=miscmics.entities.ImageEntity)
        Class to interprete the legacy json data. Default class is `ImageEntity`

    outfile : [pathlib.Path|str] (default=None)
        Outputfile to write converted data. If `None` (default), the `jsonfile`
        name is used and extended with .ent
    """

    jsonfile = Path(jsonfile)

    ent_facotry = LegacyEntityJSON()
    ent_facotry.load(jsonfile, strip=strip, cls=cls)

    if outfile is None:
        outfile = jsonfile.with_suffix('.ent')
    else:
        outfile = Path(outfile)

    with outfile.open('w') as dst:
        entity_list = list(ent_facotry.ledger.entities.values())
        json.dump(entity_list, dst, cls=EntityJSONEncoder)
