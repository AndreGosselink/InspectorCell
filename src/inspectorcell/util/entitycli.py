import re
import sys
import glob
import warnings

import argparse
import pandas as pd
from pathlib import Path
import numpy as np
from PIL import Image

from inspectorcell.entities.entitytools import (extract_to_table, read_into_manager,
                                                draw_entities)
from inspectorcell.entities import EntityFile


class DryrunWrapper():
    """Enforce usage of dryrun
    """

    def __init__(self, args):
        self._dryrun = args.dryrun

    def perform(self, func, args, kwargs, mock_ret=None):
        args_str = ', '.join(str(arg) for arg in args)
        kwargs_str = ', '.join('{}={}'.format(str(k), str(v))\
                               for k, v in kwargs.items())
        call_sig = str(func.__name__) + '(' + args_str + kwargs_str + ')'
        if self._dryrun is True:
            print('DRY RUN for:', call_sig)
            return mock_ret
        elif self._dryrun is False:
            print('performing:', call_sig)
            return func(*args, **kwargs)
        else:
            raise RuntimeError('We shouldn\'t be here...')


def extract_features(args):
    matcher = re.compile(args.nameregex, re.IGNORECASE)
    if args.strict:
        strict = True
        print('Strict Matching!')
    else:
        strict = False
        print('All globs')

    wrapper = DryrunWrapper(args)

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
    wrapper.perform(extract_to_table,
        (args.jsonfile,), dict(imagefiles=imagefiles, ext='xls'))

def merge_csv(args):
    eman = read_into_manager(args.injson, strip=True)
    dframe = pd.read_csv(args.incsv, skiprows=range(1, 3))
    # import IPython as ip
    # ip.embed()
    stop = False
    if not args.idcol in dframe.columns:
        warnings.warn('{} does not exist!'.format(args.idcol))
        stop = True
    if not args.tagcol in dframe.columns:
        warnings.warn('{} does not exist!'.format(args.idcol))
        stop = True
    if stop:
        msg = 'Column names in {} are:\n{}'
        warnings.warn(msg.format(args.incsv, str(dframe.columns)))
        return

    for ent in eman:
        rmask = dframe[args.idcol] == ent.eid
        try:
            tag, = dframe[rmask][args.tagcol]
            ent.tags.add(tag)
        except ValueError:
            msg = 'Could not find Entity-ID {} in table'
            warnings.warn(msg.format(ent.eid))

    def write_json(entities, jsonfile):
        all_ents = list(entities.iter_all())
        print('Writing {} entities to {}'.format(len(all_ents), jsonfile))
        with EntityFile.open(jsonfile, 'w') as entf:
            entf.writeEntities(all_ents)

    wrapper = DryrunWrapper(args)
    wrapper.perform(write_json, (), dict(entities=eman, jsonfile=args.outjson))

def to_pixmap(args):
    eman = read_into_manager(args.injson, strip=True)
    xres = int(args.xres)
    yres = int(args.yres)
    
    print('Clipping Entities...')
    for ent in eman:
        new_cont = []
        for cont in ent.contours:
            cur_cont = []
            new_cont.append(cur_cont)
            for (p0, p1) in cont:
                p0 = min(max(p0, 0), xres)
                p1 = min(max(p1, 0), yres)
                cur_cont.append((p0, p1))

        ent.from_contours(new_cont)
    
    def make_pixmap(xres, yres, tiffile):
        col_fn = lambda ent: ent.eid
        img = np.zeros((yres, xres, 1), np.uint16)
        draw_entities(img, eman, col_fn, stroke=0)
        pic = Image.fromarray(img[..., 0])
        pic.save(tiffile)
    
    tiffile = Path(args.outtif)
    wrapper = DryrunWrapper(args)
    wrapper.perform(make_pixmap, (), dict(xres=xres, yres=yres,
                    tiffile=args.outtif))

