from abc import ABC
import logging

import numpy as np

from pattern.field import Field

__all__ = ["AnnularMask"]

logger = logging.getLogger(__name__)


class Mask(ABC):
    def __init__(self):
        self._mask = None

    def __call__(self, field):
        if isinstance(field, Field):
            field.data *= self.mask
        else:
            field *= self.mask
        return field

    ##

    @property
    def mask(self):
        return self._mask

    ##

    def calibrate(self, field):
        pass


class AnnularMask(Mask):
    def __init__(self, d_out, d_in):
        super().__init__()
        self._d_out, self._d_in = d_out, d_in
        self._na_out, self._na_in = None, None

    ##

    @property
    def d_in(self):
        return self._d_in

    @property
    def d_out(self):
        return self._d_out

    @property
    def mask(self):
        if self._mask is None:
            raise RuntimeError("please calibrate the mask by a field first")
        return self._mask

    @property
    def na_in(self):
        return self._na_in

    @property
    def na_out(self):
        return self._na_out

    ##

    def calibrate(self, field):
        # distance to effective na
        c = field.mag / (2 * field.slm.f_slm)
        self._na_out, self._na_in = self.d_out * c, self.d_in * c
        logger.info(f"[mask] NA:{self.na_out:.4f}, na:{self.na_in:.4f}")

        # na to frequency domain size
        c = 2 * np.pi / field.wavelength
        od_na = c * self.na_out
        id_na = c * self.na_in

        # generate pupil mask
        mask = field.polar_k()
        self._mask = (mask > id_na) & (mask < od_na)

