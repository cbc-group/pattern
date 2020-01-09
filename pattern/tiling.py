from abc import ABCMeta, abstractmethod
import logging

import numpy as np

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


class Objective(object):
    def __init__(self, mag, na, f_tube, ri=1.0):
        self._mag, self._na, self._f_tube = mag, na, f_tube
        self._ri = ri

    ##

    @property
    def f(self):
        """Objective focal length."""
        return self.f_tube / self.mag

    @property
    def f_tube(self):
        """Compatible tube lens focal length."""
        return self._f_tube

    @property
    def mag(self):
        """Magnification."""
        return self._mag

    @property
    def na(self):
        """Numerical aperture."""
        return self._na

    @property
    def ri(self):
        """Refractive index."""
        return self._ri


class Field(object):
    def __init__(self, slm, obj, wavelength, f_slm, mag):
        self._slm, self._obj = slm, obj
        self._wavelength = wavelength

        self._f_slm, self._mag = f_slm, mag

        self._init_field()

    ##

    @property
    def data(self):
        return self._data

    @property
    def f_slm(self):
        """Focal length of the SLM imaging lens."""
        return self._f_slm

    @property
    def mag(self):
        """System overall magnification."""
        return self._mag

    @property
    def objective(self):
        return self._obj

    @property
    def real(self):
        return np.real(self.data)

    @property
    def slm(self):
        return self._slm

    @property
    def wavelength(self):
        return self._wavelength

    ##

    def cartesian(self):
        # effective pixel size
        dy, dx = self.slm.pixel_size
        dx /= self.mag
        dy /= self.mag
        dx = dy = 1
        # grid vector
        ny, nx = self.slm.shape
        vx = np.linspace(-(nx - 1) / 2.0, (nx - 1) / 2.0, nx) * dx
        vy = np.linspace(-(ny - 1) / 2.0, (ny - 1) / 2.0, ny) * dy
        # grid
        return np.meshgrid(vy, vx)

    def polar(self):
        gy, gx = self.cartesian()
        return np.hypot(gx, gy)

    ##

    def _init_field(self):
        self._data = np.ones(self.slm.shape, np.complex64)


class Op(ABCMeta):
    @abstractmethod
    def __call__(self, field):
        pass


class Mask(Op):
    pass


class AnnularMask(Mask):
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

    def _d_to_na(self, d):
        


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


class Lattice(Bessel):
    def __init__(self, d_out, d_in, n_beam, spacing):
        super().__init__(d_out, d_in)
        self._n_beam, self._spacing = n_beam, spacing

    def __call__(self, field):
        pass


class Defocus(Op):
    def __init__(self):
        pass

    def __call__(self, field):
        pass

    ##

    @property
    def n_beam(self):
        return self._n_beam

    @property
    def spacing(self):
        return self._spacing

    ##


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    qxga = SLM((1536, 2048), (8.2, 8.2), 1)
    nikon_10x_0p3 = Objective(10, 0.3, 200)

    field = Field(qxga, nikon_10x_0p3, 0.488, 500, 60)

    gy, gx = field.cartesian()
    plt.contourf(gx, gy, field.polar())

    plt.show()

