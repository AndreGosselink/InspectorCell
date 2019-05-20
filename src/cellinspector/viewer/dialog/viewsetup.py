# -*- coding: utf-8 -*-

import os

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw


class ViewSetupDialog(qw.QDialog):

    def __init__(self, callback, viewSetup, parent=None):
        """
        Paramters
        ---------
        Callback : callable
            function to call, when setup was accepted

        viewSetup : dict
            needs will be updated after accepting and used to
            updated values in gui
        """
        super().__init__(parent=parent)

        self.callback = callback

        self.vert_layout = None
        self.hor_layout = None
        self.hor_layout_2 = None
        self.form_layout = None
        self.button_box = None
        self.rows_label = None
        self.rows_count = None
        self.cols_label = None
        self.cols_count = None

        self._build_ui()

        self.viewSetup = viewSetup

    def updateGui(self):
        self.rows_count.setValue(self.viewSetup['rows'])
        self.cols_count.setValue(self.viewSetup['cols'])
        self.show_crosshair.setChecked(self.viewSetup['cross'])

    def _build_ui(self):
        self.vert_layout = qw.QVBoxLayout(self)
        self.hor_layout = qw.QHBoxLayout()
        self.hor_layout_2 = qw.QHBoxLayout()
        self.hor_layout_2.setObjectName("hor_layout_2")
        self.form_layout = qw.QFormLayout()
        self.rows_label = qw.QLabel(self)
        self.rows_label.setText('Rows:')
        self.form_layout.setWidget(0, qw.QFormLayout.LabelRole, self.rows_label)
        self.rows_count = qw.QSpinBox(self)
        self.rows_count.setObjectName("rows_count")
        self.form_layout.setWidget(0, qw.QFormLayout.FieldRole, self.rows_count)
        self.cols_label = qw.QLabel(self)
        self.cols_label.setObjectName("cols_label")
        self.cols_label.setText('Cols:')
        self.form_layout.setWidget(1, qw.QFormLayout.LabelRole, self.cols_label)
        self.cols_count = qw.QSpinBox(self)
        self.cols_count.setObjectName("cols_count")
        self.form_layout.setWidget(1, qw.QFormLayout.FieldRole, self.cols_count)

        self.crosshair_label = qw.QLabel(self)
        self.crosshair_label.setText('Crosshair')
        self.show_crosshair = qw.QCheckBox(self)
        self.show_crosshair.setChecked(False)
        self.form_layout.setWidget(2, qw.QFormLayout.LabelRole,
                                   self.crosshair_label)
        self.form_layout.setWidget(2, qw.QFormLayout.FieldRole,
                                   self.show_crosshair)

        self.hor_layout_2.addLayout(self.form_layout)
        self.hor_layout.addLayout(self.hor_layout_2)
        spacer = qw.QSpacerItem(40, 20,
                             qw.QSizePolicy.Expanding, qw.QSizePolicy.Minimum)
        self.hor_layout.addItem(spacer)
        self.vert_layout.addLayout(self.hor_layout)
        spacer1 = qw.QSpacerItem(20, 40,
                              qw.QSizePolicy.Minimum, qw.QSizePolicy.Expanding)
        self.vert_layout.addWidget(self.show_crosshair)
        self.vert_layout.addItem(spacer1)
        self.button_box = qw.QDialogButtonBox(self)
        self.button_box.setOrientation(qc.Qt.Horizontal)
        self.button_box.setStandardButtons(
            qw.QDialogButtonBox.Cancel|qw.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.vert_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.accepted.connect(self.acceptViewSetup)

        self.rows_count.setMinimum(1)
        self.cols_count.setMinimum(1)

        self.rows_count.setMaximum(4)
        self.cols_count.setMaximum(5)

    @qc.pyqtSlot()
    def acceptViewSetup(self):
        self.viewSetup['cols'] = self.cols_count.value()
        self.viewSetup['rows'] = self.rows_count.value()
        self.viewSetup['cross'] = self.show_crosshair.isChecked()

        self.callback()
