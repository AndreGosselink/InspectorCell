"""Make tables from miscmics classes
"""
import pandas as pd

from ..multiplex import ImageStack


def make_metadata_tabel(ims: ImageStack) -> pd.DataFrame:
    """Packs all channel metadatad of an ImageStack into a table

    Parameter
    ---------
    ims : ImageStack
        Imagestack from wich all channel information will be stored
        in the resulting pandas DataFrame

    Returns
    -------
    tab : pandas.DataFrame
        Dataframe with all channel metadata
    """
    unis = ims.unique()
    ret = {key: list() for key in unis.keys()}

    for uname in unis['name']:
        chan, = ims.find({'name': uname}, single=False)
        for mkey in ret.keys():
            mval = chan.meta.get(mkey)
            ret[mkey].append(mval)

    return pd.DataFrame(ret)
