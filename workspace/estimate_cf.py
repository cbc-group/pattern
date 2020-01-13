import logging

import imageio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fftpack import fft2, fftshift, ifftshift

from pattern import SLM, AnnularMask, Bessel, Field, Objective, Lattice
from pattern.utils import field2intensity

logger = logging.getLogger(__name__)


def optimize_cf_passthrough(field, cf_range, cf_step=0.01):
    slm_field_ideal = field.slm_field_ideal()

    cfs = np.arange(*cf_range, step=cf_step)
    ratios = []
    for cf in cfs:
        logger.debug(f"cf:{cf:.04f}")

        slm_pattern = field.slm_pattern(cf=cf, crop=False)
        slm_field_bl = np.exp(1j * slm_pattern * np.pi)
        pupil_field_bl_pre = fftshift(fft2(ifftshift(slm_field_bl)))
        power_pre = field2intensity(pupil_field_bl_pre).sum()
        print(power_pre)

        pupil_field_bl_post = field.mask(pupil_field_bl_pre)
        power_post = field2intensity(pupil_field_bl_post).sum()
        print(power_post)

        ratios.append(power_post / power_pre)

    df = pd.DataFrame({"cf": cfs, "ratio": ratios})
    df.to_csv("cf_intensity.csv", float_format="%f")


def optimize_cf_similarity(field, cf_range, cf_step=0.01):
    slm_field_ideal = field.slm_field_ideal()
    slm_field_ideal /= slm_field_ideal.max()

    imageio.imwrite("ideal.tif", field2intensity(slm_field_ideal).astype(np.float32))

    shape = slm_field_ideal.shape
    n = shape[0] * shape[1]

    cfs = np.arange(*cf_range, step=cf_step)
    sims = []
    for cf in cfs:
        logger.debug(f"cf:{cf:.04f}")

        slm_pattern = field.slm_pattern(cf=cf, crop=False)
        slm_field_bl = np.exp(1j * slm_pattern * np.pi)
        pupil_field_bl_pre = fftshift(fft2(ifftshift(slm_field_bl)))
        pupil_field_bl_post = field.mask(pupil_field_bl_pre)

        obj_field = fftshift(fft2(ifftshift(pupil_field_bl_post)))
        obj_field /= obj_field.max()

        similarity = np.square(
            field2intensity(obj_field) - field2intensity(slm_field_ideal)
        ).sum()
        print(similarity)
        sims.append(similarity)

        imageio.imwrite(
            f"_debug/cf{cf:.04f}_post.tif",
            field2intensity(obj_field).astype(np.float32),
        )

    df = pd.DataFrame({"cf": cfs, "similarity": sims})
    df.to_csv("cf_similarity.csv", float_format="%.15f")


if __name__ == "__main__":
    import coloredlogs

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    annulus = (3.824, 2.689)

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(*annulus)
    nikon_10x_0p3 = Objective(10, 0.3, 200)

    field = Field(qxga, mask, nikon_10x_0p3, 0.488, 60)

    field = Lattice(3.824, 2.689, 7, 3)(field)
    # field = Bessel(*annulus)(field)

    optimize_cf_similarity(field, [0, 0.20], 0.01)
