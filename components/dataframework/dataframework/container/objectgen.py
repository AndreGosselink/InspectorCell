# -*- coding: utf-8 -*-
"""All the objects classes and their managers live here
"""
import logging
import queue
import threading as th

import numpy as np


class ImgObj():
    """container for objects found in image
    """
    def __init__(self, objid):
        """boundingbox : (rmin, rmax, cmin, cmax)
        """
        self.tags = set([])
        self.scalars = {}

        if objid <= 0:
            msg = 'Invalid objectid, must be >= 1, got {}'
            raise ValueError(msg.format(objid))
        self.id = objid
        
        self.scalars = {}
        self.slice = None
        self.bbox = None
        self.bmask = None

    def __ge__(self, other):
        return self.id.__ge__(other.id)

    def __le__(self, other):
        return self.id.__le__(other.id)

    def __ne__(self, other):
        return self.id.__ne__(other.id)

    def __gt__(self, other):
        return self.id.__gt__(other.id)

    def __lt__(self, other):
        return self.id.__le__(other.id)

    def __eq__(self, other):
        return self.id.__eq__(other.id)

    def set_masks(self, bounding_box, bool_mask):
        """sets boundingbox, slice and mask in slice
        takes the whole image mask, saves only the part within the slice
        """
        try:
            rmin, rmax, cmin, cmax = bounding_box
        except ValueError:
            msg = 'bounding_box parameter must be a sequnence of 4 int, got {}'
            raise ValueError(msg.format(len(bounding_box)))

        # bbox_shape = (rmax-rmin, cmax-cmin)
        # if bool_mask.shape != bbox_shape:
        #     msg = 'Bounding box to small for bounding mask {} != {}'
        #     raise ValueError(msg.format(bool_mask.shape, bbox_shape))

        self.slice = np.s_[rmin:(rmax+1), cmin:(cmax+1)]
        self.bbox = (rmin, rmax, cmin, cmax)
        self.bmask = bool_mask[self.slice].copy()

    def set_masks_slice(self, bounding_box, bool_mask):
        """sets boundingbox, slice and mask
        mask must be same dim as bounding_box
        """
        try:
            rmin, rmax, cmin, cmax = bounding_box
        except ValueError:
            msg = 'bounding_box parameter must be a sequnence of 4 int, got {}'
            raise ValueError(msg.format(len(bounding_box)))

        bbox_shape = (rmax-rmin+1, cmax-cmin+1)
        if bool_mask.shape != bbox_shape:
            msg = 'Bounding box to small for bounding mask {} != {}'
            raise ValueError(msg.format(bool_mask.shape, bbox_shape))

        self.slice = np.s_[rmin:(rmax+1), cmin:(cmax+1)]
        self.bbox = (rmin, rmax, cmin, cmax)
        self.bmask = bool_mask.copy()


