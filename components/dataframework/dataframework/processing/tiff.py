"""Implements tiff pixeal and ifd handling
focus to cover enough of the tiff specification
to hanel OMEXML later on
"""

from pathlib import Path
import struct
import numpy as np
import cv2
import weakref

from . import _tiff


#TODO make a class shared between severeal other classes
# inheritances wasent the best choice here, as most of the time
# changes for one element are relevant for all esp with Bytorder being global
class BuffReader():
    """reading bytes from file desc
    """

    def __init__(self):
        self._byte_order = None
        self._buf_interface = None

    def use(self, byte_order, buf_interface):
        """set byteorder and I/O
        """
        self._byte_order = byte_order
        self._buf_interface = buf_interface

    def close(self):
        """close file/buffer interface
        """
        if not self._buf_interface is None:
            self._buf_interface.close()

    def __del__(self):
        self.close()

    def read_bytes(self, fmt, offset=None):
        """Read from offset in the format fmt
        """
        if not offset is None:
            self._buf_interface.seek(offset)

        fmt = self._byte_order + fmt

        byte_size = struct.calcsize(fmt)
        chunk = self._buf_interface.read(byte_size)
        return struct.unpack(fmt, chunk)

    def write_bytes(self, val, fmt, offset=None):
        """Packs val into fmt and writes it to offset
        """
        if not offset is None:
            self._buf_interface.seek(offset)

        fmt = self._byte_order + fmt

        packed = struct.pack(fmt, *val)
        return self._buf_interface.write(packed)


