from abc import ABC, abstractmethod
import logging

import numpy as np
from tqdm import tqdm

__all__ = ["Bessel", "Lattice", "Defocus"]

logger = logging.getLogger(__name__)


class Op(ABC):
    @abstractmethod
    def __call__(self, field):
        pass


class Bessel(Op):
    def __init__(self, d_out, d_in):
        self._d_out, self._d_in = d_out, d_in

    def __call__(self, field):
        bessel = self._generate_feature(field)
        field.data += bessel
        return field

    ##

    @property
    def d_in(self):
        return self._d_in

    @property
    def d_out(self):
        return self._d_out

    ##

    def _generate_feature(self, field):
        # distance to effective na
        c = field.mag / (2 * field.slm.f_slm)
        od_na, id_na = self.d_out * c, self.d_in * c
        logger.info(f"[bessel] NA:{od_na:.4f}, na:{id_na:.4f}")

        # na to frequency domain size
        c = 2 * np.pi / field.wavelength
        od_na *= c
        id_na *= c

        # generate and apply
        bessel = field.polar_k()
        bessel = (bessel > id_na) & (bessel < od_na)

        return bessel


class Lattice(Bessel):
    def __init__(self, d_out, d_in, n_beam, spacing, tilt=0.0):
        super().__init__(d_out, d_in)
        self._n_beam, self._spacing, self._tilt = n_beam, spacing, tilt

    def __call__(self, field):
        # tile-corrected grid
        ky, kx = field.cartesian_k()
        grid = kx * np.cos(self.tilt) + ky * np.sin(self.tilt)

        # generate position index
        n = self.n_beam
        offsets = np.linspace(-(n - 1) / 2.0, (n - 1) / 2.0, n) * self.spacing

        # mux
        offsets_sum = np.zeros_like(field.data)
        for offset in tqdm(offsets):
            logger.debug(f"offset:{offset}")
            offsets_sum += np.exp(1j * offset * grid)

        # apply bessel
        bessel = self._generate_feature(field)
        lattice = bessel * offsets_sum

        # energy conservation
        lattice /= n

        field.data += lattice

        return field

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


class Defocus(Op):
    def __init__(self, focus, weights=None):
        if weights is None:
            weights = (1,) * len(focus)
        self._focus, self._weights = tuple(focus), tuple(weights)

    def __call__(self, field):
        # template and workspace
        field_template = field.data
        field_sum = np.zeros_like(field.data)
        # focal axis resolution
        gr = field.polar_r()
        print(gr.dtype)
        print(gr.shape)
        # pre-filter
        kz2 = np.square(2 * np.pi / field.wavelength) - np.square(gr)
        n_neg = len(kz2 < 0)
        if n_neg > 0:
            logger.warning(
                f"SLM total area exceeds annulus confinement ({n_neg} element(s))"
            )
        kz2[kz2 < 0] = 0
        kz = np.sqrt(kz2)
        # iterate over weights
        for f, w in zip(self.focus, self.weights):
            field_sum += field_template * w * np.exp(1j * kz * f)
        field.data = field_sum
        return field

    ##

    @property
    def focus(self):
        return self._focus

    @property
    def weights(self):
        return self._weights
