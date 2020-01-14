import logging

import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

from pattern.utils import field2intensity, imshow

__all__ = ["Field"]

logger = logging.getLogger(__name__)


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

    def kz(self):
        gr = self.polar_r()
        kz2 = np.square(2 * np.pi / self.wavelength) - np.square(gr)
        n_neg = len(kz2 < 0)
        if n_neg > 0:
            logger.warning(
                f"SLM total area exceeds annulus confinement ({n_neg} element(s))"
            )
        kz2[kz2 < 0] = 0
        kz = np.sqrt(kz2)
        return kz

    ##

    def slm_field_ideal(self, normalize=True):
        slm_field = fftshift(fft2(ifftshift(self.data)))
        slm_field = np.real(slm_field)
        if normalize:
            slm_field /= slm_field.max()
        return slm_field

    def slm_pattern(self, binary=True, cf=0.15, crop=True, ideal=False):
        """
        Args:
            binary (bool): binary
            cf (float): cropping factor
        """
        slm_field = self.slm_field_ideal()

        # remove spurious signals
        slm_field[np.abs(slm_field) <= cf] = 0
        # remove out-of-bound features
        # if not ideal:
        #    mask = np.ones_like(slm_field)
        #    mask[self._roi()] = 0
        #    slm_field *= mask

        # binarize
        slm_pattern = np.sign(slm_field) >= 0

        # crop to fit size
        if crop:
            slm_pattern = slm_pattern[self._roi()]

        return slm_pattern

    ##

    def simulate(self, cf=0.05, zrange=(-30, 30), zstep=0.1):
        """
        slm_field

        pre_mask_field
        post_mask_field

        obj_field
        """
        # pattern
        slm_pattern = self.slm_pattern(cf=cf, crop=False)  # simluation requires no-crop
        slm_field_bl = np.exp(1j * slm_pattern * np.pi)

        plt.figure("Pattern")
        imshow(None, slm_pattern[self._roi()], cmap="binary")

        # mask
        pupil_field_bl_pre = fftshift(fft2(ifftshift(slm_field_bl)))
        pre_mask = field2intensity(pupil_field_bl_pre)
        pupil_field_bl_post = self.mask(pupil_field_bl_pre)
        post_mask = field2intensity(pupil_field_bl_post)

        vmin, vmax = tuple(np.percentile(post_mask, [0.01, 99.99]))
        logger.debug(f"vmin:{vmin:.4f}, vmax:{vmax:.4f}")

        plt.figure("Mask")
        plt.subplot(121)
        imshow("Pre", pre_mask, vmin=vmin, vmax=vmax)
        plt.subplot(122)
        imshow("Post", post_mask, vmin=vmin, vmax=vmax)

        # slm
        slm_field_ideal = self.slm_field_ideal()
        ideal = field2intensity(slm_field_ideal)

        obj_field = fftshift(fft2(ifftshift(pupil_field_bl_post)))
        bl = field2intensity(obj_field)

        plt.figure("SLM")
        plt.subplot(121)
        imshow("Ideal", ideal)
        plt.subplot(122)
        imshow("Generated", bl)

        # axial
        z = np.arange(zrange[0], zrange[1], step=zstep)
        axial = np.zeros((pupil_field_bl_post.shape[0], len(z)), dtype=bl.dtype)  # YZ
        kz = self.kz()
        for i, iz in enumerate(z):
            print(iz)
            field = pupil_field_bl_post * np.exp(1j * kz * iz)
            field = fftshift(fft2(ifftshift(field)))
            intensity = field2intensity(field)
            axial[:, i] = intensity[:, intensity.shape[1] // 2]

        plt.figure("Axial Profile")
        imshow(None, axial)

        # .. display
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
