import cv2
import skimage.measure as sk
import numpy as np


def get_cv(mask):
    # compress verticals and horizontals
    method = cv2.CHAIN_APPROX_SIMPLE
    # retrive tree hirachy
    mode = cv2.RETR_LIST
    image, contours, hierarchy = cv2.findContours(
        mask.astype(np.uint8), mode, method)
    return [cont.squeeze() for cont in contours]

def get_sk(mask):
    mask = mask.astype(np.uint8) * 2
    contours = sk.find_contours(mask.T, 1, positive_orientation='low')
    return contours

def get_testmask():
    mask1 = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 1, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ], dtype=bool)

    mask2 = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 1, 0],
        [0, 0, 0, 0, 1, 0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        ], dtype=bool)

    return mask1, mask2

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    f, axarr = plt.subplots(1, 2)
    
    for ax, mask in zip(axarr, get_testmask()):
        cv_contour = get_cv(mask)
        sk_contour = get_sk(mask)
    
        ax.imshow(mask)
        for cvc in cv_contour:
            cvl, = ax.plot(cvc[:, 0], cvc[:, 1], c='b', label='CV2', ls=':')
    
        for skc in sk_contour:
            skl, = ax.plot(skc[:, 0], skc[:, 1], c='r', label='SkI', ls='--')
    
    ax.legend([cvl, skl], ['CV2', 'SkI'])
    plt.show()