class IFDEntry():
    """IFD Tag Class
    maps tiff defined types to struct bytes
    """
    #TODO make buffreade descendant and bufreader an generator
    #that generates all the instances
    ifd_types = _tiff.IFD_TYPES
    ifd_types_lut = dict((name, (k, stru)) \
                         for k, (stru, name) in ifd_types.items())
    ifd_tags = _tiff.IFD_TAGS
    ifd_tags_lut = dict((v, k) for k, v in ifd_tags.items())

    def __init__(self):
        self.tag = None
        self.content_type = None
        self.content_fmt = None
        self.content_len = None
        self.content_num = None
        self.content = None
        self.content_offset = None

    def from_values(self, tag, content_type, content,
                    offset=None, byte_order='<'):
        """Generates ifd entry from values
        """
        try:
            tag_val = self.ifd_tags_lut[tag]
        except KeyError:
            raise KeyError('Invalid Tiff Tag: {}'.format(tag))

        try:
            type_val, type_stru = self.ifd_types_lut[content_type]
        except KeyError:
            raise KeyError('Invalid Tiff Type: {}'.format(content_type))

        #unpacke scalar lists/arrays
        try:
            content, = content
        except (ValueError, TypeError):
            pass

        # ensure all content is serialized to list
        if content_type == 'ASCII':
            try:
                content_len = len(content.encode('utf-8'))
            except AttributeError:
                msg = 'Need string as content, not {}'.format(type(content))
                raise ValueError(msg)
            content_num = len(content)
            content_fmt = '{}{}{}'.format(byte_order, content_len, type_stru)
        else:
            try:
                content_num = len(content)
            except TypeError:
                content_num = 1
            content_fmt = '{}{}{}'.format(byte_order, content_num, type_stru)
            content_len = struct.calcsize(content_fmt)
            content = np.array(content)

        self.tag = tag
        self.content_type = content_type
        self.content_fmt = content_fmt
        self.content_len = content_len
        self.content_num = content_num
        self.content = content

        if content_len <= 4:
            self.content_offset = None
        else:
            self.content_offset = offset

        if self.content_offset is None and self.content_len > 4:
            msg = 'Content is larger than 4 bytes. Must be offsetted, '+\
                  'but offset is not set!'
            raise ValueError(msg)

    def from_bytes(self, entry_bytes, byte_order='<'):
        """Tag as define by tiff6
        content hase type cont_type
        with num vlaues of cont type
        raises ValueError if content will be <= 0 bytes
        always expects byteorder '<'
        """

        # split into descriptor and data
        head_fmt = '{}2HI'.format(byte_order)
        tag_key, cont_type_key, content_num = struct.unpack(
            head_fmt, entry_bytes[:8])
        cont_byte_vals = entry_bytes[8:]

        # set tag, type and get unpack char
        tag = self.ifd_tags.get(tag_key, 'UNKNOWN({})'.format(tag_key))
        cont_fmt_char, content_type = self.ifd_types[\
                cont_type_key]

        # generate content format and get contetn length
        content_fmt = '{}{}{}'.format(byte_order, content_num, cont_fmt_char)
        content_bytes = struct.calcsize(content_fmt)

        # calculate conten directly if smaller than four bytes
        if 0 < content_bytes <= 4:
            cont_byte_vals = cont_byte_vals[:content_bytes]
            content_offset = None
        elif content_bytes > 4:
            content_offset, = struct.unpack(byte_order + 'I', cont_byte_vals)
        else:
            raise ValueError('Invalid content size')

        # everything work, lets change the instance state then
        self.tag = tag
        self.content_type = content_type
        self.content_len = content_bytes
        self.content_fmt = content_fmt
        self.content_offset = content_offset
        self.content_num = content_num

        if content_offset is None:
            self.set_content(cont_byte_vals)
        else:
            self.content = None

    def set_content(self, content_bytes):
        """parses content values from content_bytes
        """
        try:
            content = struct.unpack(
                self.content_fmt, content_bytes)
        except TypeError:
            raise ValueError('Read entry first, before setting content')
        except struct.error:
            raise ValueError('Maleformed input for entry read format')

        if self.content_type == 'ASCII':
            content = bytes(content)
            if content[-1] == 0:
                content = content[:-1]
            self.content = content.decode('utf-8')
            self.content_num = len(self.content)
        elif len(content) == 1:
            self.content, = content
            self.content_num = 1
        else:
            self.content = np.array(content)
            self.content_num = len(self.content)

    @property
    def finalized(self):
        """Returns true if finalized
        """
        if self.content is None and not self.content_offset is None:
            return False
        if not self.content is None:
            return True
        return False

    def __str__(self):
        msg = '<{} with {} {}'.format(self.tag, self.content_num,
                                      self.content_type)

        if self.content is None and self.content_offset is None:
            msg = '<UNDEFINED IFDEntry>'
        else:
            if not self.content_offset is None:
                msg += ' @ {}>'.format(hex(self.content_offset))
            if not self.content is None:
                msg += ' -> {}>'.format(self.content)

        return msg

    def __len__(self):
        """Bytesize of content
        """
        return self.content_len

    def to_bytes(self, byte_order):
        """converts to bytes
        """
        tag_val = self.ifd_tags_lut[self.tag]
        type_val, _ = self.ifd_types_lut[self.content_type]

        head_fmt = '{}2HI'.format(byte_order)

        # for ascii we want the byte encoding
        if self.content_type == 'ASCII':
            content = self.content.encode('utf-8')
            head_bytes = struct.pack(head_fmt, tag_val, type_val,
                                     self.content_len)
        elif self.content_num == 1:
            content = [self.content]
            head_bytes = struct.pack(head_fmt, tag_val, type_val,
                                     self.content_num)
        else:
            content = list(self.content)
            head_bytes = struct.pack(head_fmt, tag_val, type_val,
                                     self.content_num)

        if not self.content_fmt.startswith(byte_order):
            self.content_fmt = byte_order + self.content_fmt[1:]

        try:
            content_bytes = struct.pack(self.content_fmt, *content)
        except struct.error:
            raise ValueError('Wrong type given! Change type or change content')

        if len(content_bytes) == 4:
            entry_bytes, content_bytes = head_bytes + content_bytes, None
        elif len(content_bytes) < 4:
            content_bytes += (4 - len(content_bytes)) * b'\x00'
            entry_bytes, content_bytes = head_bytes + content_bytes, None
        else:
            offset_addr = struct.pack(byte_order + 'I', self.content_offset)
            entry_bytes = head_bytes + offset_addr

        if len(entry_bytes) != 12:
            msg = 'Something is wrong, maleformed entry: {}, {}, {}'
            raise RuntimeError(msg.format(self, entry_bytes, content_bytes))

        return entry_bytes, content_bytes


