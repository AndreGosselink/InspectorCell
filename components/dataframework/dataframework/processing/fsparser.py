# -*- coding: utf-8 -*-

"""Parser for filenames and pathes, to extract information. Based on
TiffNameParser and ExpExtractor found in MICSCrawler v 0.65
"""

import copy
from pathlib import Path
import re

from tinydb import TinyDB

from .misc import patterfy


__DEFAULT_DB_PATH = Path(__file__).parents[1]
__DEFAULT_DB_PATH = __DEFAULT_DB_PATH / 'res/abids.json'


class FsParser():
    """Extracts information from filesystem paths
    can only extract information that is really encoded
    in the path. experimenter and other stuff will not be
    touched
    """
    _cd_match_pat = r'(?<!\/)CD\d{1,4}'
    _cd_filter_pat = r'^(CD\d{1,5})$'

    _fs_pattern = r'^(?!bleach|.*?ori)(?:.*?)(?P<marker>{})' +\
                  r'[_V \-](?:.*?(?P<bit>8|16)bit.*|.*)(?P<ext>\.tiff?)$'

    _meta_templ = {'date': None,
                   'tissue': None,
                   'marker': None,
                   'bit': None,
                   'species': None,
                  }

    _wildcards = [r'DAPIi', r'DAPIf']

    def __init__(self, db_path):
        if not Path(db_path).exists():
            raise ValueError('Invalid path to db')

        #TODO unicode regex? case sensitive?
        self._cd_filter = re.compile(self._cd_filter_pat, re.IGNORECASE)

        # get all markers names from database
        antigens = TinyDB(str(db_path)).table('antigen').all()

        # flatten list
        all_names = []
        for entry in antigens:
            all_names += entry['names']

        self._fs_regex = self._get_imagename_matcher(all_names)

    def _get_imagename_matcher(self, namelist):
        """generates a pattern where all names in namelist are alternates
        for marker names encoded in filenames. returns compilte re.pattern
        """
        patterns = []
        for cur_name in namelist:
            patterns += patterfy(cur_name)

        # filter list of all names
        all_marker_pat = set()
        for cur_pat in patterns:
            generic = self.is_cdnom(cur_pat)
            valid_regex = self.is_valid_regexalt(cur_pat)
            if generic or not valid_regex:
                continue
            else:
                all_marker_pat.add(cur_pat)

        for wcard in self._wildcards:
            all_marker_pat.add(wcard)
        all_marker_pat = list(all_marker_pat)
        all_marker_pat.sort(key=len)
        all_marker_pat = all_marker_pat[::-1]
        # add the generic CD marker
        all_marker_pat.append(self._cd_match_pat)

        name_alternates = '|'.join(all_marker_pat)
        fs_pattern = self._fs_pattern.format(name_alternates)

        return re.compile(fs_pattern, re.IGNORECASE)

    def is_cdnom(self, name):
        """return True if name is a valid CD nomiclature name
        else false
        """
        return not self._cd_filter.match(name) is None

    def _gen_regextest(self, pre, post, marker_pattern):
        """Generates an regex test for name
        """
        # substitute possible regex expressions
        marker_name = marker_pattern.replace(r'[a-z]', r'b')
        marker_name = marker_name.replace(r'\.', r'.')

        test_marker = [r'AA', r'CD1337', marker_name]
        test_alternate_pat = [r'AA', self._cd_match_pat, marker_pattern]
        test_pattern = r'^(.*?)({})[_V \-](.*)$'.format(
            r'|'.join(test_alternate_pat))

        test_lines = []
        for cur_marker in test_marker:
            for sep in [r'_', r'V', r'-', r' ']:
                test_line = pre + cur_marker + sep + post
                test_lines.append((test_line, cur_marker))

        return test_pattern, test_lines

    def is_valid_regexalt(self, name_pattern):
        """return True if name can used in an regex pattern as alternate
        else false

        idea is to test the patterns in an simple regex. if it doesnt work in
        a very simple context it wont work in an complex one
        """
        # minimum requirements to be valid
        if not 3 <= len(name_pattern) <= 23 or name_pattern.startswith(' ') \
           or name_pattern.endswith(' '):
            return False

        pre, post = r'abc', r'xyz'
        test_pattern, test_lines = self._gen_regextest(
            pre, post, name_pattern)

        try:
            test_re = re.compile(test_pattern)
        except re.error:
            # does not compile to vlaid regex
            return False

        results = []
        for test_line, test_marker in test_lines:
            match = test_re.match(test_line)

            # does not match, something is wrong
            if match is None:
                results.append((False, None, test_marker))
                continue

            # missmatched groups, something is wrong
            gr0, gr1, gr2 = match.groups()
            if gr0 != pre or gr1 != test_marker or gr2 != post:
                results.append((False, match.groups(), test_marker))
                continue

            results.append((True, match.groups(), test_marker))

        # matches and works as expected, good to go
        return all(res[0] for res in results)

    def extract_from_imagename(self, image_name):
        """Extracts metainformation from path
        """
        image_match = self._fs_regex.match(str(image_name))
        if image_match is None:
            return self._get_metadata_dict()

        image_meta = image_match.groupdict()
        ret = self._get_metadata_dict(
            marker=image_meta['marker'],
            bit=image_meta['bit'],
        )
        return ret

    def _get_metadata_dict(self, date=None, tissue=None,
                           marker=None, bit=None, species=None,):
        """Returns dict with key that might be
        dynamically extractable from the filename
        """
        ret = copy.deepcopy(self._meta_templ)
        ret['date'] = date
        ret['tissue'] = tissue
        ret['marker'] = marker
        ret['bit'] = bit
        ret['species'] = species
        return ret

def get_fsparser(db_path=None):
    """Generates a FsParser instance and sets it up with a default
    marker db found in fs2ometiff/res/abid.json
    """
    if db_path is None:
        db_path = __DEFAULT_DB_PATH
    if not Path(db_path).exists():
        msg = 'abid.json is missing, not in' +\
            str(db_path)
        raise RuntimeError(msg)
    ret = FsParser(db_path)
    return ret
