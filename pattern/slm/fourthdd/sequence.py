import logging

__all__ = ["Sequence"]

logger = logging.getLogger(__name__)


class Sequence(object):
    def __init__(self, path):
        self._path = path
        with open(self.path, "rb") as f:
            self._raw = f.read()
        self._parse()

    ##

    @property
    def path(self):
        return self._path

    @property
    def raw(self):
        return self._raw

    ##

    def _parse(self):
        """Walk through the raw binaries."""
        pass
