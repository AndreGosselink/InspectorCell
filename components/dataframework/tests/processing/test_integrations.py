# -*- coding: utf-8 -*-
"""Tests for integration of fileparser and value mapper
"""

from pathlib import Path

from dataframework.processing.fsparser import FsParser, get_fsparser
from dataframework.processing.valuemapper import ValueMapper
from dataframework.processing import OMETiff


def test_maker_fn():
    """reproduce fsparser testing on same filenames
    """
    test_path = Path(
        '000_CD254__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')

    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)

    assert meta['marker'] == 'CD254'


def test_dapi_fn():
    """reproduce fsparser testing on same filenames
    """
    test_path = Path(
        '000_DAPIi__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')

    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)

    assert meta['marker'] == 'DAPIi'

def test_ome_marker_fn():
    """Test for marker containging name
    """
    test_path = Path(
        '000_EPCAM__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')

    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)

    tiff = OMETiff()
    tiff.set_metadata(marker=meta['marker'])

    assert tiff.marker == 'EPCAM'

def test_ome_dapi_fn():
    """Test for nonmatching name
    """
    test_path = Path(
        '000_DAPIi__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')

    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)

    tiff = OMETiff()
    tiff.set_metadata(marker=meta['marker'])
    
    assert tiff.marker == 'DAPIi'

def test_ome_empty():
    """Test for nonmatching name
    """
    tiff = OMETiff()
    tiff.set_metadata()

    assert tiff.marker is None
    assert tiff.tissue is None
    assert tiff.species is None

def test_dapi_fn_faulty():
    """reproduce fsparser testing on same filenames
    """
    test_path = Path(
        '000_DAPIw__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')

    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)
    
    assert meta['marker'] is None

def test_wildcard():
    """reproduce fsparser testing on same filenames
    """
    test_path = Path(
        '000_Otto__16bit_DF_FF_B - 2(fld 2 wv DAPI - DAPI).tif')
    
    FsParser._wildcards.append('Otto')
    fsp = get_fsparser()
    meta = fsp.extract_from_imagename(test_path)

    assert meta['marker'] == 'Otto'
