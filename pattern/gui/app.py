import logging
import sys

from PySide2.QtWidgets import QApplication

from .view import Dialog

logger = logging.getLogger(__name__)


class App(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dialog = Dialog()

        self.dialog.show()


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
