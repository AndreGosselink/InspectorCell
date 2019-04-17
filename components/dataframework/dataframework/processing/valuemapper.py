# -*- coding: utf-8 -*-
"""Implements ValueMapper, and other functions/classes keeping al central, share
infroamtion
"""

class ValueMapper():
    """Shared class keeping all the information about valid
    species, marker, tissues to enforce consitency between
    several modules
    perspectively at the end an database connector/interface
    """

    # all known species with the bitmask representation
    # 8 bit
    _name_maps = {
        'species': {'human': 0,
                    'mouse': 1,
                    'non-human primate': 2,
                    'other': 3,
                    'rat': 4,
                   },

        'bit': {'8': 0,
                '16': 1,
               },

        'tissue': {'pancreas': 0,
                   'ovaria': 1,
                   'lung': 2,
                   'tonsil': 3,
                   'cardiomyocytes': 4,
                   'brain': 5,
                   'glioblastoma': 6,
                   'neuro': 7,
                   'astrocyte': 8,
                   'spleen': 9,
                   'colon': 10,
                   'prostate': 11,
                   'kidney': 12,
                   'liver': 13,
                   'melanoma': 14,
                   'embryonic stem cell': 15,
                   'lymph node': 16,
                  }
    }

    _key_maps = {}
    _name_validation = {}
    _key_validation = {}

    def __init__(self):
        """setups lookupmaps on instanciation
        """
        self._mappings = None
        self._generate_maps()

    def _generate_maps(self):
        """Generate look-up maps
        """
        self._mappings = self._name_maps.keys()

        for mapping in self._mappings:
            names = self._name_maps[mapping].keys()
            keys = self._name_maps[mapping].values()

            self._name_validation[mapping] = names
            self._key_validation[mapping] = keys

            self._key_maps[mapping] = dict(zip(keys, names))

    def validate(self, name=None, key=None, mapping=''):
        """Validates if name or key are valid entries in mapping
        if both name and key are given, the mapping itself is checked
        """
        if name is None and key is None:
            raise TypeError('At least name or key must be given')
        if mapping not in self._mappings:
            raise ValueError('invalid mapping')

        # validate
        lut_key = self._name_maps[mapping].get(name, None)
        lut_name = self._key_maps[mapping].get(key, None)
        valid_name = not lut_key is None
        valid_key = not lut_name is None

        if valid_key and valid_name:
            return lut_key == key and lut_name == name
        return valid_key or valid_name

    def valid_species(self, name=None, key=None):
        """Convinience wrapper for validate species
        see ValueMapper.validate()
        """
        return self.validate(name, key, 'species')

    def valid_bit(self, name=None, key=None):
        """Convinience wrapper for validate species
        see ValueMapper.validate()
        """
        return self.validate(name, key, 'bit')

    def valid_tissue(self, name=None, key=None):
        """Convinience wrapper for validate tissue
        see ValueMapper.validate()
        """
        return self.validate(name, key, 'tissue')
