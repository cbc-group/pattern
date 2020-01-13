import logging

from pattern import SLM, AnnularMask, Bessel, Field, Objective

if __name__ == "__main__":
    import coloredlogs

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    qxga = SLM((1536, 2048), (8.2, 8.2), 500)
    mask = AnnularMask(2.39, 1.345)
    nikon_10x_0p3 = Objective(10, 0.3, 200)

    field = Field(qxga, mask, nikon_10x_0p3, 0.488, 60)

    # field = Lattice(3.824, 2.689, 7, 3)(field)
    field = Bessel(2.39, 1.345)(field)

    field.simulate()
