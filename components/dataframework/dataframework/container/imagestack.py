# -*- coding: utf-8 -*-
"""Handling image and metadata, make both accessible
"""

import logging
from pathlib import Path

import numpy as np

from ..processing import OMETiff
from ..processing.fsparser import get_fsparser


class ImageStack():
    """Does all the globing, parsing and so on.
    is the abstract representation of an dir with
    all the images and metadatastuff
    """

    def __init__(self, logger_name='ImageStack', marker_db_path=None):
        self._log = logging.getLogger(logger_name)

        self._idx_scheme = '{} - {}'

        self.dirpath = None
        self.ignored = None

        self.images = None
        self.marker_list = []

        self.shape = None

        self._fsparser = get_fsparser(marker_db_path)
        self._zeros = np.array([], dtype=np.uint16)

    def __len__(self):
        """Number of images
        """
        if self.images is None:
            return 0
        else:
            return len(self.images)

    def add_image(self, img_path, update_markerlist=True):
        if self.images is None:
            self.images = []
        img_path = Path(img_path)
        new_img = self._add_image(img_path)
        if new_img is None:
            msg = '%s is invalid (ome.)tiff, skipping'
            self._log.debug(msg, img_path.name)
            self.ignored.append(str(img_path))
            return

        if update_markerlist:
            self._generate_markerlist()

    def load_from_dir(self, dir_path):
        """Processes a dir
        """
        self.dirpath = dir_path = Path(dir_path)
        self.ignored = []

        if not dir_path.exists() or not dir_path.is_dir():
            msg = 'Invalid path: {}'.format(str(dir_path))
            self._log.error(msg)
            raise ValueError(msg)

        self.images = []
        for image_path in dir_path.glob('*.[Tt][Ii][Ff]*'):
            # get metadata if possible
            self.add_image(image_path, update_markerlist=False)

        # generate markerlist
        self._generate_markerlist()

    def _generate_markerlist(self):
        """generate a marker list. double entries are
        marked by indices
        """
        marker_list = [img.marker for img in self.images]
        all_marker = set(marker_list)

        for marker in all_marker:
            i = marker_list.count(marker)

            if i == 1: # nothing todo here
                continue

            while i:
                idx_i = marker_list.index(marker)
                marker_list[idx_i] = self._idx_scheme.format(marker, i-1)
                i = marker_list.count(marker)

        self.marker_list = marker_list

    def _get_tiff(self, image_path):
        """gets tiffs stored at image path. Tries
        to read as Tiff, returns None if not a tiff
        """
        # get the tiff
        ret_img = OMETiff()
        # read the ifds
        try:
            ret_img.read_ifds(image_path)
        except ValueError:
            return None

        return ret_img

    def _add_image(self, image_path):
        """adds image found at image_path
        adds parameter needed for caching
        """
        image_name = image_path.name

        ret_img = self._get_tiff(image_path)

        # extract meta data
        try:
            ret_img.read_xml()
        except ValueError:
            # is not an OME tiff, parse filename
            # whipe ifds
            ret_img = self._get_tiff(image_path)
            meta_data = self._fsparser.extract_from_imagename(image_name)
            marker = meta_data.get('marker', None)
            if marker is None:
                return None
            ret_img.set_metadata(marker=marker)
        except AttributeError:
            # was not a tiff, _get_tiff returned None hence attribute error
            # all is lost, killing self, returning None, NIL, nada
            return None

        # attatch the image path for later use
        ret_img.cached_path = image_path
        # set and check shape
        self._set_shape(ret_img)
        self.images.append(ret_img)

        return ret_img

    def _set_shape(self, from_img):
        """sets and checks correct shape of image
        raises error if invalid shapes are found
        """
        if self.shape is None:
            self.shape = from_img.shape
            self._zeros = np.zeros(shape=from_img.shape,
                                   dtype=np.uint16)
        elif self.shape != from_img.shape:
            raise ValueError('Inconsisten Image shapes!')

    def get_image(self, marker):
        """gets the image instance
        """
        if not marker in self.marker_list:
            msg = 'marker {} is not found!'
            raise KeyError(msg.format(marker))

        # we checked there are no doubles on creation
        idx = self.marker_list.index(marker)

        return self.images[idx]

    def get_imagedata(self, marker):
        """gets an image by marker
        does on the fly loading
        """
        marker_img = self.get_image(marker)

        if marker_img.pixel_data is None:
            marker_img.load_pixeldata_from(marker_img.cached_path)

        return marker_img.pixel_data

    def get_imagedata_origin(self, marker):
        """gets the original data source for an image by marker,
        if any was loaded. if not it tries to return the cached path
        returns None, if there is no source infromation at all
        """
        marker_img = self.get_image(marker)
 
        origin = None
        if marker_img.pixel_data_origin is None:
            try:
                origin = marker_img.cached_path
            except AttributeError:
                origin = None
        else:
            origin = marker_img.pixel_data_origin

        return origin

    def get_black_image(self):
        """returns a cached instance of background image
        of shape
        """
        return self._zeros
