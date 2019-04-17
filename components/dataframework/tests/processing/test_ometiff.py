# -*- coding: utf-8 -*-

"""Tests for file path parser
"""

import numpy as np
from pathlib import Path
import pytest

from dataframework.processing.ometiff import OMETiff, OMExml

from conftest import (OME_TESTCASE, TIFF_TESTCASE, OME_REF, MY_OME_REF,
                      INVALID_XML_TIFF)

def test_omexml_init():
    """Tests if OME tiff is loaded correctly
    """
    omexml = OMExml()

def test_ometiff_loading():
    """Tests if OME tiff is loaded correctly
    """

    ometiff = OMETiff(OME_TESTCASE)

    assert ometiff.bit == '16'
    assert ometiff.width == 462
    assert ometiff.height == 462

def test_ometiff_setting():
    """Tests if OME tiff is set correctly
    """

    img_meta = {'bit': '16',
                'width': 462,
                'height': 462,}

    bio_meta = {'tissue': 'pancreas',
                'species': 'human',
                'marker': 'CD3',}

    full_meta = bio_meta.copy()
    full_meta.update(img_meta)

    # test setting invalid values
    ometiff = OMETiff()

    with pytest.raises(TypeError):
        ometiff.set_metadata(**full_meta)

    ometiff.set_metadata(**bio_meta)

    assert ometiff.tissue == 'pancreas'
    assert ometiff.species == 'human'
    assert ometiff.marker == 'CD3'

def test_ometiff_pixelloading():
    """tests if pixels are loaded correctly
    """

    ometiff = OMETiff()
    ometiff.load_pixeldata_from(OME_TESTCASE)

    assert not ometiff.pixel_data is None
    assert ometiff.bit == '16'
    assert ometiff.width == 462
    assert ometiff.height == 462

def test_omexml_reading_tomuch():
    """tests if ome tiff read correctly
    """
    ometiff = OMETiff()
    with pytest.raises(ValueError):
        ometiff.load(OME_REF)

def test_omexml_reading():
    """tests if ome tiff read correctly
    """
    ometiff = OMETiff()
    ometiff.read_ifds(OME_TESTCASE)
    ometiff.load(OME_TESTCASE)

    # assert ometiff.name == 'tubhiswt'
    # assert ometiff.bit == '8'
    # assert ometiff.width == 512
    # assert ometiff.height == 512

def test_omexml_reading_error():
    """tests if ome xml is parsed by ifds
    """
    ometiff = OMETiff()
    ometiff.load_pixeldata_from(OME_REF)

    # wont work because no omexml was read via ifds
    with pytest.raises(ValueError):
        ometiff.read_xml()

def test_reading_nonome():
    """tests if ome xml is parsed by ifds
    """
    ometiff = OMETiff()

    # wont work because no omexml was read via ifds
    with pytest.raises(ValueError):
        ometiff.load(TIFF_TESTCASE)

def test_omexml_generation(tmpdir):
    """tests if ome tiff is generated correctly
    """
    tiss = 'pancreas'
    spec = 'human'
    mark = 'CD115'
    name = 'AVeryCoolExperiment'
    mapping = 'ThisIsNotATest!'

    tiffdir = tmpdir.mkdir('mytiff')
    tiffpath = Path(str(tiffdir.join('my.ome.tiff')))

    ometiff = OMETiff(name=name)
    ometiff.load_pixeldata_from(OME_TESTCASE)
    original_pixeldata = ometiff.pixel_data.copy()
    ometiff.read_ifds(OME_TESTCASE)
    ometiff.set_metadata(tissue=tiss,
                         species=spec,
                         marker=mark,
                         imagemap=mapping,
                         )
    ometiff.save(tiffpath)

    reload_tiff = OMETiff(tiffpath)
    assert reload_tiff.marker == mark
    assert reload_tiff.tissue == tiss
    assert reload_tiff.species == spec
    assert reload_tiff.name == name
    assert reload_tiff.imagemap == mapping
    assert np.all(original_pixeldata == reload_tiff.pixel_data)

def test_loading_my_ometiff():
    """tests if all generated fully used ome is read correctly
    """
    ometiff = OMETiff(MY_OME_REF)

    assert ometiff.marker == 'CD115'
    assert ometiff.tissue == 'pancreas'
    assert ometiff.species == 'human'
    assert ometiff.name == 'AVeryCoolExperiment'
    assert ometiff.xml.filename == Path('my_ref.ome.tiff')
    assert ometiff.xml.endianess == '<' == ometiff._byte_order
    assert ometiff.interleaved
    assert ometiff.sigbit == '12'
    assert ometiff.bit == '16'
    assert ometiff.smplperpx == '1'
    assert ometiff.pixel_data_origin == MY_OME_REF

def test_load_noneomexml_butfs():
    """test loading an image that does not have valid omexml but
    fs descriptor
    """
    ometiff = OMETiff()
    with pytest.raises(ValueError):
        ometiff.load(INVALID_XML_TIFF)
