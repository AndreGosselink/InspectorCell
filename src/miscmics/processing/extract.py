"""Extract features of entities from ImageStack
"""
from typing import Dict, Callable

import cv2
import numpy as np

from ..multiplex import ImageStack
from ..entities.ledger import EntityLedger


def extract_features(ledger: EntityLedger, stack: ImageStack,
                     key: str, raise_oob: str = 'ignore',
                     oob_tag: str = 'out-of-bounds',
                     feature_functions: Dict[str, Callable] = None):
    """ Extract features of Entities in EntityLedger on ImageStack

    Parameters
    ------------
    ledger : EntityLedger
        Ledger holding entities, for which features are to be
    stack : ImageStack
        Image source from which the features are supposed to be extracted from
    key : str
        Key to use. Will iterate over all channels in stack, having this key.
        The fusion of '{key}_{value}' will be used as scalar key per entity
    raise_oob : str (default='ignore')
        Controlls how entities out of bounds are handled. Either 'ignore',
        'raise' or 'crop'. If ignored, entities will be tagged: 'out-of-bounds'
    oob_tag : str (default='out-of-bounds')
        This tag is set if `raise_oob` is not 'raise'
    feature_functions : Dict[str, Callable] (default=None)
        List of callables. Must take as arguments pixels, the ent and an ndarray
        Each function must return a float value
        If 'None' default fetures are extracted.

    Raises
    -------
    KeyError:
        If the key is in no meta data in ImageStack at all
    ValueError:
        Invalid parameters are passed
    IndexError:
        If an entity mask is out of bounds and `raise_oob` is 'raise'

    Notes
    -----
    Changes entities in ledger in place.
    """
    # raise key error if the key is not present at all in image stack
    if not key in stack.unique().keys():
        raise KeyError(f'{key} not present in stack!')

    if feature_functions is None:
        feature_functions = dict(
            mean=lambda px, *args: np.mean(px),
            sum=lambda px, *args: np.sum(px))

    if raise_oob not in ('ignore', 'crop', 'raise'):
        raise ValueError("raise_oob must be 'ignore', 'crop' or'raise'")

    # get all valid channels, having the metadata key
    channels = [ch for ch in stack.data if key in ch.meta.keys()]

    first = channels[0]
    rest = channels[1:]

    # do a first pass to select entities
    in_bound_entities = []
    for ent in ledger.entities.values():
        try:
            pixels = first[ent.slc][ent.mask]
            in_bound_entities.append(ent)
        except IndexError:
            if raise_oob == 'raise':
                msg = f'Entity {ent.eid} with boundingbox {ent.bbox} is out' +\
                      f' of bounds for {scalar_key} with shape {first.shape}'
                raise IndexError(msg)

            ent.tags.add(oob_tag)

            if raise_oob == 'ignore':
                continue
            else:
                raise NotImplementedError('No cropping yet')

        # extract features
        try:
            for feat_name, func in feature_functions.items():
                scalar_key = f'{key}_{first.meta[key]}_{feat_name}'
                ent.scalars[scalar_key] = func(pixels, ent, first)
        except Exception as err:
            msg = f'Feature function {feat_name} raised {str(err)}'
            raise ValueError(msg)
    
    for chan in rest:
        for feat_name, func in feature_functions.items():
            scalar_key = f'{key}_{chan.meta[key]}_{feat_name}'
            for ent in in_bound_entities:
                ent.scalars[scalar_key] = func(
                    chan[ent.slc][ent.mask],
                    ent,
                    chan)


