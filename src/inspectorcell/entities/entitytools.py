"""Helpfull tools to edit or generate Entity or EntityManager instances
"""
import warnings
import numpy as np
import cv2
from pathlib import Path
from functools import partial

from ..util.image import getImagedata
from ..entities import EntityManager, EntityFile
from .entity import dilatedEntity


def _print(arr):
    img = ''
    for row in arr:
        line = ''
        for val in row:
            if val: line += '.'
            else: line += ' '
        img += line + '\n'
    print(img)

def slice_with_entity(array, entity):
    """Returns all values from array, which are sliced by entity

    Parameters
    ----------
    array : ndarray
        Array with the shape `(m x n x c)`, where `m` and `n` are the spatial
        dimensions and `c` is the number of channels

    entity : Entity
        Entity instance, must provide `entity.mask_slice` and `entity.mask`

    Returns
    -------
    values : ndarray
        Values indexed by entity, with shape `(k)` where `k == entity.mask.size`
    """
    return array[entity.mask_slice][entity.mask]

def pixmap_to_json(pixmap, jsonfile, dilate=1):
    """Converts a pixelmap to json

    Programs like CellProfiler can export cellsegmentations to pixelmap
    These are mappings of the Object/Segment ID to the pixel values
    This function generates polygons and entity objects and stores them in
    the json format.

    Parameters
    ----------
    pixmap : str, pathlib.Path
        Path to the pixelmap. Must be an image format, that can be convertet
        unambigously to 16 bit unsigned integer grayscale image

    jsonfile : str, pathlib.Path
        Path to the resulting json file

    dilate : int
        Inplace dilitation of each segment found in the `pixmap`. See Notes

    Notes
    -----
    Due to the nature of greyscale object-to-pixel-mappings, each pixel can have
    only one value. Thus each pixel can have only on object assigned.
    By dilation, overlaps lost during conversion can be modeld using dilation.
    """
    mask = getImagedata(str(pixmap))

    eman = EntityManager()
    eman.generateFromPixelmap(mask)
    total = len(eman)
    with EntityFile.open(jsonfile, 'w') as trgt:
        for n, entity in enumerate(eman, 1):
            print('\r{}/{}'.format(n, total), end='')
            entity = dilatedEntity(entity, dilate)
            trgt.writeEntity(entity)
    print('\ndone')

def read_entity_data(jsonfile, strip=False):
    """Convinience function to read entity data from a json

    Parameters
    ----------
    jsonfile : str, pathlib.Path
        Path to the json file
    strip : bool (default=True)
        If true, all historic elements are striped from the
        dataset

    Returns
    -------
    ent_data : dict of dict
        Dictionary with all entities.
        .. warning:: The keys `the ent_data` are not the Entiy ID!

    Notes
    -----
    The `ent_data` is a dict of dicts. The nested, inner dicts have at least
    the keys {'id', 'scalars', 'tags', 'contours'}
    """
    with EntityFile.open(jsonfile, 'r') as src:
        if strip:
            return [ent for ent in src.read() if not ent['historical']]
        else:
            return src.read()

def data_into_manager(entity_data, manager):
    """Converts Entities from entity_data into an Entity instance and adds them
    to the manager

    Parameters
    ----------
    ent_data : dict of dict
        Dictionary with all entities and theit data
        .. warning:: The keys `the ent_data` are not the Entiy ID!

    manager : entities.EntityManager
        EntityManager instance that is populated with the entitiy data found in
        `ent_data`
    """
    entities = []
    for entry in entity_data:
        entry['contour'] = contour = []
        for cur_cont in entry.pop('contours'):
            contour.append(np.array(cur_cont).astype(int))
        entities.append(entry)
    manager.generateEntities(entities)

def read_into_manager(jsonfile, entity_manager=None, strip=False):
    """Reads all Entities from jsonfile into an EntityManager instance

    Parameters
    ----------
    jsonfile : str, pathlib.Path
        Path to the json file with the entity data

    entity_manager : EntityManager (default=None)
        EntityManager instance in which the entities should be read
        into. If `None` a new instance will be created
    strip : bool
        Strip historic entities, see read_entity_data

    Returns
    -------
    entity_manager : EntityManager
        EntityManageger with data from `jsonfile`. If `entity_manager`      
        paramter was `None` it is a new instance. Otherwise input and
        output instances are the same

    Note
    ----
    Default is syntactic-sugar for
    `data_into_manager(read_entity_data(jsonfile, False), EntityManager())`
    """
    if entity_manager is None:
        entity_manager = EntityManager()

    data_into_manager(read_entity_data(jsonfile, strip=strip),
                      entity_manager)
    return entity_manager

