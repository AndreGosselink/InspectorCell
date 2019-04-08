# -*- coding: utf-8 -*-

import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
import PyQt5.QtWidgets as qw


class ContrastEnhanceWin(qw.QDialog):

    def __init__(self, img_item=None, enhancer=None, parent=None):
        super().__init__(parent=parent)
        self.resize(255, 267)

        self.img_item = img_item
        self.enhancer = enhancer

        self._build_ui()
        self._connect()

    def _get_adjust_slide(self, parent, value=0xffff, vmin=0,
                          vmax=0xffff, step=10, page=100):
        layout = qw.QHBoxLayout()
        label = qw.QLabel(parent)

        slider = qw.QSlider(parent)
        slider.setMinimum(vmin)
        slider.setMaximum(vmax)
        slider.setSingleStep(step)
        slider.setPageStep(page)
        slider.setOrientation(qc.Qt.Horizontal)
        slider.setProperty('value', value)

        box = qw.QSpinBox(parent)
        box.setMinimum(vmin)
        box.setMaximum(vmax)
        box.setSingleStep(step)
        box.setProperty('value', value)

        layout.addWidget(slider)
        layout.addWidget(box)

        slider.valueChanged.connect(box.setValue)
        box.valueChanged.connect(slider.setValue)

        return label, layout, slider

    def _get_adjust_box(self):
        gbox = qw.QGroupBox(self)
        gbox.setTitle('AutoAdjust')

        min_label, min_layout, min_slide = self._get_adjust_slide(gbox, value=0)
        min_label.setText('Min')

        max_label, max_layout, max_slide = self._get_adjust_slide(gbox,
                                                                  value=0xffff)
        max_label.setText('Max')

        # apply_label = qw.QLabel(gbox)
        # apply_label.setText('Apply')
        # apply_box = qw.QCheckBox(gbox)

        apply_auto = qw.QPushButton('Auto', parent=gbox)

        form = qw.QFormLayout(gbox)
        form.setWidget(0, qw.QFormLayout.LabelRole, min_label)
        form.setLayout(0, qw.QFormLayout.FieldRole, min_layout)

        form.setWidget(1, qw.QFormLayout.LabelRole, max_label)
        form.setLayout(1, qw.QFormLayout.FieldRole, max_layout)

        # form.setWidget(2, qw.QFormLayout.LabelRole, apply_label)
        # form.setWidget(2, qw.QFormLayout.FieldRole, apply_box)

        form.setWidget(3, qw.QFormLayout.LabelRole, apply_auto)

        gbox.min_slide = min_slide
        gbox.max_slide = max_slide
        # gbox.apply = apply_box
        gbox.auto = apply_auto

        return gbox

    def _get_clahe_box(self):
        gbox = qw.QGroupBox(self)
        gbox.setTitle('CLAHE')

        win_label = qw.QLabel(gbox)
        win_label.setText('Size')
        win_box = qw.QSpinBox(gbox)
        win_box.setMinimum(8)
        win_box.setMaximum(512)
        win_box.setSingleStep(8)

        clip_label = qw.QLabel(gbox)
        clip_label.setText('Clip')
        clip_box = qw.QDoubleSpinBox(gbox)
        clip_box.setMaximum(100.0)
        clip_box.setSingleStep(0.1)
        clip_box.setProperty('value', 2.0)

        # apply_label = qw.QLabel(gbox)
        # apply_label.setText('Apply')
        # apply_box = qw.QCheckBox(gbox)

        form = qw.QFormLayout(gbox)
        form.setWidget(0, qw.QFormLayout.LabelRole, win_label)
        form.setWidget(0, qw.QFormLayout.FieldRole, win_box)

        form.setWidget(1, qw.QFormLayout.LabelRole, clip_label)
        form.setWidget(1, qw.QFormLayout.FieldRole, clip_box)

        form.setWidget(2, qw.QFormLayout.LabelRole, apply_label)
        form.setWidget(2, qw.QFormLayout.FieldRole, apply_box)

        gbox.win_size = win_box
        gbox.clip = clip_box
        # gbox.apply = apply_box

        return gbox

    def _build_ui(self):

        self.vert_layout = qw.QVBoxLayout(self)
        self.setLayout(self.vert_layout)

        self.adjust = self._get_adjust_box()
        # self.clahe = self._get_clahe_box()

        self.button_box = qw.QDialogButtonBox(self)
        self.button_box.setOrientation(qc.Qt.Horizontal)
        self.button_box.setStandardButtons(qw.QDialogButtonBox.Ok)

        self.vert_layout.addWidget(self.adjust)
        # self.vert_layout.addWidget(self.clahe)
        self.vert_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)

    def _connect(self):
        self.adjust.min_slide.valueChanged.connect(self._adjust)
        self.adjust.max_slide.valueChanged.connect(self._adjust)
        self.adjust.auto.clicked.connect(self._adjust_auto)
    
    @qc.pyqtSlot()
    def _adjust(self):
        # if not self.adjust.apply.checkState():
        #     return

        img = self.img_item
        enhancer = self.enhancer

        min_value = self.adjust.min_slide.value()
        max_value = self.adjust.max_slide.value()

        enhancer.adjust_from = (min_value, max_value)
 
        lut = enhancer.get_scaling_lut()
        if not lut is None:
            img.setLookupTable(lut, update=True)

    @qc.pyqtSlot()
    def _adjust_auto(self):
        img = self.img_item
        enhancer = self.enhancer
        
        enhancer.adjust_from = enhancer.get_autobounds(img.image)

        self.set_controls()

        self._adjust()
        
    def set_controls(self):
        min_value, max_value = self.enhancer.adjust_from
        self.adjust.min_slide.setValue(min_value)
        self.adjust.max_slide.setValue(max_value)

