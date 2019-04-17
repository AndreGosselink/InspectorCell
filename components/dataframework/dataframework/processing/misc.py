# -*- coding: utf-8 -*-

"""Miscellanseloaus helper functions that work with out relevant context
"""

def _patterfy(string):
    """Removes all regex critical and all unicode characters
    """
    #TODO maybe unicode replaced by dots as well
    # removing regex critical characters
    
    string = string.strip()

    split_litdot = []
    for part in string.split('.'):
        for char in r'\|()[]/<>_-':
            part = part.replace(char, '.')
        split_litdot.append(part)

    string = r'\.'.join(split_litdot)

    # assuming all non assci is some greek abbr. with a-z
    asciistring = str(string).encode('ascii', 'replace').decode()
    asciistring = asciistring.replace('?', '[a-z]')
    return asciistring

def get_comma_alts(string):
    """parses funny comma alternates
    """
    string = string.replace(r'\.', '<<LITERALDOT>>')

    if '.' in string and ',' in string:
        # split everything
        comma_split = string.split(',')
        base_p, alts = comma_split[0], comma_split[1:]
        base_p_split = base_p.split('.')
        base = '.'.join(base_p_split[:-1])
        alts.append(base_p_split[-1])

        # put it all together
        ret = []
        for cur_alt in alts:
            new_alt = '.'.join([base, cur_alt.strip()])
            ret.append(new_alt)
    else:
        ret = [string]

    return [retval.replace('<<LITERALDOT>>', r'\.') for retval in ret]

def patterfy(string):
    """parses comma alts and then patterfies them
    """
    pattern_string = _patterfy(string) # leaves ',' intact
    comma_alts = get_comma_alts(pattern_string)
    return [alt.replace(' ', '.') for alt in comma_alts]
