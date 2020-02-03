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


# TODO create sequence/image cache


class ActivationMethod(Enum):
    Immediate = ""
    Hardware = "h"
    Software = "s"


class Cache(object):
    def __init__(self, src_dir, pattern="*"):
        self._src_dir = src_dir
        self._cache, self._paths = [], []
        self._pattern = pattern

        self._index = 0

    def __getitem__(self, name):
        try:
            i = self._cache.index(name)
            return i + 1, self._paths[i]
        except ValueError:
            # search in the library
            paths = glob.glob(os.path.join(self.src_dir, self.pattern))
            paths = {os.path.splitext(os.path.basename(p))[0]: p for p in paths}
            if name in paths.keys():
                # lookup path
                path = paths[name]

                # save it
                self._cache.append(name)
                self._paths.append(path)

                return len(self._cache), path
            else:
                raise ValueError(f'"{name}" does not exist in the library')

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._cache):
            raise StopIteration
        self._index += 1
        return self._index, self._paths[self._index - 1]

    ##

    @property
    def pattern(self):
        """Library search pattern."""
        return self._pattern

    @property
    def src_dir(self):
        return self._src_dir


class Frame(object):
    sequence_cache = None
    image_cache = None

    def __init__(self, sequence: str, image: str, wait_trigger: bool = False):
        s, _ = self.sequence_cache[sequence]
        # convert sequence id to alphabets
        if s > 26:
            raise RuntimeError("cannot store more than 26 sequences")
        self._sequence = chr(ord("@") + s)

        self._image, _ = self.image_cache[image]

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
        self._frames.append(Frame(sequence, image, wait_trigger))

    def compile(self):
        frames = "".join(f"{f.compile()} " for f in self._frames)
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
    def __init__(self, sequence_lib, image_lib):
        Frame.sequence_cache = Cache(sequence_lib, "*.seq11")
        Frame.image_cache = Cache(image_lib, "*.bmp")

        self._ro = dict()
        self._default_ro = None

        self._sequences, self._images = [], []

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
    def default_ro(self):
        if self._default_ro is None:
            return next(iter(self._ro.keys()))
        else:
            return self._default_ro

    @default_ro.setter
    def default_ro(self, default_ro):
        self._default_ro = default_ro

    @property
    def images(self):
        assert self._images is not None, "repertoire not compiled yet"
        return self._images

    @property
    def sequences(self):
        assert self._sequences is not None, "repertoire not compiled yet"
        return self._sequences

    ##

    def compile(self):
        rep = StringIO()

        # sequences
        print("SEQUENCES", file=rep)
        for i, p in Frame.sequence_cache:
            i = chr(ord("@") + i)  # convert to alphabet by definition
            self._sequences.append(p)
            p = os.path.basename(p)
            print(f'{i} "{p}"', file=rep)
        print("SEQUENCES_END", file=rep)
        print(file=rep)

        # images
        print("IMAGES", file=rep)
        for i, p in Frame.image_cache:
            self._images.append(p)
            p = os.path.basename(p)
            print(f'1 "{p}"', file=rep)
        print("IMAGES_END", file=rep)
        print(file=rep)

        # running orders
        logger.debug(f'default ro "{self.default_ro}"')
        for name, ro in self._ro.items():
            if name == self.default_ro:
                print("DEFAULT ", end="", file=rep)
            print(f'"{name}"', file=rep)
            print(ro.compile(), file=rep)
            print(file=rep)

        return rep.getvalue()

    ##


class RepertoireArchive(object):
    def __init__(self, rep: Repertoire):
        self._rep = rep

    ##

    @property
    def repertoire(self):
        return self._rep

    ##

    def save(self, uri):
        with ZipFile(uri, "w") as repz:
            rep = self.repertoire.compile()
            print(">>>")
            print(rep)
            print("<<<")

            # repertoire
            logger.debug(f"generating repertoire text")
            repz.writestr("repertoire.rep", rep)

            # sequences
            logger.debug(f"packing sequences into repz")
            print(self.repertoire.sequences)
            for sequence in self.repertoire.sequences:
                repz.write(sequence, arcname=os.path.basename(sequence))

            # images
            logger.debug(f"packing images into repz")
            print(self.repertoire.images)
            for image in self.repertoire.images:
                repz.write(image, arcname=os.path.basename(image))

