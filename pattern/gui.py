from functools import partial
import logging
import sys

import pyqtgraph as pq
from PySide2.QtWidgets import QApplication, QMainWindow

from pattern import SLM, AnnularMask, Field, Objective
from pattern.dialog import Ui_Dialog

__all__ = ["Dialog"]

logger = logging.getLogger(__name__)


def connect_signals_to_callbacks(signals, callbacks):
    for signal in signals:
        for callback in callbacks:
            signal.connect(callback)


class Dialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()

        self.setup_ui()

    ##

    ##

    def regenerate(self):
        wavelength = self.ui.wavelength_spinbox.value()
        mag = self.ui.system_magnification_spinbox.value()

        print(dir(self))
        # attempt to initizlie uninit components
        init_funcs = {
            "slm": self._update_slm,
            "mask": self._update_mask,
            "objective": self._update_objective,
        }
        for name, func in init_funcs.items():
            if not hasattr(self, f"_{name}"):
                logger.debug(f'implicit update "{name}"')
                func()

        # create field
        field = Field(self._slm, self._mask, self._objective, wavelength, mag)

        from pattern import Bessel

        print(field.data)
        field = Bessel(3.824, 2.689)(field)
        print(field.data)
        results = field.simulate()

        image = pq.ImageItem(results["ideal"])
        self.ui.ideal.addItem(image)

        # complete update, disable
        self.ui.regenerate.setEnabled(False)

    ##

    def setup_ui(self):
        # generate layout from the ui file
        self.ui.setupUi(self)

        self._setup_slm_parameters()
        self._setup_mask_parameters()
        self._setup_objective_parameters()
        self._setup_system_parameters()

        self._setup_binarize_parameters()

        self._setup_bessel_parameters()
        self._setup_linear_bessel_parameters()
        self._setup_tiling_parameters()

        self.ui.regenerate.clicked.connect(self.regenerate)

    def _setup_slm_parameters(self):
        # populate screen size options
        for size in ("QXGA", "SXGA"):
            self.ui.screensize_combobox.addItem(size)

        signals = [
            self.ui.screensize_combobox.currentIndexChanged,
            self.ui.pixel_size_spinbox.valueChanged,
            self.ui.focal_length_spinbox.valueChanged,
        ]
        callbacks = [self._update_slm, self._requires_regenerate]
        connect_signals_to_callbacks(signals, callbacks)

    def _setup_mask_parameters(self):
        signals = [
            self.ui.mask_od_spinbox.valueChanged,
            self.ui.mask_id_spinbox.valueChanged,
        ]
        callbacks = [self._update_mask, self._requires_regenerate]
        connect_signals_to_callbacks(signals, callbacks)

    def _setup_objective_parameters(self):
        signals = [
            self.ui.objective_magnification_spinbox.valueChanged,
            self.ui.objective_na_spinbox.valueChanged,
            self.ui.tube_lens_spinbox.valueChanged,
        ]
        callbacks = [self._update_objective, self._requires_regenerate]
        connect_signals_to_callbacks(signals, callbacks)

    def _setup_system_parameters(self):
        signals = [
            self.ui.wavelength_spinbox.valueChanged,
            self.ui.system_magnification_spinbox.valueChanged,
            self.ui.dither_steps_spinbox.valueChanged,
            self.ui.dither_interval_spinbox.valueChanged,
        ]
        callbacks = [self._update_system, self._requires_regenerate]
        connect_signals_to_callbacks(signals, callbacks)

        self.ui.dither_steps_spinbox.valueChanged.connect(self._toggle_dithering)

    def _setup_binarize_parameters(self):
        pass

    def _setup_bessel_parameters(self):
        pass

    def _setup_linear_bessel_parameters(self):
        self.ui.bessel_parameters.toggled.connect(self._toggle_bessel_array)
        self.ui.same_as_mask.toggled.connect(self._toggle_same_as_mask)

        self.ui.fill_screen_checkbox.toggled.connect(self._toggle_fill_screen)
        self.ui.auto_spacing.toggled.connect(self._toggle_auto_spacing)

    def _setup_tiling_parameters(self):
        pass

    ##

    def _requires_regenerate(self):
        self.ui.regenerate.setEnabled(True)

    ##

    def _update_slm(self):
        logger.debug("updating slm")

        size = {"QXGA": (1536, 2048), "SXGA": (1024, 1280)}[
            self.ui.screensize_combobox.currentText()
        ]
        self._slm = SLM(
            size,
            (self.ui.pixel_size_spinbox.value(),) * 2,
            self.ui.focal_length_spinbox.value(),
        )

    def _update_mask(self):
        logger.debug("updating mask")

        # clear na
        self.ui.mask_od_na.setText("-")
        self.ui.mask_id_na.setText("-")

        d_out = self.ui.mask_od_spinbox.value()
        d_in = self.ui.mask_id_spinbox.value()
        self._mask = AnnularMask(d_out, d_in)

    def _update_objective(self):
        logger.debug("updating objective")

        mag = self.ui.objective_magnification_spinbox.value()
        na = self.ui.objective_na_spinbox.value()
        tl = self.ui.tube_lens_spinbox.value()
        self._objective = Objective(mag, na, tl)

    def _update_system(self):
        pass

    ##

    def _toggle_dithering(self, n_steps):
        self.ui.dither_interval_spinbox.setEnabled(n_steps > 1)

    def _toggle_bessel_array(self, active):
        if not active:
            self.ui.linear_bessel_array_parameters.setChecked(False)

    def _toggle_same_as_mask(self, active):
        self.ui.bessel_od_spinbox.setEnabled(not active)
        self.ui.bessel_id_spinbox.setEnabled(not active)

    def _toggle_fill_screen(self, active):
        self.ui.fill_screen_spinbox.setEnabled(active)

    def _toggle_auto_spacing(self, active):
        self.ui.spacing_spinbox.setEnabled(not active)


if __name__ == "__main__":
    import coloredlogs

    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    coloredlogs.install(
        level="DEBUG", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    app = QApplication(sys.argv)

    window = Dialog()
    window.show()

    sys.exit(app.exec_())
