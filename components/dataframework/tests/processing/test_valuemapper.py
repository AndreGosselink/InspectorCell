# -*- coding: utf-8 -*-

"""Testing for ValueMapper
"""

import pytest

from dataframework.processing.valuemapper import ValueMapper


def test_none_error_conv():
    """test for convinience methods
    """
    valm = ValueMapper()

    with pytest.raises(TypeError):
        valm.valid_species()

    with pytest.raises(TypeError):
        valm.valid_tissue()

    with pytest.raises(TypeError):
        valm.valid_bit()

def test_none_error_valid():
    """test for convinience methods
    """
    valm = ValueMapper()

    with pytest.raises(TypeError):
        valm.validate(mapping='species')

def test_species_valid():
    """test chekcing of valid names or keys
    """
    valm = ValueMapper()

    valid_names = ['human', 'mouse', 'non-human primate', 'other', 'rat']
    validations = [valm.valid_species(name=name) for name in valid_names]
    assert all(validations)

    # from all defined values in the 8 bit ranges, some must be valid
    id_validations = [valm.valid_species(key=2**i) for i in range(8)]
    assert any(id_validations)

def test_species_invalid():
    """test chekcing of invalid names or keys
    """
    valm = ValueMapper()

    invalid_names = ['Human', 'moUse', 'otto', 'bern', '1234']
    validations = [not valm.valid_species(name=name) for name in invalid_names]

    assert all(validations)

    # from all defined values in the 8 bit ranges, some must be valid
    id_validations = [not valm.valid_species(key=2**i) for i in \
            (8, 10, 14, 15, 30)]
    assert all(id_validations)

def test_species_valid_mapping():
    """test if the mapping checker works
    """
    valm = ValueMapper()

    assert valm.valid_species('human', 0)

def test_species_invalid_mapping():
    """test if the mapping checker works for invlaid input
    """
    valm = ValueMapper()

    assert not valm.valid_species('human', 2**1)

def test_species_validate_errors():
    """test if the mapping checker works for invlaid input
    """
    valm = ValueMapper()

    # no key or name
    with pytest.raises(TypeError):
        valm.validate(mapping='species')

    # wrong name/key pair, invalid mapping
    with pytest.raises(ValueError):
         valm.validate('human', 2**1, 'otto')

    # correct name/key pair, invalid mapping
    with pytest.raises(ValueError):
         valm.validate('human', 0, 'otto')

    # correct name/key pair, no mapping
    with pytest.raises(ValueError):
         valm.validate('human', 0)

def test_bit():
    """test if bits are correctly checked
    """
    valm = ValueMapper()

    assert not valm.valid_bit(8)
    assert not valm.valid_bit(16)
    assert not valm.valid_bit(12)
    assert not valm.valid_bit(32)

    assert valm.valid_bit('8')
    assert valm.valid_bit('16')
