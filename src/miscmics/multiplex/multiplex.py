# -*- coding: utf-8 -*-
"""Handling image and metadata, make both accessible
"""
from typing import List, Iterable
import copy
import logging
from pathlib import Path

import imageio
from PIL import Image

import numpy as np

from ..util import find_matches


LOG = logging.getLogger(__name__)
# logging.captureWarnings(True)


#TODO make me a dataclass?
class ImageStack():
    """Does all the globing, parsing and so on.
    is the abstract representation of an dir with
    all the images and metadatastuff

    handels meta data provided by the reader is simply attached
    to the image data by the meta attribute.

    methods for manipulating the image data and metadata directly
    """

    def __init__(self, reader=None, meta: dict = None):
        self.data = []
        self._reader = reader

        if meta is None:
            self.meta = {}
        else:
            self.meta = copy.deepcopy(meta)

        try:
            uri = self.meta['uri']
            LOG.warning('Found URI %s, might be overwritten!', str(uri))
        except KeyError:
            self.meta['uri'] = generic_uri()

    def __str__(self):
        ret = [f'{k}: {v}' for k, v in self.meta.items()]
        ret = '|'.join(ret)
        return f'<ImageStack - {ret}>'

    def get_stack(self, metaqueries: List[dict],
                  deep: bool = False) -> 'ImageStack':
        """Returns all data where matching metadata as ImageStack

        Parameter
        ---------
        metaqueries : List[dict]
            List of metaquery dicts as used in `ImageStack.find`. Each
            metaquery must unambigious return exactly on image.

        deep : bool
            If `False` (default) the actual image and metadata is just
            referenced by the new ImageStack. If deep is `True`, all data
            including all metadata is copyied deeply into the new ImageStack.

        Returns
        -------
        ndimg : ImageStack
            An ImageStack only containing the data as defined by the
            metaqueries. All metadata is copied.

        Raises
        ------
        ValueError
            If any of the metaqueries returns no or multiple images
            or if the dimension of the images for each channel are different
            or if the single channel images have more than one channel.
            -> ch.shape == (y, x) OR ch.shape == (y, x, 1)
        """
        channels = []
        for qures, mqu in zip(self.find_multiple(metaqueries), metaqueries):
            try:
                cand_ch, = qures
                channels.append(cand_ch)
            except ValueError:
                msg = f"'{str(mqu)}' returns {len(qures)} images but must be 1."
                raise ValueError(msg)
        
        if deep:
            new_stack = self.fromarray(channels, meta=self.meta)
            for new_img, src_img in zip(new_stack.data, channels):
                new_img.meta.update(src_img.meta)
        else:
            new_stack = self.fromarray([])
            new_stack.data = channels

        new_stack.meta.update(self.meta)

        return new_stack
    
    @classmethod
    def fromarray(cls, data: Iterable, meta: dict = None):
        """Create a new ImageStack from an iterable

        Data will be fully copied!
        
        Parameter
        ---------
        data : Iterable
            Iterable to use for creation of new ImageStack
            Each item in the iterabel must be convertabel
            to an numpy array. The order of data in the
            data is preserved in ImageStack.data

        meta : dict
            Meta data for the image stack. Metadata for channels
            can be set by iterating over ImageStack.data

        Returns
        -------
        stack : ImageStack
            New image stack with `data` from
        """

        new_stack = cls(meta=meta)
        for cur_ch in data:
            new_stack.add_image(image_data=imageio.core.Array(cur_ch),
                                meta_data={})

        return new_stack

    def get_ndimage(self) -> imageio.core.Array:
        """Returns all data where matching metadata as ndimage

        Returns
        -------
        ndimg : imageio.core.Array
            An ndimage with shape (x, y, c) where x and y are the dimension
            and c ist the number of channels. In c = 0...n is the image data
            that matches the repective entriy in metaqueries[0...n]

            The metadata of the ndimage keeps the metaqueris and uri
        """

        chans = []
        nd_meta = []
        for cur_ch in self.data:
            cur_meta = copy.deepcopy(cur_ch.meta)
            cur_ch = np.array(cur_ch).squeeze()
            if len(cur_ch.shape) != 2:
                msg = f'Image {str(cur_meta)} is not grayscale, with' +\
                      f' image shape {cur_ch.shape}'
                raise ValueError(msg)
            chans.append(cur_ch)
            nd_meta.append(cur_meta)

        # create ndimg
        try:
            ret = imageio.core.Array(np.dstack(chans))
        except ValueError:
            lst = ', '.join(str(np.shape(ch)) for ch in chans)
            raise ValueError(f'Could not stack channels with shapes: {lst}')

        # add metadata
        ret.meta.update(copy.deepcopy(self.meta))
        ret.meta['channels'] = nd_meta

        return ret

    def find_multiple(self, metaqueries):
        """Returns all data where a matching metadata

        list of images generated from multiple queries. ordered according to
        queries. Synthactic sugar for
        `[ImageStack.find(mq, single=False) for mq in metaqueries]`

        Parameter
        ---------
        metaqueries : List[dict]
            List of metaquery dicts as used in `ImageStack.find`

        Returns
        -------
        images : List[List[imageio.core.Array]]
            List of images found by the metaqueries. If an metaquery did
            not return any matches, an empty list is appended
        """
        # process the queries
        ret = []
        for metaq in metaqueries:
            chan = self.find(metaq, single=False)
            ret.append(chan)
        return ret

    def find(self, metaquery, single=True) -> List[imageio.core.Array]:
        """Returns all data where matching metadata

        Parameter
        ---------
        metaquery : Dictionary
            Abritary key and values. Each provided key is match
            againts data.meta. If the meta value matches the provided
            value

        single : bool (default True)
            If True, return only first match, else a list of all
            data matching the metaquery

        Returns
        -------
        ret : List[imageio.core.Array]
            List of images that match the metaquere
        """
        return find_matches(metaquery, self.data, single)

    def unique(self):
        """Returns all unique values in the metadata

        Returns
        -------
        unique_meta : Dictionary
            Dictionary with key beeing the meta data field name and
            the value is the list of all unique values for the respective
            field

        Note
        ----
        Does not assume homogenity of the data. Hence some unique meta
        data entries might be only applicable for part of the data stored
        -> uniquness only given on a per atrtibute level
        """
        unique = {}

        for dat in self.data:
            for key, val in dat.meta.items():
                uni = unique.get(key, set())
                uni.add(val)
                unique[key] = uni

        return unique

    # TODO read this uri, the reader will do the pasring of uri
    def read_dir(self, dir_path):
        """globs through dir_path and processes all images with
        image loader.
        """

        # if self.meta.get('uri') is None:
        #     self.meta['uri'] = str(dir_path)
        # else:
        #     LOG.error('Can only load once!')
        #     return

        # TODO askt the reader if exist, what are the components, etc.
        dir_path = Path(dir_path)

        if not dir_path.exists() or not dir_path.is_dir():
            # raise ValueError('Does not exist or is not a dir')
            LOG.error('%s does not exist or is not a dir', str(dir_path))
            return

        # TODO for image in reader
        for file_path in dir_path.glob('*.*'):
            # TODO only return the image_data with metadata already attatched
            image_data, meta_data = self._reader(file_path)

            if image_data is None:
                LOG.debug('Dismissing %s', str(file_path))
                continue

            # NOTE core functionality
            LOG.debug('Adding %s', str(file_path))
            self.add_image(image_data, meta_data)

    # TODO write to this uri, use the writer
    # shoudl go into a writer class
    def write_dir(self, dir_path, name_sheme='{name}.tif'):
        dir_path = Path(dir_path)

        if not dir_path.exists() or not dir_path.is_dir():
            # raise ValueError('Does not exist or is not a dir')
            LOG.error('%s does not exist or is not a dir', str(dir_path))
            return

        for img_data in self.data:
            img = Image.fromarray(img_data)
            fname = name_sheme.format(**img_data.meta)
            img_path = dir_path / fname
            img.save(img_path)
            LOG.debug('Saving %s', str(img_path))

    def add_image(self, image_data: imageio.core.Array, meta_data: dict):
        """Handling tracking of meta data and image data

        ImageStack preserves order. The order images are added is reflected
        kept in ImageStack.data as well

        Parameter
        ---------
        image_data: imageio.core.Array
            Image data array to be added.

        """
        image_data.meta.update(meta_data)
        self.data.append(image_data)

    def clip(self, slc):
        """Clips all images with a slice in place

        Parameter
        ---------
        slc : slice
            Slice object
        """
        #TODO return new instance with data = np.view?
        self.data = [dat[slc] for dat in self.data]

    # @property
    # def meta(self):
    #     raise NotImplementedError


