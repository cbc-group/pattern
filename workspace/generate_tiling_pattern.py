import logging

import coloredlogs
import numpy as np
import pyqtgraph as pg

from pattern import (
    SLM,
    AnnularMask,
    Bessel,
    Defocus,
    Field,
    Lattice,
    Objective,
    Synthesizer,
)
from pattern.utils import write_pattern_bmp

pg.setConfigOptions(imageAxisOrder="row-major")

logging.getLogger("matplotlib").setLevel(logging.ERROR)
coloredlogs.install(
    level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

if __name__ == "__main__":
    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(3.824, 2.689)
    nikon_10x_0p25 = Objective(10, 0.25, 200)

    """
    qxga = SLM((1536, 2048), (8.2, 8.2), 350)
    mask = AnnularMask(3.824, 2.689)
    so_29x_0p7 = Objective(28.6, 0.71, 70)
    """

    field = Field(qxga, nikon_10x_0p25, 0.488, 60)
    # field = Lattice(3.54025, 2.689, 7, 3)(field)
    field = Bessel(mask.d_out, mask.d_in)(field)
    field = Defocus(7)(field)

    synth = Synthesizer(field, mask)

    options = ["excitation_xy"]
    results = synth.simulate(
        options, bounded=True, crop=False, zrange=(-50, 50), zstep=2, cf=0.0
    )

    w = pg.image(results["excitation_xy"])
    w.getView().setAspectLocked(ratio=2 / (8.2 / 60))

    w = pg.image(results["excitation_xz"])
    w.getView().setAspectLocked()

    # write_pattern_bmp("pattern.bmp", slm_pattern)

    app = pg.mkQApp()
    app.instance().exec_()
