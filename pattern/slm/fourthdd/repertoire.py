import logging
from zipfile import ZipFile

__all__ = ["Repertoire", "RepertoireArchive"]

logger = logging.getLogger(__name__)


class Repertoire(object):
    def __init__(self, filename=None):
        if filename:
            # TODO parse the file
            pass
        self._sequences = []
        self._images = []
        self._running_orders = []

    ##
    @property
    def images(self):
        return self._images

    @property
    def running_orders(self):
        return self._running_orders

    @property
    def sequences(self):
        return self._sequences

    ##

    def add_image(self, image):
        self._images.append(image)


class RepertoireArchive(object):
    def __init__(self, rep=None):
        self._repertoire = rep if isinstance(rep, Repertoire) else Repertoire(rep)

    ##

    @property
    def repertoire(self):
        return self._repertoire

    ##

    @staticmethod
    def dump(self, uri, repz):
        with ZipFile(uri, "w") as repz:
            # TODO all files point to files instead of abstracted info, fix that

            # write repertoire first
            repz.write(self.repertoire.filename)

            # write sequences and images
            for f in (self.sequences, self.images):
                repz.write(f)

    @staticmethod
    def load(self, uri):
        pass
