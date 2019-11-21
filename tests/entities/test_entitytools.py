"""Testing entitietools functions
"""
import pytest
from pathlib import Path
import numpy as np
from uuid import uuid4

from cellinspector.entities import (EntityManager, pixmap_to_json,
                                    read_into_manager)

from cellinspector.entities.entitytools import (extract_features,
                                                extract_annotations)


DUMMYPIXMAP = Path(__file__).parent / '..' / 'res' / 'testmask.png'
DUMMYJSON = Path(__file__).parent / '..' / 'res' / 'testmask_anno.json'

PXMAPDATA = [
    (DUMMYPIXMAP, 0),
    (DUMMYPIXMAP, 1),
    (DUMMYPIXMAP, 2),
    (DUMMYPIXMAP, 3),
]

@pytest.mark.parametrize('src,dil', PXMAPDATA)
def test_pixmap_conversion(src, dil, tmp_path):
    testdir = tmp_path / 'pm2json'
    testdir.mkdir()

    dst = testdir / (uuid4().hex + '.json')
    pixmap_to_json(src, dst, dilate=dil)
    
    eman = EntityManager()
    eman_out = read_into_manager(dst, eman, strip=False)
    eman_new = read_into_manager(dst, strip=True)

    assert len(eman) == 14
    assert len(eman_out) == 14
    assert len(eman_new) == 14
    assert eman is eman_out
    assert not eman is eman_new

def test_pixmap_conversion_err(tmp_path):
    with pytest.raises(ValueError):
        test_pixmap_conversion(DUMMYPIXMAP, -1, tmp_path)

def test_extract_features():
    """Testing feature extraction for correctness
    """
    eman = EntityManager()
    read_into_manager(DUMMYJSON, eman)

    features = extract_features(eman, {'dummy': DUMMYPIXMAP})
    assert all(features['id'] == features['dummy_median'])
    assert all(features['id'] == features['dummy_mean'])
    
def test_extract_annotations():
    """Testing feature extraction for correctness
    """
    eman = EntityManager()
    read_into_manager(DUMMYJSON, eman)

    annotations = extract_annotations(eman)

    assert all(annotations['id'] % 2 == annotations['eid MOD 2'])

    for _, row in annotations.iterrows():
        tag = 'eid_{}'.format(int(row['id']))
        assert row[tag] == 1
    
    tags = [name for name in annotations.columns if name.startswith('eid_')]
    assert all(annotations[tags].sum() == 1)
