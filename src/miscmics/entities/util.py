"""Helperfunctions needed at several points in entitiy generation
"""

# built-in
from typing import List

# external
import numpy as np
import cv2


def simplify_contour(contour: List[np.ndarray]) -> List[np.ndarray]:
    """Simplify a contour, if possible

    Just removing doublicates

    Parameters
    --------
    contour : List[np.ndarray]
        Contour to be simplified. Will remove doublicates

    Returns
    --------
    contour : List[np.ndarray]
        Now hopfully simplified contour
    """

    simplified = []
    for shape in contour:
        simple_shape = []
        last_pt = None, None
        for cur_pt in shape:
            if cur_pt[0] != last_pt[0] or cur_pt[1] != last_pt[1]:
                simple_shape.append(cur_pt)
            last_pt = cur_pt
        simplified.append(simple_shape)
    return simplified


def mask_to_contour(mask_slice: List[slice],
                    mask: np.ndarray) -> List[np.ndarray]:
    """Generates a contour for a mask, ofsetted by an slice

    Parameters
    ------------
    mask_slice : List[slice]
        List of slices. As e.g. returned by numpy.s_ wich is interpreted
        as offset. The array returned after indexind with mask_slice must
        have the same shape as mask

    mask : np.ndarray
        Boolean mask, selecting the pixel within mask_slice that are inside
        the contour

    Returns
    --------
    contour : List[np.ndarray]
        Contour of the mask
    """

    slice_shape = []
    for slc in mask_slice:
        try:
            slice_shape.append(slc.stop - slc.start // slc.step)
        except TypeError:
            slice_shape.append(slc.stop - slc.start)

    if tuple(slice_shape) != mask.shape:
        raise ValueError('Mask slice and mask do not match')

    # compress verticals and horizontals
    method = cv2.CHAIN_APPROX_SIMPLE

    # retrive tree hirachy
    # mode = cv2.RETR_EXTERNAL
    mode = cv2.RETR_LIST

    contour_data = cv2.findContours(
        mask.astype(np.uint8), mode, method)
    try:
        # opencv version 3
        _, contour, _ = contour_data
    except ValueError:
        # opencv version 2
        contour, _ = contour_data

    contour = [shape.squeeze() for shape in contour]

    if mask_slice is None:
        return contour

    shifted_contour = []
    for shape in contour:
        row_of, col_of = mask_slice

        try:
            shape[:, 0] += col_of.start
            shape[:, 1] += row_of.start
        except IndexError:
            # catch exception if contour is just a point
            shape = shape.reshape(1, 2)
            shape[:, 0] += col_of.start
            shape[:, 1] += row_of.start

        shifted_contour.append(shape)

    return shifted_contour


def get_sliced_mask(arr, value, seek=1000):
    """Find the slice and bool mask for value in array. Search in
    in around seek indices around first occurence of value in array

    Returns
    --------
    value_slice : tuple of slices
        slicecing objects, locating bool mask in the array arr

    mask : boolean ndarray mask
        boolian mask, masking all values in arr

    Notess
    ------
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
