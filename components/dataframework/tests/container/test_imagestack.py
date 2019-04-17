"""Unit testing for ImageStack class
"""
import numpy as np
from pathlib import Path
import pytest
import cv2

from dataframework.container import ImageStack

from conftest import (SOME_LARGE_IMG, MANY_SMALL_IMG, SOME_SMALL_IMG,
                      MY_OME_REF, FS_TIF_REF, INVALID_XML_DIR)


def test_dirloading():
    """tests if all files are found and matched correctly
    """
    ims = ImageStack()
    ims.load_from_dir(SOME_LARGE_IMG)

    assert len(ims) == 10

def test_adding_to_initialized(tmpdir):
    """tests if all files are found and matched correctly
    """
    ims = ImageStack()
    ims.load_from_dir(SOME_LARGE_IMG)

    assert len(ims) == 10

    new_name = '012_CD556_something.tif'
    new_img = np.random.randint(0, 0xff, 2048**2).reshape(2048, 2048)
    new_path = tmpdir.mkdir('test').join(new_name)
    cv2.imwrite(str(new_path), new_img)

    ims.add_image(str(new_path))

    assert len(ims) == 11

def test_adding_single(tmpdir):
    """tests if all files are found and matched correctly
    """
    ims = ImageStack()

    assert not len(ims)

    new_name = '012_CD556_something.tif'
    new_img = np.random.randint(0, 0xff, 2048**2).reshape(2048, 2048)
    new_path = tmpdir.mkdir('test').join(new_name)
    cv2.imwrite(str(new_path), new_img)

    assert Path(str(new_path)).exists()

    ims.add_image(str(new_path))
    
    assert len(ims) == 1
    assert np.all(new_img == ims.get_imagedata('CD556'))

def test_adding_different_dims(tmpdir):
    """tests if error is raised on different dims and if the error returns
    with consistent state
    """
    test_dir = tmpdir.mkdir('test')

    new_name0 = '012_CD556_something.tif'
    new_img0 = np.random.randint(0, 0xff, 100).reshape(10, 10)
    new_path0 = str(test_dir.join(new_name0))
    cv2.imwrite(new_path0, new_img0)

    new_name1 = '012_DAPIi_something.tif'
    new_img1 = np.random.randint(0, 0xff, 121).reshape(11, 11)
    new_path1 = str(test_dir.join(new_name1))
    cv2.imwrite(new_path1, new_img1)

    _seq_loading(new_img0, new_img1, 'CD556', 'DAPIi', new_path0, new_path1)
    _seq_loading(new_img1, new_img0, 'DAPIi', 'CD556', new_path1, new_path0)

def _seq_loading(img0, img1, name0, name1, path0, path1):
    ims = ImageStack()
    ims.add_image(path0)

    with pytest.raises(ValueError):
        ims.add_image(path1)

    assert len(ims) == 1
    assert np.all(img0 == ims.get_imagedata(name0))

    with pytest.raises(KeyError):
        _ = ims.get_imagedata(name1)

def test_adding_single_markerlist(tmpdir):
    """tests if all files are found and matched correctly
    """
    ims = ImageStack()

    assert not len(ims)

    new_name = '012_CD556_something.tif'
    new_img = np.random.randint(0, 0xff, 2048**2).reshape(2048, 2048)
    new_path = tmpdir.mkdir('test').join(new_name)
    cv2.imwrite(str(new_path), new_img)

    ims.add_image(str(new_path), update_markerlist=False)
    
    with pytest.raises(KeyError):
        _ = ims.get_imagedata('CD556')

    ims.images = []
    ims.add_image(str(new_path))
    assert np.all(new_img == ims.get_imagedata('CD556'))

def test_wrongdir():
    """tests if all files are found and matched correctly
    """
    ims = ImageStack()
    with pytest.raises(ValueError):
        ims.load_from_dir(Path('.does/not/exits'))

    assert not ims.images

