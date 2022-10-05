"""Testing entitie related misc functions
"""
import pytest

import numpy as np

from inspectorcell.entities.misc import get_kernel
from miscmics.processing.entities.extract import get_sliced_mask

def test_get_masks_grey():
    mapping = np.zeros((300, 500), np.uint16)

    cur_val = 0
    values = []
    for r in (10, 15, 100, 250):
        for c in (5, 10, 230, 450):
            cur_val += 1
            values.append(cur_val)
            # fill with current value and make some edgeds
            mapping[r:r + 10, c:c + 8] = cur_val
            mapping[r + 5, c + 3] = 0
            mapping[r, c] = 0

    # a reference mask
    for cur_val in values:
        value_slice, mask = get_sliced_mask(mapping, cur_val)

        # assert everything in the mask is found
        # import IPython as ip
        # ip.embed()
        arr_slice = mapping[value_slice]
        assert np.all(arr_slice[mask] == cur_val)
        assert np.all(arr_slice[~mask] == 0)

        # assert nothin outside of masked slice
        mapping[value_slice][mask] = 0
        assert np.sum(mapping == cur_val) == 0

def test_kernel_generation():

    with pytest.raises(ValueError):
        kern = get_kernel(0)

    one = get_kernel(1)
    assert one.dtype == np.uint8
    assert np.all(one.ravel() == np.ones(4, np.uint8))

    assert np.all(get_kernel(2) == np.array(
        [[0, 1, 1, 0],
         [1, 1, 1, 1],
         [1, 1, 1, 1],
         [0, 1, 1, 0],
        ], dtype=np.uint8)
    )
