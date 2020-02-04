import logging

from PySide2.QtWidgets import QObject, Slot

from pattern import SLM, AnnularMask, Field, Objective

__all__ = ["SLMController"]

logger = logging.getLogger(__name__)


class SLMController(QObject):
    def __init__(self, model):
        super().__init__()

        self._model = model

        self._f_slm = 500
        self._pixel_size = (8.2,) * 2
        self._shape = (1536, 2048)

    ##

    @Slot(str)
    def update_screen_shape(self, shape):
        self._shape = {"QXGA": (1536, 2048), "SXGA": (1024, 1280)}[shape]

    @Slot(float)
    def update_pixel_shape(self, p):
        self._pixel_size = (p,) * 2

    @Slot(int)
    def update_f(self, f):
        self._f_slm = f
