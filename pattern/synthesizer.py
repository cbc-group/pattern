import logging

import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

from .field import Field

__all__ = ["Simulation"]

logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, field: Field):
        self._field = field

    ##

    @property
    def field(self):
        return self._field

    ##

    def excitation_xz(self):
        pass

    def excitation_yz(self):
        pass

    ##

    def _dither(self):
        pass

    def ideal_field(self, bounded=False):
        """
        Ideal field after applying all the operations.

        Args:
            bounded (bool): pattern is bounded to SLM physical size   
        """
        n = max(*self.field.shape)
        ideal_field = np.zeros((n,) * 2, np.complex64)

        for op in self.field.ops:
            ideal_field = op.apply(ideal_field)

        # restore to real space
        ideal_field = fftshift(fft2(ifftshift(ideal_field)))
        ideal_field = np.real(ideal_field)

        # normalize to [-1, 1]
        ideal_field /= np.abs(ideal_field).max()

        # bounded?
        if bounded:
            slm_roi = np.zeros_like(ideal_field)
            slm_roi[self._roi()] = 1
            ideal_field *= slm_roi

        return ideal_field

    def slm_pattern(self, binary=True, cf=0.15, crop=True, bounded=False):
        """
        Generate target SLM pattern.

        Args:
            binary (bool, optional): binary pattern # TODO should be inferred from field.slm
            cf (float, optional): cropping factor # TODO should be inferred by dithered side lobe ratio
            crop (bool, optiona): crop result to SLM boundary
            bounded (bool, optional): pattern is bounded to SLM physical size   
        """
        ideal_field = self.ideal_field(bounded)

        # remove spurious signals
        ideal_field[np.abs(ideal_field) <= cf] = 0

        if binary:
            pattern = np.sign(ideal_field) >= 0
        else:
            raise NotImplementedError("gray-scale pattern generation not vetted yet")

        # crop to slm boundary
        if crop:
            pattern = pattern[self.field._roi()]

        return pattern
