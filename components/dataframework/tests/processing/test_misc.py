# -*- coding: utf-8 -*-

"""Test for functions implemented in the misc module
"""

from dataframework.processing.misc import patterfy, get_comma_alts
from conftest import NAME_PATTERN_PAIRS

def test_patterfy():
    """test sanitazition of unicode containing
    strings
    """
    patterfy_tests = [(in_name, [out_pat]) for in_name, out_pat \
        in NAME_PATTERN_PAIRS]

    patterfy_tests.append((r'HLA-A2, A28', [r'HLA.A2', r'HLA.A28']))

    outcome = [set(out_list) == set(patterfy(in_string)) \
        for in_string, out_list in patterfy_tests]

    for i, correct in enumerate(outcome):
        if not correct:
            in_name, out_exp = patterfy_tests[i]
            print(in_name, out_exp, '<>', patterfy(in_name))

    assert all(outcome)

def test_comma_alts():
    """Tests all known comma alt cases
    """
    pairs = [('HLA.DR, DP, DQ', ['HLA.DR', 'HLA.DP', 'HLA.DQ']),
             ('b, c', ['b, c']),
             ('HLA.B7, B27', ['HLA.B7', 'HLA.B27']),
             ('HLA.A2, A28', ['HLA.A2', 'HLA.A28']),
             (r'TCR.V.11\.1, 11\.2', [r'TCR.V.11\.1', r'TCR.V.11\.2']),
            ]

    outcome = [set(out_list) == set(get_comma_alts(in_string)) \
        for in_string, out_list in pairs]

    for i, correct in enumerate(outcome):
        if not correct:
            in_name, out_exp = pairs[i]
            print(in_name, out_exp, 'got>', get_comma_alts(in_name))

    assert all(outcome)
