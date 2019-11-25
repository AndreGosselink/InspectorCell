
# -*- coding: utf-8 -*-
"""
All viewer related events to prevent proxies, singletons and/or a mix thereof
implemented to confine the view elements in the view only
"""
from pathlib import Path

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw


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
            tid = qc.QEvent.registerEventType(tid)
            cls._type_ids[subcls] = tid
        return tid


class ActiveEntity(BaseEvent):

    def _init(self, entity, isActive, rect=None):
        """entity: data connected with event
        isActive: leaving or entering the representation
        rect: boundingbox of representation
        """
        self.entity = entity
        self.isActive = isActive
        self.rect = rect


class ScalarAssignmentChanged(BaseEvent):

    def _init(self, change):
        """change that occured
        """
        self.change = change


class ResetZoomEvent(BaseEvent):

    def _init(self, autorange):
        """change that occured
        """
        self.autorange = autorange


class ZoomEvent(BaseEvent):

    def _init(self, zoomIn=True):
        self.zoomIn = zoomIn


class EntityChangedEvent(BaseEvent):

    def _init(self, entity):
        self.entity = entity
