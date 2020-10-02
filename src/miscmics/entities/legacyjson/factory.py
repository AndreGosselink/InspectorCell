from typing import Type
import logging
import warnings

from pathlib import Path
import copy

from .legacyfile import read_entity_data

from ..imageentity import ImageEntity
from ..entity import (EntityType, Entity, GenericEntityType as GenericEntity)
from ..factory import EntityFactory


class LegacyEntityJSON(EntityFactory):

    def load(self, jsonfile: Path, strip: bool = False,
             cls: GenericEntity = ImageEntity):
        """Loads entities from legacy JSON file

        Parameter
        ---------
        jsonfile : [pathlib.Path|str]
            Path to JSON file containing the Entity data

        strip : bool (default=True)
            If true, all historic elements are striped from the
            dataset

        cls : Type[Entity] (default=miscmics.entities.ImageEntity)
            Class to instanciate and return. The default class is `ImageEntity`
        """
        for old_ent in read_entity_data(Path(jsonfile), strip=strip):
            new_ent = self.create_entity(cls=cls)

            # translate historic flag into state
            if old_ent['historical']:
                new_ent.etype = EntityType.Historic
            else:
                new_ent.etype = EntityType.Cell

            # translate old mask value / onject id
            # into scalar
            new_ent.scalars['object_id'] = old_ent['id']

            # copy tags
            new_ent.tags = set(old_ent['tags'])

            # translate old scalar types
            for (sc_key, sc_type), sc_value in old_ent['scalars'].items():
                if sc_type == 0:
                    new_ent.scalars[sc_key] = float(sc_value)
                else:
                    new_ent.generic[sc_key] = float(sc_value)

            contour = []
            for cont in old_ent['contour']:
                new_cont = []
                for (pt0, pt1) in cont:
                    new_cont.append([float(pt0), float(pt1)])
                contour.append(new_cont)

            try:
                new_ent.update_contour(contour)
            except ValueError:
                logging.getLogger().warn(
                    f'Invalid contour for {new_ent.eid}: {str(contour)}')
