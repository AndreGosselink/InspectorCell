# -*- coding: utf-8 -*-
"""Allows to keep track of ViewContext state
"""
import os
from pathlib import Path
import copy
import json

class ViewContext():
    """Dropin replacement for previous dict
    saves state and can be yamled
    """

    __slots__ = ['rows', 'cols', 'cross', 'backgrounds', 'enhancments',
                 'globalAlpha', 'foregrounds', '_key']

    def __init__(self, key=None):
        self._key = key

        # number of rows and colums used in the layout
        self.rows = 2
        self.cols = 2

        # crosshair
        self.cross = True

        # global alpha for entities
        self.globalAlpha = 100

        # backround image key-value-store.
        #     key: channel index
        #   value: is the image name in channel background
        #          (for look up in image repository)
        self.backgrounds = {}

        # foregounds setup key-value-store.
        #     key: channel index
        #   value: boolean, show foreground or not
        self.foregrounds = {}

        # backround image key-value-store.
        #     key: name
        #   value: enhancement values
        self.enhancments = {}

    def __getitem__(self, key):
        """Mimic dict getitem
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(str(key))

    def __setitem__(self, key, value):
        """Mimic dict setitem
        """
        if not hasattr(self, key):
            raise KeyError(str(key))
        else:
            try:
                curValue = self.__getitem__(key)
                curValue.update(value)
            except AttributeError:
                setattr(self, key, value)

    def __iter__(self):
        return ((sl, getattr(self, sl)) for sl in self.__slots__)

    def items(self):
        return iter(self)

    def update(self, other):
        for key, otherValue in other.items():
            self.__setitem__(key, otherValue)

    def toDict(self):
        ret = {'rows': self.rows,
               'cols': self.cols,
               'cross': self.cross,
               'globalAlpha': self.globalAlpha,
               'enhancments': self.enhancments,
               # 'enhancments': {str(k):v for k,v in  self.enhancments.items()},
               'backgrounds': list(self.backgrounds.items()),
               'foregrounds': list(self.foregrounds.items()),
               }
        return ret

    def fromDict(self, other):
        self.rows  = other['rows']
        self.cols  = other['cols']
        self.cross = other['cross']
        self.enhancments = other['enhancments']
        # self.enhancments = {eval(k):v for k, v in other['enhancments'].items()}
        self.backgrounds = {tuple(k):v for k, v in other['backgrounds']}
        self.foregrounds = {tuple(k):v for k, v in other['foregrounds']}

class ViewContextManager():
    """Proxis all calls to different ViewContexts
    """

    def __init__(self):
        self._trackedViews = {None: ViewContext(None)}
        self.activeView = self._trackedViews[None]
        
    @property
    def activeViewKey(self, value):
        """Controls which ViewContext is used"""
        return self.activeView._key

    @activeViewKey.setter
    def activeViewKey(self, key):
        try:
            if self.activeView._key is None:
                self.activeView = self._trackedViews.pop(None)
                self._trackedViews[key] = self.activeView
                self.activeView._key = key
            else:
                self.activeView = self._trackedViews.setdefault(
                        key, ViewContext(key))
        except TypeError:
            raise ValueError('activeViewKey must be hashable!')

    def __setitem__(self, key, value):
        self.activeView[key] = value

    def __getitem__(self, key):
        return self.activeView[key]

    def __iter__(self, *args, **kwargs):
        return iter(self.activeView)

    def __str__(self):
        ret = 'ViewSetup <{}>'.format(id(self.activeView))
        ret += '{\n'
        for key in self.activeView.__slots__:
            ret += '  {}: {}\n'.format(key, self.activeView[key])
        ret += '}'
        return ret

    def update(self, other):
        self.activeView.update(other)

    def items(self):
        return self.activeView.items()

    def save(self, sess):
        contexts = {str(k): v.toDict() for k, v in self._trackedViews.items()}
        with Path(sess).open('w') as fout:
            fout.write(json.dumps(contexts, indent=2))

    def load(self, sess):
        with Path(sess).open('r') as fin:
            cont = fin.read()

        asDict = json.loads(cont)
        for keys, dicts in asDict.items():
            try:
                key = int(keys)
            except ValueError:
                key = None

            self._trackedViews[key] = ViewContext(key)
            self.activeView = self._trackedViews[key]
            self.activeView.fromDict(dicts)