def test_unusable_dir(tmpdir):
    """tests if all files are found and matched correctly
    """
    silly_names = ['a.tiff', '314_CCD_tuff.tiff', 'hey.tif']
    the_dir = tmpdir.mkdir('the_dir')
    for silly in silly_names:
        the_dir.join(silly).write('mock')

    ims = ImageStack()
    ims.load_from_dir(str(the_dir))

    assert not ims.images

    src = list(MANY_SMALL_IMG.glob('*CD8V*.[Tt][Ii][Ff]*'))[0]
    dst = the_dir.join('000_CD8V_xyz.tiff')

    with src.open('rb') as bsrc:
        with dst.open('wb') as bdst:
            bdst.write(bsrc.read())

    ims.load_from_dir(str(the_dir))
    assert len(ims.images) == 1
    assert ims.images[0].marker == 'CD8'

    with dst.open('wb') as bdst:
        bdst.seek(0)
        bdst.write(b'MM IT LOOKS LIKE, BUT IT ISNT!')

    ims.load_from_dir(str(the_dir))
    assert not ims.images

def test_markerlist_gen(tmpdir):
    """tests if all files are found and matched correctly
    """
    count = 2
    markername = 'CD8'
    file_temp = '00{}_{}V_xyz.tiff'

    # generate two similar
    the_dir = tmpdir.mkdir('the_dir')
    dsts = [the_dir.join(file_temp.format(i, markername)) for i in range(count)]

    src = list(MANY_SMALL_IMG.glob('*CD8V*.[Tt][Ii][Ff]*'))[0]
    with src.open('rb') as bsrc:
        for dst in dsts:
            bsrc.seek(0)
            with dst.open('wb') as bdst:
                bdst.write(bsrc.read())

    ims = ImageStack()
    ims.load_from_dir(str(the_dir))

    assert ims.marker_list[0] != ims.marker_list[1]
    assert markername in ims.marker_list[0]
    assert markername in ims.marker_list[1]

def test_markerlist_gen_mix(tmpdir):
    """tests if all files are found and matched correctly
    """
    markername = 'CD8'
    not_marker = 'CD9'
    file_temp = '00{}_{}V_xyz.tiff'

    # generate two similar
    the_dir = tmpdir.mkdir('the_dir')
    dst0 = the_dir.join(file_temp.format(1, not_marker + '5'))
    dst1i = the_dir.join(file_temp.format(2, markername))
    dst2 = the_dir.join(file_temp.format(3, not_marker + '4'))
    dst3i = the_dir.join(file_temp.format(4, markername))
    dst4 = the_dir.join(file_temp.format(5, not_marker + '22'))

    dsts = [dst0, dst1i, dst2, dst3i, dst4]

    src = list(MANY_SMALL_IMG.glob('*CD8V*.[Tt][Ii][Ff]*'))[0]
    with src.open('rb') as bsrc:
        for dst in dsts:
            bsrc.seek(0)
            with dst.open('wb') as bdst:
                bdst.write(bsrc.read())

    ims = ImageStack()
    ims.load_from_dir(str(the_dir))

    assert len(ims.marker_list) == 5
    indexed_marker = [n for n, mn in enumerate(ims.marker_list) \
        if markername in mn]

    for idx in range(5):
        idx_fn = str(ims.images[idx].cached_path)
        if idx in indexed_marker:
            assert idx_fn in [str(inpath) for inpath in [dst1i, dst3i]]
        else:
            cur_marker = ims.marker_list[idx]
            cur_fn = str(ims.images[idx].cached_path)
            assert cur_marker in  cur_fn

def test_imagestack_shape():
    """test get image including caching
    """
    ims = ImageStack()
    ims.load_from_dir(INVALID_XML_DIR)

    # assert shape is propageted correctly from tiff images
    assert ims.shape == (462, 420)

def test_invalid_shapes(tmpdir):
    """test get image including caching
    """
    fake_dir = tmpdir.mkdir('fake')
    tiff0 = fake_dir.join('0_CD3_huhu.tif')
    tiff1 = fake_dir.join('0_CD8_huhu.tif')

    for hei, wid, to_file in [(10, 20, tiff0), (11, 20, tiff1)]:
        img_dat = np.round(np.random.random(hei*wid) * 0xffff)
        img_dat = img_dat.astype(np.uint16).reshape(hei, wid)
        cv2.imwrite(str(to_file), img_dat)

    ims = ImageStack()
    with pytest.raises(ValueError):
        ims.load_from_dir(str(fake_dir))

