import logging

import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

from pattern.utils import field2intensity

__all__ = ["Field"]

logger = logging.getLogger(__name__)


class Field(object):
    """
    Field describes how the final product is formed, including system specification and 
    physical spatial filters.
    
    Args:
        slm (SLM): the SLM used in the system
        obj (Objective): the objective that face toward the sample
        wavelength (float): excitation wavelength in microns
        mag (float): system magnification
    """

    def __init__(self, slm, obj, wavelength, mag, shape=None):
        self._slm, self._obj = slm, obj
        self._wavelength = wavelength

        self._mag = mag

        self._shape = shape if shape else slm.shape

        self._ops = []

    ##

    @property
    def shape(self):
        return self._shape

    @property
    def mag(self):
        """System overall magnification."""
        return self._mag

    @property
    def objective(self):
        return self._obj

    @property
    def ops(self):
        return tuple(self._ops)

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
        n = max(*self.shape)
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
        n = max(*self.shape)
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

    def kz(self):
        gr = self.polar_k()
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

    def simulate(self, cf=0.05, zrange=(-30, 30), zstep=0.1):
        """
        slm_field

        pre_mask_field
        post_mask_field

        obj_field
        """
        import matplotlib.pyplot as plt

        # pattern
        slm_pattern = self.slm_pattern(cf=cf, crop=False)  # simluation requires no-crop
        slm_field_bl = np.exp(1j * slm_pattern * np.pi)

        # REMOVE
        plt.figure("Pattern")
        imshow(None, slm_pattern[self._roi()], cmap="binary")

        # mask
        pupil_field_bl_pre = fftshift(fft2(ifftshift(slm_field_bl)))
        pre_mask = field2intensity(pupil_field_bl_pre)
        pupil_field_bl_post = self.mask(pupil_field_bl_pre)
        post_mask = field2intensity(pupil_field_bl_post)

        vmin, vmax = tuple(np.percentile(post_mask, [0.01, 99.99]))
        logger.debug(f"vmin:{vmin:.4f}, vmax:{vmax:.4f}")

        # REMOVE
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

        # REMOVE
        plt.figure("SLM")
        plt.subplot(121)
        imshow("Ideal", ideal)
        plt.subplot(122)
        imshow("Generated", bl)

        ## axial
        # z = np.arange(zrange[0], zrange[1], step=zstep)
        # axial = np.zeros((pupil_field_bl_post.shape[0], len(z)), dtype=bl.dtype)  # YZ
        # kz = self.kz()
        # for i, iz in enumerate(z):
        #    print(f"{i}, z={iz}um")
        #    field = pupil_field_bl_post * np.exp(1j * kz * iz)
        #    field = fftshift(fft2(ifftshift(field)))
        #    intensity = field2intensity(field)
        #    axial[:, i] = intensity[:, intensity.shape[1] // 2]

        # plt.figure("Axial Profile")
        # imshow(None, axial)
        # plt.gca().set_aspect(self.slm.pixel_size[1] / zstep)

        # .. display
        plt.show()

        return {
            "ideal": ideal,
            "generated": bl,
            "pre_mask": pre_mask,
            "post_mask": post_mask,
        }

    def clear_ops(self, op=None):
        if op is None:
            self._ops = []
        else:
            self._ops.remove(op)

    def register_op(self, op):
        self._ops.append(op)

    ##

    def _roi(self):
        ny0, nx0 = self.slm.shape
        ny, nx = self.shape
        ox, oy = (nx - nx0) // 2, (ny - ny0) // 2
        return slice(oy, oy + ny0), slice(ox, ox + nx0)
