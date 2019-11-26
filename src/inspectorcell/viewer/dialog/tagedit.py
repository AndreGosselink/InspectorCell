# -*- coding: utf-8 -*-

from pathlib import Path
import os, logging

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw


class TagEditDialog(qw.QDialog):

    def __init__(self, callback, currentTags, parent=None):
        """
        Paramters
        ---------
        Callback : callable
            function to call, when setup was accepted

        currentTags : set SHARED
            all the tags already there

        Notes
        -----
        Will modify currentTags and then trigger callback
        """
        super().__init__(parent=parent)

        # shared object
        self.currentTags = currentTags

        self.callback = callback

        self._buildUi()

    def updateGui(self):
        self._updateFields(self.currentTags)

    def _updateFields(self, tags):
        self.tagList.clear()
        tags = list(tags)
        tags.sort()
        for lineNo, tag in enumerate(tags, 1):
            if lineNo <= 10:
                tag = '{: >2d} {}'.format(lineNo, tag)
            else:
                tag = '   {}'.format(tag)
            self.tagList.addItem(tag)

        # self.tagList.sortItems()
        # for aTag in tags:
        #     lnoTags.append(aTag)

        self.tagEdit.setPlainText('\n'.join(tags))

    @qc.pyqtSlot()
    def _loadFile(self):
        txtPath, _ = qw.QFileDialog.getOpenFileName(
            parent=None,
            caption='Select file to parse',
            # directory=self.last_dir,
            filter='Plain text (*.txt)',
        )
        txtPath = Path(txtPath)
        if txtPath.exists() and str(txtPath) != '':
            with txtPath.open('r') as src:
                self.tagEdit.setPlainText(src.read())
            self._parseEdit()

    @qc.pyqtSlot()
    def _parseEdit(self):
        text = self.tagEdit.toPlainText()
        text = text.replace(';', '<<BREAK>>')
        text = text.replace('\n', '<<BREAK>>')
        parsedTags = []
        for atag in text.split('<<BREAK>>'):
            atag = atag.strip(' ')
            atag = atag.replace('\n', '')
            atag = atag.replace('\r', '')
            if atag == '':
                continue
            parsedTags.append(atag)
        self._updateFields(parsedTags)

    def _buildUi(self):
        self.setLayout(qw.QVBoxLayout())
        self.vertLayout = self.layout()

        # horizontal layout for group boxes
        gboxLayout = qw.QHBoxLayout()
        # gbox_layout = self.vert_layout.layout()

        # group boxes custom tag list
        gBox = qw.QGroupBox(self)
        gBox.setTitle('Parsed Tags')
        vertLayout = qw.QVBoxLayout(gBox)
        self.tagList = qw.QListWidget(gBox)
        vertLayout.addWidget(self.tagList)
        gboxLayout.addWidget(gBox)

        # group boxes Tageditor
        gBox = qw.QGroupBox(self)
        gBox.setTitle('Tag Editor')
        vertLayout = qw.QVBoxLayout(gBox)
        self.tagEdit = qw.QTextEdit(gBox)
        self.parseBtn = qw.QPushButton('Parse', parent=gBox)
        self.loadBtn = qw.QPushButton('Load...', parent=gBox)
        vertLayout.addWidget(self.tagEdit)
        vertLayout.addWidget(self.parseBtn)
        vertLayout.addWidget(self.loadBtn)
        gboxLayout.addWidget(gBox)

        # button box
        self.buttonBox = qw.QDialogButtonBox(self)
        self.buttonBox.setOrientation(qc.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            qw.QDialogButtonBox.Cancel|qw.QDialogButtonBox.Ok)

        # add widgets
        self.vertLayout.addLayout(gboxLayout)
        self.vertLayout.addWidget(self.buttonBox)

        # connect elements
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.buttonBox.accepted.connect(self.acceptedTagEdit)

        self.parseBtn.clicked.connect(self._parseEdit)
        self.loadBtn.clicked.connect(self._loadFile)

    def _getTags(self):
        tags = []
        tagCount = self.tagList.count()
        for row in range(tagCount):
            curItem = self.tagList.item(row)
            lnoTag = curItem.text()
            tag = lnoTag[3:]
            tags.append(tag)
        return set(tags)

    @qc.pyqtSlot()
    def acceptedTagEdit(self):
        self.currentTags.clear()
        self.currentTags.update(self._getTags())
        self.callback()
