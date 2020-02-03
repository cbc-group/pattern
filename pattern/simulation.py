import logging

from .field import Field

__all__ = ["Simulation"]

logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, field: Field):
        self._field = field

    ##

    @property
    def field(self):
        return self._field

    ##

    def excitation_xz(self):
        pass

    def excitation_yz(self):
        pass

    ##

    def _dither(self):
        pass
