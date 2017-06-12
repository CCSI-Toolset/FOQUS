# input_variable_dlg.py
import copy
import sys
from PySide.QtGui import *
from foqus_lib.framework.drmbuilder.input_variable import InputVariable
from input_variable_dlg_ui import Ui_inputVariableDlg
from ccsi_double_validator import CCSIDoubleValidator


class InputVariableDlg(QDialog, Ui_inputVariableDlg):
    """
        The Dialog class for the specification of input variables
    """

    def __init__(self, dat_init, parent=None):
        super(InputVariableDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.lineEdit_SamplingTime.setText(str(self.dat['dt_sampling']))
        self.lineEdit_RampTime.setText(str(self.dat['dt_ramp']))
        self.lineEdit_UnitSamplingTime.setText(self.dat['unit_time'])
        self.lineEdit_UnitRampTime.setText(self.dat['unit_time'])
        self.label_SolverMinTimeStep.setText('Solver minimum time step: ' + str(self.dat['dt_min_solver']) + ' ' + self.dat['unit_time'])
        self.update_number_of_varied_inputs()
        self.lineEdit_NumberOfVariedVariables.setText(str(self.nvaried))
        icount = 0
        for item in self.dat['input_list']:
            icount += 1
            self.listWidget_InputList.addItem("{0}. {1}".format(icount, item.key_sinter))
        self.listWidget_InputList.setCurrentRow(0)
        self.lineEdit_Name.setText(self.dat['input_list'][0].name)
        self.lineEdit_Description.setText(self.dat['input_list'][0].desc)
        self.lineEdit_Unit.setText(self.dat['input_list'][0].unit)
        self.lineEdit_Default.setText(str(self.dat['input_list'][0].xdefault))
        self.lineEdit_Lower.setText(str(self.dat['input_list'][0].xlower))
        self.lineEdit_Upper.setText(str(self.dat['input_list'][0].xupper))
        self.lineEdit_RampRate.setText(str(self.dat['input_list'][0].ramp_rate))
        self.checkBox_UseRamp.setChecked(self.dat['input_list'][0].bramp)
        self.checkBox_VariesWithTime.setChecked(self.dat['input_list'][0].bvaried)
        self.lineEdit_Default.setEnabled(self.dat['input_list'][0].bvaried)
        self.lineEdit_Lower.setEnabled(self.dat['input_list'][0].bvaried)
        self.lineEdit_Upper.setEnabled(self.dat['input_list'][0].bvaried)
        self.lineEdit_RampRate.setEnabled(self.dat['input_list'][0].bvaried and self.dat['input_list'][0].bramp)
        self.checkBox_UseRamp.setEnabled(self.dat['input_list'][0].bvaried)
        # validators
        self.validator_SamplingTime = CCSIDoubleValidator(1e-10, 1000, self.label_SamplingTime.text())
        self.validator_RampTime = CCSIDoubleValidator(1e-10, 1000, self.label_RampTime.text())
        self.validator_Default = CCSIDoubleValidator(-1e20, 1e20, self.label_Default.text())
        self.validator_Lower = CCSIDoubleValidator(-1e20, 1e20, self.label_Lower.text())
        self.validator_Upper = CCSIDoubleValidator(-1e20, 1e20, self.label_Upper.text())
        self.validator_RampRate = CCSIDoubleValidator(0, 1e20, self.label_RampRate.text())
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.listWidget_InputList.currentItemChanged.connect(self.on_list_item_changed)
        self.lineEdit_SamplingTime.editingFinished.connect(self.on_edit_sampling_time_changed)
        self.lineEdit_RampTime.editingFinished.connect(self.on_edit_ramp_time_changed)
        self.lineEdit_Description.editingFinished.connect(self.on_edit_description_changed)
        self.lineEdit_Default.editingFinished.connect(self.on_edit_default_changed)
        self.lineEdit_Lower.editingFinished.connect(self.on_edit_lower_changed)
        self.lineEdit_Upper.editingFinished.connect(self.on_edit_upper_changed)
        self.lineEdit_RampRate.editingFinished.connect(self.on_edit_ramp_rate_changed)
        self.checkBox_UseRamp.clicked.connect(self.on_ramp_checked)
        self.checkBox_VariesWithTime.clicked.connect(self.on_varied_checked)
        self.pushButton_Up.clicked.connect(self.on_move_up)
        self.pushButton_Down.clicked.connect(self.on_move_down)

    def update_number_of_varied_inputs(self):
        self.nvaried = 0
        for item in self.dat['input_list']:
            if item.bvaried:
                self.nvaried += 1

    def on_list_item_changed(self):
        index = self.listWidget_InputList.currentRow()
        self.lineEdit_Name.setText(self.dat['input_list'][index].name)
        self.lineEdit_Description.setText(self.dat['input_list'][index].desc)
        self.lineEdit_Unit.setText(self.dat['input_list'][index].unit)
        self.lineEdit_Default.setText(str(self.dat['input_list'][index].xdefault))
        self.lineEdit_Lower.setText(str(self.dat['input_list'][index].xlower))
        self.lineEdit_Upper.setText(str(self.dat['input_list'][index].xupper))
        self.lineEdit_RampRate.setText(str(self.dat['input_list'][index].ramp_rate))
        self.checkBox_UseRamp.setChecked(self.dat['input_list'][index].bramp)
        self.checkBox_VariesWithTime.setChecked(self.dat['input_list'][index].bvaried)
        self.lineEdit_Default.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_Lower.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_Upper.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_RampRate.setEnabled(self.dat['input_list'][index].bvaried and self.dat['input_list'][index].bramp)
        self.checkBox_UseRamp.setEnabled(self.dat['input_list'][index].bvaried)

    def on_edit_sampling_time_changed(self):
        txt = self.lineEdit_SamplingTime.text()
        if self.validator_SamplingTime.validate(txt) is False:
            self.lineEdit_SamplingTime.selectAll()
            self.lineEdit_SamplingTime.setFocus()
        else:
            self.dat['dt_sampling'] = float(txt)
    
    def on_edit_ramp_time_changed(self):
        txt = self.lineEdit_RampTime.text()
        if self.validator_RampTime.validate(txt) is False:
            self.lineEdit_RampTime.selectAll()
            self.lineEdit_RampTime.setFocus()
        else:
            self.dat['dt_ramp'] = float(txt)

    def on_edit_description_changed(self):
        txt = self.lineEdit_Description.text()
        index = self.listWidget_InputList.currentRow()
        self.dat['input_list'][index].desc = txt

    def on_edit_default_changed(self):
        txt = self.lineEdit_Default.text()
        if self.validator_Default.validate(txt) is False:
            self.lineEdit_Default.selectAll()
            self.lineEdit_Default.setFocus()
        else:
            index = self.listWidget_InputList.currentRow()
            self.dat['input_list'][index].xdefault = float(txt)

    def on_edit_lower_changed(self):
        txt = self.lineEdit_Lower.text()
        if self.validator_Lower.validate(txt) is False:
            self.lineEdit_Lower.selectAll()
            self.lineEdit_Lower.setFocus()
        else:
            index = self.listWidget_InputList.currentRow()
            self.dat['input_list'][index].xlower = float(txt)

    def on_edit_upper_changed(self):
        txt = self.lineEdit_Upper.text()
        if self.validator_Upper.validate(txt) is False:
            self.lineEdit_Upper.selectAll()
            self.lineEdit_Upper.setFocus()
        else:
            index = self.listWidget_InputList.currentRow()
            self.dat['input_list'][index].xupper = float(txt)

    def on_edit_ramp_rate_changed(self):
        txt = self.lineEdit_RampRate.text()
        if self.validator_RampRate.validate(txt) is False:
            self.lineEdit_RampRate.selectAll()
            self.lineEdit_RampRate.setFocus()
        else:
            index = self.listWidget_InputList.currentRow()
            self.dat['input_list'][index].ramp_rate = float(txt)

    def on_ramp_checked(self):
        bramp = self.checkBox_UseRamp.isChecked()
        index = self.listWidget_InputList.currentRow()
        self.dat['input_list'][index].bramp = bramp
        self.lineEdit_RampRate.setEnabled(self.dat['input_list'][index].bvaried and self.dat['input_list'][index].bramp)

    def on_varied_checked(self):
        bvaried = self.checkBox_VariesWithTime.isChecked()
        index = self.listWidget_InputList.currentRow()
        self.dat['input_list'][index].bvaried = bvaried
        self.lineEdit_Default.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_Lower.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_Upper.setEnabled(self.dat['input_list'][index].bvaried)
        self.lineEdit_RampRate.setEnabled(self.dat['input_list'][index].bvaried and self.dat['input_list'][index].bramp)
        self.checkBox_UseRamp.setEnabled(self.dat['input_list'][index].bvaried)
        self.update_number_of_varied_inputs()
        self.lineEdit_NumberOfVariedVariables.setText(str(self.nvaried))

    def on_move_up(self):
        index = self.listWidget_InputList.currentRow()
        if index==0:
            return
        curItem = self.listWidget_InputList.currentItem()
        upItem = self.listWidget_InputList.item(index-1)
        tmp = self.dat['input_list'][index]
        self.dat['input_list'][index] = self.dat['input_list'][index-1]
        self.dat['input_list'][index-1] = tmp
        curItem.setText("{0}. {1}".format(index+1, self.dat['input_list'][index].key_sinter))
        upItem.setText("{0}. {1}".format(index, self.dat['input_list'][index-1].key_sinter))
        self.listWidget_InputList.setCurrentRow(index-1)

    def on_move_down(self):
        index = self.listWidget_InputList.currentRow()
        if index==self.listWidget_InputList.count()-1:
            return
        curItem = self.listWidget_InputList.currentItem()
        downItem = self.listWidget_InputList.item(index+1)
        tmp = self.dat['input_list'][index]
        self.dat['input_list'][index] = self.dat['input_list'][index+1]
        self.dat['input_list'][index+1] = tmp
        curItem.setText("{0}. {1}".format(index+1, self.dat['input_list'][index].key_sinter))
        downItem.setText("{0}. {1}".format(index+2, self.dat['input_list'][index+1].key_sinter))
        self.listWidget_InputList.setCurrentRow(index+1)

    def accept(self):
        if self.nvaried==0:
            QMessageBox.warning(self, "Warning", "No input variable is selected to vary with time!")
            return
        icount = 0
        for item in self.dat['input_list']:
            icount += 1
            if item.bvaried:
                if item.xlower > item.xdefault:
                    QMessageBox.warning(self, "Warning", "Lower limit of Input {0} is higher than its default!".format(icount))
                    return
                if item.xupper < item.xdefault:
                    QMessageBox.warning(self, "Warning", "Upper limit of Input {0} is lower than its default!".format(icount))
                    return
        icount = 0
        for item in self.dat['input_list']:
            icount += 1
            if item.bvaried and item.bramp:
                if (item.xupper - item.xlower)/self.dat['dt_sampling'] > item.ramp_rate*0.5:
                    QMessageBox.warning(self, "Warning", "The ramp rate of Input {0} is too low to ramp from minimum to maximum within half of the sampling time interval!!".format(icount))
                    return
        QDialog.accept(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dat = dict()
    dat['unit_time'] = "sec"
    dat['dt_sampling'] = 0.1
    dat['dt_min_solver'] = 0.001
    input_list = list()
    for i in xrange(4):
        input_list.append(InputVariable())
    dat['input_list'] = input_list
    form = InputVariableDlg(dat)
    result = form.exec_()
    print result
    if result==1:
        print form.dat['dt_sampling']
    app.exec_()
