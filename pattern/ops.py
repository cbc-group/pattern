from abc import ABC, abstractmethod
import logging

import numpy as np
from tqdm import tqdm

from .field import Field

__all__ = ["Bessel", "Lattice", "Defocus"]

logger = logging.getLogger(__name__)


class Op(ABC):
    def __call__(self, field: Field):
        assert isinstance(field, Field), "Ops can only apply register with a Field"
        field.register_op(self)

        self.update(field)

        return field

    ##

    @abstractmethod
    def apply(self, field: np.ndarray):
        """Apply effect to a proposed field."""
        return field  # noop

    def update(self, field: Field):
        """Trigger update using current field."""
        pass


class Bessel(Op):
    def __init__(self, d_out, d_in):
        self._d_out, self._d_in = d_out, d_in

    ##

    @property
    def d_in(self):
        return self._d_in

    @property
    def d_out(self):
        return self._d_out

    @property
    def na_in(self):
        return self._na_in

    @property
    def na_out(self):
        return self._na_out

    ##

    def apply(self, field):
        field += self._bessel
        return field

    def update(self, field):
        # distance to effective na
        c = field.mag / (2 * field.slm.f_slm)
        self._na_out, self._na_in = self.d_out * c, self.d_in * c
        logger.info(f"[bessel] NA:{self.na_out:.4f}, na:{self.na_in:.4f}")

        # na to frequency domain size
        c = 2 * np.pi / field.wavelength
        od_na = c * self.na_out
        id_na = c * self.na_in

        # generate template
        bessel = field.polar_k()
        bessel = (bessel > id_na) & (bessel < od_na)

        self._bessel = bessel


class Lattice(Bessel):
    def __init__(self, d_out, d_in, n_beam, spacing, tilt=0.0):
        super().__init__(d_out, d_in)
        self._n_beam, self._spacing, self._tilt = n_beam, spacing, tilt

    ##

    @property
    def n_beam(self):
        return self._n_beam

    @property
    def spacing(self):
        return self._spacing

    @property
    def tilt(self):
        return self._tilt

    ##

    def apply(self, field):
        field += self._lattice
        return field

    def update(self, field):
        # generate bessel template
        super().update(field)

        # tile-corrected grid
        ky, kx = field.cartesian_k()
        grid = kx * np.cos(self.tilt) + ky * np.sin(self.tilt)

        # generate position index
        n = self.n_beam
        offsets = np.linspace(-(n - 1) / 2.0, (n - 1) / 2.0, n) * self.spacing

        # mux
        n = max(*field.shape)
        offsets_sum = np.zeros((n,) * 2, np.complex64)
        for offset in tqdm(offsets):
            logger.debug(f"offset:{offset}")
            offsets_sum += np.exp(1j * offset * grid)

        # apply bessel
        lattice = self._bessel * offsets_sum

        # energy conservation
        lattice /= n

        self._lattice = lattice


class Defocus(Op):
    def __init__(self, focus):
        self._focus = focus

    ##

    @property
    def focus(self):
        return self._focus

    @property
    def weights(self):
        return self._weights

    ##

    def apply(self, field):
        field *= self._defocus
        return field

    def update(self, field):
        kz = field.kz()
        self._defocus = np.exp(1j * kz * self.focus)
