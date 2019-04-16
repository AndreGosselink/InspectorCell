# -*- coding: utf-8 -*-
import contextlib
import shutil
import tempfile
import pandas as pd

import PyQt5.QtCore as qc
from dataframework import ImgObj


class CallBack(qc.QObject):

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        ret = '{}\n{}\n{}\n{}\n'
        self_str = super().__str__()
        return ret.format(self_str, self.func, self.args, self.kwargs)

    def __call__(self, *args, **kwargs):
        args = self.args + args
        kwargs.update(self.kwargs)
        ret = self.func(*args, **kwargs)
        return ret


@contextlib.contextmanager
def get_tempdir():
    """Creates an temporary dir within a contect
    ensures execution of the deletion statement
    when with statemen ends
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

def parse_orange(csv_path):
    """Extracts tag information from orange file
    """
    dframe = pd.read_csv(csv_path, sep=',')
    update_list = []
    for _, row in dframe.iterrows():
        try:
            objid = int(float(row.ObID))
        except ValueError:
            continue
        new_object = ImgObj(objid)
        new_object.tags = set([str(row.Cluster)])
        update_list.append(new_object)

    return update_list
