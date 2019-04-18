# -*- coding: utf-8 -*-
from pathlib import Path
import os, logging

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw

from ..events import ModifyResReq


class TagEditWindow(qw.QDialog):

    accepted = qc.pyqtSignal(str, list)

    def __init__(self, custom_tags, parent=None):
        super().__init__(parent=parent)

        self.vert_layout = None
        self.custom_tags = None
        self.tag_list = None
        self.tag_edit = None
        self.parse_button = None

        self._build_ui()
        self._connect()

        self.last_dir = str(Path('.').absolute())

        self.update_custom_tags(custom_tags)

    def update_custom_tags(self, custom_tags):
        self.custom_tags = custom_tags
        self.tag_list.clear()

        for tag in custom_tags:
            self.tag_list.addItem(tag)
        self.tag_list.sortItems()

        self.tag_edit.setPlainText('; '.join(custom_tags))

    def _connect(self):
        self.parse_btn.clicked.connect(self._parse_edit)
        self.load_btn.clicked.connect(self._load_file)

    def _get_custom_tags(self):
        custom_tags = []
        custom_count = self.tag_list.count()
        for row in range(custom_count):
            cur_item = self.tag_list.item(row)
            custom_tags.append(cur_item.text())
        return custom_tags

    @qc.pyqtSlot()
    def _load_file(self):
        txt_path, _ = qw.QFileDialog.getOpenFileName(
            parent=None,
            caption='Select file to parse',
            directory=self.last_dir,
            filter='Plain text (*.txt)',
        )
        txt_path = Path(txt_path)
        if txt_path.exists() and str(txt_path) != '':
            self.last_dir = str(txt_path.parent)
            with txt_path.open('r') as src:
                self.tag_edit.setPlainText(src.read())
            self._parse_edit()

    @qc.pyqtSlot()
    def _parse_edit(self):
        text = self.tag_edit.toPlainText()
        tags = []
        for atag in text.split(';'):
            atag = atag.strip(' ')
            atag = atag.replace('\n', '')
            atag = atag.replace('\r', '')
            if atag == '':
                continue
            tags.append(atag)
        self.update_custom_tags(tags)

    def _build_ui(self):
        self.setLayout(qw.QVBoxLayout())
        self.vert_layout = self.layout()

        # horizontal layout for group boxes
        gbox_layout = qw.QHBoxLayout()
        # gbox_layout = self.vert_layout.layout()

        # group boxes custom tag list
        g_box = qw.QGroupBox(self)
        g_box.setTitle('Parsed Tags')
        vert_layout = qw.QVBoxLayout(g_box)
        self.tag_list = qw.QListWidget(g_box)
        vert_layout.addWidget(self.tag_list)
        gbox_layout.addWidget(g_box)

        # group boxes Tageditor
        g_box = qw.QGroupBox(self)
        g_box.setTitle('Tag Editor')
        vert_layout = qw.QVBoxLayout(g_box)
        self.tag_edit = qw.QTextEdit(g_box)
        self.parse_btn = qw.QPushButton('Parse', parent=g_box)
        self.load_btn = qw.QPushButton('Load...', parent=g_box)
        vert_layout.addWidget(self.tag_edit)
        vert_layout.addWidget(self.parse_btn)
        vert_layout.addWidget(self.load_btn)
        gbox_layout.addWidget(g_box)

        # button box
        self.button_box = qw.QDialogButtonBox(self)
        self.button_box.setOrientation(qc.Qt.Horizontal)
        self.button_box.setStandardButtons(
            qw.QDialogButtonBox.Cancel|qw.QDialogButtonBox.Ok)

        # add widgets
        self.vert_layout.addLayout(gbox_layout)
        self.vert_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.accepted.connect(self.accepted_tag_edit)

    @qc.pyqtSlot()
    def accepted_tag_edit(self):
        mod_tags = ModifyResReq('tags', self._get_custom_tags())
        qc.QCoreApplication.postEvent(self.parent(), mod_tags)