def draw_cluster(args):
    eman = read_into_manager(args.injson, strip=True)
    xres = int(args.xres)
    yres = int(args.yres)
    stroke = int(args.stroke)
    
    #TODO Make me a function and REUSE ME!
    print('Clipping Entities...')
    for ent in eman:
        new_cont = []
        for cont in ent.contours:
            cur_cont = []
            new_cont.append(cur_cont)
            for (p0, p1) in cont:
                p0 = min(max(p0, 0), xres)
                p1 = min(max(p1, 0), yres)
                cur_cont.append((p0, p1))

        ent.from_contours(new_cont)
    
    def get_colorfun(colorcsv):
        colscheme = pd.read_csv(colorcsv)
        defaul = colscheme
        LUT = {}
        default = (50, 50, 50)
        for i, r in colscheme.iterrows():
            tag = r['tag']
            rgb = r['red'], r['green'], r['blue']
            if not tag == 'default':
                LUT[tag] = rgb 
            if tag == 'default':
                default = rgb

        def _colfn(ent):
            ret = default
            for curt in ent.tags:
                ret = LUT.get(curt, default)
                if ret != default:
                    break
            return ret

        return _colfn

    def make_pixmap(xres, yres, stroke, colorcsv, tiffile):
        col_fn = get_colorfun(colorcsv)
        img = np.zeros((yres, xres, 3), np.uint8)
        draw_entities(img, eman, col_fn, stroke=stroke)
        pic = Image.fromarray(img)
        pic.save(tiffile)
    
    tiffile = Path(args.outtif)
    wrapper = DryrunWrapper(args)
    wrapper.perform(make_pixmap, (), dict(xres=xres, yres=yres,
                    stroke=stroke, colorcsv=args.colorcsv,
                    tiffile=args.outtif))


def main(*args, **kwargs):
    entitycli = argparse.ArgumentParser(
        prog='Entity CLI tool',
        description='CLI tool to work with the InspectorCell output')
    
    
    command_parser = entitycli.add_subparsers(
        title='Commands',
        description='Main functionality the util script supplies',
        )
    
    # Extract Features
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

    # Load features from table
    mergecsv = command_parser.add_parser(
        'mergecsv',
         description='Merges tags from CSV file into EntityFile',
        )
    
    mergecsv.add_argument('injson', type=str, help='json file to read Entities from')
    mergecsv.add_argument('incsv', type=str, help='json file to read Entities from')
    mergecsv.add_argument('outjson', type=str, help='json file to write Entities to')
    mergecsv.add_argument('idcol', type=str, default='CellID', nargs='?',
                          help='Name of column in CSV with EntityID')
    mergecsv.add_argument('tagcol', type=str, default='Cluster', nargs='?',
                          help='Name of column in CSV with tag information')
    mergecsv.add_argument('-n', '--dryrun', action='store_true')
    mergecsv.set_defaults(func=merge_csv)

    # Make pixmap
    totif = command_parser.add_parser(
        'totif',
         description='Exports the segment information to a 16 bit tif',
        )
    
    totif.add_argument('injson', type=str, help='json file to read Entities from')
    totif.add_argument('outtif', type=str, help='tif file to write to')
    totif.add_argument('--xres', type=int, help='tif pixel width', nargs='?',
                       default=2048)
    totif.add_argument('--yres', type=int, help='tif pixel hight', nargs='?',
                       default=2048)
    totif.add_argument('-n', '--dryrun', action='store_true')
    totif.set_defaults(func=to_pixmap)

    # Make pixmap with color based on clustering
    drawme = command_parser.add_parser(
        'clusterdraw',
         description='Draws Segments based on the clustering',
        )
    
    drawme.add_argument('injson', type=str, help='json file to read Entities from')
    drawme.add_argument('outtif', type=str, help='tif file to write to')
    drawme.add_argument('colorcsv', type=str, help='CSV with coloring information')
    drawme.add_argument('--stroke', type=int, help='Stroke width', nargs='?',
                        default=0)
    drawme.add_argument('--xres', type=int, help='tif pixel width', nargs='?',
                        default=2048)
    drawme.add_argument('--yres', type=int, help='tif pixel hight', nargs='?',
                       default=2048)

    drawme.add_argument('-n', '--dryrun', action='store_true')
    drawme.set_defaults(func=draw_cluster)


    
    # Done
    parsed_args = entitycli.parse_args(sys.argv[1:])
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)
    else:
        entitycli.print_usage()

if __name__ == '__main__':
    main()
