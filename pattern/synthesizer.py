from functools import partial
import logging
from typing import Optional

import numpy as np
from scipy.fftpack import fft2, fftshift, ifftshift

from .field import Field
from .mask import Mask

__all__ = ["Synthesizer"]

logger = logging.getLogger(__name__)


class Synthesizer(object):
    def __init__(self, field: Field, mask: Optional[Mask] = None):
        self._field = field
        self._mask = mask  # spatial filter

    ##

    @property
    def field(self):
        return self._field

    @property
    def mask(self):
        return self._mask

    ##

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
            slm_roi[self.field._roi()] = 1
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

    ##

    def simulate(self, options, crop=False, zrange=(-100, 100), zstep=10, **kwargs):
        from multiprocessing import cpu_count, Pool

        results = dict()

        def save(key, _image, e_field=True):
            image = _image.copy()
            if e_field:
                image = np.square(image)
                image = np.real(image)
            results[key] = image

        pattern = self.slm_pattern(crop=False, **kwargs)  # do not crop in the process
        save("pattern", pattern, e_field=False)

        slm_field = np.exp(1j * pattern * np.pi)

        pre_mask = fftshift(fft2(ifftshift(slm_field)))
        save("pre_mask", pre_mask)

        self.mask.calibrate(self.field)
        post_mask = self.mask(pre_mask.copy())
        save("post_mask", post_mask)

        obj_field = fftshift(fft2(ifftshift(post_mask)))
        save("excitation_xz", obj_field)

        if "excitation_xy" in options:
            from tqdm import tqdm

            y = np.arange(*zrange, step=zstep)
            xy = np.zeros((self.field.shape[1], len(y)), dtype=obj_field.dtype)
            kz = self.field.kz()

            """
            # defocus term
            defocus = np.einsum("ji,k->jik", kz, y)
            defocus = np.exp(1j * defocus)

            # scan over z
            f = np.einsum("ji,jik->jik", post_mask, defocus)

            # back to real space
            f = ifftshift(f, axes=(0, 1))
            f = fft2(f, axes=(0, 1))
            f = fftshift(f, axes=(0, 1))

            # E field to intensity
            f = np.square(f)
            f = np.real(f)

            # select XY view
            xy = f.max(axis=0)
            """

            logger.info("iterating over Y axis")
            """
            for i, iy in tqdm(enumerate(y), total=len(y)):
                f = post_mask * np.exp(1j * kz * iy)
                f = fftshift(fft2(ifftshift(f)))

                f = np.square(f)
                f = np.real(f)

                xy[:, i] = f.max(axis=0)
            """
            with Pool(cpu_count()) as pool:
                func = partial(self._simulate_xy, post_mask=post_mask, kz=kz)
                xy = [r for r in tqdm(pool.imap_unordered(func, y), total=len(y))]
            xy.sort(key=lambda x: x[0])
            xy = np.vstack([i for _, i in xy])

            save("excitation_xy", xy.T)

        if crop:
            for key, image in results.items():
                results[key] = image[self.field._roi()]

        return results

    def _simulate_xy(self, y, post_mask, kz):
        defocus = np.exp(1j * kz * y)

        f = post_mask * defocus
        f = fftshift(fft2(ifftshift(f)))

        f = np.square(f)
        f = np.real(f)

        return y, f.max(axis=0)

    ##

    def _dither(self):
        pass
