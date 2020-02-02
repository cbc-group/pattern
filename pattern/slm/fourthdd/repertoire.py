from enum import Enum
from io import StringIO
import logging
from zipfile import ZipFile

__all__ = ["Repertoire", "RepertoireArchive", "ActivationMethod"]

logger = logging.getLogger(__name__)


class ActivationMethod(Enum):
    Immediate = ""
    Hardware = "h"
    Software = "s"


class Frame(object):
    def __init__(self, sequence: str, image: str, wait_trigger: bool = False):
        self._sequence, self._image = sequence, image
        self._wait_trigger = wait_trigger

    ##

    @property
    def image(self):
        return self._image

    @property
    def sequence(self) -> str:
        return self._sequence

    @property
    def wait_trigger(self):
        return self._wait_trigger

    ##

    def compile(self):
        return f"{'t' if self.wait_trigger else ''}({self.sequence},{self.image})"


class FrameGroup(object):
    """
    Args:
        loop (bool): loop current frame group indefinitely
    """

    def __init__(self, sequences: dict, images: dict, loop=False):
        # lookup library
        self._sequences, self._images = sequences, images

        self._loop = False

        self._frames = []

    ##

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, loop):
        self._loop = loop

    ##

    def add_frame(self, sequence: str, image: str, wait_trigger=False):
        """
        Args:
            sequence (str): path to the sequence definition
            image (str): path to the image
        """
        self._frames.append(Frame(sequence, image, wait_trigger))

    def compile(self):
        frames = " ".join(f.compile() for f in self._frames)
        return f"{{{frames}}}" if self.loop else f"<{frames}>"


class RunningOrder(object):
    def __init__(self):
        self._fg = []

        self._activation = ActivationMethod.Immediate

    ##

    @property
    def activation(self):
        return self._activation

    @activation.setter
    def activation(self, method: ActivationMethod):
        self._activation = method

    ##

    def add_frame_group(self, fg):
        self._fg.append(fg)

    def compile(self):
        ro = StringIO()

        # header
        print(f"[HWA {self.activation}", file=ro)
        # content
        for fg in self._fg:
            print(" ", end="", file=ro)  # indent
            print(fg.compile(), file=ro)
        # footer
        print("]", file=ro)

        return ro.getvalue()


class Repertoire(object):
    def __init__(self):
        self._ro = dict()
        self._default_ro = None

    def __getitem__(self, name):
        return self._ro[name]

    def __setitem__(self, name, ro):
        if name in self._ro:
            raise ValueError(f'"{name}" already exists')
        # reconfigure ro name
        ro.name = name
        self._ro[name] = ro

    ##

    @property
    def images(self):
        # TODO collect images by iterate over ro
        pass

    @property
    def sequences(self):
        # TODO collect sequences by iterate oer sequences
        pass

    ##

    def compile(self):
        rep = StringIO()

        # sequences
        print("SEQUENCES", file=rep)
        # TODO sequences
        print("SEQUENCES_END", file=rep)

        # images
        print("IMAGES", file=rep)
        # TODO images
        print("IMAGES_END", file=rep)

        # running orders
        for name, ro in self._ro.items():
            if name == self._default_ro:
                print("DEFAULT ", end="", file=rep)
            print(f'"{name}"', file=rep)
            print(ro.compile(), file=rep)

        return rep.getvalue()

    def set_default_ro(self, ro=None):
        if ro is None:
            ro = self._ro.keys()[0]
        self._default_ro = ro


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
