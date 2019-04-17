# -*- coding: utf-8 -*-

"""Test shared data
"""

from pathlib import Path
from io import BytesIO
import struct
import math
import numpy as np


RES_PATH = Path(__file__).parents[1] / 'res'


SOME_LARGE_IMG = RES_PATH / 'some_large'
MANY_SMALL_IMG = RES_PATH / 'scaled_paca'
SOME_SMALL_IMG = RES_PATH / 'some_small'

INVALID_XML_DIR = RES_PATH / r'errornous'
INVALID_XML_TIFF = INVALID_XML_DIR / r'058_HLA-DQ_noneXMLImageDesc.tif'

ORIENTATION_REF = RES_PATH / r'256x512-30-60-90.tiff'

MY_OME_REF = RES_PATH / r'ometiffs/my_ref.ome.tiff'
FS_TIF_REF = RES_PATH / (r'007_CD45ROV11.PE_16bit_CROP.tif')


NAME_PATTERN_PAIRS = [('dfag', 'dfag'),
                      ('12dfag', '12dfag'),
                      (' 12dfag', '12dfag'),
                      ('12 dfag', '12.dfag'),
                      ('12dfag43', '12dfag43'),
                      ('dfag43', 'dfag43'),
                      ('dfa.g43', r'dfa\.g43'),
                      ('dfa.g43 ', r'dfa\.g43'),
                      (r'CD13/CD16', r'CD13.CD16'),
                      ('dfag3', 'dfag3'),
                      ('6dfag', '6dfag'),
                      ('fas?dafs', r'fas[a-z]dafs'),
                      ('xazα', 'xaz[a-z]'),
                      ('xαazα', 'x[a-z]az[a-z]'),
                      (' xαazα ', 'x[a-z]az[a-z]'),
                      ('x(az', r'x.az'),
                      ('x)az', r'x.az'),
                      ('x[az', r'x.az'),
                      ('x]az', r'x.az'),
                      (r'x\az', r'x.az'),
                      (r'x/az', r'x.az'),
                      (r'x|az', r'x.az'),
                      (r'TCRβVβ3.2', r'TCR[a-z]V[a-z]3\.2'),
                      (r'TCR-V/3.2', r'TCR.V.3\.2'),
                      (r'TNF-?', r'TNF.[a-z]'),
                      (r'TCR-V\/3\.2', r'TCR.V..3.\.2'),
                      (r'CD158e1/e2', r'CD158e1.e2'),
                      (r'CD140b pY857', r'CD140b.pY857'),
                     ]

test_in_file = Path(r'./res/scaled_paca/002_CD8V11.PE_16bit_DF_FF_CORR_B - '+\
                     '2(fld 1 wv Cy3 - Cy3 wix 1).tif')
test_out_file = Path(r'./res/ometiffs/converted.ome.tiff')
OME_TESTCASE = Path(r'./res/ometiffs/testcase_ref.ome.tiff')
OME_REF = Path(r'./res/ometiffs/tubhiswt.ome.tif')
MY_OME_REF = Path(r'./res/ometiffs/my_ref.ome.tiff')
TIFF_TESTCASE = Path(r'./res/test.tif')


