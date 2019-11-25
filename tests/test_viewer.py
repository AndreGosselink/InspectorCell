"""Test ViewContext integration
"""
import pytest

from inspectorcell.viewer import ViewContext
from inspectorcell.datamanager import DataManager
from inspectorcell.entities import EntityManager

from AnyQt.QtGui import QPainterPath
from AnyQt.QtCore import QRectF, QPoint


def _setup(qtbot):
    contours = [
        (1, [[(10, 10),
              (20, 10),
              (20, 20),
              (10, 20),]]),

        (2, [[(15, 15),
              (25, 15),
              (25, 25),
              (15, 25),]]),
    ]

    # setup
    eman = EntityManager()
    eman.generateFromContours(contours)
    dman = DataManager()
    viewer = ViewContext(dataManager=dman, entityManager=eman)
    viewer.setGridlayout(1, 1)
    qtbot.addWidget(viewer)
    qtbot.waitForWindowShown(viewer)
    qtbot.mouseMove(viewer, QPoint(12, 12))

    # add entities
    for ent in eman:
        viewer.addEntity(ent)

    # selecte and assure that they are selected
    sel = QPainterPath()
    sel.addRect(QRectF(14, 14, 16, 16))
    viewer.entity_scn.setSelectionArea(sel)
    assert len(viewer.entity_scn.selectedItems()) == 2

    return eman, dman, viewer


def test_gfx_merge(qtbot):
    """Test integration for ViewContext, ViewContextScene and Entity
    """

    eman, _, viewer = _setup(qtbot)
    viewer.entity_scn.merge()

    assert len(eman) == 3
    hist = [ent for ent in eman if ent.historical]
    active = [ent for ent in eman if not ent.historical]
    assert len(hist) == 2
    assert len(active) == 1

    ref = set([(10, 10),
               (20, 10),
               (10, 20),
               (15, 20),
               (20, 15),
               (25, 15),
               (25, 25),
               (15, 25),])

    pt = set(tuple(p) for p in active[0].contours[0])

    assert pt == ref

def test_viewcontext_integration(qtbot):
    """Test if ViewContextManager works and Dialogs
    """
    eman, _, viewer = _setup(qtbot)
    diag = viewer.dialogs['viewSetup']

    viewer.showViewSetupDialog()
    qtbot.waitForWindowShown(diag)

    cur_rows = viewer.viewSetup['rows']
    cur_cols = viewer.viewSetup['cols']

    new_rows = min(cur_rows + 1, 4)
    new_cols = min(cur_cols + 1, 4)

    assert new_cols != cur_cols
    assert new_rows != cur_rows

    # manipulate the values
    diag.rows_count.setValue(new_rows)
    diag.cols_count.setValue(new_cols)
    diag.acceptViewSetup()

    assert viewer.viewSetup['rows'] == new_rows
    assert viewer.viewSetup['cols'] == new_cols
