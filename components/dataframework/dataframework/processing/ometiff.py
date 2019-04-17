# -*- coding: utf-8 -*-

"""Experiment frontent to backend OME tiffs
"""
import warnings

from pathlib import Path
import numpy as np

import uuid
from lxml import etree

from .tiff import TiffImage, IFDEntry
from .valuemapper import ValueMapper
from . import _tiff


class OMExml():
    """Very loose implementation fo omexlm, so that it just works...
    hide please hide it behind as many abstraction layers as possible
    Has just ONE image
    dimension order is always XYZCT, with sizes Z == C == T == 1
    will always be uint8 or unit16. significant bits always 12
    """

    _ome_ns = r'http://www.openmicroscopy.org/Schemas/OME/2016-06'
    _nsmap = {None: 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
    _omenstag = '{' + _ome_ns + '}'

    _true_key = 'true'
    _false_key = 'false'

    def __init__(self, creator='fs2ometiff'):
        init = str(_tiff.OME_INFO + _tiff.OME_COMMENT + _tiff.OME_ROOT)

        self._root = etree.XML(init.encode('ascii'))
        self._root.set('Creator', creator)
        self._root.set('UUID', 'urn:uuid:' + str(uuid.uuid1()))

        self._pixels = None
        self._channel = None
        self._tiffdata = None
        self._uuid = None

        self._meta = None
        self._bio = None

        self._set_image()

    @property
    def _tree(self):
        """generate roottree from root element
        """
        return self._root.getroottree()

    def __str__(self):
        string = etree.tostring(self._tree, pretty_print=True).decode('utf-8')
        return string

    def bytes(self):
        """generates byte representation of xml tree
        """
        string = etree.tostring(self._tree)
        return _tiff.XML_PROCESSING + string

    def _set_image(self):
        """Generates an ome image entry and adds it to root
        for now dimension order is always XYZTC, with sizes for
        Z == C == T == 1
        will always be uint8 or unit16
        """
        # image stuff
        # generate elements
        self._img = etree.Element(self._omenstag + u'Image', nsmap=self._nsmap)
        pixels = etree.Element(self._omenstag + u'Pixels', nsmap=self._nsmap)
        channel = etree.Element(self._omenstag + u'Channel', nsmap=self._nsmap)
        tiffdata = etree.Element(self._omenstag + u'TiffData',
                                 nsmap=self._nsmap)
        img_uuid = etree.Element(self._omenstag + u'UUID', nsmap=self._nsmap)

        # build tree
        self._root.append(self._img)
        pixels.append(channel)
        tiffdata.append(img_uuid)
        pixels.append(tiffdata)
        self._img.append(pixels)

        self._img.set(u'ID', u'Image:0')
        self._img.set(u'Name', u'')

        pixels.set(u'DimensionOrder', u'XYZTC')
        pixels.set(u'BigEndian', u'')
        pixels.set(u'Type', u'')
        pixels.set(u'Interleaved', u'')
        pixels.set(u'SignificantBits', u'12')
        for dim in u'ZCT':
            pixels.set(u'Size' + dim, u'1')

        channel.set(u'Color', u'-1')
        channel.set(u'ID', u'Channel:0:0')
        channel.set(u'SamplesPerPixel', u'1')

        tiffdata.set(u'IFD', u'0')
        tiffdata.set(u'PlaneCount', u'1')
        for dim in 'ZCT':
            tiffdata.set(u'First' + dim, u'0')

        img_uuid.text = 'urn:uuid' + str(uuid.uuid1())

        # meta stuff
        self._meta = etree.Element(u'StructuredAnnotations', nsmap=self._nsmap)
        self._root.append(self._meta)

        # set the references
        self._parse_img()
        self._parse_meta()

    def _get_n(self, element, tag, n=-1):
        """gets exactly one tag out of element
        if there are more, raise an error
        """
        children = element.findall(self._omenstag + tag)

        if len(children) != n and n != -1:
            msg = 'Supports only ome with exactly {} tag(s) {}'.format(n, tag)
            raise ValueError(msg)

        try:
            return children[0]
        except IndexError:
            return None

    def fromstring(self, xml_string):
        """read data from string
        """
        self._pixels = None
        self._channel = None
        self._tiffdata = None
        self._uuid = None

        self._meta = None
        self._bio = None

        self._root = etree.fromstring(xml_string.encode())

        self._img = self._get_n(self._root, 'Image', 1)
        self._meta = self._get_n(self._root, 'StructuredAnnotations', 1)

        self._parse_img()
        self._parse_meta()

    def _parse_img(self):
        self._pixels = self._get_n(self._img, 'Pixels', 1)
        self._channel = self._get_n(self._pixels, 'Channel', 1)
        self._tiffdata = self._get_n(self._pixels, 'TiffData', 1)
        self._uuid = self._get_n(self._tiffdata, 'UUID', 1)

    def _parse_meta(self):
        # try to get it
        bio = self._get_n(self._meta, 'MICSmeta', -1)
        # if there is no bio..
        if self._bio is None and bio is None:
            # generate it!
            bio = etree.Element(self._omenstag + u'MICSmeta')
            bio.set(u'Marker', u'')
            bio.set(u'Tissue', u'')
            bio.set(u'Species', u'')
            self._meta.append(bio)
            self._bio = bio
        elif not bio is None and self._bio is None:
            self._bio = bio

    @property
    def uuid(self):
        """get image uuid
        """
        return self._uuid.text

    @uuid.setter
    def uuid(self, uuid):
        """set image uuid
        """
        self._uuid.text = uuid

    @property
    def name(self):
        """get image name
        """
        return self._img.get('Name')

    @name.setter
    def name(self, name):
        """set image name
        """
        self._img.set('Name', name)

    @property
    def filename(self):
        """get image filename
        """
        return Path(self._uuid.get('FileName'))

    @filename.setter
    def filename(self, filename):
        """set image filename
        """
        self._uuid.set('FileName', str(filename))

    @property
    def marker(self):
        """get marker used
        """
        return self._bio.get('Marker')

    @marker.setter
    def marker(self, marker):
        """set marker used
        """
        self._bio.set('Marker', marker)

    @property
    def tissue(self):
        """get tissue used
        """
        return self._bio.get('Tissue')

    @tissue.setter
    def tissue(self, tissue):
        """set tissue used
        """
        self._bio.set('Tissue', tissue)

    @property
    def species(self):
        """get species used
        """
        return self._bio.get('Species')

    @species.setter
    def species(self, species):
        """set species used
        """
        self._bio.set('Species', species)

    @property
    def imagemap(self):
        """get mapping
        """
        return self._bio.get('ImageMap')

    @imagemap.setter
    def imagemap(self, imagemap):
        """set mapping
        """
        self._bio.set('ImageMap', imagemap)

    @property
    def sigbit(self):
        """get sigbit used
        """
        return self._pixels.get('SignificantBits')

    @sigbit.setter
    def sigbit(self, sigbit):
        """set sigbit used
        """
        self._pixels.set('SignificantBits', sigbit)

    @property
    def bit(self):
        """get bit used
        """
        ret = self._pixels.get('Type')

        if ret == 'uint8':
            return '8'
        elif ret == 'uint16':
            return '16'
        else:
            return '?'

    @bit.setter
    def bit(self, bit):
        """set bit used
        """
        bit = str(bit)
        if bit == '8':
            typ = 'uint8'
        elif bit == '16':
            typ = 'uint16'
        else:
            typ = '?'

        self._pixels.set('Type', typ)

    @property
    def interleaved(self):
        """get interleaved mode
        """
        return self._pixels.get('Interleaved') == self._true_key

    @interleaved.setter
    def interleaved(self, interleaved):
        """set interleaved mode
        """
        if interleaved:
            key = self._true_key
        else:
            key = self._false_key
        self._pixels.set('Interleaved', key)

    @property
    def endianess(self):
        """get endianess mode
        """
        is_big = self._pixels.get('BigEndian') == self._true_key
        if is_big:
            return '>'
        return '<'

    @endianess.setter
    def endianess(self, byte_order):
        """set endianess mode
        """
        if byte_order == '>':
            key = self._true_key
        else:
            key = self._false_key
        self._pixels.set('BigEndian', key)

    @property
    def width(self):
        """get image width
        """
        return self._pixels.get('SizeX')

    @width.setter
    def width(self, width):
        """set image width
        """
        self._pixels.set('SizeX', str(width))

    @property
    def height(self):
        """get image height
        """
        return self._pixels.get('SizeY')

    @height.setter
    def height(self, height):
        """set image height
        """
        self._pixels.set('SizeY', str(height))

    @property
    def smplperpx(self):
        """get samples per pixel
        """
        return str(self._channel.get('SamplesPerPixel'))

    @smplperpx.setter
    def smplperpx(self, smplperpx):
        """set samples per pixel
        """
        self._channel.set('SamplesPerPixel', str(smplperpx))


class OMETiff(TiffImage):
    """Wrapper class around ome tiff. will be an adapter later
    on"""

    valmapper = ValueMapper()

    def __init__(self, filepath=None, name=None):
        super().__init__()

        # biostuff
        self.tissue = None
        self.species = None
        self.marker = None
        self.imagemap = None

        # deduced from image
        self.sigbit = None
        self.interleaved = None
        self.smplperpx = None

        #omexml stuff
        self.xml = OMExml()

        # about stuff
        self.name = name

        if not filepath is None:
            self.load(Path(filepath))

    def read_ifds(self, image_path):
        """decorate original read_ifds to update
        xml afterwards
        """
        super().read_ifds(image_path)

        ome_ifd = self.ifds[0]
        
        try:
            planeconf = ome_ifd['PlanarConfiguration']
            if planeconf == 1:
                self.interleaved = True
            elif planeconf == 2:
                self.interleaved = False
            else:
                raise ValueError('Invalid PalanarConfiguration')
        except KeyError:
            pass
        
        try:
            self.smplperpx = str(ome_ifd['SamplesPerPixel'])
        except KeyError:
            pass

        self.update_xml(filename=Path(image_path).name)

    def load(self, filepath):
        """loads image at filepath as ome tiff
        """
        self.read_ifds(filepath)
        self.read_xml()
        self.load_pixeldata_from(filepath)

    def save(self, filepath, overwrite=False):
        """save data as ome.tiff at filepath
        """
        filepath = Path(filepath)
        # save the pixeldata
        fpname = filepath.name
        valid_name = [fpname.endswith(ext) for ext in ('ome.tif', 'ome.tiff')]
        if not any(valid_name):
            filepath = filepath.parent / (filepath.name + 'ome.tiff')

        self.update_xml(fpname)

        # save pixeldata
        self.save_pixeldata_to(filepath, overwrite=overwrite)
        # read back what cv2 hase done
        self.read_ifds(filepath)
        # close file
        self.close()

        # select ifd conatining ome data, must be first ifd
        ifd0 = self.ifds[0]

        # open file for writing, and find the EOF
        out_file = filepath.open('r+b')
        self.use(buf_interface=out_file, byte_order=self._byte_order)

        # overwrite ifd in tiff file
        self.write_bytes([45054], 'H', ifd0.offset)
        for _ in range(2, ifd0.bytesize, 2):
            self.write_bytes([45054], 'H')

        # seek the filend, use it as ome offset
        # after the ome set the new ifd
        xml_bytes = self.xml.bytes()

        # seek end -> ome offset
        self._buf_interface.seek(0, 2)
        omexml_offset = self._buf_interface.tell()
        new_ifd_offset = omexml_offset + len(xml_bytes)

        # generate the ome entry and append it
        ome_entry = IFDEntry()
        ome_entry.from_values(
            tag='ImageDescription',
            content_type='ASCII',
            content=xml_bytes.decode('utf-8'),
            offset=omexml_offset,
            byte_order=self._byte_order)
        ifd0.append(ome_entry)

        #update the tiff header
        self.write_bytes([new_ifd_offset], 'I', offset=4)

        ifd0.use(buf_interface=out_file, byte_order=self._byte_order)
        ifd0.write(offset=new_ifd_offset)

        self._buf_interface.flush()

    def read_xml(self):
        """reads xml from first ifd
        """
        if not self.ifds:
            raise ValueError('Read IFDs first!')

        src_ifd = self.ifds[0]

        try:
            xml_string = src_ifd['ImageDescription']
            self.xml.fromstring(xml_string)
        except (KeyError, etree.XMLSyntaxError):
            raise ValueError('Not a valid ome.tiff')

        self.marker = self.xml.marker
        self.tissue = self.xml.tissue
        self.species = self.xml.species
        self.imagemap = self.xml.imagemap

        self.name = self.xml.name
        self.sigbit = self.xml.sigbit

    def set_metadata(self, tissue=None, species=None,
                     marker=None, sigbit=None, imagemap=None):
        """ Setting metadata not derivable from image directly
        """

        if not species is None:
            if not self.valmapper.valid_species(species):
                raise ValueError('Invalid Species: {}'.format(species))
            self.species = species

        if not tissue is None and self.valmapper.valid_tissue(tissue):
            if not self.valmapper.valid_tissue(tissue):
                raise ValueError('Invalid Tissue: {}'.format(tissue))
            self.tissue = tissue

        if not marker is None:
            self.marker = marker

        if not sigbit is None:
            self.sigbit = str(sigbit)

        if not imagemap is None:
            self.imagemap = str(imagemap)

        self.update_xml()

    def load_pixeldata_from(self, image_path, dtype=np.uint16):
        """Decorating original pixel loading routine
        to set metadata

        # only one image at a time is possible
        """
        super().load_pixeldata_from(image_path)

        self.update_xml(filename=Path(image_path).name)

    def update_xml(self, filename=None):
        """Updates the xml
        """
        #TODO distribute over the whole class to the functions, where the values
        # are actually set via the interface/loading

        #TODO make a real mapping
        
        biovals = ['', '', '']
        for i, bva in enumerate([self.marker, self.species, self.tissue]):
            if bva is None:
                continue
            else:
                biovals[i] = bva

        marker, species, tissue = biovals
        self.xml.marker = marker
        self.xml.species = species
        self.xml.tissue = tissue

        imgvals = ['', '', '', '', '', '', '', '', '', '']
        for i, iva in enumerate([filename, self.name, self.bit, self.sigbit,
                                 self.interleaved, self._byte_order, self.width,
                                 self.height, self.smplperpx, self.imagemap]):
            if iva is None:
                continue
            else:
                imgvals[i] = iva

        filename, name, bit, sigbit, interleaved, endianess, width, height,\
            smplperpx, imagemap = imgvals
        self.xml.filename = filename
        self.xml.name = name
        self.xml.bit = bit
        self.xml.sigbit = sigbit
        self.xml.interleaved = interleaved
        self.xml.endianess = endianess
        self.xml.width = width
        self.xml.height = height
        self.xml.smplperpx = smplperpx
        self.xml.imagemap = imagemap