class ImageReader():
    """ Baseclass for reader

    basic class for loading images. defines the per image
    data format and provides metadata parsing
    """

    def __call__(self, uri):
        """Called by ImageStack. Must return an scipy.ndimage/ndarray
        containing the image data and a meta data dict
        """
        image_data = np.array([])
        meta_data = {}
        LOG.warning('Using a base class here... better be debugging...')
        return image_data, meta_data

    @staticmethod
    def read_image(uri, meta=None):
        """Reads the image data from the uri and returns
        the image data in an array
        """
        # somehow very slow
        # return imageio.imread(uri, format='tif')

        # fast reading of image files +
        # imageio sublclass of ndarray with meta data
        img = Image.open(uri)
        return imageio.core.Array(np.array(img), meta)

    @staticmethod
    def sanetize_meta(meta):
        """sanetizes the meta dict a bit

        removes trailing white spaces and tries to find and convert numeric
        values to floats
        """
        ret = {}
        for key, val in meta.items():
            val = val.strip()
            try:
                val = float(val)
            except ValueError:
                pass
            ret[key] = val

        return ret

def generic_uri() -> str:
    import platform
    import time
    import sys
    import os

    cwd = Path(os.getcwd()).expanduser().absolute()
    try:
        script = Path(sys.argv[0])
        if not script.is_absolute():
            script = (cwd / script).resolve()
        if not script.exists():
            script = ''
        script = f'PYS{script}'
    except (ValueError, TypeError):
        script = 'PYS?'
    cwd = f'CWD{cwd}'

    try:
        exe = Path(sys.executable).expanduser().absolute()
        if not exe.exists():
            exe = 'EXE?'
        else:
            exe = f'EXE{exe}'
    except (ValueError, TypeError):
        exe = 'EXE?'

    host = platform.node()
    lc = time.localtime()
    tstamp = f'{lc.tm_year}.{lc.tm_mon}.{lc.tm_mday}-{lc.tm_hour}:{lc.tm_min}'

    return f'<{tstamp}|{host}>///{exe}///{cwd}///{script}'