class IFD(BuffReader):
    """parser for singel IFD element
    generates ifd Tags
    """

    def __init__(self, byte_order, buf_interface):
        super().__init__()
        self.use(byte_order, buf_interface)
        self.offset = None
        self.next_offset = None
        self.entries = []
        self._entries_dict = {}
        self.bytesize = 0

    def read(self, offset=4):
        """entry addr ist the byte adress where the ifd starts
        The first 4 starting from entry_addr will be interpretet as
        offset where the first entry is to be expected
        """
        self.offset = offset
        self._buf_interface.seek(offset)

        # jump to offset address and read the number of idf entries
        entry_count, = self.read_bytes('H', offset)

        # the very next byte is the offset address for the
        for _ in range(entry_count):
            ifd_entry_bytes = bytearray(self.read_bytes('12B'))
            cur_ifd = IFDEntry()
            cur_ifd.from_bytes(entry_bytes=ifd_entry_bytes,
                               byte_order=self._byte_order)
            self.entries.append(cur_ifd)

        self.next_offset, = self.read_bytes('I')
        # infere bytesize
        self.bytesize = self._buf_interface.tell() - offset

        # finalize entries
        for entr in self.entries:
            if not entr.finalized:
                self._buf_interface.seek(entr.content_offset)
                content_bytes = self._buf_interface.read(
                    entr.content_len)
                entr.set_content(content_bytes)

        # populate tag dict
        edict = {}
        for entr in self.entries:
            edict[entr.tag] = entr
        self._entries_dict = edict

    def get(self, key, default=None):
        """dict like acces to ifd fields
        """
        return self._entries_dict.get(key, default)

    def append(self, ifd_entry):
        """Adds ifd_entry to IFD
        """
        self.entries.append(ifd_entry)
        self._entries_dict[ifd_entry.tag] = ifd_entry

    def tags(self):
        """all entry tags
        """
        return self._entries_dict.keys()

    def write(self, offset=None):
        """Writes back the IFD to the used file
        """
        if not offset is None:
            self.offset = offset

        if self.offset is None:
            raise ValueError('Offset musst be set or given!')

        if self.next_offset is None:
            self.next_offset = 0

        to_offsets = []
        # number of entries
        self.write_bytes([len(self.entries)], 'H', offset=self.offset)
        for entry in self.entries:
            entry_bytes, content_bytes = entry.to_bytes(
                byte_order=self._byte_order)
            self.write_bytes(bytearray(entry_bytes), '12B')
            if not content_bytes is None:
                to_offsets.append((entry.content_offset, content_bytes))
        # write where to find next ifd
        self.write_bytes([self.next_offset], 'I')

        for off, byt in to_offsets:
            fmt = '{}B'.format(len(byt))
            self.write_bytes(byt, fmt, offset=off)

    def __getitem__(self, key):
        return self._entries_dict[key].content

    def __setitem__(self, key, value):
        self._entries_dict[key].content = value

    def __len__(self):
        return len(self.entries)

    def __str__(self):
        if self.entries:
            msg = 'IFD with {} entries'.format(len(self))
        else:
            msg = 'Empty IFD'

        if not self.offset is None:
            msg += ' @ {:>08}'.format(hex(self.offset))

        for entr in self.entries:
            msg += '\n' + str(entr)

        return msg