def get_mocktiff(byte_order='<'):
    """generates buffer filled with a tiff, with two ifds
    and nonsense data
    """
    byo = byte_order # shorthand
    entry_head = byte_order + '2HI'
    buf = BytesIO()

    # make a header...
    # ...endianess
    if byo == '<':
        buf.write(b'II')
    elif byo == '>':
        buf.write(b'MM')
    # ...magic number
    buf.write(struct.pack(byo + 'H', 42))
    ifd0_offset_addr = buf.tell()

    # delimite header (leave four bytes for first ifd offset)
    buf.write(b'\xbe\xef\xbe\xef<<<HEADER END>>>')

    # my datablock 0
    buf.write(b'<<<DATABLOCK 02 START>>>')
    e02_offset = buf.tell()
    e02_data = [i*2 for i in range(20)]
    e02_len = len(e02_data)
    buf.write(struct.pack(byo + '{}H'.format(e02_len), *e02_data))
    buf.write(b'<<<DATABLOCK 02 END>>>')

    # generate some entries for first ifd
    e00 = struct.pack(entry_head + 'f', 286, 11, 1, 0.5)
    e01 = struct.pack(entry_head + 'f', 287, 11, 1, -0.5)
    e02 = struct.pack(entry_head + 'I', 288, 3, e02_len, e02_offset)
    # write first ifd
    buf.write(b'<<<IFD 0 START>>>')
    ifd0_offset = buf.tell()
    buf.write(struct.pack(byo + 'H', 3))
    buf.write(e00)
    buf.write(e01)
    buf.write(e02)
    ifd1_offset_addr = buf.tell()
    # (leave four bytes for ifd1 offset)
    buf.write(b'\xbe\xef\xbe\xef<<<IFD 0 END>>>')

    # my datablock 1
    buf.write(b'<<<DATABLOCK 11 START>>>')
    e11_offset = buf.tell()
    e11_data = [math.sin(i/10.0) for i in range(-40, 40)]
    e11_len = len(e11_data)
    buf.write(struct.pack(byo + '{}f'.format(e11_len), *e11_data))
    buf.write(b'<<<DATABLOCK 11 END>>>')

    # inline data
    e12_data = bytearray(b'\x2a\x2a\xff\xff')
    e13_data = bytearray(b'READ THIS!')

    # generate some entries for second ifd
    e10 = struct.pack(entry_head + 'f', 290, 11, 1, 0.5)
    e11 = struct.pack(entry_head + 'I', 291, 11, e11_len, e11_offset)
    e12 = struct.pack(entry_head + '4B', 272, 1, 2, *e12_data)
    e13 = struct.pack(entry_head + '4B', 270, 2, len(e13_data),
                      *bytearray(b'\xbe\xef\xbe\xef'))
    # write second ifd
    buf.write(b'<<<IFD 1 START>>>')
    ifd1_offset = buf.tell()
    # test enclosing
    buf.seek(ifd1_offset + 2 + (4 * 12))
    buf.write(b'\x00\x00\x00\x00<<<IFD 1 END>>>') # (0x00000000 for last ifd)
    # end the file
    buf.write(b'<<<DATABLOCK 13 START>>>')
    e13_offset = buf.tell()
    buf.write(e13_data)
    buf.write(b'<<<DATABLOCK 13 END>>>')

    buf.seek(ifd1_offset)
    # number of entries
    buf.write(struct.pack(byo + 'H', 4))
    buf.write(e10)
    buf.write(e11)
    buf.write(e12)
    buf.write(e13)
    e13_data_offset_addr = buf.tell() - 4
    # ifd was finished before
 
    # set remaining offsets
    # e13
    buf.seek(e13_data_offset_addr)
    buf.write(struct.pack(byo + 'I', e13_offset))

    # ifd0
    buf.seek(ifd0_offset_addr)
    buf.write(struct.pack(byo + 'I', ifd0_offset))
    # ifd1
    buf.seek(ifd1_offset_addr)
    buf.write(struct.pack(byo + 'I', ifd1_offset))

    buf.seek(0)
    return buf, ifd0_offset, ifd1_offset

def pretty_print(buf):
    """pretty prints the buffer content
    """
    def pp_line(addr0, vals, asc=False, end='\n'):
        pre = hex(addr0).split('x')[-1]
        pre = '{:0>8}:'.format(pre)
        cont = []
        for val in vals:
            if 33 <= val <= 126 and asc:
                cont.append('  ' + chr(val))
            else:
                cont.append(' {:0>2}'.format(hex(val).split('x')[-1]))
        wspaces = len(pre)
        cont_str = ''
        cur_line = pre
        for c in cont:
            if len(cur_line) >= 75:
                cont_str += cur_line
                cur_line = '\n' + (' ' * wspaces)
            cur_line += c
        cont_str += cur_line

        print(cont_str, end=end)

    def pp_ifd(offset, bytevals):
        pp_line(offset, bytevals[:2])
        bytevals = bytevals[2:]
        offset += 2
        while len(bytevals) > 4:
            pp_line(offset, bytevals[:12])
            bytevals = bytevals[12:]
            offset += 12
        pp_line(offset, bytevals, end='\t\t\t\t# next IFD addr\n')

    buf.seek(0)
    bytevals = buf.read()
    buf.seek(0)

    # pp header
    pp_line(0, bytevals[0:4])
    pp_line(4, bytevals[4:8], end='   # IFD0 offset\n')

    splits = bytevals.split(b'<<<')
    elements = []
    for spl in splits:
        if b'START' in spl or b'END' in spl:
            elements.append(b'<<<' + spl)
        else:
            elements.append(spl)

    header = elements[0]
    addr = len(header)
    elements = elements[1:]
    in_ifd = False
    for elm in elements:
        if elm.startswith(b'<<<') and elm.endswith(b'>>>'):
            addr += len(elm)
            print(elm.decode('ascii'))
            if b'IFD' in elm and b'START' in elm:
                in_ifd = True
            elif b'IFD' in elm and b'END' in elm:
                in_ifd = False

        elif elm.startswith(b'<<<'):
            debug_tag, bytevals = elm.split(b'>>>')
            debug_tag += b'>>>'
            print(debug_tag.decode('ascii'))
            addr += len(debug_tag)
            if b'IFD' in debug_tag and b'START' in debug_tag:
                in_ifd = True
            elif b'IFD' in debug_tag and b'END' in debug_tag:
                in_ifd = False

            if not in_ifd:
                pp_line(addr, bytevals)
            else:
                pp_ifd(addr, bytevals)

            addr += len(bytevals)

def get_object_data():
    """generate a fake object map
    """
    ret = np.zeros((50, 50), dtype='uint16')
    obj0 = np.s_[5:10, 5:10]
    obj1 = np.s_[-10:-5, -10:-5]
    ret[obj0] = 1
    ret[obj1] = 2
    return obj0, obj1, ret.copy()

if __name__ == '__main__':
    pretty_print(get_mocktiff('>')[0])
