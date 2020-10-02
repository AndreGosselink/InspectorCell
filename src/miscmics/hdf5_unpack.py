from pathlib import Path
import h5py
import numpy as np
import IPython as ip
import imageio

from .multiplex import ImageStack


def read_h5(infile):
    """
    Returns
    -------
    imstacks : Dict[Int, ImageStack]
        Dictionary with in key corresponding to fields and the values
        as the image stacks.
    """
    infile = Path(infile)

    hdf = h5py.File(infile, 'r')

    image_stacks = {}
    fields = {}
    for index, dataset in hdf.items():
        fld = dataset.attrs['field']
        chunks = fields.get(fld, None)
        if chunks is None:
            chunks = []
        chunks.append(dataset)
        fields[fld] = chunks
    
    ds_meta = dict(dataset.attrs)
    channels = ds_meta.pop('channels')
    _ = ds_meta.pop('section_index')
    for fld, chunks in fields.items():
        steps = np.sqrt(len(chunks))
        assert (int(steps) - steps) == 0
        steps = int(steps)
        
        chunk_shape = chunks[0].shape
        ndimg = np.asarray(chunks).reshape((steps, steps) + chunk_shape)

        ndimg = np.transpose(ndimg, (0, 2, 1, 3, 4))
        ndimg = np.concatenate(ndimg, 0)
        ndimg = np.transpose(ndimg, (1, 2, 0, 3))
        ndimg = np.concatenate(ndimg, 0)

        ims = ImageStack(reader=None,
                         meta={'order': channels, 'uri': str(infile)})
        for cidx in range(ndimg.shape[-1]):
            meta = dict(name=channels[cidx])
            im_dat = imageio.core.Array(ndimg[..., cidx], meta)
            ims.add_image(im_dat, meta)

        image_stacks[fld] = ims

    return image_stacks


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.special import expit
    # infile = Path('/home/andre/datasets/ovca318/ovca318chunks_f1_center.h5')
    infile = Path('/home/andre/datasets/ovca318/ovca318chunks_all.h5')
    ims_stacks = read_h5(infile)
    
    
    f, axarr = plt.subplots(1, len(ims_stacks))
    
    for ax, ims in zip(axarr, ims_stacks.values()):
        r = ims.find(dict(name='CD8'))
        g = ims.find(dict(name='CD4'))
        b = ims.find(dict(name='CD3'))
        
        rgb = np.stack([r, g, b], 2)
        ax.imshow(rgb, vmin=0, vmax=1)

    plt.show()