class ObjGen():
    """Keeps track of objects, generates them
    handles writing, saving and so on and so forth
    """

    def __init__(self, objid_map=None, logger_name='ObjGen'):
        self._log = logging.getLogger(logger_name)

        self._sorted_objects = None
        self._objects_dict = None

        if not objid_map is None:
            self.generate_objects(objid_map)

    def get_object_generators(self, objid_map, number=3):
        def _gen(object_ids, objid_map):
            for cur_id in object_ids:
                bbox, bmask = get_masks(cur_id, objid_map)
                cur_obj = ImgObj(cur_id)
                cur_obj.set_masks_slice(bbox, bmask)
                yield cur_obj

        self._objid_map = objid_map.copy()

        valid_ids = list(set(objid_map[objid_map > 0]))
        total_ids = len(valid_ids)
        generators = []
        ids_per_process = total_ids // number

        for _ in range(number - 1):
            id_slice = valid_ids[:ids_per_process]
            if id_slice:
                gen = _gen(id_slice, objid_map)
                generators.append(gen)
            valid_ids = valid_ids[ids_per_process:]

        # get the last bits
        gen = _gen(valid_ids, objid_map)
        generators.append(gen)

        return generators

    def generate_objects(self, objid_map):
        """Generates ImgObj instances from objid_map
        keeps copy of objid map used for generation
        """
        if objid_map.dtype != np.dtype('uint16'):
            raise ValueError('objid_map must be uint16!')

        self._objects_dict = {}

        obj_gens = self.get_object_generators(objid_map, 1)
        self._add_from_generators(obj_gens)

        self._log.debug('Generated %d objects!', len(self._objects_dict))

    def _add_from_generators(self, object_generators):
        for ogen in object_generators:
            for obj in ogen:
                self.add_object(obj, update_map=False)

    def generate_objects_threaded(self, objid_map, cpus=3):
        """Generates ImgObj instances from objid_map
        keeps copy of objid map used for generation
        """
        if objid_map.dtype != np.dtype('uint16'):
            raise ValueError('objid_map must be uint16!')
        
        # TODO unify this into a "set_map" method and use it instead of scater
        # it all around
        self._objects_dict = {}
        self._objid_map = objid_map.copy()

        def _pipe(que, gen):
            for obj in gen:
                que.put(obj)

        que = queue.Queue()
        threads = []
        obj_gens = self.get_object_generators(objid_map, cpus)
        for gen in obj_gens:
            thr = th.Thread(target=_pipe, args=(que, gen))
            threads.append(thr)
            thr.start()
        
        for thr in threads:
            thr.join()

        for _ in range(que.qsize()):
            new_obj = que.get()
            self.add_object(new_obj, update_map=False)

        self._log.debug('Generated %d objects!', len(self._objects_dict))

    def get_object(self, objid):
        """gets object by id

        Raises
        ------
        KeyError : if object id is not found
        """
        try:
            return self._objects_dict[objid]
        except TypeError:
            msg = 'Object with ID {objid} not found'
            raise KeyError(msg.format(objid))

    def delete_object(self, objid):
        """delete object by id

        Raises
        ------
        KeyError : if object id is not found
        ValueError : if no map was loaded
        """
        if self._objid_map is None:
            raise ValueError('No map was loaded or created!')

        try:
            #TODO remove the double ref entries
            delete_me = self._objects_dict.pop(objid)
            self._paint_object(delete_me, value=0)
            self._sorted_objects = None
        except (TypeError, KeyError):
            msg = 'Object with ID {objid} not found'
            raise KeyError(msg.format(objid))

        return delete_me

    def set_free_oid(self, new_object):
        """Sets oid to a free one. if new_objects
        id is not taken, it stays

        Raises
        ------
        ValueError : if no map was loaded
        """
        if self._objid_map is None:
            raise ValueError('No map was loaded or created!')

        other = self._objects_dict.get(new_object.id, None)
        if other is None:
            return

        # def find_missing(d):
        left = 0
        right = len(self.objects) - 1

        if self.objects[right].id == len(self.objects):
            self._log.debug('fast free id')
            return len(self.objects) + 1

        if self.objects[left].id != 1:
            self._log.debug('fast free id')
            return 1

        while True:
            mid = left + (right - left) // 2
            val = self.objects[mid].id - 1
            if val != mid:
                right = mid
            else:
                left = mid
            if right - left == 1:
                break

        lval = self.objects[left].id
        rval = self.objects[right].id

        if rval - lval <= 1:
            self._log.debug('missed...')
            return len(self.objects) + 1

        new_object.id = lval + 1

    def add_object(self, obj, update_map=True):
        """add an object, the id will be changed according to
        the available ids in the map.
        mask must be set!

        Raises
        ------
        KeyError : if object id is not found
        ValueError : if no map was loaded
        """
        if self._objid_map is None:
            raise ValueError('No map was loaded or created!')

        if self._objects_dict is None:
            self._objects_dict = {}

        self.set_free_oid(obj)

        if not self._objects_dict.get(obj.id) is None:
            msg = 'set_free_oid() set id to {} which is alredy in use!'
            raise RuntimeError(msg.format(obj.id))

        self._objects_dict[obj.id] = obj
        self._sorted_objects = None

        if update_map:
            self._paint_object(obj)

    def _paint_object(self, obj, value=None):
        """updates the object id map as found according to obj
        bbox and mask
        if value != None then the objid is written, oterhwise the value
        """
        rmin, rmax, cmin, cmax = obj.bbox
        msl = np.s_[rmin:rmax+1, cmin:cmax+1]
        if value is None:
            paint_val = obj.id
        else:
            paint_val = value

        self._log.debug('Painting object %d @%s to %d', obj.id, str(obj.bbox),
                        paint_val)

        self._objid_map[msl][obj.bmask] = paint_val

    @property
    def objects(self):
        if self._sorted_objects is None:
            self._sorted_objects = list(self._objects_dict.values())
            self._sorted_objects.sort()
        return self._sorted_objects


def get_masks(object_id, idmap, seek=110):
    """returns the view bounds for the binary seg mask
    meaning first/last cols and rows indices defining the bounding box

    returns
    -------
    bounds : tuple
        bounds = (rmin, rmax, cmin, cmax)

    bool_mask : bool ndarray

    notes
    -----
    bounds is closed thus rmin and rmax are both pixels in the box
    while slices are half open!
    """
    first_index = np.argmax(idmap == object_id)
    row, col = np.unravel_index(first_index, idmap.shape)
    max_row, max_col = idmap.shape

    row0 = max(row-seek, 0)
    col0 = max(col-seek, 0)
    row1 = min(row+seek, max_row)
    col1 = min(col+seek, max_col)

    bool_mask = idmap[row0:row1, col0:col1] == object_id
    # print_ascii(bool_mask)

    rows = np.any(bool_mask, axis=1)
    cols = np.any(bool_mask, axis=0)

    rownum, colnum = bool_mask.shape
    rmin, rmax = np.argmax(rows), rownum - np.argmax(rows[::-1]) - 1
    cmin, cmax = np.argmax(cols), colnum - np.argmax(cols[::-1]) - 1

    bmask = bool_mask[rmin:rmax+1, cmin:cmax+1]

    rmin += row0
    rmax += row0
    cmin += col0
    cmax += col0

    return (rmin, rmax, cmin, cmax), bmask
