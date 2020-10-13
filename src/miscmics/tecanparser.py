"""Script for converting processed MICS/Tecan images in a format suitable
for further processing in TensorFlow
"""
import logging
import re

from pathlib import Path
import h5py
import numpy as np
from scipy import ndimage
from scipy.special import expit

from .multiplex.multiplex import ImageStack, ImageReader
from .histpick_old import score_imgstack, strip_nonopt


LOG = logging.getLogger(__name__)


class ProcessedReader(ImageReader):
    """Read image data using abritary regex patter
    for extraction of metadata
    """

    def __init__(self, pattern=None):
        """
        Parameters
        ----------
        pattern : str
            regex pattern

        Notess
        ------
        Named groups define fully, which metadata is used/stored extracted
        """
        # to filename matcher
      
        if pattern is None:
            pattern = '^(?P<cycle>[0-9]{3})' + \
                '_(?P<name>[a-z0-9]*)[V_ ][0-9]*.*' + \
                'wix ?(?P<exp>[0-9]*).*(?P<ext>.tiff?)$'

        self._matcher = re.compile(pattern, re.IGNORECASE)

    def __call__(self, uri):

        meta = self.get_meta(uri)

        if meta is None:
            return None, None

        meta = self.sanetize_meta(meta)
        
        dat = self.read_image(uri, meta)

        return dat, meta

    def get_meta(self, uri):
        match = self._matcher.match(uri.name)
        try:
            meta = match.groupdict()
            meta['filename'] = uri.name
            return meta
        except AttributeError:
            return None

def set_attr_gray(h5ds):
    h5ds.attrs['CLASS'] = np.string_('IMAGE')
    h5ds.attrs['IMAGE_SUBCLASS'] = np.string_('IMAGE_GRAYSCALE')
    h5ds.attrs['IMAGE_VERSION'] = np.string_('1.2')
    h5ds.attrs['IMAGE_MINMAXRANGE'] = np.array([0.0, 1.0], dtype=float)
    h5ds.attrs['IMAGE_WHITE_IS_ZERO'] = np.uint8(0)

def scale(arr, meta, sc):
    arr = arr * sc
    meta['scaled'] = sc
    return arr
 
def noise_filter(arr, meta):
    arr = ndimage.median_filter(arr, 3)
    meta['filter'] = 'median 3x3'
    return arr

def pack_h5(image_stacks, outfile, rowsplit=2, colsplit=2):
    """packs image stack in a training dataset
    """

    outfile = Path(outfile)

    hdf = h5py.File(outfile, 'w')
    # meta = hdf['meta']

    marker_names = [set(ims.unique()['name']) for ims in image_stacks]
    assert all(marker_names[0] == other for other in marker_names[1:])
    marker_names = list(marker_names[0])
    marker_names.sort()

    print(f'order is: {marker_names}')

    for n, ims in enumerate(image_stacks):
        LOG.debug('Processing stack for %s', str(ims))

        # preprocess and merging
        ndimg = []
        for name in marker_names:
            img = ims.find(dict(name=name), single=False)
            if len(img) != 1:
                raise ValueError('Must have one image for each marker only!')
            img = img[0]
            assert name == img.meta['name'], 'Find is broken...'
            arr = np.asarray(img).astype(np.float32)
            # arr = noise_filter(arr, ims.meta)
            ndimg.append(arr)

        ndimg = np.stack(ndimg, -1)
        flat_ndimg = ndimg.reshape(-1, len(marker_names))
        max_norm = np.max(flat_ndimg, 0)
        sc_ndimg = ndimg / max_norm[None, None, :]
        glob_sc = np.sum(sc_ndimg, -1).mean()
        sc_ndimg = sc_ndimg / glob_sc

        #TODO Remove preprocessing from packing
        mask = np.all(ndimg > 0, -1)

        expit_a = 3
        expit_b = -1
        eff_sc = (sc_ndimg[mask] / ndimg[mask])[0]
        sc_ndimg = expit((sc_ndimg + expit_b) * expit_a)

        for i, row in enumerate(np.split(sc_ndimg, 2, 0)):
            for j, section in enumerate(np.split(row, 2, 1)):
                key = f'{n}{i}{j}'
                LOG.info('Creating %s', key)
                ds = hdf.create_dataset(key, data=section, dtype=section.dtype)
                ds.attrs['section_index'] = np.array([i, j], np.uint8)

                for ims_meta_key, ims_meta_val in ims.meta.items():
                    ds.attrs[ims_meta_key] = ims_meta_val
                # set_attr_gray(ds)
                ds.attrs['channels'] = marker_names
                ds.attrs['scale'] = eff_sc
                ds.attrs['expit_a'] = expit_a
                ds.attrs['expit_b'] = expit_b

    hdf.close()

def make_stack(path, field, reader):
    """higly specifiv for ovca 318
    """
    meta = {'field': field, 'run': 318, 'tissue': 'OvCa'}
    ims = ImageStack(reader, meta=meta)
    ims.read_dir(path)
    score_imgstack(ims)
    strip_nonopt(ims)
    return ims
