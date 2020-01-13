import numpy as np


def field2intensity(field):
    e_field = np.real(field)
    return np.square(e_field)
