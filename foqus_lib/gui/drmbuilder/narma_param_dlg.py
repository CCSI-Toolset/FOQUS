# narma_param_dlg.py
import copy
import sys
from PySide.QtGui import *
from narma_param_dlg_ui import Ui_narmaParamDlg
from foqus_lib.framework.drmbuilder.narma_input import NARMAInput
from ccsi_int_validator import CCSIIntValidator


class NARMAParamDlg(QDialog, Ui_narmaParamDlg):
    """
        The Dialog class for specification of NARMA model parameters
    """

    def __init__(self, dat_init, parent=None):
        super(NARMAParamDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.narma_input = self.dat['narma_input']
        self.lineEdit_NumberOfHistoryData.setText(str(self.narma_input.nhistory))
        self.lineEdit_NumberOfNeurons.setText(str(self.narma_input.nneuron_hid))
        self.lineEdit_MaxNumberOfIterations.setText(str(self.narma_input.nmax_iter_bp))
        # validators
        self.validator_NumberOfHistoryData = CCSIIntValidator(1, 4, self.label_NumberOfHistoryData.text())
        self.validator_NumberOfNeurons = CCSIIntValidator(2, 50, self.label_NumberOfNeurons.text())
        self.validator_MaxNumberOfIterations = CCSIIntValidator(100, 100000, self.label_MaxNumberOfIterations.text())
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_ResetToDefault.clicked.connect(self.on_button_reset_to_default_clicked)
        self.lineEdit_NumberOfHistoryData.editingFinished.connect(self.on_edit_number_of_history_data_changed)
        self.lineEdit_NumberOfNeurons.editingFinished.connect(self.on_edit_number_of_neurons_changed)
        self.lineEdit_MaxNumberOfIterations.editingFinished.connect(self.on_edit_max_number_of_iterations_changed)

    def on_edit_number_of_history_data_changed(self):
        txt = self.lineEdit_NumberOfHistoryData.text()
        if self.validator_NumberOfHistoryData.validate(txt) is False:
            self.lineEdit_NumberOfHistoryData.selectAll()
            self.lineEdit_NumberOfHistoryData.setFocus()
        else:
            self.narma_input.nhistory = int(txt)

    def on_edit_number_of_neurons_changed(self):
        txt = self.lineEdit_NumberOfNeurons.text()
        if self.validator_NumberOfNeurons.validate(txt) is False:
            self.lineEdit_NumberOfNeurons.selectAll()
            self.lineEdit_NumberOfNeurons.setFocus()
        else:
            self.narma_input.nneuron_hid = int(txt)

    def on_edit_max_number_of_iterations_changed(self):
        txt = self.lineEdit_MaxNumberOfIterations.text()
        if self.validator_MaxNumberOfIterations.validate(txt) is False:
            self.lineEdit_MaxNumberOfIterations.selectAll()
            self.lineEdit_MaxNumberOfIterations.setFocus()
        else:
            self.narma_input.nmax_iter_bp = int(txt)

    def on_button_reset_to_default_clicked(self):
        self.narma_input.set_to_default_values()
        self.lineEdit_NumberOfHistoryData.setText(str(self.narma_input.nhistory))
        self.lineEdit_NumberOfNeurons.setText(str(self.narma_input.nneuron_hid))
        self.lineEdit_MaxNumberOfIterations.setText(str(self.narma_input.nmax_iter_bp))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dat = dict()
    dat['narma_input'] = NARMAInput()
    form = NARMAParamDlg(dat)
    result = form.exec_()
    print result
    app.exec_()
