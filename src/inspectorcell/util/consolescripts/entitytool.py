import sys
import re
from pathlib import Path
import glob

import argparse

from inspectorcell.entities.entitytools import extract_to_table

def extract_features(args):
    matcher = re.compile(args.nameregex, re.IGNORECASE)
    if args.strict:
        strict = True
        print('Strict Matching!')
    else:
        strict = False
        print('All globs')

    if args.dryrun:
        print('Dry-run, will not write anything')

    if not args.imageglob:
        imagefiles = None
    else:
        imagefiles = {}
        for ipath in (Path(p) for p in glob.glob(args.imageglob)):
            match = matcher.match(ipath.name)

            if not match is None:
                name = match.groups()[0]
            else:
                name = ipath.name
            
            if strict:
                if not match is None:
                    imagefiles[name] = str(ipath)
            else:
                imagefiles[name] = str(ipath)

    for name, path in imagefiles.items():
        print('{}\t->\t{}'.format(Path(path).name, name))

    print('extracting for', args.jsonfile)
    if not args.dryrun:
        extract_to_table(args.jsonfile, imagefiles=imagefiles, ext='xls')


def main():
    entitytool = argparse.ArgumentParser(
        prog='Entity CLI tool',
        description='CLI tool to work with the InspectorCell output')
    
    
    command_parser = entitytool.add_subparsers(
        title='Commands',
        description='Main functionality the util script supplies',
        )
    
    extract = command_parser.add_parser(
        'extract',
         description='Extracts annotations and scalar values from InspectorCell' +\
                     'output',
        )
    
    extract.add_argument('jsonfile', type=str)
    extract.add_argument('imageglob', type=str, nargs='?', default='')
    extract.add_argument('nameregex', type=str, nargs='?',
                          default='^(.{1,10}).*\.[a-z]{1,3}$')
    extract.add_argument('-n', '--dryrun', action='store_true')
    extract.add_argument('-s', '--strict', action='store_true',
                         help='Only select matching images')
    extract.set_defaults(func=extract_features)

    parsed_args = entitytool.parse_args(sys.argv[1:])

    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)


if __name__ == '__main__':
    main()
