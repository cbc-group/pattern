import logging

__all__ = ["Objective"]

logger = logging.getLogger(__name__)


class Objective(object):
    def __init__(self, mag, na, f_tube, ri=1.0):
        self._mag, self._na, self._f_tube = mag, na, f_tube
        self._ri = ri

    ##

    @property
    def f(self):
        """Objective focal length."""
        return self.f_tube / self.mag

    @property
    def f_tube(self):
        """Compatible tube lens focal length."""
        return self._f_tube

    @property
    def mag(self):
        """Magnification."""
        return self._mag

    @property
    def na(self):
        """Numerical aperture."""
        return self._na

    @property
    def ri(self):
        """Refractive index."""
        return self._ri
