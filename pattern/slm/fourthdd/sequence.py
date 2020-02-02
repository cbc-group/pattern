import logging

__all__ = ["Sequence"]

logger = logging.getLogger(__name__)


class Sequence(object):
    def __init__(self, path):
        self._path = path

        self._parse_metadata()

    ##

    @property
    def path(self):
        return self._path

    ##

    def _parse_metadata(self):
        pass
