import pytest
import numpy as np

from dataframework.processing.tiff import TiffImage, IFDEntry, IFD
from io import BytesIO

import IPython as ip


def test_writing():
    """test the writing
    """
    byo = '<'
    buf = BytesIO()

    ifd = IFD(byte_order=byo, buf_interface=buf)

    entr01 = IFDEntry() 
    entr01.from_values(content=[1, 2, 3, 4, 65555], byte_order=byo,
        tag='ColorMap', content_type='LONG', offset=512)

    entr0 = IFDEntry() 
    entr0.from_values(content=1, byte_order=byo,
        tag='ImageLength', content_type='SHORT')

    entr1 = IFDEntry() 
    entr1.from_values(content=5, byte_order=byo,
        tag='ImageWidth', content_type='SHORT')

    entr2 = IFDEntry() 
    entr2.from_values(content=45054, byte_order=byo,
        tag='YPosition', content_type='LONG')

    entr3 = IFDEntry() 
    entr3.from_values(content='Das ist ein Test, diggi',
        byte_order=byo, tag='ImageDescription',
        content_type='ASCII', offset=1337)

    ifd.append(entr01)
    ifd.append(entr0)
    ifd.append(entr1)
    ifd.append(entr2)
    ifd.append(entr3)

    ifd.use(byte_order=byo, buf_interface=buf)
    ifd.write(offset=7)

def test_entry_setting_nums():
    """test the writing
    """
    byo = '<'
    entrl0 = IFDEntry() 
    entrl0.from_values(content=1, byte_order=byo,
        tag='ColorMap', content_type='SHORT', offset=0)

    assert entrl0.content_len == 2
    assert entrl0.content_num == 1

    entrl1 = IFDEntry() 
    entrl1.from_values(content=[1, 2, 3, 4, 65555], byte_order=byo,
        tag='ColorMap', content_type='LONG', offset=512)

    assert entrl1.content_len == 4 * 5
    assert entrl1.content_num == 5


def test_entry_setting_ascii():
    byo = '<'
    entrs0 = IFDEntry() 
    entrs0.from_values(content='a', byte_order=byo,
        tag='ColorMap', content_type='ASCII', offset=None)

    assert entrs0.content_len == 1
    assert entrs0.content_num == 1

    entrs1 = IFDEntry() 
    entrs1.from_values(content='abcdefghijx', byte_order=byo,
        tag='ColorMap', content_type='ASCII', offset=0)

    assert entrs1.content_len == 11
    assert entrs1.content_num == 11


def test_missing_offset():
    byo = '<'
    entrs0 = IFDEntry() 
    with pytest.raises(ValueError):
        entrs0.from_values(content='abcdefg', byte_order=byo,
            tag='ColorMap', content_type='ASCII', offset=None)


def test_forth_back():
    """test the writing and reading again
    """
    byo = '<'

    buf = BytesIO()
    tests = [
        ([i for i in range(10)], 'LONG', 100),
        ([i*2 for i in range(20)], 'SHORT', 200),
        ('Affen µsen durch den Wald', 'ASCII', 300),
        ('A', 'ASCII', None),
        ([1, 3, 4, 5], 'LONG', 50),
        ([3.14, 1.45, 4.0, 6], 'FLOAT', 150),
        (3, 'BYTE', None),
        ([24, 42], 'SHORT', None),
    ]

    for cont, typ, off in tests:
        if off is None:
            set_off = 1000
        else:
            set_off = off

        new_entry = IFDEntry()
        new_entry.from_values(content=cont,
                              tag='ImageDescription',
                              offset=set_off,
                              byte_order=byo,
                              content_type=typ,)

        ent_by, cont_by = new_entry.to_bytes(byte_order=byo)
        re_entry = IFDEntry()
        re_entry.from_bytes(ent_by)
        if not cont_by is None:
            re_entry.set_content(cont_by)
        
        if not typ is 'FLOAT':
            assert str(re_entry) == str(new_entry)
        else:
            assert re_entry.content_num == new_entry.content_num
            assert re_entry.content_len == new_entry.content_len
            assert np.sum(re_entry.content - new_entry.content) / \
                   len(new_entry.content) <= 0.00001

def test_entries_fromvalues():
    """test the writing and reading again
    """
    byo = '<'
    ifd_offset = 10
    
    # different contents with different lens
    contents = [
        1,
        [10, 1],
    ]
    types = ['SHORT', 'BYTE']
    
    for i, typ in enumerate(types):
        for j, cont in enumerate(contents):
            try:
                cnum = len(cont)
            except TypeError:
                cnum = 1

            new_entry = IFDEntry()
            new_entry.from_values(content=cont,
                                  tag='ImageDescription',
                                  offset=10,
                                  byte_order=byo,
                                  content_type=typ,)

            assert new_entry.tag == 'ImageDescription'
            assert new_entry.content_offset == None
            assert 1 <= new_entry.content_len <= 4
            assert new_entry.content_num == cnum
            assert np.all(new_entry.content == cont)

def test_entries_fromvalues_off():
    """test the writing and reading again
    """
    byo = '<'
    # different contents with different lens
    tests = [
        ([i for i in range(10)], 'LONG'),
        ([i*2 for i in range(20)], 'SHORT'),
        ('Affen µsen durch den Wald', 'ASCII'),
    ]
    
    for i, (cont, typ) in enumerate(tests):
        off = (i+1) * 10
        cnum = len(cont)

        new_entry = IFDEntry()
        new_entry.from_values(content=cont,
                              tag='ImageDescription',
                              offset=off,
                              byte_order=byo,
                              content_type=typ,)

        assert new_entry.tag == 'ImageDescription'
        assert new_entry.content_offset == off
        assert new_entry.content_len > 4
        assert new_entry.content_num == cnum
        if not typ == 'ASCII':
            assert np.all(new_entry.content == cont)
        else:
            assert new_entry.content == cont

def test_ifd_forth_back():
    """test the writing and reading again
    """
    byo = '<'
    ifd_offset = 10
    buf = BytesIO()

    tests = [
        ([i for i in range(10)], 'LONG', 100),
        ([i*2 for i in range(20)], 'SHORT', 200),
        ('Affen µsen durch den Wald', 'ASCII', 300),
        ([1, 3, 4, 5], 'LONG', 400),
        ('A', 'ASCII', None),
        (3, 'BYTE', None),
        ([24, 42], 'SHORT', None),
    ]
    
    ifd = IFD(byte_order=byo, buf_interface=buf)
    for cont, typ, off in tests:
        new_entry = IFDEntry()
        ifd.append(new_entry)
        new_entry.from_values(content=cont,
                              tag='ImageDescription',
                              offset=off,
                              byte_order=byo,
                              content_type=typ,)

    ifd.write(offset=ifd_offset)

    re_ifd = IFD(byte_order=byo, buf_interface=buf)
    re_ifd.read(offset=ifd_offset)

    assert str(ifd) == str(re_ifd)

