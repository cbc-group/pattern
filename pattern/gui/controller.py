import logging

from PySide2.QtWidgets import QObject

__all__ = ["Controller"]

logger = logging.getLogger(__name__)


class Controller(QObject):
    def __init__(self, model):
        super().__init__()

        self._model = model

    ##
