import copy
from enum import Enum
import glob
from io import StringIO
import logging
import os
from zipfile import ZipFile

__all__ = [
    "ActivationMethod",
    "FrameGroup",
    "Repertoire",
    "RepertoireArchive",
    "RunningOrder",
]

logger = logging.getLogger(__name__)


class ActivationMethod(Enum):
    Immediate = ""
    Hardware = "h"
    Software = "s"


class FrameGroup(object):
    """
    Args:
        loop (bool): loop current frame group indefinitely
    """

    def __init__(self, loop=False):
        self._loop = loop
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
        self._frames.append(Repertoire.Frame(sequence, image, wait_trigger))

    def compile(self):
        frames = " ".join(f.compile() for f in self._frames)
        return f"{{{frames}}}" if self.loop else f"<{frames}>"


class RunningOrder(object):
    def __init__(self, activation=ActivationMethod.Immediate):
        self._fg = []

        self._activation = activation

    ##

    @property
    def activation(self):
        return self._activation

    @activation.setter
    def activation(self, method: ActivationMethod):
        self._activation = method

    ##

    def add_frame_group(self, fg: FrameGroup):
        self._fg.append(fg)

    def compile(self):
        ro = StringIO()

        # header
        print(f"[HWA {self.activation.value}", file=ro)
        # content
        for fg in self._fg:
            print(" ", end="", file=ro)  # indent
            print(fg.compile(), file=ro)
        # footer
        print("]", file=ro)

        return ro.getvalue()


class Repertoire(object):
    _sequences = dict()
    _images = dict()

    _sequence_lib = []
    _image_lib = []

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
            s = Repertoire.lookup_sequence_id(self.sequence)
            i = Repertoire.lookup_image_id(self.image)
            return f"{'t' if self.wait_trigger else ''}({s},{i})"

    def __init__(self, sequence_lib, image_lib):
        self._sequence_lib.append(sequence_lib)
        self._image_lib.append(image_lib)

        self._ro = dict()
        self._default_ro = None

    def __getitem__(self, name: str):
        return self._ro[name]

    def __setitem__(self, name: str, ro: RunningOrder):
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

    @classmethod
    def lookup_sequence_id(cls, sequence, pattern="*.seq*"):
        if sequence in cls._sequences:
            return cls._sequences[sequence][0]

        # search in the library
        paths = []
        for s in cls._sequence_lib:
            paths.extend(glob.glob(os.path.join(s, pattern)))
        paths = {os.path.splitext(os.path.basename(p))[0]: p for p in paths}
        if sequence in paths.keys():
            # lookup path
            path = paths[sequence]

            # assign id
            n = len(cls._sequences) + 1
            if n > 26:
                raise RuntimeError("cannot store more than 26 sequences")
            c = chr(ord("@") + n)

            logger.debug(f'found sequence at "{path}", assign id "{c}"')
            cls._sequences[sequence] = (c, path)
            return c
        else:
            raise ValueError(f'sequence "{sequence}" does not exist in the library')

    @classmethod
    def lookup_image_id(cls, image, pattern="*.bmp"):
        if image in cls._images:
            return cls._images[image][0]

        # search in the library
        paths = []
        for s in cls._image_lib:
            paths.extend(glob.glob(os.path.join(s, pattern)))
        paths = {os.path.splitext(os.path.basename(p))[0]: p for p in paths}
        if image in paths.keys():
            # lookup path
            path = paths[image]

            # assign id
            n = len(cls._images) + 1

            logger.debug(f'found image at "{path}", assign id "{n}"')
            cls._images[image] = (n, path)
            return n
        else:
            raise ValueError(f'image "{image}" does not exist in the library')

    ##

    def compile(self):
        rep = StringIO()

        # sequences
        print("SEQUENCES", file=rep)
        sequences = [(i, p) for i, p in self._sequences.items()]
        print(self._sequences)
        print(self._images)
        sequences.sort(key=lambda x: x[0])
        for i, p in sequences:
            print(f'{i} "{p}"', file=rep)
        print("SEQUENCES_END", file=rep)
        print(file=rep)

        # images
        print("IMAGES", file=rep)
        images = [(i, p) for i, p in self._images.items()]
        images.sort(key=lambda x: x[0])
        for i, p in images:
            print(f'{i} "{p}"', file=rep)
        print("IMAGES_END", file=rep)
        print(file=rep)

        # running orders
        for name, ro in self._ro.items():
            if name == self._default_ro:
                print("DEFAULT ", end="", file=rep)
            print(f'"{name}"', file=rep)
            print(ro.compile(), file=rep)
            print()

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


if __name__ == "__main__":
    images = ""
    start_fg = FrameGroup(loop=False)
    start_fg.add_frame("48071 HHMI 50ms")

