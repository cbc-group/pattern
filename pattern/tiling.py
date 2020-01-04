from abc import ABCMeta, abstractmethod
import logging

import numpy as np
import pyqtgraph as pg

__all__ = []

logger = logging.getLogger(__name__)


class SLM(object):
    def __init__(self, shape, pixel_size, bit_depth):
        self._shape = shape
        self._pixel_size = pixel_size
        self._bit_depth = bit_depth

    ##

    @property
    def pixel_size(self):
        return self._pixel_size

    @property
    def shape(self):
        return self._shape


class Field(object):
    def __init__(self, slm, wavelength, oversample=1):
        self._slm = slm
        self._wavelength = wavelength

        self._oversample = oversample

        self._init_field()

    ##

    @property
    def amplitude(self):
        return self._amplitude

    @amplitude.setter
    def amplitude(self, amp):
        if amp.shape != self.amplitude.shape:
            raise ValueError("shape mismatch")
        if amp.dtype != self.amplitude.dtype:
            logger.warning(f'coerce to "{self.amplitude.dtype}"')
            amp = amp.astype(self.amplitude.dtype)
        self._amplitude = amp

    @property
    def oversample(self):
        return self._oversample

    @property
    def phase(self):
        return self._phase

    @property
    def slm(self):
        return self._slm

    @property
    def wavelength(self):
        return self._wavelength

    ##

    def grid(self):
        pass

    ##

    def _init_field(self):
        self._amplitude = np.ones(self.slm.shape, np.float32)
        self._phase = np.zeros_like(self.amplitude)


class Op(ABCMeta):
    @abstractmethod
    def __call__(self, field):
        pass


class Mask(Op):
    def __init__(self, d_out, d_in):
        self._d_out, self._d_in = d_out, d_in

    def __call__(self, field):
        pass

    ##

    @property
    def d_in(self):
        return self._d_in

    @property
    def d_out(self):
        return self._d_out


class Bessel(Op):
    def __init__(self, d_out, d_in):
        self._d_out, self._d_in = d_out, d_in

    def __call__(self, field):
        pass

    ##

    @property
    def d_in(self):
        return self._d_in

    @property
    def d_out(self):
        return self._d_out

    ##


class FocusTiling(Op):
    def __init__(self):
        pass

    def __call__(self, field):
        pass

    ##

    ##


if __name__ == "__main__":
    qxga = SLM((1536, 2048), (8.2, 8.2), 1)
    field = Field(qxga, 0.488)

    annular = (0.64, 0.45)

    bessel = Bessel(*annular)(field)
    mask = Mask(*annular)(bessel)

