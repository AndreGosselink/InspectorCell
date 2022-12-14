"""Some controller integration tests
"""
from pathlib import Path

import cv2
import pytest
import numpy as np

from inspectorcell.control import Controller


def testEntityDataGen(qtbot):
    """test if mailfromed data raises errors correctly
    """
    path = np.array([[0, 0], [0, 5], [5, 5], [5, 0]])
    cont = [(10, [path])]
    mask = np.array(
        [[1, 2, 2],
         [1, 2, 2],
         [0, 3, 0]],
        dtype=np.uint16)

    ctrl = Controller()
    qtbot.addWidget(ctrl.viewer)

    with pytest.raises(ValueError):
        ctrl.generateEntities(entityMask=mask, entityContours=cont)

    # ctrl.generateEntities(entityContours=cont)
    ctrl.generateEntities(entityMask=mask)

def test_entity_data_integration_mask(qtbot):
    """test mask generation integrates nicely
    """
    mask = np.array(
        [[0, 0, 1, 0, 0],
         [0, 1, 1, 0, 0],
         [0, 1, 1, 1, 1],
         [0, 1, 1, 1, 0],
         [0, 1, 1, 1, 0],
         [0, 0, 1, 1, 0]],
        dtype=np.uint16)

    ctrl = Controller()
    qtbot.addWidget(ctrl.viewer)

    ctrl.generateEntities(entityMask=mask)

    ctrl.entityManager.lookupEntity(objectId=1)

    e = ctrl.entityManager.lookupEntity(objectId=1)
    assert not e is None # relevant integration test

    # Also testing entit manager here
    assert e.mask_slice == (slice(0, 6, None), slice(1, 5, None))
    assert np.all(e.mask == mask[0:6, 1:5])

def test_entity_data_integration_contour(qtbot):
    """test contour generation integrates nicely
    """
    path = np.array([[0, 0], [0, 5], [5, 5], [5, 0]])
    cont = [(5, [path]),
            (6, [path]),
            (7, [path])]

    ctrl = Controller()
    qtbot.addWidget(ctrl.viewer)

    ctrl.generateEntities(entityContours=cont)

    assert not ctrl.entityManager.lookupEntity(objectId=5) is None
    e = ctrl.entityManager.lookupEntity(objectId=7)

    # Also testing entit manager here
    assert e.mask.shape == (6, 6)


def test_entity_data_integration_mask_path(qtbot):
    """test mask generation integrates nicely
    """
    test_mask_path = Path('./tests/res/testmask.png')

    ctrl = Controller()
    qtbot.addWidget(ctrl.viewer)

    ctrl.generateEntities(entityMaskPath=test_mask_path)

    assert len(ctrl.entityManager)
