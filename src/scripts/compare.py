"""Calculates the distance matrix between all entities in image
"""

import sys
from pathlib import Path
import warnings

from inspectorcell.entities.entitytools import (
    draw_entities, read_into_manager, simplify_contours)

from inspectorcell.util.image import getImagedata

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

import IPython as ip


one = Path('/home/rikisa/seg_318/data/segments_ago.json')
other = Path('/home/rikisa/seg_318/data/segments_niw3.json')
dapi = Path('/home/rikisa/seg_318/data/images/000_DAPIi__16bit_DF_FF_C - 2(fld 1 wv DAPI - DAPI)_subset.tif')
dapi = getImagedata(dapi).astype(float)
dapi /= dapi.max()
# one, other = other, one

one = read_into_manager(one, strip=True)
other = read_into_manager(other, strip=True)

for eman in (one, other):
    for ent in eman.iter_active():
        # ent.moveBy(20, 20)
        ent.polygon = Polygon(ent.contours[0]).simplify(
            tolerance=0.5, preserve_topology=True).buffer(0)

# faulty = []
# pairing = {}
# for ent0 in one.iter_active():
#     cur_pairs = pairing[ent0.eid] = {}
#     for ent1 in other.iter_active():
#         try:
#             if ent0.polygon.area < ent1.polygon.area:
#                 ent0, ent1 = ent1, ent0
#             if ent0.polygon.intersects(ent1.polygon):
#                 area = ent0.polygon.intersection(ent1.polygon).area
#                 ratio = area/ent1.polygon.area
#                 cur_pairs[ratio] = ent1.eid
#         except:
#             faulty.append((ent0.eid, ent1.eid))
#             print('!!', faulty[-1])
# 
# for k, v in pairing.items():
# 
#     vals = list(v.keys())
#     best = max(vals)
#     best_eid = v[best]
#     print(f'{k}: {best_eid} ({best}) <-{vals}')
# 
# ip.embed()
indices = np.dstack(np.meshgrid(np.arange(len(one)), np.arange(len(other)))).reshape(-1, 2)
entsi = [ent for ent in one.iter_active()]
entsj = [ent for ent in other.iter_active()]

def get_bound(ent, min_x=np.inf, max_x=-np.inf, min_y=np.inf, max_y=-np.inf):
    s0, s1 = ent.mask_slice
    ex0, ex1 = s0.start, s0.stop
    ey0, ey1 = s1.start, s1.stop
    min_x = min(min_x, ex0)
    max_x = max(max_x, ex1)
    min_y = min(min_y, ey0)
    max_y = max(max_y, ey1)
    return min_x, max_x, min_y, max_y

min_x = np.inf
max_x = -np.inf
min_y = np.inf
max_y = -np.inf

for ent in entsi:
    min_x, max_x, min_y, max_y = get_bound(ent, min_x, max_x, min_y, max_y)

for ent in entsj:
    min_x, max_x, min_y, max_y = get_bound(ent, min_x, max_x, min_y, max_y)

# for i, j in indices:
#     e0 = entsi[i]
#     e1 = entsi[j]
#     if e0.polygon.area < e1.polygon.area:
#         e0 = entsi[j]
#         e1 = entsi[i]
#     if e0.polygon.area == 0 or e1.polygon.area == 0: 
#         canvas[i, j] = -1
#     else:
#         canvas[i, j] = e0.polygon.intersection(e1.polygon).area / e1.polygon.area
padx = max(0, max_x - dapi.shape[0])
pady = max(0, max_y - dapi.shape[1])
canvas = np.pad(dapi, ((abs(min_x), padx), (abs(min_y), pady)), mode='constant')
canvas = (np.broadcast_to(canvas[:, :, None], canvas.shape + (3,))).copy()
for ent in entsi:
    ent.moveBy(abs(min_x), abs(min_y))
for ent in entsj:
    ent.moveBy(abs(min_x), abs(min_y))

buddies = {}
buddies_rev = {}
for ei in entsi:
    buddies[ei.eid] = []
    for ej in entsj:
        brev = buddies_rev.get(ej.eid, None)
        if brev is None:
            brev = []
            buddies_rev[ej.eid] = brev
        if ei.polygon.area < ej.polygon.area:
            e0 = ej
            e1 = ei
        else:
            e0 = ei
            e1 = ej
        if e0.polygon.area == 0 or e1.polygon.area == 0: 
            continue
        area_ratio = e0.polygon.intersection(e1.polygon).area / e1.polygon.area
        if area_ratio >= 0.70:
            buddies[ei.eid].append(ej.eid)
            brev.append(ei.eid)

for eidi, budeids in buddies.items():
    enti = one.getEntity(eidi)
    if len(buddies) == 0:
        canvas[enti.mask_slice][enti.mask] += [0, 0, 1]
    else:
        together = np.random.random(3)
        canvas[enti.mask_slice][enti.mask] += together
        for beid in budeids:
            entj = other.getEntity(beid)
            canvas[entj.mask_slice][entj.mask] += together

# canvas /= canvas.max()
# plt.imshow(canvas)
# plt.show()
single_cells = [] 
for eidi, beids in buddies.items():
    enti = one.getEntity(eidi)
    if len(buddies) == 0:
        continue
    min_x, max_x, min_y, max_y = get_bound(enti, np.inf, -np.inf, np.inf, -np.inf)
    for beid in beids:
        entj = other.getEntity(beid)
        min_x, max_x, min_y, max_y = get_bound(entj, min_x, max_x, min_y, max_y)
    w = max_x - min_x
    h = max_y - min_y
    cur = np.zeros((w, h, 3), float)
    cur += canvas[min_x:max_x, min_y:max_y, :]
    
    enti.moveBy(-min_x, -min_y)
    cur[enti.mask_slice][enti.mask] += [1, 0, 0]
    enti.moveBy(min_x, min_y)
    for beid in beids:
        entj = other.getEntity(beid)
        entj.moveBy(-min_x, -min_y)
        cur[entj.mask_slice][entj.mask] += [0, 1, 0]
        entj.moveBy(min_x, min_y)
    single_cells.append(cur)

maxh, maxw = -np.inf, -np.inf
for sc in single_cells:
    maxh = max(maxh, sc.shape[0])
    maxw = max(maxw, sc.shape[1])

column = np.asarray([np.zeros((maxh, maxw, 3)) for _ in single_cells])
for i, sc in enumerate(single_cells):
    slc = np.s_[:sc.shape[0], :sc.shape[1], :]
    column[(i,) + slc] = (sc / sc.max())

dim = int(np.ceil(np.sqrt(column.shape[0])))

f, axarr = plt.subplots(dim, dim)
for sc, ax in zip(column, axarr.ravel()):
    ax.imshow(sc)
    ax.axis('off')

plt.show()
ip.embed()
