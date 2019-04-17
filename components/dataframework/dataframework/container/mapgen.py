# -*- coding: utf-8 -*-
"""All the mapping classes and their managers live here
"""
import warnings
import numpy as np

# for lut stuff
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


from ..processing.tiff import RawImage


class RgbMapArray(np.ndarray):
    """RGB data array
    """

    def set_alpha(self, alpha):
        """sets the alpha channel if applicable
        """
        try:
            self[:, :, 3] = alpha
        except IndexError:
            msg = 'No alphachannel found. Need shape (y, x, 4), got {}'
            warnings.warn(msg.format(self.shape))


class LUT():

    def __init__(self):
        # create lookuptable to dsitribute objects over spectrum
        np.random.seed(46873136)
        self._lut = np.zeros(2**16)
        self._lut[1:] = np.arange(1, 2**16)
        np.random.shuffle(self._lut[1:])

        # create color id to color mapper
        norm = Normalize(vmin=1, vmax=2**16+1, clip=False)
        self._scalecmap = ScalarMappable(norm=norm, cmap='rainbow')
        cmap = self._scalecmap.get_cmap()
        cmap.set_under([0, 0, 0])
        self._scalecmap.set_cmap(cmap)

    def to_rgba(self, input_array, alpha, scale=False):
        """creates and lut for input_array, return rgba map
        with alpha channel
        """
        if scale:
            input_array = input_array.astype(float)
            input_array = input_array / input_array.max() * (2**16 - 1)
        lut_map = self._lut[input_array.astype(np.uint16)]
        overlay = self._scalecmap.to_rgba(lut_map, alpha=alpha, bytes=True)
        return overlay


class MapGen():
    """Has reference from images
    """

    def __init__(self, objid_map=None, image_stack=None, obj_gen=None):
        self._lut = LUT()

        self.tag_numbers = {}

        self.objid_map = objid_map
        self.image_stack = image_stack
        self.obj_gen = obj_gen

    def get_object_overlay(self, alpha=0.1):
        """generates an rgb overlay from the uint16 objid_map
        """
        if self.objid_map is None:
            raise ValueError('Objectid map must be set!')
        return self._lut.to_rgba(self.objid_map, alpha=alpha, scale=True)

    def get_merge_background(self, marker_names):
        """generates an rgb background image from uint16 marker images
        """
        if len(marker_names) != 3:
            msg = 'need 3 times a marker name or None, got {}'
            raise ValueError(msg.format(len(marker_names)))

        image_list = []
        for mname in marker_names:
            if mname is None:
                image_list.append(self.image_stack._zeros)
            else:
                new_ch = self.image_stack.get_imagedata(mname)
                image_list.append(new_ch.astype(float))

        #rescaling to 8 bit
        ret = np.dstack(image_list) / 0xffff
        ret = np.round(ret * 255).astype(np.uint8)
        return ret

    def get_merge_overlay(self, marker_names, alpha=1.0):
        """generates an rgb background image from uint16 marker images
        with alpha channel to overlay this shit
        """
        rgb_img = self.get_merge_background(marker_names)

        # set and add alpha
        alpha_ch = self.image_stack._zeros + (alpha * 255)
        ret = np.dstack([rgb_img, alpha_ch.astype(np.uint8)])

        return ret

    def get_tag_num(self, tag):
        step_width = 100
        try:
            next_tagnum = max(self.tag_numbers.values())
            next_tagnum += step_width
        except ValueError:
            next_tagnum = 35

        if next_tagnum >= 65535:
            for k, v in self.tag_numbers.items():
                new_v = v / next_tagnum * 65534
                self.tag_numbers[k] = new_v
            next_tagnum = 65534

        num = self.tag_numbers.get(tag, None)
        if num is None:
            num = next_tagnum
            self.tag_numbers[tag] = num
        return num

    def get_tagcolor_overlay(self, tags, alpha=0.1):
        """generates an rgb overlay from uint16 objid_map
        shape same as objid_map.shape
        """
        cluster_map = np.zeros(self.objid_map.shape, np.uint16)

        # assigne objects to cluster
        cluster_mapping = {}
        #TODO multiple tags?
        for cur_tag in tags:
        # for cluster_num, cur_tag in enumerate(tags, 1):
            for cur_obj in self.obj_gen.objects:
                in_cluster = cur_tag in cur_obj.tags
                if not in_cluster:
                    continue
                else:
                    mapping = cluster_mapping.get(cur_obj.id, None)
                if mapping is None:
                    cluster_num = self.get_tag_num(cur_tag)
                    mapping = cluster_mapping[cur_obj.id] = cluster_num
                    sli = cur_obj.slice
                    bmask = cur_obj.bmask
                    cluster_map[sli][bmask] = cluster_num
                else:
                    # find amigious tag
                    msg = 'Ambigious tags! Object.id {} has multiple cluster'
                    msg += ' assignments: {}'
                    amb_tags = set(cur_obj.tags).intersection(set(tags))
                    # give precise error
                    raise ValueError(msg.format(cur_obj.id, amb_tags))

        ret = self._lut.to_rgba(cluster_map, alpha=alpha, scale=False)
        return ret
