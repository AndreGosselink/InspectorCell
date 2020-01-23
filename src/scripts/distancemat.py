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
import networkx as nx
import logging
from functools import partial

import IPython as ip


def logwrap(logfunc):
    return partial(logfunc, logger=logging.getLogger('NH'))

@logwrap
def info(msg, *args, logger=None):
    logger.info(msg, *args)

@logwrap
def debug(msg, *args, logger=None):
    logger.debug(msg, *args)

@logwrap
def warn(msg, *args, logger=None):
    logger.warn(msg, *args)


class DistanceMatrix():

    def __init__(self):
        self._entry_fmt = '<2h1f'
        self.dist_dict = {}

    def __iter__(self):
        def _iterator():
            for k0, ref_dict in self.dist_dict.items():
                for k1, dist in ref_dict.items():
                    yield (k0, k1), dist
        return _iterator()

    def __setitem__(self, eids, val):
        k0, k1 = eids
        ref_dict = self.dist_dict.get(k0, None)
        if not ref_dict is None:
            ref_dict[k1] = val
        else:
            self.dist_dict[k0] = dict([(k1, val)])

    def _lookup(self, one, other):
        ref_dict = self.dist_dict.get(one, None)
        if not ref_dict is None:
            return ref_dict.get(other, None)
        else:
            return None

    def __getitem__(self, eids):
        one, other = eids
        val = self._lookup(one, other)

        if not val is None:
            return val
        else:
            val = self._lookup(other, one)

        if not val is None:
            return val
        elif one == other:
            return 0.0
        else:
            raise KeyError(f'No valid pair: {eids}')
        
    def dump(self, fname):
        entry_fmt = self._entry_fmt
        header_txt = bytes(f'struct::{entry_fmt}::', 'ascii')
        with Path(fname).open('wb') as bfile:
            bfile.write(header_txt)
            for k0, ref_dict in self.dist_dict.items():
                for k1, value in ref_dict.items():
                    packed = struct.pack(entry_fmt, k0, k1, value)
                    bfile.write(packed)

    def clear(self, overwrite):
        if len(self.dist_dict):
            if not overwrite:
                raise ValueError('Overwriting...')
            else:
                self.dist_dict = {}
                self._eid_lookup = None

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
                self[k0, k1] = val
                packed = bfile.read(entry_bytes)
        return self.dist_dict

    def calculate_for(self, entity_manager, overwrite=False):
        raise NotImplementedError('Fixme to ack nested dicts')
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
                logging.info(f'\r{n}', end='')
        tn = time.time()
        dt = tn - t0
        dps = n / float(dt)
        info('%d distances in %.2f s (%.2f d/s)', n, dt, dps)


logger = logging.getLogger('NH')
log_stream = logging.StreamHandler()
log_stream.setFormatter(logging.Formatter(
    '%(relativeCreated)d %(name)s %(levelname)s %(message)s'))
logger.setLevel(logging.DEBUG)
logger.addHandler(log_stream)


info('Starting')
root = Path('~/fileserver/R&D_Reagents/$Central_Documents',
            '1a_Studenten/Andre_Gosselink/colabsegmentation',
            'features_annotations_ovca').expanduser()
jsonf = root / 'jsons/Fld1/OvCa_Fld1_CellInspector.json'
clusf = root / 'OvCa_Fld1_CellInspector_features_log_lin_clustered.csv'
distf = root / 'distances.bin'

info('Creating entities')
eman = read_into_manager(jsonf, strip=True)
info('Loading cluster information')
dframe = pd.read_csv(clusf, skiprows=range(1, 3))

cluster_ids = set([])
clst_key = ('clst', 1)
invalid = set([])
for ent in eman:
    try:
        cluster, = dframe[dframe.CellID == ent.eid].Cluster
        # ent.tags.add(cluster)
        ent.scalars[clst_key] = int(cluster[1:])
        cluster_ids.add(int(cluster[1:]))
    except ValueError:
        warn('no cluster assignment for %d', ent.eid)
        ent.isActive = False
        invalid.add(ent.eid)
        continue
for inv_eid in invalid:
    assert eman.popEntity(inv_eid) == inv_eid
info('Using %d cluster: %s', len(cluster_ids), str(cluster_ids))

info('Loading distance matrix')
distmat = DistanceMatrix()
distmat.load(distf)

info('Building neighborhood graph')
graph = nx.Graph()
for ent in eman.iter_active():
    poly = Polygon(ent.contours[0])
    ppos = tuple(*poly.centroid.coords)
    props = dict(
        cluster=ent.scalars[clst_key],
        pos=ppos,)
    graph.add_node(ent.eid, **props)

for edge, dist in distmat:
    if dist <= 1:
        graph.add_edge(*edge, distance=dist)

# n0 = len(graph.nodes)
# isolated = [n for n, d in iter(graph.degree) if not d]
# graph.remove_nodes_from(isolated)
# n1 = len(graph.nodes)
# info('Removed %d nodes', n0 - n1)

info('Plotting')
f, ax = plt.subplots()
npos = {}
for node in graph.nodes:
    npos[node] = graph.nodes[node].get('pos')
nx.draw_networkx(graph, pos=npos)#, with_labels=True, ax=ax)
plt.show()

ip.embed()