class RawImage(BuffReader):
    """Base class of all image formats. Asserts consitent image handling
    and contains shared imaging functions. Leaving all the pixeldata
    handling to cv2
    """

    def __init__(self):
        """Opens image_path if it exists and loads the image found there
        """
        super().__init__()
        self._pixel_data = None
        self._pixel_data_origin = None

    def load_pixeldata_from(self, image_path, dtype=np.uint16):
        """Loads pixeldata from file found at file_path

        Parameter
        ---------
        image_path : Path
            Path to file containing pixeldata to read

        dtype : np.dtype
            Type to convert the image data to

        Raises
        ------
        ValueError: image_path.exists() == False
        """

        image_path = Path(image_path)

        if not image_path.exists() or image_path.is_dir():
            raise ValueError('Not a valid file: {}!'.format(str(image_path)))

        img_dat = cv2.imread(str(image_path), cv2.IMREAD_ANYDEPTH)

        if img_dat is None:
            msg = 'Cold not read image at {}'.format(str(image_path))
            raise ValueError(msg)

        #TODO move this to the map creation
        # self.pixel_data = np.flipud(img_dat.T).astype(dtype)
        self._pixel_data_origin = Path(image_path)
        self._pixel_data = img_dat.astype(dtype)

    def save_pixeldata_to(self, image_path, overwrite=False):
        """Saves pixeldata to file path

        Parameter
        ---------
        image_path : Path
            Path to file where pixeldata should be written to

        Raises
        ------
        ValueError: if image_path.exists() and overwrite is False
        """

        image_path = Path(image_path)

        if image_path.exists() and not overwrite:
            raise ValueError('File {} allready exist!'.format(str(image_path)))

        # cv2.imwrite(str(image_path), np.flipud(self.pixel_data).T)
        cv2.imwrite(str(image_path), self._pixel_data)

    @property
    def bit(self):
        """inferes bitness
        """
        if self._pixel_data is None:
            ret = None
        elif self._pixel_data.dtype == np.uint16:
            ret = '16'
        elif self._pixel_data.dtype == np.uint8:
            ret = '8'

        return ret

    @property
    def width(self):
        """inferes width
        """
        return self.shape[1]

    @property
    def height(self):
        """inferes height
        """
        return self.shape[0]

    @property
    def shape(self):
        """synthactic sugar
        """
        if self._pixel_data is None:
            return (None, None)

        return self._pixel_data.shape

    @property
    def pixel_data(self):
        return self._pixel_data

    @pixel_data.setter
    def pixel_data(self, obj):
        self._pixel_data_origin = weakref.ref(obj)
        self._pixel_data = obj

    @property
    def pixel_data_origin(self):
        try:
            # is a ref?
            return self._pixel_data_origin()
        except TypeError:
            # not a ref
            return self._pixel_data_origin


class TiffImage(RawImage):
    """Very basic tiff image wrapper. Will just read the first IFD
    find the ImageDescription tag and mange this entry only, for later ometiff
    use
    """

    def __init__(self):
        super().__init__()
        self.ifds = []

    def read_ifds(self, image_path):
        """Processes Tiff
        raise error, is not valid tiff
        """
        image_path = Path(image_path)
        file_interface = image_path.open('rb')

        # read file endiandess
        byte_order = file_interface.read(2)
        if byte_order == b'II':
            byte_order = '<'
        elif byte_order == b'MM':
            byte_order = '>'
        else:
            raise ValueError('Invalid tiff header')

        # setup file interface
        self.use(byte_order, file_interface)

        # check
        magic_number, = self.read_bytes('H')
        if magic_number != 42:
            raise ValueError('Invalid tiff header')

        # generating ifd list, starting from the first IFD
        self.ifds = [ifd for ifd in self._ifd_reader()]

    def _ifd_reader(self):
        """Generates and populated ifd_list
        will start seeking first offset at byte 4
        """
        offset, = self.read_bytes('I')
        # set to initial offst position
        cur_ifd = IFD(self._byte_order, self._buf_interface)
        cur_ifd.read(offset=offset)
        yield cur_ifd

        while cur_ifd.next_offset != 0:
            offset = cur_ifd.next_offset
            cur_ifd = IFD(self._byte_order, self._buf_interface)
            cur_ifd.read(offset=offset)
            yield cur_ifd

    @property
    def shape(self):
        """ifd inferred width and height
        """
        data_shape = super().shape

        try:
            ifd0 = self.ifds[0]
            ifd_w = ifd0.get('ImageWidth', None)
            ifd_h = ifd0.get('ImageLength', None)
            ifd_shape = (ifd_h.content, ifd_w.content)
        except IndexError:
            ifd_shape = (None, None)

        if ifd_shape == data_shape:
            return data_shape

        ifd_valid = not None in ifd_shape
        data_valid = not None in data_shape

        if ifd_valid and not data_valid:
            return ifd_shape
        elif data_valid and not ifd_valid:
            return data_shape

        # both valid but not equal
        # overwrite ifd content with data shape
        # and return data shape
        new_height, new_width = data_shape
        # w_entry = ifd0['ImageWidth']
        # h_entry = ifd0['ImageLength']
        # w_entry.content = new_width
        # h_entry.content = new_height
        ifd0['ImageWidth']  = new_width
        ifd0['ImageLength'] = new_height
        return data_shape
