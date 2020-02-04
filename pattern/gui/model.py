import logging

from PySide2.QtCore import QObject, Signal, Slot

__all__ = ["Model"]

logger = logging.getLogger(__name__)


class Model(QObject):
    update_mask_na = Signal()
    update_bessel_na = Signal()

    def __init__(self):
        super().__init__()

        self.slm = None
        self.mask = None
        self.objective = None
        self.field = None
