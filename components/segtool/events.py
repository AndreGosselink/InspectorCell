# -*- coding: utf-8 -*-
"""
All viewer related events to prevent proxies, singletons and/or a mix thereof
implemented to confine the view elements in the view only
"""
from pathlib import Path

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw


class BaseEvent(qc.QEvent):

    _type_ids = {}
    type_id = -1

    def __eq__(self, other):
        try:
            return self.type_id == other.type_id
        except AttributeError:
            return False

    def __new__(cls, *args, **kwargs):
        cls.type_id = cls._get_typeid(cls)
        new_instance = super().__new__(cls, cls.type_id)
        return new_instance

    def __init__(self, *args, **kwargs):
        super().__init__(self.type_id)
        self._init(*args, **kwargs)

    def _init(self):
        pass

    @classmethod
    def _get_typeid(cls, subcls):
        tid = cls._type_ids.get(subcls, None)
        if tid is None:
            tid = len(cls._type_ids) + 1001
            cls._type_ids[subcls] = tid
        return tid


class ErrorEvent(BaseEvent):

    def _init(self, msg):
        self.msg = msg


class LoadResReq(BaseEvent):

    def _init(self, res_type, res_path=None, res_pathes=None):
        self.res_type = res_type
        if not res_path is None:
            self.res_path = str(Path(res_path).absolute())
        if not res_pathes is None:
            abs_path = [str(Path(path).absolute()) for path in res_pathes]
            self.res_pathes = abs_path


class SaveResReq(BaseEvent):

    def _init(self, res_type, res_path=None, res_pathes=None):
        self.res_type = res_type
        if not res_path is None:
            self.res_path = str(Path(res_path).absolute())
        if not res_pathes is None:
            abs_path = [str(Path(path).absolute()) for path in res_pathes]
            self.res_pathes = abs_path


class ModifyResReq(BaseEvent):

    def _init(self, res_type, modification):
        self.res_type = res_type
        self.modification = modification


class ReposUpdated(BaseEvent):

    def _init(self, repos, wipe=True, roi=False):
        #TODO add a safety wrapper if a functionptr gets voidptr
        self.repos = repos
        self.wipe = wipe
        self.roi = roi


class NewViewProps(BaseEvent):

    def _init(self, view_props):
        #TODO add a safety wrapper if a functionptr gets voidptr
        self.view_props = view_props.copy()


class GenOverlayReq(BaseEvent):

    def _init(self, req_type='', args=(), name=''):
        self.req_type = req_type
        self.args = args
        self.name = name


class ModifyView(BaseEvent):

    def _init(self, mod_type, modification):
        self.mod_type = mod_type
        self.modification = modification
