"""Just some imageing function to ensure consistent access to images in the project
"""

# extern
import cv2
import numpy as np


def flipped(image):
    return np.flipud(np.rot90(image))

def getImagedata(imgPath):
    """ read image, return contents as numpy array
    """

    imgData = cv2.imread(str(imgPath), cv2.IMREAD_ANYDEPTH)

    if imgData is None:
        raise ValueError('No valid image at {}'.format(str(imgPath)))

    return imgData

def getFlippedImagedata(imgPath):
    return flipped(getImagedata(imgPath))
