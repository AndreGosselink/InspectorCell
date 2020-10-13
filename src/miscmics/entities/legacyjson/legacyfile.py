"""Reference Implementation for object file. Can be binary or json

Legacy Fileformat as used by InspectorCell
"""

from pathlib import Path
import numpy as np
import io
import json


class _ObjPropertieTable():

    def __init__(self):
        """generates a lookuptable for tags and scalars with abritary IDs
        called properties

        bijective mapping
        """
        self._prop = {}

    def __len__(self):
        return len(self._prop)

    def set_pair(self, idx, prop):
        self._prop[int(idx)] = prop
        self._prop[prop] = int(idx)

    def get_index(self, prop):
        idx = self._prop.get(prop)
        if idx is None:
            idx = len(self._prop)
            self.set_pair(idx, prop)
        return idx

    def get_prop(self, idx):
        try:
            prop = self._prop[int(idx)]
        except KeyError:
            raise IndexError('No property with index {}'.format(idx))
        return prop

    def toJson(self):
        idx_mapping = {idx: prop for idx, prop in self._prop.items() \
                       if isinstance(idx, int)}
        return json.dumps(idx_mapping)

    def fromDict(self, jsonDict):
        for idx, prop in jsonDict.items():
            self.set_pair(int(idx), prop)


class _ObjTable():

    def __init__(self, properties):
        """generates a lookuptable for tags with abritary IDs
        """
        self._objects = []
        self._prop = properties
        self._objcount = 0

        self.tags = set([])

    def __len__(self):
        return self._objcount

    def toJson(self, objId, tags, scalars, contours, ancestors, historical):
        if contours is None:
            contours = []
        try:
            _objId = int(objId)
            if objId - _objId != 0: raise ValueError
            obj = {'id': _objId, 'tags': [], 'scalars': [],
                   'contours': [], 'ancestors': [],
                   'historical': historical}
            self._objects.append(obj)
        except:
            raise ValueError('objId must be unambigiuosly castable to int')

        for tag in tags:
            tag_idx = self._prop.get_index(str(tag))
            obj['tags'].append(tag_idx)

        for sc_name, sc_val in scalars.items():
            idx = self._prop.get_index(str(sc_name))
            obj['scalars'].append((idx, sc_val))

        for cnt in contours:
            cur_cnt = []
            for pnt in cnt:
                pnt = tuple(int(c) for c in np.round(pnt))
                cur_cnt.append(pnt)
            obj['contours'].append(cur_cnt)

        for anc in ancestors:
            obj['ancestors'].append(int(anc))

        ret = json.dumps(obj)
        self._objcount += 1
        return ret

    def fromDicts(self, json_dicts):
        self.tags = set([])
        for obj in json_dicts:
            tags = []
            for idx in obj['tags']:
                a_tag = self._prop.get_prop(int(idx))
                tags.append(a_tag)
                self.tags.add(a_tag)
            obj['tags'] = tags

            scalars = {}
            for idx, val in obj['scalars']:
                scalars[self._prop.get_prop(int(idx))] = val
            # obj['scalars'] = scalars
            obj['scalars'] = {}
            for keyString, val in scalars.items():
                scalarName, scalarType = eval(keyString)
                obj['scalars'][(scalarName, scalarType)] = val
            
            contours = []
            for cnt in obj['contours']:
                cur_cnt = []
                for pnt in cnt:
                    pnt = tuple(int(c) for c in np.round(pnt))
                    cur_cnt.append(pnt)
                contours.append(cur_cnt)
            obj['contours'] = contours

            self._objects.append(obj)

    def to_dicts(self):
        return self._objects.copy()


class _Header():

    def __init__(self, props, objects, version):
        """ is fixed size
        """
        if len(version) > 8:
            raise ValueError('Only 8 chars are possible for version string')
        self._version = version
        self._props = props
        self._objects = objects
        self._magic = '\x06Enty\r\n\x03'
        self.bytesize = 8 * 7

    @property
    def objCount(self):
        return len(self._props)

    @property
    def tagCount(self):
        return len(self._objects)

    def toJson(self):
        # not flushed only in json version
        ret = {
            # 'magicBytes': self._magic, # 8 bytes
            'version': self._version,   # 8 bytes = 8 chars
            'tagCount': self.tagCount,  # 8 bytes = max 2**64 tags
            # 'tagSize': self.tagSize,    # 8 bytes = max 2**64 bytes tag data
            # 'tagAddr': self.tagAddr,    # 8 bytes = max 2**64 bytes in data
            'objCount': self.objCount,  # 8 bytes = max 2**64 objects
            # 'objSize': self.objSize,    # 8 bytes = max 2**64 - 8
        }
        return json.dumps(ret)
    
    def fromJson(self, jsonDict):
        self._tags = jsonDict.copy()


