# -*- coding: utf-8 -*-

"""Tests for the abid.xlsx/abid.csv parser and the helperfunctions
"""


from pathlib import Path
import numpy as np
import pytest

from dataframework.processing.csv2db import (AbIdCSVreader, filter_valid,
                               parse_gensymbol)


def test_valid_abids():
    """Test valid abids
    """
    parser = AbIdCSVreader()

    valid_abids = (
        'ab0012',
        'xyz0012',
        'abc00000012',
        'abc1000',
        )

    for vabid in valid_abids:
        parsed_abid = parser.parse_abid(vabid)
        assert vabid == parsed_abid


def test_invalid_abids():
    """Test invalid abids
    """
    parser = AbIdCSVreader()

    invalid_abids = (
        '0012',
        '0012xyz',
        'abc00000012xyz',
        'ab00012,ab00013',
        'ab00012;ab00013',
        )

    for ivabid in invalid_abids:
        with pytest.raises(ValueError):
            parser.parse_abid(ivabid)

def test_missing_abids():
    """Test valid abids
    """
    parser = AbIdCSVreader()

    missing = (
        None,
        np.nan
        )

    for miss in missing:
        parsed_abid = parser.parse_abid(miss)
        assert parsed_abid is None

def test_valid_filter_mix():
    """Test the global validation filter
    for invalid values
    """
    invalid = [
        'ab',
        '12',
        '3a',
        '9)',
        float('nan'),
        np.nan,
        None,
        ]

    valid = [
        'GOOD VAL)',
        'ab00012,ab00013',
        'ab00012;ab00013',
        'None',
        ]

    values_mix = invalid + valid

    filtered = filter_valid(values_mix)
    assert filtered == valid

def test_valid_filter_invalid():
    """Test the global validation filter
    for invalid values
    """
    values_mix = (
        'ab',
        '12',
        '3a',
        '9)',
        float('nan'),
        np.nan,
        None,
        )

    filtered = filter_valid(values_mix)
    assert filtered == []

def test_gensymbol_parser():
    """Test gensymbol parsing
    """
    gensym_pairs = [
        ('"a;b"', []), #invlaid length, dissmissed by global filter
        ('"None;"', ['None']),
        ('"abc"', ['abc']),
        ('abcd', ['abcd']),
        ('ab00012,ab00013', ['ab00012,ab00013']),
        ('ab00012;ab00013', ['ab00012', 'ab00013']),
        ('"ab00012;ab00013"', ['ab00012', 'ab00013']),
        ]
    
    for in_str, out_list in gensym_pairs:
        assert parse_gensymbol(in_str) == out_list

def test_species_parser_valid():
    """Test species parsing
    """

    parser = AbIdCSVreader()

    valid = [
        ('human', ['human']),
        ('Human', ['human']),
        ('HUMAN,mouse', ['human', 'mouse']),
        ('other,Mouse', ['other', 'mouse']),
        ('RAT,Mouse', ['rat', 'mouse']),
        ('non-human primate', ['non-human primate']),
        ('non-human primate ', ['non-human primate']),
        ('HUMAN , mouse', ['human', 'mouse']),
        (' HUMAN , mouse ', ['human', 'mouse']),
        (' human ', ['human']),
        ]
    
    for in_str, out_list in valid:
        assert out_list == parser.parse_species(in_str)

def test_species_parser_invalid():
    """Test species parsing for invlaid inputs
    """
    parser = AbIdCSVreader()

    invalid = ['otto', 'HUMAN;mouse',  'HUMAN ; mouse ']

    for in_str in invalid:
        with pytest.raises(ValueError):
            parser.parse_species(in_str)

def test_antigen_parser():
    """Test antigen parser with and wihtout alternatives
    """
    parser = AbIdCSVreader()

    pairs = [
        ('bjka', ['bjka']),
        ('CD134', ['CD134']),
        ('CD134(OTTTO)', ['CD134', 'OTTTO']),
        ('CD134 (OTTTO, bernd)', ['CD134', 'OTTTO, bernd']),
        ('CD134(Ben)amin)', ['CD134', 'Ben)amin']),
        ('CD134 (Ben)amin)', ['CD134', 'Ben)amin']),
        ('ABC (A(B)C)', ['ABC', 'A(B)C']),
        ('ABC (A(BZ)', ['ABC', 'A(BZ']),
        (u'ABCα (A(BZ)', [u'ABCα', 'A(BZ']),
        (u' ABCα  (A(BZ) ', [u'ABCα', 'A(BZ']),
        (u'ABC XYZ (A(BZ)', ['ABC XYZ', 'A(BZ']),
        ]

    for in_str, out_list in pairs:
        assert out_list == parser.parse_antigen(in_str)