def simplify_contours(contours):
    """Simplifies contours

    Iterates over all polygons found in contours. In each polygon redundant,
    dublicated points are removed

    Parameters
    ----------
    contours : list of list of tuple
        list of polygons, where each polygon is a sequense of 2d points

    Returns
    -------
    simplified : list of list of tuple
        Simplified `contours`
    """
    simplified = []
    for poly in contours:
        simple_poly = []
        last_pt = None, None
        for cur_pt in poly:
            if cur_pt[0] != last_pt[0] or cur_pt[1] != last_pt[1]:
                simple_poly.append(cur_pt)
            last_pt = cur_pt
        simplified.append(simple_poly)
    return simplified

def strip_historic(entity_data):
    """Generates new list with all historic entities removed

    Parameters
    ----------
    entity_data : list of dicts
        List of entity data entries as returned by `read_entity_data`

    Returns
    -------
    active : list of dicts
        List of entity data entries that are not historic

    historic : list of dicts
        List of entity data entries that are historic
    """
    active = []
    historic = []
    for ent in entity_data:
        if not ent['historical']:
            active.append(ent)
        else:
            historic.append(ent)

    return active, historic

def extract_annotations(eman):
    """Reads all Entities in EntityManager and extracts tags/scalars into
    pandas.DataFrame

    Parameters
    ----------
    eman : EntityManager
        EntityManager instance with entities

    Returns
    -------
    features : pandas.DataFrame
        DataFrame with tags and scalars for each Entity in `eman`
    """
    import pandas as pd

    all_tags = set()
    all_scalars = set()

    for ent in eman:
        all_tags = all_tags.union(ent.tags)
        all_scalars = all_scalars.union(set(ent.scalars.keys()))

    data = []
    for ent in eman:
        entry = {
            'id': ent.eid,
                }

        for scalar in all_scalars:
            sc_name, sc_type = scalar
            sc_val = ent.scalars.get(scalar, 0)
            entry[sc_name] = sc_val

        for tag in all_tags:
            if tag in ent.tags:
                entry[tag] = 1
            else:
                entry[tag] = 0

        data.append(entry)

    return pd.DataFrame(data)

def extract_features(eman, imagefiles):
    """Reads all Entities in EntityManager and extracts features into
    pandas.DataFrame

    Parameters
    ----------
    eman : EntityManager
        EntityManager instance with entities used to mask images in imagedir

    imagefiles : dict
        Dictionary with a string key, that is used as name in the table and
        the value being a string or pathlib.Path pointing to the image files 
        used for feature extraction for entities in `eman`

    Returns
    -------
    features : pandas.DataFrame
        DataFrame with extracted features for each Entity in `eman` for each
        image descibed in `imagefiles`
    """
    import pandas as pd

    # feature definitions
    def feature(func):
        def _feature(func, ent, img):
            try:
                return func(slice_with_entity(img, ent))
            except Exception as e:
                err = str(e)
                warnings.warn(f'Exception during feature extraction: {err}')
                return np.nan
        return partial(_feature, func)

    def get_center_x(entity):
        as_arr = np.array(entity.contours[0], float)
        return as_arr[:,0].mean()

    def get_center_y(entity):
        as_arr = np.array(entity.contours[0], float)
        return as_arr[:,1].mean()


    #TODO parameterize
    featmap = dict(mean=feature(np.mean),
                   integrated=feature(np.sum),
                   median=feature(np.median),
                   area=feature(np.size),
                   )

    # read image data
    img_data = {}
    for img_name, img_path in imagefiles.items():
        img_data[img_name] = getImagedata(img_path)

    # define columns
    feat_columns = []
    feat_columns.append(
        dict(title='id', func=lambda e, i: e.eid, img=None))
    feat_columns.append(
        dict(title='x', func=lambda e, i: get_center_x(e), img=None))
    feat_columns.append(
        dict(title='y', func=lambda e, i: get_center_y(e), img=None))

    for img_name, img_data in img_data.items():
        for feat_name, feat_func in featmap.items():
            cur_col = {
                'title': '{}_{}'.format(img_name, feat_name),
                'func': feat_func,
                'img': img_data,
                    }
            feat_columns.append(cur_col)

    data = []
    for ent in eman:
        entry = {}
        for feat in feat_columns:
            entry[feat['title']] = feat['func'](ent, feat['img'])
        data.append(entry)

    return pd.DataFrame(data)

