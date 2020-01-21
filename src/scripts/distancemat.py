"""Calculates the distance matrix between all entities in image
"""

import sys
from pathlib import Path
import warnings

from inspectorcell.entities.entitytools import (
    draw_entities, read_into_manager)

from inspectorcell.entities import EntityManager, EntityFile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from shapely.geometry import Polygon
from collections import OrderedDict
from itertools import combinations
import scipy.misc as spm
import time
import struct

import IPython as ip


class DistanceMatrix():

    def __init__(self):
        self._entry_fmt = '<2h1f'
        self.dist_dict = {}

    def dump(self, fname):
        entry_fmt = self._entry_fmt
        header_txt = bytes(f'struct::{entry_fmt}::', 'ascii')
        with Path(fname).open('wb') as bfile:
            bfile.write(header_txt)
            for (k0, k1), value in self.dist_dict.items():
                packed = struct.pack(entry_fmt, k0, k1, value)
                bfile.write(packed)


    def clear(self, overwrite):
        if len(self.dist_dict):
            if not overwrite:
                raise ValueError('Overwriting...')
            else:
                self.dist_dict = {}

    def load(self, fname, overwrite=False):
        entry_fmt = '<2h1f'
        header_txt = bytes(f'struct::{entry_fmt}::', 'ascii')
        entry_bytes = struct.calcsize(entry_fmt)
        header_bytes = len(header_txt)
        self.clear(overwrite)
        with Path(fname).open('rb') as bfile:
            assert bfile.read(15) == header_txt
            packed = bfile.read(entry_bytes)
            while packed:
                k0, k1, val = struct.unpack(entry_fmt, packed)
                self.dist_dict[(k0, k1)] = val
                packed = bfile.read(entry_bytes)
        return self.dist_dict

    def calculate_for(self, entity_manager, overwrite=False):
        object_polygons = OrderedDict((ent.eid, Polygon(ent.contours[0]))\
                                      for ent in entity_manager)
        entity_combinations = combinations([ent.eid for ent in entity_manager],
                                           2)

        self.clear(overwrite)

        t0 = time.time()
        for n, comb in enumerate(1, entity_combinations):
            eid0, eid1 = comb
            self.dist_dict[comb] = object_polygons[eid0].distance(
                object_polygons[eid1])
            if n % 1000:
                print(f'\r{n}', end='')
        tn = time.time()
        dt = tn - t0
        dps = n / float(dt)
        print(f'{n} distances in {dt:.2f} s ({dps:.2f} d/s)')


root = Path('~/fileserver/R&D_Reagents/$Central_Documents',
            '1a_Studenten/Andre_Gosselink/colabsegmentation',
            'features_annotations_ovca').expanduser()
jsonf = root / 'jsons/Fld1/OvCa_Fld1_CellInspector.json'
clusf = root / 'OvCa_Fld1_CellInspector_features_log_lin_clustered.csv'
distf = root / 'distances.bin'

eman = read_into_manager(jsonf, strip=True)
dframe = pd.read_csv(clusf, skiprows=range(1, 3))

distmat = DistanceMatrix()
distmat.load(distf)

for ent in eman:
    try:
        cluster, = dframe[dframe.CellID == ent.eid].Cluster
    except ValueError:
        print('no cluster assignment for', ent.eid)
        continue
    ent.tags.add(cluster)


def neighbours_for(distmat, ent, thr):
    all_items = distmat.dist_dict.items()
    ret = []
    for key, dist in all_items:
        if ent.eid in key and dist <= thr:
            ret.append(key)
    return ret

print(neighbours_for(distmat, eman.getEntity(103)), 1)

ip.embed()
