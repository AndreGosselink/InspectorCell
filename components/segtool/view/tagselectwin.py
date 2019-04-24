# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tagadder.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

import os, logging

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw

from ..events import GenOverlayReq, NewViewProps


class TagSelectWindow(qw.QDialog):

    accepted = qc.pyqtSignal(str, list)

    def __init__(self, tag_selection, parent=None):
        super().__init__(parent=parent)

        self.vert_layout = None
        self.available_list = None
        self.selected_list = None
        self.tag_selection = None

        self.default_tag_count = 3
        self.custom_name = False

        self._build_ui()
        self._connect()

        self.update_tag_selection(tag_selection)

    def update_tag_selection(self, tag_selection):
        self.custom_name = False
        self.tag_selection = tag_selection
        self.selected_list.clear()

        for tag in tag_selection:
            self.available_list.addItem(tag)
        self.selected_list.sortItems()

    def _connect(self):
        self.available_list.itemActivated.connect(self.selection)
        self.selected_list.itemActivated.connect(self.selection)
        self.map_name.textEdited.connect(self.custom_name_choosen)

    @qc.pyqtSlot(str)
    def custom_name_choosen(self, text):
        self.custom_name = True

    @qc.pyqtSlot()
    def selection(self):
        if self.sender() is self.available_list:
            src_list, to_list = self.available_list, self.selected_list
        else:
            to_list, src_list = self.available_list, self.selected_list

        self._swap_from_to(src_list, to_list)

        if not self.custom_name:
            self._update_tagname()

    def _update_tagname(self):
        now_selected = self._get_selected_tags()
        now_selected.sort()

        tag_count = len(now_selected)
        new_name = '_'.join(now_selected[:self.default_tag_count])
        if tag_count > self.default_tag_count:
            new_name += '+{}'.format(tag_count - self.default_tag_count)

        self.map_name.setText(new_name)

    def _swap_from_to(self, src_list, to_list):
        row_idx = src_list.currentRow()
        cur_item = src_list.takeItem(row_idx)
        tag_text = cur_item.text()
        del cur_item
        to_list.addItem(tag_text)
        to_list.sortItems()

    def _build_ui(self):
        self.setLayout(qw.QVBoxLayout())
        self.vert_layout = self.layout()

        # group boxes with lists
        gbox_avl, available_list = self._get_groupbox()
        gbox_sel, selected_list = self._get_groupbox()
        gbox_avl.setTitle('Available Tags')
        gbox_sel.setTitle('Selected Tags')

        self.available_list = available_list
        self.selected_list = selected_list

        gbox_layout = qw.QHBoxLayout()
        # gbox_layout = self.vert_layout.layout()
        gbox_layout.addWidget(gbox_avl)
        gbox_layout.addWidget(gbox_sel)

        # name box
        name_box = qw.QGroupBox(self)
        name_box.setTitle('Map name')
        hor_layout = qw.QHBoxLayout(name_box)
        self.map_name = qw.QLineEdit(name_box)
        hor_layout.addWidget(self.map_name)

        # button box
        self.button_box = qw.QDialogButtonBox(self)
        self.button_box.setOrientation(qc.Qt.Horizontal)
        self.button_box.setStandardButtons(
            qw.QDialogButtonBox.Cancel|qw.QDialogButtonBox.Ok)

        # add widgets
        self.vert_layout.addWidget(name_box)
        self.vert_layout.addLayout(gbox_layout)
        self.vert_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.accepted.connect(self.accepted_tag_selection)

    def _get_groupbox(self):
        g_box = qw.QGroupBox(self)
        hor_layout = qw.QHBoxLayout(g_box)
        text_edit = qw.QListWidget(g_box)
        hor_layout.addWidget(text_edit)
        return g_box, text_edit

    def _get_selected_tags(self):
        selected_tags = []
        selected_count = self.selected_list.count()
        for row in range(selected_count):
            cur_item = self.selected_list.item(row)
            selected_tags.append(cur_item.text())
        return selected_tags

    @qc.pyqtSlot()
    def accepted_tag_selection(self):
        """Trigger event requesting a the
        map according to the selected tags
        """
        selected_tags = self._get_selected_tags()
        map_name = self.map_name.text()
        tagmap_req = GenOverlayReq(req_type='tagmap', name=map_name,
                                   args=selected_tags)

        qc.QCoreApplication.postEvent(self.parent(), tagmap_req)
