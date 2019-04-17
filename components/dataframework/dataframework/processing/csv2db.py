# -*- coding: utf-8 -*-

"""Transforms the csv into a TinyDB, allowing for queries with omitted details
and easier extensibility
"""

import re
from tinydb import TinyDB
import pandas as pd

from .valuemapper import ValueMapper


class AbIdCSVreader():
    """Reads a csv derived from all_antibodies.xlsx and
    transfers it into a queryable database
    """

    alt_pattern = re.compile(r'(.*?) ?\((.*?)\) ?$', re.IGNORECASE)
    abid_pattern = re.compile(r'^(?P<pre>[a-z]{1,3})(?P<num>[0-9]*)$',
                              re.IGNORECASE)

    def __init__(self):
        """reads the abid.csv found at csv_path
        parses it and stores it at db_path
        """
        self.entry_cache = set()
        self.valmapper = ValueMapper()

    def parse_csv(self, csv_path):
        """Parses entries found in csv_path and writes them into the
        entry_cache
        """
        ab_data = pd.read_csv(str(csv_path), sep=';', encoding='utf-8')
        for abidx, ab_item in ab_data.iterrows():
            print('\r', abidx / len(ab_data), end='')

            species = self.parse_species(ab_item['SPECIES'])
            antigen = self.parse_antigen(ab_item['ANTIGEN'])
            gensym = parse_gensymbol(ab_item['GENSYMBOL'])
            abid = self.parse_abid(ab_item['ABID'])

            self.add_entry(
                species=species,
                antigen=antigen,
                gensym=gensym,
                abid=abid,
                )

    def add_entry(self, species=None, antigen=None, gensym=None, abid=None):
        """generates entry from lists
        will be tuple of tuple for hashability
        """
        species = species[::]
        species.sort()
        names = antigen + gensym
        names.sort()

        new_entry = []
        if not species is None:
            stup = tuple(set(species))
            new_entry.append(('species', stup))
        if not names is None:
            ntup = tuple(set(names))
            new_entry.append(('names', ntup))
        if not abid is None:
            new_entry.append(('abid', abid))

        new_entry = tuple(new_entry)
        self.entry_cache.add(new_entry)

    def parse_abid(self, abid_string):
        """parses abid entry from abid.csv
        returns string or None
        """
        abid_string = abid_string
        abids = filter_valid([abid_string])

        if not abids:
            return None
        if len(abids) > 1:
            raise ValueError('Invalid abid: {}'.format(abid_string))

        abid = abids[0]

        abmatch = self.abid_pattern.match(abid)
        if abmatch is None:
            raise ValueError('Invalid abid: {}'.format(abid_string))

        return abid

    def parse_species(self, species_string):
        """parses species entry from abid.csv
        returns list of all species or empty list
        """
        species = [ty.strip().lower() for ty in species_string.split(',')]
        valid = [self.valmapper.valid_species(cur_sp) for cur_sp in species]
        if not all(valid):
            msg = 'Unknown species:\n\nName\t\tValid\n'
            rows = ['{}\t\t{}'.format(csp, cval) for csp, cval in \
                    zip(species, valid)]
            tab = '\n'.join(rows)
            raise ValueError(msg+tab)
        return species

    def parse_antigen(self, ag_name):
        """parses antigen entry from abid.csv
        returns list of all andtigen names or empty list
        """
        match = self.alt_pattern.match(ag_name)
        alt_names = []
        if not match is None:
            for alt in match.groups():
                alt_names.append(alt.strip())
        else:
            alt_names.append(ag_name)
        
        return alt_names

    def write_db(self, db_path):
        """Write all cached entries to the db
        """
        out_db = TinyDB(str(db_path))
        out_tab = out_db.table('antigen')
        all_entries = [dict(entry) for entry in self.entry_cache]
        out_tab.insert_multiple(all_entries)

def parse_type(*args, **kwargs):
    """Parse the antibody types
    """
    raise NotImplementedError

def parse_gensymbol(gen_string):
    """parses gensymbol entry from abid.csv
    returns list of all gesymbols or empty list
    """
    gen_string = str(gen_string)
    gen_string = gen_string.strip('"')
    genes = [gen.strip() for gen in gen_string.split(';')]
    valid_genes = filter_valid(genes)
    return valid_genes

def filter_valid(list_of_strings):
    """Filter out to short or NaN entries. bascically everything
    that might interfere with regexes later on
    returns a filtered list or an empty one
    """
    ret = []
    for cand in list_of_strings:
        condt0 = len(str(cand)) >= 3
        condt1 = str(cand).lower() != 'nan'
        condt2 = not cand is None
        if all([condt0, condt1, condt2]):
            ret.append(cand)
    return ret

def generate_abid_db(csv_path, db_path):
    """ Generates db at db_path from abid.csv at csv_path
    """
    parser = AbIdCSVreader()
    parser.parse_csv(csv_path)
    parser.write_db(db_path)
