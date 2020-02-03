import logging

from pattern import SLM, AnnularMask, Bessel, Defocus, Field, Lattice, Objective
from pattern.utils import write_pattern_bmp

if __name__ == "__main__":
    import coloredlogs
    import imageio
    import numpy as np
    import pyqtgraph as pg

    pg.setConfigOptions(imageAxisOrder="row-major")

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(3.824, 2.689)
    # nikon_10x_0p3 = Objective(10, 0.3, 200)
    nikon_10x_0p25 = Objective(10, 0.25, 200)
    # so_0p65 = Objective(1, 0.65, 7.14)

    field = Field(qxga, mask, nikon_10x_0p25, 0.488, 60)
    field = Lattice(3.54025, 2.97275, 43, 3)(field)
    # field = Bessel(3.54025, 2.97275)(field)
    # field = Defocus(50)(field)

    slm_pattern = field.slm_pattern(cf=0.15, crop=True)
    pg.image(slm_pattern.astype(np.uint8))

    # field.simulate(cf=0.05, zrange=(-200, 200), zstep=10)
    # preview_simulation(results)

    write_pattern_bmp("pattern.bmp", slm_pattern)

