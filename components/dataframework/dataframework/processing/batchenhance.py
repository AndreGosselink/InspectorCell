# -*- coding: utf-8 -*-

"""batchprocessing images in folder, scaling and enhancing contrast
"""

from data import ImageStack
import cv2
import numpy as np
from pathlib import Path

import IPython as ip


print('Starting')

imgdir = Path('stains')
clahe = cv2.createCLAHE(clipLimit=80, tileGridSize=(16, 16))
w, h = 0, 0

images = imgdir.glob('*.[Tt][Ii][Ff]*')
for img_path in images:
    # cropping and rescaling
    
    print(img_path)
    cur_img = np.flipud(cv2.imread(str(img_path), cv2.IMREAD_ANYDEPTH)).T

    process_img = cur_img[100:-100, 100:-100]
    process_img = cv2.resize(process_img, (0,0), fx=0.25, fy=0.25) 

    # hist processing
    process_img = clahe.apply(process_img)
    # dynamic range correction
    # contrast /= np.max(contrast)
    # contrast *= 255
    # contrast = contrast.astype(np.uint8)
    # try:
    #     equ = cv2.equalizeHist(contrast)
    # except:
    #     ip.embed()
    
    # change bitness
    process_img = process_img.astype(float)
    process_img /= 0xff # / 0xffff * 0xff
    process_img = process_img.astype(np.uint8)
    
    name = Path('scaled') / img_path.name
    cv2.imwrite(str(name), process_img)

print('Processed')

# selected = []
# for cimg in imgs.image_data:
#     cv2.imshow('image',cimg)
#     k = cv2.waitKey(0)
#     if k == 27:         # wait for ESC key to exit
#         cv2.destroyAllWindows()
#         break 
#     elif k == ord('n'):
#         cv2.destroyAllWindows()
#         continue
#     
#     selected.append(cimg)
#     cv2.destroyAllWindows()
# 
# # generate pillar
# pillar = []
# for i in range(len(imgs) // 2):
#     ri0 = i * 2
#     ri1 = i * 2 + 1
#     row = np.vstack([imgs.image_data[ri0], imgs.image_data[ri1]])
#     pillar.append(row)
# 
# pillar = np.hstack(pillar)
# print('Stacked')
# 
# # save it
# cv2.imwrite('pillar.tiff', pillar)
# print('Saved')
