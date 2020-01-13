import logging

from pattern import SLM, AnnularMask, Bessel, Defocus, Field, Objective

if __name__ == "__main__":
    import coloredlogs

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(2.39, 1.345)
    nikon_10x_0p3 = Objective(10, 0.3, 200)
    # so_0p65 = Objective(1, 0.65, 7.14)

    field = Field(qxga, mask, so_0p65, 0.488, 60)
    # field = Lattice(3.824, 2.689, 7, 3)(field)
    field = Bessel(3.824, 2.689)(field)
    field = Defocus((0, 30))(field)

    pattern = field.slm_pattern(cf=0.05)

    field.simulate()