class EntityFile():

    _version = '1.0'

    def __init__(self, buffio, fmt):
        self._props = _ObjPropertieTable()
        self._objects = _ObjTable(self._props)
        self._header = _Header(self._props, self._objects, self._version)

        self._fmt = fmt
        self._buffio = buffio
        
        self.buffer = None

    def __enter__(self):
        if self._fmt == 'binary' and self._buffio.writable():
            self._buffio.seek(self._header.bytesize)
        elif self._fmt == 'json' and self._buffio.writable():
            self._buffio.write('{"objects": [')

        return self

    def __exit__(self, *args, **kwargs):
        self.close()
    
    def close(self):
        if self._buffio is None:
            raise IOError('No file opened!')
        if self._fmt == 'binary' and self._buffio.writable():
            # write tags right now
            # update header
            # seek begin and write header
            pass
        elif self._fmt == 'json' and self._buffio.writable():
            self._buffio.write('],\n"props": ')
            self._buffio.write(self._props.toJson())
            self._buffio.write(',\n"header": ')
            self._buffio.write(self._header.toJson())
            self._buffio.write('}')

        if hasattr(self._buffio, 'close'):
            self._buffio.close()

    def read(self):
        if self._fmt is 'json':
            dat = self._buffio.read()
            dat = json.loads(dat)
            self._props.fromDict(dat['props'])
            self._objects.fromDicts(dat['objects'])

        return self._objects.to_dicts()

    def write(self, objId, tags=[], scalars={}, contours=[], ancestors=[],
              historical=False):
        if self._buffio is None:
            raise IOError('No file opened!')

        if self._fmt is 'json':
            dmp = self._objects.toJson(objId=objId, tags=tags, scalars=scalars,
                                       contours=contours, ancestors=ancestors,
                                       historical=historical)
            if len(self._objects) > 1:
                self._buffio.write(',\n')
            self._buffio.write(dmp)

    def writeEntities(self, entities, sort=True):
        if sort:
            entities.sort(key=lambda ent: ent.eid)
        for ent in entities:
            self.writeEntity(ent)

    def writeEntity(self, entity):
        if entity.parentEid is None:
            anc = []
        else:
            anc = [entity.parentEid]
        self.write(
            objId=entity.eid,
            tags=list(entity.tags),
            scalars=entity.scalars,
            contours=entity.contours,
            ancestors=anc,
            historical=entity.historical,
        )

    @property
    def tags(self):
        return set(self._objects.tags)
    
    @classmethod
    def open(cls, filename, mode):
        if 'b' in mode:
            _mode = mode.replace('b', '')
            fmt = 'enty'
        else:
            _mode = mode
            fmt = 'json'
        if not _mode in ('w', 'r'):
            raise ValueError('Invalid mode: {}'.format(mode))

        filename = Path(filename).with_suffix('.{}'.format(fmt))
        fdesc = filename.open(mode)

        return cls(fdesc, fmt)

    @classmethod
    def open_buffer(cls, mode):
        if 'b' in mode:
            _mode = mode.replace('b', '')
            fmt = 'enty'
        else:
            _mode = mode
            fmt = 'json'
        if not _mode in ('w', 'r'):
            raise ValueError('Invalid mode: {}'.format(mode))

        if fmt == 'json':
            fdesc = io.StringIO()
        elif fmt == 'enty':
            fdesc = io.BytesIO()

        inst = cls(fdesc, fmt)
        inst.buffer = fdesc
        return inst


def read_entity_data(jsonfile, strip=False):
    """Convinience function to read entity data from a json

    Parameterss
    -------------
    jsonfile : str, pathlib.Path
        Path to the json file
    strip : bool (default=True)
        If true, all historic elements are striped from the
        dataset

    Returns
    --------
    ent_data : dict of dict
        Dictionary with all entities.
        .. warning:: The keys `the ent_data` are not the Entiy ID!

    Notess
    ------
    The `ent_data` is a dict of dicts. The nested, inner dicts have at least
    the keys {'id', 'scalars', 'tags', 'contours'}
    """
    with EntityFile.open(jsonfile, 'r') as src:
        ent_data = []
        for ent in src.read():
            if ent['historical'] and strip:
                continue
            ent_data.append(ent)

    entities = []
    for entry in ent_data:
        entry['contour'] = contour = []
        for cur_cont in entry.pop('contours'):
            contour.append(np.array(cur_cont).astype(int))
        entities.append(entry)

    return entities


#XXX reuse or delete 
#         entityData = []
# 
#         for entityDict in entityDicts:
#             # get data or defaults
#             eid = entityDict['id']
#             contours = entityDict['contours']
#             tags = entityDict.get('tags', [])
#             scalars = entityDict.get('scalars', {})
#             historic = entityDict.get('historic', False)
#             ancestors = entityDict.get('ancestors', [])
# 
#             # normalize contour data
#             contours = [np.round(np.array(cont)) for cont in contours]
#             contours = [cont.astype(int) for cont in contours]
#             entityData.append({'id': eid,
#                                 'contour': contours,
#                                 'tags': tags,
#                                 'scalars': scalars,
#                                 'historical': historical,
#                                 'ancestors': []})





#TODO MAKE ME A TEST!
# # with CellObjFile.open_buffer('w') as trgt:
# with CellObjFile.open('testj', 'w') as trgtj:
#     with CellObjFile.open('testb', 'wb') as trgtb:
#         for trgt in (trgtj, trgtb):
#             trgt.write(1, tags=['a', 'b'], scalars={'a': 1, 'b':0},
#                        contours=[[(0, 0), (1, 4), (2, 2)]], ancestors=[],
#                        historic=False)
# 
#             trgt.write(10, tags=['c', 'b'], scalars={'a': 1, 'c':-30},
#                        contours=[[(10, 10), (11, 15), (12, 12)]],
#                        ancestors=[100], historic=False)
#             trgt.write(100, tags=['c'], scalars={}, contours=[],
#                        ancestors=[111], historic=True)
#             trgt.write(111, tags=['c'], scalars={'c': 42}, contours=[],
#                        ancestors=[], historic=True)
# 
# with CellObjFile.open('testj', 'r') as trgt:
#     objectsj = trgt.read()
# 
# with CellObjFile.open('testb', 'rb') as trgt:
#     objectsb = trgt.read()
# 
# print('json readback')
# for obj in objectsj:
#     print(obj)
# 
# for obj in objectsb:
#     print(obj)
