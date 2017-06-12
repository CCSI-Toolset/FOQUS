# noise_dlg.py
import copy
import sys
from PySide.QtGui import *
from foqus_lib.framework.drmbuilder.dabnet_input import DABNetInput
from noise_dlg_ui import Ui_noiseDlg
from ccsi_double_validator import CCSIDoubleValidator


class NoiseDlg(QDialog, Ui_noiseDlg):
    """
        The Dialog class for process and measurement noise specification
    """

    def __init__(self, dat_init, parent=None):
        super(NoiseDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.lineEdit_StdState.setText(str(self.dat['fq_state']))
        self.num_of_outputs = len(self.dat['fr_output'])
        icount = 0
        for item in self.dat['output_list']:
            icount += 1
            self.listWidget_Output.addItem("{0:d}. {1}".format(icount, item.key_sinter))
        self.lineEdit_StdOutput.setText(str(self.dat['fr_output'][0]))
        self.listWidget_Output.setCurrentRow(0)
        self.lineEdit_NumberOfOutputs.setText(str(self.num_of_outputs))
        #validator
        self.validator_StdState = CCSIDoubleValidator(1e-10, 0.5, self.label_StdState.text())
        self.validator_StdOutput = CCSIDoubleValidator(1e-10, 0.5, self.label_StdOutput.text())
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.listWidget_Output.currentItemChanged.connect(self.on_list_item_changed)
        self.lineEdit_StdState.editingFinished.connect(self.on_edit_fq_state_changed)
        self.lineEdit_StdOutput.editingFinished.connect(self.on_edit_fr_output_changed)


    def on_list_item_changed(self):
        index = self.listWidget_Output.currentRow()
        self.lineEdit_StdOutput.setText(str(self.dat['fr_output'][index]))

    def on_edit_fq_state_changed(self):
        txt = self.lineEdit_StdState.text()
        if self.validator_StdState.validate(txt) is False:
            self.lineEdit_StdState.selectAll()
            self.lineEdit_StdState.setFocus()
        else:
            self.dat['fq_state'] = float(txt)

    def on_edit_fr_output_changed(self):
        txt = self.lineEdit_StdOutput.text()
        if self.validator_StdOutput.validate(txt) is False:
            self.lineEdit_StdOutput.selectAll()
            self.lineEdit_StdOutput.setFocus()
        else:
            index = self.listWidget_Output.currentRow()
            self.dat['fr_output'][index] = float(txt)

    def accept(self):
        if self.dat['fq_state']<1e-10 or self.dat['fq_state']>0.5:
            QMessageBox.warning(self, "Warning", "Please set the ratio of standard deviation of state variable\
             to the initial value between 1e-10 and 0.5")
            return
        for i in xrange(self.num_of_outputs):
            if self.dat['fr_output'][i]<1e-10 or self.dat['fr_output'][i]>0.5:
                QMessageBox.warning(self,"Warning", "Please set the ratio of standard deviation of output variable\
                 {0} to the initial value between 1e-10 and 0.5".format(i+1))
                return
        else:
            QDialog.accept(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dabnet_input = DABNetInput()
    dat = dict()
    dat['fq_state'] = dabnet_input.fq_state
    dat['fr_output'] = [0.01, 0.1, 0.03, 0.6]
    form = NoiseDlg(dat)
    result = form.exec_()
    print result
    if result:
        print dat["fr_output"]
        print form.dat["fr_output"]
    app.exec_()
