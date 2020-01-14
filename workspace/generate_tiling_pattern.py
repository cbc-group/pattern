import logging

from pattern import SLM, AnnularMask, Bessel, Defocus, Field, Lattice, Objective
from pattern.utils import preview_simulation

if __name__ == "__main__":
    import coloredlogs

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(3.824, 2.689)
    nikon_10x_0p3 = Objective(10, 0.3, 200)
    # so_0p65 = Objective(1, 0.65, 7.14)

    field = Field(qxga, mask, nikon_10x_0p3, 0.488, 60)
    field = Lattice(3.824, 2.689, 1, 3)(field)
    # field = Bessel(3.824, 2.689)(field)
    field = Defocus(80)(field)

    field.simulate(cf=0.05, zrange=(0, 200), zstep=5)
    # preview_simulation(results)
