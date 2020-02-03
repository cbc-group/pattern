import logging

import numpy as np
from PIL import Image

__all__ = ["write_pattern_bmp"]


logger = logging.getLogger(__name__)


def field2intensity(field):
    return np.real(np.square(field))


def write_pattern_bmp(uri, image):
    """Fix binary BMP writeback."""
    image = Image.frombytes("1", image.shape[::-1], np.packbits(image, axis=1))
    image.save(uri)
