from functools import partial
import logging
import sys

from PySide2.QtWidgets import QApplication, QMainWindow

from pattern import SLM, AnnularMask, Field, Objective
from pattern.dialog import Ui_Dialog

__all__ = ["Dialog"]

logger = logging.getLogger(__name__)


class Dialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()

        self._setup_ui()

        # parts
        self._slm, self._mask, self._objective = None, None, None
        # system
        self._field = None

    ##

    ##

    def regenerate(self):
        # complete update, disable
        self.ui.regenerate.setEnabled(False)

    ##

    def _setup_ui(self):
        # generate layout from the ui file
        self.ui.setupUi(self)

        # populate screen size options
        for size in ("QXGA", "SXGA"):
            self.ui.screensize_combobox.addItem(size)

        # enable regenerate at the beginning
        self.ui.regenerate.clicked.connect(self.regenerate)

        # connect generator signals
        # .. slm
        self.ui.screensize_combobox.currentIndexChanged.connect(self._update_slm)
        self.ui.screensize_combobox.currentIndexChanged.connect(
            self._requires_regenerate
        )
        self.ui.pixel_size_spinbox.valueChanged.connect(self._update_slm)
        self.ui.pixel_size_spinbox.valueChanged.connect(self._requires_regenerate)
        self.ui.focal_length_spinbox.valueChanged.connect(self._update_slm)
        self.ui.focal_length_spinbox.valueChanged.connect(self._requires_regenerate)

        # .. mask
        self.ui.mask_od_spinbox.valueChanged.connect(self._update_mask)
        self.ui.mask_od_spinbox.valueChanged.connect(self._requires_regenerate)
        self.ui.mask_id_spinbox.valueChanged.connect(self._update_mask)
        self.ui.mask_id_spinbox.valueChanged.connect(self._requires_regenerate)

        # .. objective
        self.ui.objective_magnification_spinbox.valueChanged.connect(
            self._update_objective
        )
        self.ui.objective_magnification_spinbox.valueChanged.connect(
            self._requires_regenerate
        )
        self.ui.objective_na_spinbox.valueChanged.connect(self._update_objective)
        self.ui.objective_na_spinbox.valueChanged.connect(self._requires_regenerate)
        self.ui.tube_lens_spinbox.valueChanged.connect(self._update_objective)
        self.ui.tube_lens_spinbox.valueChanged.connect(self._requires_regenerate)

        # .. system
        self.ui.wavelength_spinbox.valueChanged.connect(self._update_system)
        self.ui.wavelength_spinbox.valueChanged.connect(self._requires_regenerate)
        self.ui.system_magnification_spinbox.valueChanged.connect(self._update_system)
        self.ui.system_magnification_spinbox.valueChanged.connect(
            self._requires_regenerate
        )

        # connect ops signals
        # .. bessel
        self.ui.bessel_parameters.toggled.connect(self._toggle_bessel_array)
        self.ui.bessel_parameters.clicked.connect(self._requires_regenerate)
        self.ui.same_as_mask.toggled.connect(self._toggle_same_as_mask)
        # default to sync with mask
        self._toggle_same_as_mask(True)

        # .. linear bessel array
        # self.ui.linear_bessel_array_parameters.toggled.connect()
        self.ui.linear_bessel_array_parameters.clicked.connect(
            self._requires_regenerate
        )

    ##

    def _requires_regenerate(self):
        self.ui.regenerate.setEnabled(True)

    ##

    def _update_slm(self):
        size = {"QXGA": (1536, 2048), "SXGA": (1024, 1280)}[
            self.ui.screensize_combobox.currentText()
        ]
        self._slm = SLM(
            size,
            (self.ui.pixel_size_spinbox.value(),) * 2,
            self.ui.focal_length_spinbox.value(),
        )

    def _update_mask(self):
        od = self.ui.mask_od_spinbox.value()
        id_ = self.ui.mask_id_spinbox.value()
        self._mask = AnnularMask(od, id_)

        # clear na
        self.ui.mask_od_na.setText("-")
        self.ui.mask_id_na.setText("-")

    def _update_objective(self):
        mag = self.ui.objective_magnification_spinbox.value()
        na = self.ui.objective_na_spinbox.value()
        tl = self.ui.tube_lens_spinbox.value()
        objective = Objective(mag, na, tl)
        self._objective = objective

    def _update_system(self):
        wavelength = self.ui.wavelength_spinbox.value()
        mag = self.ui.system_magnification_spinbox.value()

        # attempt to initizlie uninit components
        init_funcs = {
            self._update_slm: self._slm,
            self._update_mask: self._mask,
            self._update_objective: self._objective,
        }
        for func, item in init_funcs.items():
            if item is None:
                func()

        # create field
        self._field = Field(self._slm, self._mask, self._objective, wavelength, mag)

        # update mask na
        self.ui.mask_od_na.setText(f"{self._mask.na_out:.4f}")
        self.ui.mask_id_na.setText(f"{self._mask.na_in:.4f}")
        # update bessel na
        if self.ui.same_as_mask.isChecked():
            self.ui.bessel_od_na.setText(self.ui.mask_od_na.text())
            self.ui.bessel_id_na.setText(self.ui.mask_id_na.text())

    ##

    def _toggle_bessel_array(self, toggled):
        self.ui.linear_bessel_array_parameters.setChecked(toggled)

    def _toggle_same_as_mask(self, same):
        self.ui.bessel_od_spinbox.setEnabled(not same)
        self.ui.bessel_id_spinbox.setEnabled(not same)

        if same:
            self.ui.mask_od_spinbox.valueChanged.connect(self._sync_bessel_od_with_mask)
            self.ui.mask_id_spinbox.valueChanged.connect(self._sync_bessel_id_with_mask)

            # trigger it
            self._sync_bessel_od_with_mask()
            self._sync_bessel_id_with_mask()
        else:
            self.ui.mask_od_spinbox.valueChanged.disconnect(
                self._sync_bessel_od_with_mask
            )
            self.ui.mask_id_spinbox.valueChanged.disconnect(
                self._sync_bessel_id_with_mask
            )

    def _sync_bessel_od_with_mask(self):
        self.ui.bessel_od_spinbox.setValue(self.ui.mask_od_spinbox.value())
        self.ui.bessel_od_na.setText(self.ui.mask_od_na.text())

    def _sync_bessel_id_with_mask(self):
        self.ui.bessel_id_spinbox.setValue(self.ui.mask_id_spinbox.value())
        self.ui.bessel_id_na.setText(self.ui.mask_id_na.text())


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
