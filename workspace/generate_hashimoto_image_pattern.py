import logging
import os

import coloredlogs
import imageio
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from skimage.color import rgb2gray
from skimage.exposure import rescale_intensity
from skimage.transform import rescale, rotate
from skimage.util import pad

logging.getLogger("tifffile").setLevel(logging.ERROR)
coloredlogs.install(
    level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

src_path = "hashimoto_2.jpg"
dst_shape = (1536, 2048)

scale = 3

image = imageio.imread(src_path)

# rotate +90d
# image = rotate(image, 90, resize=True, preserve_range=True)

# rescale
src_shape = image.shape
image = rescale(
    image, scale, preserve_range=True, multichannel=True, anti_aliasing=True
)
logging.info(f"rescale image from {src_shape} to {image.shape}")

# pad to destination shape
src_shape = image.shape[:2]  # potentially colored
pad_shape = tuple(d - s for d, s in zip(dst_shape, src_shape))
# update pad shape to before/after
pad_shape = tuple((p // 2, p - p // 2) for p in pad_shape)
logging.info(f"pad width: {pad_shape}")
if len(image.shape) == 3:
    # color dimension does not need padding
    pad_shape += ((0, 0),)
image = pad(image, pad_shape, mode="constant", constant_values=0)

# convert to u8
image = image.astype(np.uint8)

# gray scale
image_gray = rgb2gray(image)
image_gray = rescale_intensity(image_gray, out_range=np.uint8)
image_gray = image_gray.astype(np.uint8)
imageio.imwrite("hashimoto_slm_gray.bmp", image_gray)

# write RGB
for c, cname in zip(range(3), ("r", "g", "b")):
    imageio.imwrite(f"hashimoto_slm_rgb_{cname}.bmp", np.squeeze(image[..., c]))

