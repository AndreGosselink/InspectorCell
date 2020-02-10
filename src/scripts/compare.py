"""Calculates the distance matrix between all entities in image
"""

import sys
from pathlib import Path
import warnings

from inspectorcell.entities.entitytools import (
    draw_entities, read_into_manager, simplify_contours)

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

one = read_into_manager(one, strip=True)
other = read_into_manager(other, strip=True)

for eman in (one, other):
    for ent in eman.iter_active():
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
canvas = np.zeros((len(one), len(other)))
indices = np.dstack(np.meshgrid(np.arange(len(one)), np.arange(len(other)))).reshape(-1, 2)
print(indices[:10, :])
entsi = [ent for ent in one.iter_active()]
entsj = [ent for ent in other.iter_active()]
for i, j in indices:
    e0 = entsi[i]
    e1 = entsi[j]
    if e0.polygon.area < e1.polygon.area:
        e0 = entsi[j]
        e1 = entsi[i]
    if e0.polygon.area == 0 or e1.polygon.area == 0: 
        canvas[i, j] = -1
    else:
        canvas[i, j] = e0.polygon.intersection(e1.polygon).area / e1.polygon.area

plt.imshow(canvas)
plt.show()
