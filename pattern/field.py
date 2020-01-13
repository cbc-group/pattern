import logging

import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

from pattern.utils import field2intensity

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

    def slm_field_ideal(self, normalize=True):
        slm_field = fftshift(fft2(ifftshift(self.data)))
        slm_field = np.real(slm_field)
        if normalize:
            slm_field /= slm_field.max()
        return slm_field

    def slm_pattern(self, binary=True, cf=0.15, crop=True):
        """
        Args:
            binary (bool): binary
            cf (float): cropping factor
        """
        slm_field = self.slm_field_ideal()

        # remove spurious signals
        slm_field[np.abs(slm_field) <= cf] = 0

        slm_pattern = np.sign(slm_field) >= 0
        if crop:
            slm_pattern = slm_pattern[self._roi()]
        return slm_pattern

    ##

    def simulate(self):
        slm_field_ideal = self.slm_field_ideal()

        # simluation requires no-crop
        slm_pattern = self.slm_pattern(cf=0.01, crop=False)
        slm_field_bl = np.exp(1j * slm_pattern * np.pi)

        temp = fftshift(fft2(ifftshift(slm_field_bl)))
        pupil_field_bl_pre = temp.copy()
        pupil_field_bl_post = self.mask(temp)

        obj_field = fftshift(fft2(ifftshift(pupil_field_bl_post)))
        intensity = np.square(obj_field)

        def imshow(title, image, ratio=0.25, **kwargs):
            if title:
                plt.title(title)
            plt.imshow(image, cmap="hot", **kwargs)
            plt.axis("scaled")

            ny, nx = image.shape
            cx, cy = nx // 2, ny // 2
            plt.xlim(cx * (1 - ratio), cx * (1 + ratio))
            plt.ylim(cy * (1 - ratio), cy * ((1 + ratio)))

        plt.figure("SLM")
        plt.subplot(121)
        imshow("Ideal", np.square(slm_field_ideal))
        plt.subplot(122)
        imshow("Generated", intensity)

        # cropped
        slm_pattern = self.slm_pattern(cf=0.01, crop=True)

        plt.figure("Pattern")
        imshow(None, slm_pattern, ratio=1)

        pupil_field_bl_pre = field2intensity(pupil_field_bl_pre)
        pupil_field_bl_post = field2intensity(pupil_field_bl_post)
        # match scale of post
        vmin, vmax = tuple(np.percentile(pupil_field_bl_post, [0.01, 99.99]))
        logger.debug(f"vmin:{vmin}, vmax:{vmax}")
        plt.figure("Mask")
        plt.subplot(121)
        imshow("Pre", pupil_field_bl_pre, vmin=vmin, vmax=vmax)
        plt.subplot(122)
        imshow("Post", pupil_field_bl_post, vmin=vmin, vmax=vmax)

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
