# -*- coding: utf-8 -*-
from pathlib import Path
import logging
import numpy as np

import json
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile

import cv2

import dataframework
from dataframework import ImageStack, MapGen, ObjGen, TiffImage

from .logutil import get_logger_name
from .util import get_tempdir, parse_orange


class DataLoader():
    """ Implements functions to load data
    """

    def __init__(self, logger_name=None, marker_db_path=None):
        self._istack_log_name = get_logger_name(name='ImageStack',
                                                domain=logger_name)
        self.log = logging.getLogger(get_logger_name(name=logger_name))

        self.log.info('Using dataframework v{}'.format(
            dataframework.__version__))

        # just to have them defined in the init. it is ugly but it is
        # rare
        self._ims, self._obg, self._mpg, self._cache, self._tags = self.clear()

        self.zipmap_name = 'objmap.tif'
        self.zipdat_name = 'objdat.json'
        self.zipext = 'obj.zip'

        self._marker_db_path = marker_db_path

    def clear(self):
        """ returns a clear state for the datamanager, to prevent
        corruption
        """
        self._ims = None
        self._obg = None
        self._mpg = MapGen()
        self._cache = {}
        self._loaded = {}
        self._tags = set([])
        return self._ims, self._obg, self._mpg, self._cache, self._tags

    def load_imagedir(self, dir_path):
        """loads a dir_path as image stack
        """
        self._ims = ImageStack(logger_name=self._istack_log_name,
                               marker_db_path=self._marker_db_path)
        self._ims.load_from_dir(dir_path)

        # link imagestack and mapgen
        self._mpg.image_stack = self._ims

        # clear cache, as it might have changed
        self._cache = {}

        if self._obg is None:
            self._add_objectgen()

    def load_image_selection(self, image_paths):
        if self._ims is None:
            self._ims = ImageStack(logger_name=self._istack_log_name,
                                   marker_db_path=self._marker_db_path)
        for img_path in image_paths:
            self._ims.add_image(img_path)

        # link imagestack and mapgen
        self._mpg.image_stack = self._ims

        # clear cache, as it might have changed
        self._cache = {}

        if self._obg is None:
            self._add_objectgen()

    def _add_objectgen(self):
        """adds an empty object generator based on imagestack
        shape
        """
        oid_data = np.zeros(self._ims.shape, dtype='uint16')
        self._set_obg(oid_data)

    def _set_obg(self, oid_data):
        """creates an object generator on oid_data
        """
        self._obg = ObjGen(oid_data)

        # generate objects
        self._obg.generate_objects(oid_data)

        # link objectgen and mapgen
        self._mpg.obj_gen = self._obg

    def objects_from_map(self, objid_map_path):
        """creates objects from a objid map
        """
        # load image containing object infromation
        oidmap = TiffImage()
        oidmap.load_pixeldata_from(objid_map_path)

        self.objects_from_array(oidmap.pixel_data)

    def objects_from_array(self, objid_map):
        self._mpg.objid_map = objid_map

        self._set_obg(objid_map)

        # clear cache, as it might have changed
        self._cache = {}

    def save_object_map(self, map_path):
        """saves current objectmap to map_path
        Overwrites files! Requires the app to ask if overwriting is ok!

        Raises
        ------
        ValueError : if object_id map is not set
        """
        # load image containing object infromation
        oidmap = TiffImage()
        oidmap.pixel_data = self._mpg.objid_map
        if oidmap.pixel_data is None:
            raise ValueError('Object ID map is not set!')

        oidmap.save_pixeldata_to(str(map_path), overwrite=True)


class DataProxy(DataLoader):
    """Implements direct access to low level properties of the internal classes
    """

    @property
    def marker_list(self):
        """returns marker loaded by the ImageStack
        """
        if self._ims is None:
            raise ValueError('No images loaded yet!')

        return self._ims.marker_list

    @property
    def objects(self):
        """returns marker loaded by the ImageStack
        """
        if self._obg is None:
            raise ValueError('No objects loaded yet!')

        return self._obg.objects


