# -*- coding: utf-8 -*-
import sys
import argparse

from pathlib import Path
from logging import getLogger, DEBUG, INFO

from .logutil import setup_logging
from .control import AppControl
from ._version import __version__


def update_db(csv_file):
    if not csv_file.exists():
        msg = 'invalid csv path: {}'.format(str(csv_file))
        raise ValueError(msg)
    from dataframework.processing.csv2db import generate_abid_db
    from ._config import __marker_db_dir as db_dir
    try:
        json_file = Path(sys.prefix) / db_dir / 'abids.json'
        print('Regenerating abid database at {}'.format(str(json_file)))
        generate_abid_db(csv_path=csv_file, db_path=json_file)
    except Exception as err:
        msg = 'Unable to update abids.json file: {}'.format(str(err))
        raise ValueError(msg)
    if json_file.exists() and not json_file.is_dir():
        print('\nSuccess!')
        sys.exit(0)
    else:
        print('\nSomething went wrong')
        sys.exit(-1)

def get_parser():
    verstring = 'segtool {}'
    the_version = verstring.format(__version__)

    argparser = argparse.ArgumentParser(
        prog='segtool',
        description='Visualizing and annotating for MICS images')

    db_help_msg = 'path to csv file wich can be parsed into a abid database'
    argparser.add_argument('-c', '--csv', action='store', type=str,
                           metavar='path to csv', help=db_help_msg)

    argparser.add_argument('--version', action='version',
                           version=the_version)

    argparser.add_argument('-v', '--verbose', action='count')

    return argparser

def main():
    argp = get_parser()
    args = argp.parse_args(sys.argv[1:])

    if not args.csv is None:
        update_db(Path(args.csv))

    if not args.verbose is None:
        setup_logging(logfile_path=Path('debug.log'),
                      global_level=DEBUG)
    else:
        setup_logging(logfile_path=Path('debug.log'),
                      global_level=INFO)

    root_log = getLogger()
    app_log = getLogger('App')

    app_log.info('Version: %s', __version__)
    app_log.debug('DEBUG')

    AppControl([]).exec()


if __name__ == '__main__':
    main()
