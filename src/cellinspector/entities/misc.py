"""Helperfunctions needed at several points in entitiy generation
"""
import numpy as np


def get_sliced_mask(arr, value, seek=50):
    """Find the slice and bool mask for value in array. Search in
    in around seek indices around first occurence of value in array

    Returns
    -------
    value_slice : tuple of slices
        slicecing objects, locating bool mask in the array arr

    mask : boolean ndarray mask
        boolian mask, masking all values in arr

    Notes
    -----
    slice is inclusive, thus arr[slice].shape == mask.shape

    seek defines a view on arry to look for a slice. Given ath the index (n, m)
    is the first occurence of value in arr, then the mask will be genarted only
    for the view arr[n - seek:n + seek, m - seek:m + seek]
    """
    # find index of first occurence
    first_index = np.argmax(arr == value)
    first_row, first_col = np.unravel_index(first_index, arr.shape)
    arr_rows, arr_cols = arr.shape

    # get arr offset, and serach window
    view_row0 = max(first_row - seek, 0)
    view_col0 = max(first_col - seek, 0)
    view_row1 = min(first_row + seek, arr_rows)
    view_col1 = min(first_col + seek, arr_cols)
    window = arr[view_row0:view_row1, view_col0:view_col1]

    window = window == value
    rows = np.any(window, axis=1)
    cols = np.any(window, axis=0)
    win_rows, win_cols = window.shape
    rmin, rmax = np.argmax(rows), win_rows - np.argmax(rows[::-1]) - 1
    cmin, cmax = np.argmax(cols), win_cols - np.argmax(cols[::-1]) - 1

    mask = window[rmin:rmax+1, cmin:cmax+1]
    mask_rows, mask_cols = mask.shape

    row_offset = view_row0 + rmin
    col_offset = view_col0 + cmin

    value_slice = np.s_[row_offset:row_offset + mask_rows,
                        col_offset:col_offset + mask_cols]

    return value_slice, mask