class DataManager(DataProxy):
    """renders images based on the loaded images in the image stack
    not objects
    """

    _valid_res = ['tags.rgba', 'merge.rgb', 'merge.rgba', 'overlay.rgba']

    def _get_cached(self, key, func, args=(), kwargs={}, name=None):
        """abstract caching
        """
        #TODO cache class
        cache_entry = self._cache.get(key, {})

        if not name is None:
            all_names = self.get_cached_names()
            suffix = 1
            new_name = name
            while new_name in all_names:
                new_name = '{}_{}'.format(name, suffix)
                suffix += 1
            name = new_name

        if cache_entry == {}:
            self.log.debug('Generating %s', key)
            # None name is 'invisible'
            # if name is None:
            #     rtype, arglist = key
            #     argstr = ', '.join(arglist)
            #     name = rtype + '-' + argstr
            ret = func(*args, **kwargs)

            cache_entry['name'] = name
            cache_entry['ret'] = ret

            self._cache[key] = cache_entry
            return self._cache[key]

        self.log.debug('Using cached %s', key)
        return cache_entry

    def load_overlay_map_image(self, path):
        key = self._get_key(res_type='overlay.rgba',
                            unique_arglist=(str(path),))

        image = cv2.imread(str(path), cv2.IMREAD_ANYCOLOR)
        if image is None:
            self.log.error('Could not load %s', str(path))
            return

        if image.dtype == np.uint16:
            maxval = 0xffff
            bits = '16'
        elif image.dtype == np.uint8:
            maxval = 0xff
            bits = '8'
        else:
            self.log.error('Invalid datatype: %s', str(image.dtype))
            raise ValueError('Invalid image format!')

        if len(image.shape) == 2:
            img_type = 'mono'
            new_shape = image.shape + (4,)
            rgba_img = np.zeros(new_shape, image.dtype)
            rgba_img[:, :, :-1] = image.reshape(image.shape + (1,))
            rgba_img[:, :, -1] = maxval
        elif len(image.shape) == 3:
            if image.shape[-1] == 3:
                img_type = 'RGB'
                new_shape = image.shape[:-1] + (4,)
                rgba_img = np.zeros(new_shape, image.dtype)
                rgba_img[:, :, :-1] = image
                rgba_img[:, :, -1] = maxval
            elif image.shape[-1] == 4:
                img_type = 'RGBA'
            elif not image.shape[-1] in (3, 4):
                self.log.error('Invalid format %s', str(image.shape))
                raise ValueError('Invalid image format!')

        msg = 'Loading %s image from %s with %s @ %s bit'
        self.log.debug(msg, img_type, str(path), str(image.shape), bits)
        
        transparent_rgba = self._with_transparency(rgba_img)
        loaded_entry = {'ret': transparent_rgba,
                       'name': str(Path(path).name),}
        self._loaded[key] = loaded_entry

    def load_map_selection(self, map_pathes):
        for map_path in map_pathes:
            try:
                self.load_overlay_map_image(map_path)
            except ValueError:
                self.log.error('Could not load %s', str(map_path))

    def get_merge_overlay(self, marker_list):
        """get a merge of different markers
        """
        key = self._get_key(res_type='merge.rgba',
                            unique_arglist=marker_list)
        entry = self._get_cached(key, self._mpg.get_merge_overlay,
                                 args=(marker_list,))
        return entry['ret']

    def get_merge_bg(self, marker_list):
        """get a merge of different markers
        """
        key = self._get_key(res_type='merge.rgb',
                            unique_arglist=marker_list)
        entry = self._get_cached(key, self._mpg.get_merge_background,
                                 args=(marker_list,))
        return entry['ret']

    def get_raw_image(self, marker_name):
        """get a merge of different markers
        """
        self.log.debug('Looking up marker %s', marker_name)
        if not self.markers_loaded:
            self.log.error('No markers loaded!')
        try:
            img = self._ims.get_imagedata(marker_name)
            return img
        except KeyError:
            self.log.error('Marker %s not found in stack', marker_name)

    def get_object_overlay(self, alpha=1):
        """get map of generated objects
        """
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')
        ret = self._mpg.get_object_overlay(alpha=alpha)
        return self._with_transparency(ret)

    def _with_transparency(self, rgba):
        zeros = rgba[:,:,:-1] == 0
        transp = np.all(zeros, axis=2)
        rgba[:,:,-1][transp] = 0
        return rgba

    def get_empty_image(self):
        """get an empty marker image
        """
        if not self.markers_loaded:
            return np.zeros((2, 2), np.uint16)
        else:
            return self._ims.get_black_image()

    def get_empty_map(self):
        """get empty rgba map with dimension of imstack
        """
        if not self.markers_loaded:
            return np.zeros((2, 2, 4), np.uint8)
        else:
            dim = self._ims.get_black_image().shape
            ret = np.zeros((dim[0], dim[1], 4), np.uint8)
            return ret

    def get_object_map(self):
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')
        return self._mpg.objid_map.copy()

    def get_object(self, object_id):
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')
        return self._obg.get_object(object_id)

    def update_objects(self, object_list):
        """expects a list of objects, updates
        the already stored objects with the new ones

        Only updates, never creates!
        """
        try:
            for obj in object_list:
                old = self.get_object(obj.id)
                old.tags = set(obj.tags)
        except KeyError:
            msg = 'No object with id {} that can be updated'
            raise ValueError(msg.format(obj.id))

    def get_object_tags(self):
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')
        tags = set([])
        for obj in self.objects:
            tags.update(set(obj.tags))
        return tags

    def save_object_data(self, data_path):
        # bring obj data into json format
        obj_data = {}
        for obj in self.objects:
            new_obj = obj_data[str(obj.id)] = {}
            new_obj['tags'] = list(obj.tags)

        ### dump everyting into the tempory file
        # dump the object data
        with Path(data_path).open('w') as obj_file:
            json.dump(obj_data, obj_file, ensure_ascii=False)

    def load_object_data(self, data_path):
        # dump the object data
        with data_path.open('r') as obj_file:
            obj_data = json.load(obj_file, ensure_ascii=False)

        new_objects = {}
        for obj_id, obj_data in obj_data.items():
            new_obj_data = {'tags': obj_data['tags']}
            new_objects[int(obj_id)] = new_obj_data

        self.set_object_data(new_objects)

    def set_object_data(self, object_data):
        for obj_id, obj_data in object_data.items():
            a_obj = self.get_object(obj_id)
            # implicit copy, ensure tha we can append later on
            a_obj.tags = set(obj_data['tags'])

    def save_object_zip(self, zip_path):
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')

        with get_tempdir() as temp_dir:
            map_path = Path(temp_dir) / self.zipmap_name
            dat_path = Path(temp_dir) / self.zipdat_name

            # save everyting to disk
            self.save_object_map(map_path)
            self.save_object_data(dat_path)

            # create the zipfile
            with ZipFile(str(zip_path), 'w', ZIP_DEFLATED) as zipf:
                zipf.write(str(map_path), map_path.name)
                zipf.write(str(dat_path), dat_path.name)

    def load_object_zip(self, zip_path):
        with get_tempdir() as temp_dir:
            map_path = Path(temp_dir) / self.zipmap_name

            try:
                with ZipFile(str(zip_path), 'r', ZIP_DEFLATED) as zipf:
                    # obj map
                    zipf.extract(self.zipmap_name, temp_dir)
                    new_obj_dat = zipf.read(self.zipdat_name)
                    new_obj_dat = new_obj_dat.decode('utf-8')
                    json_obj_dat = json.loads(new_obj_dat)
            #       not correct zip or json object
            except (KeyError, json.JSONDecodeError):
                raise IOError('Not a valid .obj.zip file!')

            try:
                self.objects_from_map(map_path)
            # couldn't read the tif oidmap
            except ValueError:
                raise IOError('Not a valid .obj.zip file!')

            # obj data
            obj_dat = {}
            for a_obj_id, a_obj_dat in json_obj_dat.items():
                new_obj_dat = obj_dat[int(a_obj_id)] = {}
                new_obj_dat['tags'] = a_obj_dat['tags']

            self.set_object_data(obj_dat)

    def _get_key(self, res_type, unique_arglist):
        if res_type not in self._valid_res:
            raise ValueError('Invalid res-type!')
        unique_arglist = tuple(str(arg) for arg in unique_arglist)
        return (res_type, unique_arglist)

    def get_tag_overlay(self, tags, name, alpha=1):
        if not self.objects_loaded:
            raise ValueError('Load/Create objects first!')

        key = self._get_key(res_type='tags.rgba',
                            unique_arglist=tags)
        entry = self._get_cached(key, self._mpg.get_tagcolor_overlay,
                                 args=(tags, alpha), name=name)
        return entry['ret']

    def get_tags(self):
        try:
            obj_tags = set(self.get_object_tags())
        except ValueError:
            self.log.debug('Could not load tags. Objects not generated')
            obj_tags = set([])
        custom_tags = set(self._tags)
        return obj_tags, custom_tags

    def set_custom_tags(self, taglist):
        self._tags = set(taglist)

    def get_cached_names(self):
        all_names = set([])
        for cache_entry in self._cache.values():
            name = cache_entry.get('name', None)
            if name is None: continue
            all_names.add(name)

        for loaded_entry in self._loaded.values():
            name = loaded_entry.get('name', None)
            if name is None: continue
            all_names.add(name)

        return all_names

    def get_by_name(self, name):
        cached = None
        loaded = None

        for cache_entry in self._cache.values():
            entry_name = cache_entry.get('name', None)
            if entry_name == name and not entry_name is None:
                cached = cache_entry['ret']

        for loaded_entry in self._loaded.values():
            entry_name = loaded_entry.get('name', None)
            if entry_name == name and not entry_name is None:
                loaded = loaded_entry['ret']

        if not cached is None:
            return cached
        elif not loaded is None:
            return loaded
        else:
            return None

    @property
    def objects_loaded(self):
        obg = not self._obg is None
        mpg = not self._mpg.objid_map is None
        return obg and mpg

    @property
    def markers_loaded(self):
        ims = not self._ims is None
        return ims