def test_get_imagedata():
    """test get image including caching
    """
    fetch_idx = 1

    ims = ImageStack()
    ims.load_from_dir(SOME_SMALL_IMG)

    # is loaded?
    assert len(ims) == 3

    # but not data yet?
    px_data = [img.pixel_data for img in ims.images]
    assert all([data is None for data in px_data])

    # select marker
    marker_to_fetch = ims.images[fetch_idx].marker
    img_data = ims.get_imagedata(marker_to_fetch)

    # but now we have the data!
    assert not img_data is None

    # while the rest is untouched
    px_data = [ims.images[i].pixel_data for i in range(3) \
            if i != fetch_idx]
    assert all([data is None for data in px_data])

    # assert we get the chached image next time
    img_data_again = ims.get_imagedata(marker_to_fetch)
    assert img_data is img_data_again

def test_get_invalid_imagedata():
    """test get image including caching
    """
    ims = ImageStack()
    ims.load_from_dir(SOME_SMALL_IMG)

    with pytest.raises(KeyError):
        ims.get_imagedata('MeinKopfTutWeh')

def test_get_ome_fs_mix(tmpdir):
    """test get image including caching
    """
    tmpd = tmpdir.mkdir('test')
    fs_meta = tmpd.join(FS_TIF_REF.name)
    ome_meta = tmpd.join(MY_OME_REF.name)

    with FS_TIF_REF.open('rb') as src:
        with fs_meta.open('wb') as dst:
            dst.write(src.read())

    with MY_OME_REF.open('rb') as src:
        with ome_meta.open('wb') as dst:
            dst.write(src.read())

    ims = ImageStack()
    ims.load_from_dir(str(tmpd))

    fs_img = ims.get_image('CD45RO')
    ome_img = ims.get_image('CD115')

    assert ome_img.name == 'AVeryCoolExperiment'

    fs_img_dat = ims.get_imagedata('CD45RO')
    ome_img_dat = ims.get_imagedata('CD115')

    assert np.all(fs_img.pixel_data == fs_img_dat)
    assert np.all(ome_img.pixel_data == ome_img_dat)

    assert fs_img.bit == '16'
    assert ome_img.bit == '16'

def test_load_noneomexml_butfs():
    """test loading an image that does not have valid omexml but
    fs descriptor, ometiff raises a wanted error but imagestack
    should also handle this error and try for fs
    """
    ims = ImageStack()
    ims.load_from_dir(INVALID_XML_DIR)

    #TODO mock dir and mock file in tempdir
    assert ims.marker_list == ['HLA-DQ']

def test_get_origin(tmpdir):
    """test get image including caching
    """
    tmpd = tmpdir.mkdir('test')
    fs_meta = tmpd.join(FS_TIF_REF.name)
    ome_meta = tmpd.join(MY_OME_REF.name)

    with FS_TIF_REF.open('rb') as src:
        with fs_meta.open('wb') as dst:
            dst.write(src.read())

    with MY_OME_REF.open('rb') as src:
        with ome_meta.open('wb') as dst:
            dst.write(src.read())

    ims = ImageStack()
    ims.load_from_dir(str(tmpd))

    fs_path = Path(str(fs_meta))
    ome_path = Path(str(ome_meta))

    fs_img = ims.get_image('CD45RO')
    ome_img = ims.get_image('CD115')

    assert ims.get_imagedata_origin('CD45RO') == fs_path
    assert ims.get_imagedata_origin('CD115') == ome_path

    _ = ims.get_imagedata('CD115')

    assert ims.get_imagedata_origin('CD115') == ome_path
    
    assert not ims.get_imagedata_origin('CD115') == fs_path
    new_dat = np.arange(25).reshape(5, 5, 1)
    fs_img.pixel_data = new_dat
    assert ims.get_imagedata_origin('CD45RO') is new_dat
