"""Testing tiff functionality
"""


from pathlib import Path
from io import BytesIO
import struct
import pytest
import math
import numpy as np
import cv2

from conftest import get_mocktiff, OME_TESTCASE, OME_REF, ORIENTATION_REF

from dataframework.processing.tiff import (TiffImage, BuffReader, IFDEntry, IFD,
                                           RawImage)


def test_orientation(tmpdir):
    """generate mock image and check if shapes/width/height/orientation
    is correct.
    """
    img = RawImage()
    img.load_pixeldata_from(ORIENTATION_REF)

    assert img.width == 512
    assert img.height == 256
    assert img.shape == (256, 512)
    assert img.shape == img.pixel_data.shape
    assert img.pixel_data_origin == ORIENTATION_REF

    left_upper = np.s_[0:3, 0:3]
    right_upper = np.s_[0:3, 509:512]
    left_lower = np.s_[253:256, 0:3]
    right_lower = np.s_[253:256, 509:512]

    assert np.all(img.pixel_data[left_upper] == 7710)
    assert np.all(img.pixel_data[right_upper] == 15420)
    assert np.all(img.pixel_data[left_lower] == 0)
    assert np.all(img.pixel_data[right_lower] == 23130)

def test_tiffelement():
    """Test basic binary operations
    """
    buf = BytesIO()

    cafe_string = struct.pack('<4s', b'cafe')
    cafe_hex = struct.pack('<3B', 0, 202, 254)

    # default starting
    buf.seek(59)
    buf.write(cafe_hex)

    buf.seek(3)
    buf.write(cafe_string)
    buf.seek(3)

    tiffel = BuffReader()
    tiffel.use('<', buf)

    # testing if the BuffReader Continues where left of
    ret_string, = tiffel.read_bytes('4s')
    ret_hex = tiffel.read_bytes('2B', 60)

    assert ret_hex == (202, 254)
    assert ret_string == b'cafe'
    assert buf.tell() == 62

def test_ifd_entry_val():
    """Test ifd_entries for ifd contained values
    """
    entry_bytes = struct.pack('<2HI1f', 269,
                              11, 1, 3.1415926)
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes)
    assert ifd.content_offset is None
    assert abs(ifd.content - 3.1415) <= 0.0001
    assert ifd.content_num == 1
    assert ifd.content_fmt == '<1f'
    assert len(ifd) == 4
    assert ifd.tag == 'DocumentName'

    entry_bytes = struct.pack('<2HI4B', 269,
                              1, 3, *bytearray(b'\x10\x12\x13\xab'))
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes)
    assert ifd.content_offset is None
    assert ifd.content_num == 3
    assert ifd.content_fmt == '<3B'
    assert np.all(ifd.content == [v for v in b'\x10\x12\x13'])
    assert len(ifd) == 3
    assert ifd.tag == 'DocumentName'

    entry_bytes = struct.pack('<2HI4B', 270,
                              1, 1, *bytearray(b'\x2A\xbe\xef\xab'))
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes)
    assert ifd.content_fmt == '<1B'
    assert ifd.content_num == 1
    assert ifd.content_offset is None
    assert ifd.content == 42
    assert len(ifd) == 1
    assert ifd.tag == 'ImageDescription'

def test_ifde_wrong_byteorder():
    """Test ifd_entries for wrong offsets
    """
    entry_bytes = struct.pack('>2HII', 269, 11, 10, 10)
    ifd = IFDEntry()

    with pytest.raises(KeyError):
        ifd.from_bytes(entry_bytes)

    with pytest.raises(KeyError):
        ifd.from_bytes(entry_bytes, byte_order='<')

    assert ifd.tag is None
    ifd.from_bytes(entry_bytes, byte_order='>')
    assert not ifd.tag is None

def test_ifd_entry_offset():
    """Test ifd_entries for offsetted values
    """
    # ten floats
    entry_bytes = struct.pack('>2HII', 269, 11, 10, 10)
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes, byte_order='>')
    assert ifd.content is None
    assert ifd.content_fmt == '>10f'
    assert len(ifd) == 40
    assert ifd.tag == 'DocumentName'
    assert ifd.content_offset == 10

    # one double
    entry_bytes = struct.pack('<2HII', 269, 12, 1, 42)
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes)
    assert ifd.content is None
    assert ifd.content_num == 1
    assert ifd.content_offset == 42
    assert ifd.content_fmt == '<1d'
    assert len(ifd) == 8
    assert ifd.tag == 'DocumentName'

    # several doubles somewhere else
    entry_bytes = struct.pack('<2HII', 269, 12, 1, 0xffffff)
    ifd = IFDEntry()
    ifd.from_bytes(entry_bytes)
    assert ifd.content is None
    assert ifd.content_offset == 0xffffff
    assert ifd.content_fmt == '<1d'
    assert len(ifd) == 8
    assert ifd.tag == 'DocumentName'

def test_ifd():
    """Test ifd tiff element
    """
    buf, ifd0_offset, ifd1_offset = get_mocktiff(
        byte_order='>')

    ifd0 = IFD('>', buf)
    ifd0.read(offset=ifd0_offset)

    ifd1 = IFD('>', buf)
    ifd1.read(offset=ifd1_offset)

    assert ifd0.entries[0].tag == 'XPosition'
    assert ifd0.entries[1].content == -0.5
    assert ifd0.entries[2].content_type == 'SHORT'

    assert ifd1.entries[0].content == 0.5
    assert ifd1.entries[1].tag == 'GrayResponseCurve'
    assert ifd1.entries[2].content_num == 2
    assert ifd1.entries[2].content_len == 2
    assert ifd1.entries[3].content_len == 10

