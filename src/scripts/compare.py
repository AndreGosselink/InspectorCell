"""Calculates the distance matrix between all entities in image
"""

import sys
from pathlib import Path
import warnings
from itertools import combinations

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


def modify_ents(eman, pad):
    """Creates polygons and adds them as attribute
    inplace
    """
    for ent in eman.iter_active():
        ent.moveBy(pad, pad)
        ent.polygon = Polygon(ent.contours[0]).simplify(
            tolerance=0.5, preserve_topology=True).buffer(0)
    return eman

def get_image(img_path, pad):
    dapi = getImagedata(img_path).astype(float)
    dapi /= dapi.max()
    canvas = np.pad(dapi, ((pad, pad), (pad, pad)), mode='constant')
    return (np.broadcast_to(canvas[:, :, None], canvas.shape + (3,))).copy()

def overlay(img, eman, rgb):
    """overlays eman additively in img with color rgb
    """
    img = img.copy()
    for ent in eman:
        img[ent.mask_slice][ent.mask] += rgb

    return img

def match(eman0, eman1, thr):
    """matches entities in the eman. adds them inplace
    """
    for ent0 in eman0:
        ent0.matches = []
    for ent1 in eman1:
        ent1.matches = []

    for ent0 in eman0:
        for ent1 in eman1:
            if ent0.polygon.intersects(ent1.polygon):
                areai = ent0.polygon.intersection(ent1.polygon).area
                # skip line only intersections
                if areai == 0:
                    continue
                area0 = ent0.polygon.area
                area1 = ent1.polygon.area
                if areai / area0 > thr or areai / area1 > thr:
                    ent0.matches.append(ent1)
                    ent1.matches.append(ent0)

def sc_agreement(ent0, ent1):
    s0 = ent0.scalars
    s1 = ent1.scalars
    if not s0 and not s1:
        return 1
    if not s0:
        return 0
    if not s1:
        return 0
    all_keys = set(list(s0.keys()) + list(s1.keys()))
    pos0 = [s0.get(k, -1) > 0 for k in all_keys]
    pos1 = [s1.get(k, -1) > 0 for k in all_keys]
    return sum(int(p0 == p1) for p0, p1 in zip(pos0, pos1)) / len(all_keys)

def quanti_stats(ents):
    agreement = []
    for eman in ents:
        man_agree = []
        for ent in eman:
            assert sc_agreement(ent, ent) == 1
            ent_agree = []
            for ment in ent.matches:
                ent_agree.append(sc_agreement(ent, ment))
            if ent_agree == []:
                if ent.scalars == {}:
                    continue
                else:
                    man_agree.append(0)
                    continue
            man_agree.append(sum(ent_agree) / len(ent_agree))
        agreement.append(sum(man_agree) / len(man_agree))
    return agreement

def matching_stats(emans):
    data = dict(
        unique_seg=[sum([1 for ent in eman if not len(ent.matches)])\
                    for eman in emans],
        matched_seg=[sum([1 for ent in eman if len(ent.matches)])
                     for eman in emans],
        total_seg=[len(eman) for eman in emans],)
    data['agree_seg'] = [m / t for t, m in zip(data['total_seg'],
                         data['matched_seg'])]
    data['agree_marker'] = quanti_stats(emans)
    return data

root = Path('/home/andre/seg318')
json_dir = root / 'jsons'
img_dir = root / 'images'
padding = 10

jloader = lambda path: modify_ents(
    read_into_manager(path, strip=True), pad=padding)
entry_maker = lambda path: (path.name.split('.')[0].split('_')[1], jloader(path))

jsons = dict(entry_maker(path) for path in json_dir.glob('*.json'))

indices = list(enumerate(jsons.keys()))
seg_agree = np.zeros((len(indices), len(indices)))
marker_agree = seg_agree.copy()

for (i, key0), (j, key1) in combinations(indices, 2):
    eman0 = jsons[key0]
    eman1 = jsons[key1]
    match(eman0, eman1, 0.5)
    stats_fwd = matching_stats([eman0, eman1])
    seg_agree[i, j] = stats_fwd['agree_seg'][0]
    marker_agree[i, j] = stats_fwd['agree_marker'][0]
    seg_agree[j, i] = stats_fwd['agree_seg'][1]
    marker_agree[j, i] = stats_fwd['agree_marker'][1]

# the diag
for ij, key01 in indices:
    eman01 = jsons[key01]
    match(eman01, eman01, 0.5)
    stats_fwd = matching_stats([eman01, eman01])
    seg_agree[ij, ij] = stats_fwd['agree_seg'][0]
    marker_agree[ij, ij] = stats_fwd['agree_marker'][0]

cols = [k for _, k in indices]
excelwriter = pd.ExcelWriter(root / 'agreement.xlsx')
pd.DataFrame(data=marker_agree, columns=cols).to_excel(excelwriter, startcol=0)
pd.DataFrame(data=seg_agree, columns=cols).to_excel(excelwriter, startcol=10)
excelwriter.save()
excelwriter.close()
