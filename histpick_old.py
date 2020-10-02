from pathlib import Path
import numpy as np
import shutil
import logging


LOG = logging.getLogger(__name__)


def score(x, ref):
    score = x / ref
    if score >= 1:
        # score = np.exp(1 - score)
        score = 0
    return score


# import matplotlib.pyplot as plt
# x = np.linspace(0, 0xffff, 200)
# vec_score = np.vectorize(score)
# plt.plot(x, vec_score(x, 0xfff))
# plt.show()


def part_ratio(img, bincount=0xfff, cutoff=0xfff, sat_trgt=0.001):
    """returns the ratio of counts in inverse lower slice and uppe slice
    minimized for all the counts in the lower slice and none in the upper
    ret > 1 more in upper than in lower
    ret < 1 more in lower than in upper

    """
    counts, bins = np.histogram(img.ravel(), bins=bincount)
    bins = bins[1:]
    
    sat_trgt = sat_trgt * img.size
    tail = 0
    edge = 1
    for i in range(1, len(bins)):
        tail += counts[-i]
        if tail >= sat_trgt:
            edge = bins[-i]
            break
    
    return score(edge, cutoff)


def select_optimal(src, markerfilter=None):
    """for each marker selects the one with the best part_ratio
    """
    selection = {}
    log = logging.getLogger()
    ims = ImageStack()
    ims.load_from_dir(src)
    unique = set(m.split(' - ')[0] for m in ims.marker_list)
    if not markerfilter is None:
        unique = [uni for uni in unique if uni in markerfilter]
    log.info('Processing %d markers:', len(unique))
    log.info(', '.join(unique))
    for uni in unique:
        best = ('', -np.inf)
        all_scores = []
        for i in range(-1, 6):
            if i == -1:
                marker = uni
            else:
                marker = f'{uni} - {i}'
            try:
                img = ims.get_imagedata(marker)
                score = part_ratio(img)
                all_scores.append(score)
                if score > best[1]:
                    best = (marker, score)
            except KeyError:
                pass
        best_marker, best_score = best
        if best_marker == '':
            log.warn('No image for %s!', uni)
            selection[uni] = None
            continue

        best_img = ims.get_image(best_marker)
        selection[uni] = (best_img.cached_path, best_score, all_scores)

    return selection


def score_imgstack(image_stack):
    """Evaluates all images in image stack and adds an score
    as metadata _in place_. Highest score -> best use of histogram
    Changes metadata 
    """
    for img in image_stack.data:
        sc = part_ratio(np.asarray(img))
        img.meta['hist_score'] = sc


def strip_nonopt(image_stack, by_key='name'):
    """strips all images, that have non-optimal hist_score
    _in place_
    """
    # struct data by key
    all_images = {}
    for img in image_stack.data:
        key_val = img.meta[by_key]
        cands = all_images.get(key_val, [])
        cands.append(img)
        all_images[key_val] = cands
    
    # sort and select
    for key_val, cands in all_images.items():
        # inplace sorting
        cands.sort(key=lambda i: i.meta['hist_score'])
        LOG.debug(['{:.1e}'.format(i.meta['hist_score']) for i in cands])
        all_images[key_val] = cands[-1]

    image_stack.data = list(all_images.values())