def test_ifd_fin():
    """test finalization of tiff elements
    """
    buf, ifd0_offset, ifd1_offset = get_mocktiff(
        byte_order='>')

    ifd0 = IFD('>', buf)
    ifd0.read(offset=ifd0_offset)

    ifd1 = IFD('>', buf)
    ifd1.read(offset=ifd1_offset)

    assert ifd0.entries[0].content == 0.5
    assert ifd0.entries[1].content == -0.5
    assert np.all(ifd0.entries[2].content == [i*2 for i in range(20)])


def test_eof_eoifd():
    """tests if the file stops after last IFD
    """
    byo = '>'

    buf, first_ifd_off, _ = get_mocktiff(byo)

    ifd0 = IFD(byo, buf)
    ifd0.read(offset=first_ifd_off)

    ifd1 = IFD(byo, buf)
    ifd1.read(offset=ifd0.next_offset)

    assert ifd1.next_offset == 0

def test_tiffimage():
    """Integration test of all components
    """
    tiff = TiffImage()
    tiff.read_ifds(OME_TESTCASE)

    assert len(tiff.ifds) == 1
    assert len(tiff.ifds[0].entries) == 16

def test_ifdentry_final():
    """tests if the file stops after last IFD
    """

    ifd = IFDEntry()
    assert not ifd.finalized

    not_fin = struct.pack('<2HII', 270, 4, 2, 100)
    ifd.from_bytes(not_fin)
    assert not ifd.finalized

    fin = struct.pack('<2HII', 270, 4, 1, 0)
    ifd.from_bytes(fin)
    assert ifd.finalized

    cont = list(range(10))
    fin = struct.pack('<2HII', 270, 4, 10, 696)
    ifd.from_bytes(fin)
    ifd.set_content(struct.pack('<10I', *cont))
    assert ifd.finalized
    assert np.all(ifd.content == cont)

def test_ifd_content():
    """test content processing
    """

    buf, ifd0_offset, ifd1_offset = get_mocktiff(
        byte_order='<')

    ifd0 = IFD('<', buf)
    ifd0.read(offset=ifd0_offset)

    ifd1 = IFD('<', buf)
    ifd1.read(offset=ifd1_offset)

    assert ifd0.entries[0].content == 0.5
    assert ifd0.entries[1].content == -0.5
    assert np.all(ifd0.entries[2].content == [i*2 for i in range(20)])

    assert ifd1.entries[0].content == 0.5
    assert np.all(ifd1.entries[2].content == [42, 42])
    assert ifd1.entries[3].content == 'READ THIS!'

    for i, val in enumerate([math.sin(i/10.0) for i in range(-40, 40)]):
        diff = abs(ifd1.entries[1].content[i] - val)
        assert diff < 1e-7

def test_omeloading():
    """test if ome tiff ifds can be loaded
    """
    t0 = TiffImage()
    t0.read_ifds(OME_TESTCASE)

    t1 = TiffImage()
    t1.read_ifds(OME_REF)

def test_asciiprocessing():
    """test if ome tiff ifds can be loaded
    """
    tiff0 = TiffImage()
    tiff0.read_ifds(OME_TESTCASE)
    string0 = tiff0.ifds[0]['ImageDescription']
    assert string0.encode()[-1] != 0

    tiff1 = TiffImage()
    tiff1.read_ifds(OME_REF)
    string1 = tiff1.ifds[0]['Software']
    assert string1.encode()[-1] != 0

def test_shape_consistency(tmpdir):
    """test if ome tiff ifds can be loaded
    """
    height = 22
    width = 54

    mock_dir = tmpdir.mkdir('mock')
    mock_file = mock_dir.join('0_CD3_mock.tif')
    mock_dat = np.round(np.random.random(height*width) * 0xffff)
    mock_dat = mock_dat.astype(np.uint16).reshape(height, width)
    cv2.imwrite(str(mock_file), mock_dat)

    # test ifd_reading first
    # init
    test_tiff = TiffImage()
    assert test_tiff.shape == (None, None)
    # from ifd
    test_tiff.read_ifds(str(mock_file))
    assert test_tiff.shape == (height, width)
    # from pixeldata but ifd for real
    test_tiff.load_pixeldata_from(str(mock_file))
    assert test_tiff.shape == (height, width)

    # test pixeldata reading first
    # init
    test_tiff = TiffImage()
    assert test_tiff.shape == (None, None)
    # from pixeldata
    test_tiff.load_pixeldata_from(str(mock_file))
    assert test_tiff.shape == (height, width)
    # from ifd
    test_tiff.read_ifds(str(mock_file))
    assert test_tiff.shape == (height, width)

def test_data_reshape(tmpdir):
    """test if ome tiff ifds can be loaded
    """
    height0 = 22
    width0 = 54

    height1 = 16
    width1 = 32

    mock_dir = tmpdir.mkdir('mock')
    mock_file = mock_dir.join('0_CD3_mock.tif')
    mock_dat = np.round(np.random.random(height0*width0) * 0xffff)
    mock_dat = mock_dat.astype(np.uint16).reshape(height0, width0)
    cv2.imwrite(str(mock_file), mock_dat)

    # test ifd_reading first
    # init
    test_tiff = TiffImage()
    assert test_tiff.shape == (None, None)

    test_tiff.read_ifds(str(mock_file))
    test_tiff.load_pixeldata_from(str(mock_file))

    # reshape data
    test_tiff.pixel_data = test_tiff.pixel_data[:height1, :width1]

    assert test_tiff.shape == (height1, width1)
    ifd = test_tiff.ifds[0]
    assert ifd['ImageWidth'] == width1
    assert ifd['ImageLength'] == height1
