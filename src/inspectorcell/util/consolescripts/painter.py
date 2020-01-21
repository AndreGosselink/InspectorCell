"""Paints entities with cluster number
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


def get_colorpicker(dframe, mapping):
    red = np.array([1, 0, 0], float)
    black = np.array([0, 0, 0], float)
    grey = np.array([.3, .3, .3], float)
    def colorpicker(entity):
        rmask = dframe['CellID'] == entity.eid
        try:
            tag, = dframe[rmask]['Cluster']
        except ValueError:
            msg = 'Could not find ID {} in table'
            warnings.warn(msg.format(entity.eid))
            return red

        return mapping.get(tag, grey)

    return colorpicker


root = Path('~/fileserver/R&D_Reagents/$Central_Documents',
            '1a_Studenten/Andre_Gosselink/colabsegmentation',
            'features_annotations_ovca').expanduser()
jsonf = root / 'jsons/Fld1/OvCa_Fld1_InspectorCell.json'
clusf = root / 'OvCa_Fld1_InspectorCell_features_log_lin_clustered.csv'

dframe = pd.read_csv(clusf, skiprows=range(1, 3))

eman = read_into_manager(jsonf, strip=True)

mapping = dict(C1=np.array([70, 190, 250], float), # (Fibroblasts)
               C2=np.array([237, 70, 47], float), # (Ki-67+ tumor)
               C3=np.array([170, 242, 43], float), # (Tumor)
               C4=np.array([245, 174, 50], float), # (Endothelium)
               C5=np.array([255, 255, 0], float), # (Plasma cells)
               C6=np.array([255, 0, 255], float), # (Myeloid cells)
               C7=np.array([0, 255, 255], float), # (NKs)
               C8=np.array([128, 0, 255], float), # (CD4+ T cells)
               C9=np.array([0, 128, 255], float), # (CD25+ CD4+ T cells)
               C10=np.array([255, 223, 128], float), # (CD8+ T cells)
)
img = np.zeros((2100, 2100, 3), float)

draw_entities(img, eman, get_colorpicker(dframe, mapping))
# plt.imshow(img)
# plt.show()

pic = Image.fromarray(np.round(img[:2048,:2048]).astype(np.uint8), mode='RGB')
pic.save(clusf.with_name(clusf.name + '.png'))
