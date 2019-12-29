import logging

__all__ = []

logger = logging.getLogger(__name__)


class Repertoire(object):
    def __init__(self):
        pass


class RepertoireArchive(object):
    def __init__(self, rep: Repertoire = None):
        self._rep = rep
        self._sequences, self._images = [], []

    ##

    @property
    def images(self):
        return self._images

    @property
    def repertoires(self):
        return self._rep

    @property
    def sequences(self):
        return self._sequenecs

    ##

    @staticmethod
    def load(self, path):
        pass

    @staticmethod
    def dump(self, path):
        pass
