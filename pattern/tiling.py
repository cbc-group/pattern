from abc import ABC, abstractmethod
import logging

import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

__all__ = []

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
    def __init__(self, slm, mask, obj, wavelength, mag):
        self._slm, self._mask, self._obj = slm, mask, obj
        self._wavelength = wavelength

        self._mag = mag

        self._init_field()
        self.mask.calibrate(self)

    ##

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):
        if self.data.shape != new_data.shape:
            raise ValueError("shape mismatch")
        self._data = new_data

    @property
    def mag(self):
        """System overall magnification."""
        return self._mag

    @property
    def mask(self):
        return self._mask

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

    def cartesian_r(self):
        # effective pixel size
        dy, dx = self.slm.pixel_size
        dx /= self.mag
        dy /= self.mag
        # grid vector
        n = max(*self.slm.shape)
        v = np.linspace(-(n - 1) / 2.0, (n - 1) / 2.0, n)
        vx, vy = v * dx, v * dy
        # grid
        return np.meshgrid(vy, vx, indexing="ij")

    def polar_r(self):
        gy, gx = self.cartesian_r()
        return np.hypot(gx, gy)

    def cartesian_k(self):
        # effective pixel size
        dy, dx = self.slm.pixel_size
        dx /= self.mag
        dy /= self.mag
        # effective resolution unit
        n = max(*self.slm.shape)
        dkx = 2 * np.pi / n / dx
        dky = 2 * np.pi / n / dy
        # grid vector
        v = np.linspace(-(n - 1) / 2.0, (n - 1) / 2.0, n)
        vkx, vky = v * dkx, v * dky
        # grid
        return np.meshgrid(vky, vkx, indexing="ij")

    def polar_k(self):
        gky, gkx = self.cartesian_k()
        return np.hypot(gkx, gky)

    ##

    def slm_field_ideal(self, normalize=True):
        slm_field = fftshift(fft2(ifftshift(self.data)))
        slm_field = np.real(slm_field)
        if normalize:
            slm_field /= slm_field.max()
        return slm_field

    def slm_pattern(self, binary=True, cf=0.15):
        """
        Args:
            binary (bool): binary
            cf (float): cropping factor
        """
        slm_field = self.slm_field_ideal()
        return np.abs(slm_field) > cf

    ##

    def simulate(self):
        slm_field_ideal = self.slm_field_ideal()

        slm_pattern = self.slm_pattern()
        slm_field_bl = np.exp(1j * slm_pattern)

        pupil_field_bl_pre = fftshift(fft2(ifftshift(slm_field_bl)))
        pupil_field_bl_post = self.mask(pupil_field_bl_pre)

        obj_field = fftshift(fft2(ifftshift(pupil_field_bl_post)))
        intensity = np.square(np.abs(obj_field))

        def imshow(title, image, ratio=0.25):
            plt.title(title)
            plt.imshow(image)
            plt.axis("scaled")

            ny, nx = image.shape
            cx, cy = nx // 2, ny // 2
            plt.xlim(cx * (1 - ratio), cx * (1 + ratio))
            plt.ylim(cy * (1 - ratio), cy * ((1 + ratio)))

        plt.figure(1)
        plt.subplot(221)
        imshow("Ideal SLM Field", slm_field_ideal)
        plt.subplot(222)
        imshow("Final Intensity", intensity)
        plt.subplot(212)
        imshow("SLM Pattern", slm_pattern, ratio=1)

        plt.figure(2)
        plt.subplot(121)
        imshow("Pre Mask", np.abs(pupil_field_bl_pre))
        plt.subplot(122)
        imshow("Post Mask", np.abs(pupil_field_bl_post))

        plt.show()

    ##

    def _init_field(self):
        # use maximum confinement
        n = max(*self.slm.shape)
        self._data = np.zeros((n,) * 2, np.complex64)

    def _roi(self):
        ny0, nx0 = self.slm.shape
        ny, nx = self.data.shape
        ox, oy = (nx - nx0) // 2, (ny - ny0) // 2
        return slice(oy, oy + ny0), slice(ox, ox + nx0)


class Op(ABC):
    @abstractmethod
    def __call__(self, field):
        pass


class Mask(Op):
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

    ##

    def calibrate(self, field):
        # distance to effective na
        c = field.mag / (2 * field.slm.f_slm)
        od_na, id_na = self.d_out * c, self.d_in * c
        logger.info(f"[mask] NA:{od_na:.4f}, na:{id_na:.4f}")

        # na to frequency domain size
        c = 2 * np.pi / field.wavelength
        od_na *= c
        id_na *= c

        # generate pupil mask
        mask = field.polar_k()
        self._mask = (mask > id_na) & (mask < od_na)


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
        bessel = self._generate_feature(field)

        # generate position index
        n = self.n_beam
        offsets = np.linspace(-(n - 1) / 2.0, (n - 1) / 2.0, n) * self.spacing
        ky, kx = field.cartesian_k()
        lattice = np.zeros_like(field.data)
        for offset in offsets:
            logging.debug(f"offset:{offset}")
            offset = np.exp(
                1j * offset * (kx * np.cos(self.tilt) + ky * np.sin(self.tilt))
            )
            lattice += bessel * offset

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


def preview(x, y, z, cmap=None):
    if not cmap:
        cmap = "binary" if z.dtype == np.bool else "hot"
    plt.pcolormesh(x, y, z, cmap=cmap)
    plt.axis("scaled")
    plt.show()


if __name__ == "__main__":
    import coloredlogs
    import matplotlib.pyplot as plt

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(3.824, 2.689)
    nikon_10x_0p3 = Objective(10, 0.3, 200)

    field = Field(qxga, mask, nikon_10x_0p3, 0.488, 60)

    # for plotter
    gy, gx = field.cartesian_r()

    lattice = Lattice(3.824, 2.689, 7, 3)
    field = lattice(field)
    # bessel = Bessel(3.824, 2.689)
    # field = bessel(field)

    field.simulate()
