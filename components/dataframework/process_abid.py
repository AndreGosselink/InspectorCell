# -*- coding: utf-8 -*-

"""Simple script to parse abid.csv into TinyDB
"""
from pathlib import Path

from fs2ometiff.util.csv2db import generate_abid_db

generate_abid_db(csv_path=Path('./res/abids.csv'),
                 db_path=Path('./res/abids.json'),
                 )
