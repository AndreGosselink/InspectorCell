import cv2
import pytest
import numpy as np


from cellinspector.control import Controller


def test_entity_data_check(qtbot):
    """test if mailfromed data raises errors correctly
    """
    _cont = {1: [[(0,0), (1, 0), (1, 1)]]}
    _mask = 'mask', np.array(
        [[1, 2, 2],
         [1, 2, 2],
         [0, 3, 0]],
        dtype=np.uint16)

    ctrl = Controller()
    qtbot.addWidget(ctrl.viewer)

    with pytest.raises(ValueError):
        ctrl.generateEntities(entityMask=_mask, entityContours=_cont)

    ctrl.generateEntities(entityContours=_cont)
    ctrl.generateEntities(entityMask=_mask)
