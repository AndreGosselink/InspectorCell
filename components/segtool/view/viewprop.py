# -*- coding: utf-8 -*-

import os, logging

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw


class PropWindow(qw.QDialog):

    accepted = qc.pyqtSignal(dict)

    def __init__(self, view_props, parent=None):
        super().__init__(parent=parent)

        self.vert_layout = None
        self.hor_layout = None
        self.hor_layout_2 = None
        self.form_layout = None
        self.button_box = None
        self.rows_label = None
        self.rows_count = None
        self.cols_label = None
        self.cols_count = None

        self.view_props = view_props.copy()

        self._build_ui()
        self._set_previous()

    def _set_previous(self):
        self.rows_count.setValue(self.view_props['rows'])
        self.cols_count.setValue(self.view_props['cols'])

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
        self.hor_layout_2.addLayout(self.form_layout)
        self.hor_layout.addLayout(self.hor_layout_2)
        spacer = qw.QSpacerItem(40, 20,
                             qw.QSizePolicy.Expanding, qw.QSizePolicy.Minimum)
        self.hor_layout.addItem(spacer)
        self.vert_layout.addLayout(self.hor_layout)
        spacer1 = qw.QSpacerItem(20, 40,
                              qw.QSizePolicy.Minimum, qw.QSizePolicy.Expanding)
        self.vert_layout.addItem(spacer1)
        self.button_box = qw.QDialogButtonBox(self)
        self.button_box.setOrientation(qc.Qt.Horizontal)
        self.button_box.setStandardButtons(
            qw.QDialogButtonBox.Cancel|qw.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.vert_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.accepted.connect(self.accept_view_props)

        self.rows_count.setMinimum(1)
        self.cols_count.setMinimum(1)

        self.rows_count.setMaximum(4)
        self.cols_count.setMaximum(5)

    @qc.pyqtSlot()
    def accept_view_props(self):
        self.view_props['cols'] = self.cols_count.value()
        self.view_props['rows'] = self.rows_count.value()
        self.accepted.emit(self.view_props.copy())


