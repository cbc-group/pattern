import logging

__all__ = ["SLM"]

logger = logging.getLogger(__name__)


class SLM(object):
    def __init__(self, shape, pixel_size, f_slm):
        self._shape = shape
        self._pixel_size = pixel_size
        self._f_slm = f_slm

    ##

    @property
    def f_slm(self):
        """Focal length of the SLM imaging lens."""
        return self._f_slm

    @property
    def pixel_size(self):
        return self._pixel_size

    @property
    def shape(self):
        return self._shape
