import sys

from AnyQt import QtWidgets as qw

from .control import Controller


def runApp():
    app = qw.QApplication([])
    ctrl = Controller()
    
    ctrl.viewer.setGridlayout(2, 2)
    
    ctrl.viewer.show()
    
    sys.exit(app.exec())