def extract_to_table(jsonfile, imagefiles=None, ext='csv'):
    """Reads all Entities EntityManager and extracts features and tags into xls

    Parameters
    ----------
    jsonfile : str, pathlib.Path
        Path to the json file with the entity data

    imagefiles : dict
        Dictionary with a string key, that is used as name in the table and the
        value being a string or pathlib.Path pointing to the image files used
        for feature extraction for entities in `jsonfile`
        If it is `None` or empty `{}`, no feature extraction is performed

    ext : str
        Extension passed to pandas.DataFrame. Possible values are `csv` or
        `xls`

    Note
    ----
    Requires the packages pandas and depending on the extension openpyxls
    """
    # loading data and striping
    ent_data, _ = strip_historic(read_entity_data(jsonfile))

    if imagefiles is None:
        imagefiles = {}

    if imagefiles:
        # simplification of contours for extraction
        for ent in ent_data:
            ent['contours'] = simplify_contours(ent['contours'])

    eman = EntityManager()
    data_into_manager(ent_data, eman)

    entity_annotations = extract_annotations(eman)

    json_stem = Path(jsonfile).stem

    if ext.endswith('xls'):
        if imagefiles:
            extract_features(eman, imagefiles).to_excel(
                json_stem + '_features.xlsx')
        extract_annotations(eman).to_excel(
            json_stem + '_annotations.xlsx')
    elif ext.endswith('csv'):
        if imagefiles:
            extract_features(eman, imagefiles).to_excel(
                json_stem + '_features.csv')
        extract_annotations(eman).to_excel(
            json_stem + '_annotations.csv')
    else:
        raise ValueError('Unknown extension: {}'.format(ext))

def draw_entities(canvas, eman, color_func, stroke=3, mode='set'):
    """Draws an image of all entities in an EntityManager

    Parameters
    ----------
    canvas : ndarray
        NumpArray with the shape `(y, x, c)`, where `y` is the
        number of pixel rows, `x` is the number of columns and
        `c` is the number of channels. Canvas will be altered!
    eman : EntityManager
        EntityManager instance with entities to be drawn onto the
        canvas
    color_func : callable
        Callable that must have take an Entity instance as argument
        and return a color tuple/iterable/array. The signature must be
        `color_func(enitity) -> color`, where color must have the shape
        `(c,)` and `c` must be of the same size as in `canvas`.
    stroke : int
        Stroke width of drawn segments in pixels
    mode : str either `set` or `add`
        With `set` a black stroke is drawn and filled with the entity.
        Everything under the entity segment will be overdrawn
        With `add` only the entity is added to the canvas
    """
    # min_vals = {'row': np.inf, 'col': -np.inf}
    # max_vals = {'row': np.inf, 'col': -np.inf}
    # for entitiy in eman:
    #     rvals, cvals = entitiy.mask_slice

    for entity in eman:
        color = color_func(entity)
        try:
            ch = len(color)
        except:
            ch = 1
        try:
            stroke_sl = entity.mask_slice[::]
            stroke_mk = entity.mask.copy()
            if mode == 'set':
                if stroke == 0:
                    canvas[stroke_sl][stroke_mk] = color
                elif stroke > 0:
                    dilatedEntity(entity, stroke)
                    canvas[entity.mask_slice][entity.mask] = 0
                    canvas[stroke_sl][stroke_mk] = color
                elif stroke < 0:
                    dilatedEntity(entity, -stroke)
                    keep = canvas[stroke_sl][stroke_mk].copy()
                    canvas[entity.mask_slice][entity.mask] = color
                    canvas[stroke_sl][stroke_mk] = keep
            elif mode == 'add':
                canvas[stroke_sl][stroke_mk] += color
            else:
                raise ValueError('Invalid mode: {}'.format(mode))
        except Exception as e:
            msg = 'Could not paint entity {} with error {}'
            warnings.warn(msg.format(entity.eid, str(e)))
    return canvas
