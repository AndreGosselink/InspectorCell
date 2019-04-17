# -*- coding: utf-8 -*-

"""Tests for file path parser
"""

from pathlib import Path

from dataframework.processing.fsparser import FsParser, get_fsparser
from conftest import NAME_PATTERN_PAIRS


def get_testing_parser():
    """Get the testing FsParser
    """
    return get_fsparser()

def test_fsparser_nopath():
    """Test if error is rased when invlaid
    input path is used
    """
    fsp = get_testing_parser()

    meta = fsp.extract_from_imagename(r'NotAPath//\\')
    for _, val in meta.items():
        assert val is None

def test_fsparser_validpath():
    """Test if error is rased when invlaid
    input path is used
    """
    fsp = get_testing_parser()

    meta = fsp.extract_from_imagename(r'NotAPath//\\')
    for _, val in meta.items():
        assert val is None

def test_valid_imagenames():
    """testing on generic tiff names
    """
    fsp = get_testing_parser()

    full_templates = [
        '010_{marker:} V5.PE_{bit:}bit_DF_x 1).tif',
        '042_{marker:}V2,5.PE_{bit:}bit_DFix1).tif',
        '080_{marker:}_V2,5.PE_{bit:}bit_Dx 1).tif',
        ]

    marker_templates = [
        '028_{marker:} V5.PE_afas_Fix 1).tif',
        '095_{marker:}_V11.PE_33bit_i 1).tif',
        ]

    base = [('date', None), ('tissue', None), ('species', None)]

    values = [
        dict(base + [('bit', '16'), ('marker', 'CD45')]),
        dict(base + [('bit', '16'), ('marker', 'KLRG1')]),
        dict(base + [('bit', '8'), ('marker', 'KLRG1')]),
        dict(base + [('bit', None), ('marker', 'CD15')]),
        dict(base + [('bit', '16'), ('marker', 'CD95')]),
        dict(base + [('bit', '16'), ('marker', 'CD326')]),
        dict(base + [('bit', '8'), ('marker', 'CD298')]),
        dict(base + [('bit', '16'), ('marker', 'TNF-a')]),
        dict(base + [('bit', '8'), ('marker', 'HLA-BC')]),
        dict(base + [('bit', '16'), ('marker', 'CD200R1')]),
        dict(base + [('bit', '8'), ('marker', 'CD16/CD32')]),
        dict(base + [('bit', '8'), ('marker', 'CD16/CD32')]),
        dict(base + [('bit', '8'), ('marker', 'CD158e1/e2')]),
        dict(base + [('bit', '16'), ('marker', 'CD140b pY857')]),
        ]

    outcome = []
    for full in full_templates:
        for val in values:
            path = Path(full.format(marker=val['marker'], bit=val['bit']))
            meta = fsp.extract_from_imagename(path)

            res = (path,
                   (meta['marker'], val['marker']),
                   (meta['bit'], val['bit']),
                   meta['marker'] == val['marker'],
                   meta['bit'] == val['bit'],
                   )

            outcome.append(res)
    # for o in outcome:
    #     print(o)
    assert all(res[-2] and res[-1] for res in outcome)

    for half in marker_templates:
        for val in values:
            path = half.format(marker=val['marker'])
            meta = fsp.extract_from_imagename(path)
            assert meta['marker'] == val['marker']
            assert meta['bit'] is None

def test_bleaches():
    """asser filtering of bleach images
    """
    fsp = get_testing_parser()

    paths = [
        '001_ori-CD3V11.PE_16bit_DF_FF_B - 2(fld 1 wv Cy3 - Cy3 wix 1).tif',
        'bleach_001_ori-CD3V11.PE_16bit_DF_B - 2(fld 1 wv Cy3 - Cy3 wix 1).tif',
        'bleach_013_CD45V80.PE_16bit_DF_FF_B - 2(fld 1 wv Cy3 - Cy3 wix 1).tif',
        'bleach_091_KLRG1V5.PE_16bit_DF_FF_B - 2(fld 1 wv Cy3 - Cy3 wix 1).tif',
        'bleach_091_KLRG1V5.PE_8bit_DF_FF_B - 2(fld 1 wv Cy3 - Cy3 wix 1).tif',
        ]
    for cur_path in paths:
        meta = fsp.extract_from_imagename(cur_path)
        assert all([val is None for val in meta.values()])

def test_cdnom_checking():
    """Test the checker for cd nomeclatur
    """
    fsp = get_testing_parser()

    pairs = [('CD42', True),
             ('CD42a', False),
             ('Bernd', False),
             ('CDa13', False),
             ('CD13.5', False),
             ('CD4a5', False),
             ('15', False),
             ('CD15', True),
            ]
    outcome = [fsp.is_cdnom(in_name) == in_bool for in_name, in_bool in pairs]
    assert all(outcome)


def test_alt_checking():
    """Test the checker for alternates used in regex
    """
    fsp = get_testing_parser()

    valid = [('CD42', True),
             ('CD42a', True),
             ('Bernd', True),
             ('CDa13', True),
             ('CD13.5', True),
             ('CD4a5', True),
             (r'CD.4a5', True),
             ('CD15', True),
             (r'TCR.V.3.2', True),
             (r'TCR/.V.3.2', True),
             (r'TCR].V.3.2', True),
             (r'/TCR.V.3.2', True),
             (r']TCR.V.3.2', True),
             (r'TCR.V.3.2/', True),
             (r'TCR.V.3.2]', True),
            ]

    # specific invalids
    invalid = [(r'12', False),
               (r'ax', False),
               (r't', False),
               (r'CD4a5 ', False),
               (r' CD4a5 ', False),
               (r' CD4a5', False),
               (r'1234567890abcdefghijklmn', False),
              ]

    # generic invalids
    for char in r'\()[?':
        invalid.append((r'CD123{}uY0'.format(char), False))
        invalid.append((r'AYK{}'.format(char), False))

    pairs = valid + invalid

    outcome = []
    for in_name, in_bool in pairs:
        out_bool = fsp.is_valid_regexalt(in_name) == in_bool
        outcome.append(out_bool)

    assert all(outcome)

def test_altcheck_patterfy_integration():
    """Test if patterfy generates pattern that are recognized
    as valit alternates by the alte checker
    """
    from dataframework.processing.misc import patterfy
    fsp = get_testing_parser()

    all_patterns = []
    for in_name, _ in NAME_PATTERN_PAIRS:
        all_patterns += patterfy(in_name)

    outcome = [fsp.is_valid_regexalt(pat) \
        for pat in all_patterns]

    for out_bool, test_in in zip(outcome, NAME_PATTERN_PAIRS):
        if not out_bool:
            print(test_in)

    assert all(outcome)

def test_fsparsergen():
    """Tests if the fileparser is correctly
    loaded with default abid.json
    """
    fp = get_fsparser()
    assert not fp is None
