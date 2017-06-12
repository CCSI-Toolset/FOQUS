# dabnet_param_dlg.py
import copy
import sys
from PySide.QtGui import *
from foqus_lib.framework.drmbuilder.dabnet_input import DABNetInput
from foqus_lib.framework.drmbuilder.input_variable import InputVariable
from foqus_lib.framework.drmbuilder.output_variable import OutputVariable
from ccsi_double_validator import CCSIDoubleValidator
from ccsi_int_validator import CCSIIntValidator
from dabnet_param_dlg_ui import Ui_dabnetParamDlg


class DABNetParamDlg(QDialog, Ui_dabnetParamDlg):
    """
        The Dialog class for the specification of DABNet model parameters
    """

    def __init__(self, dat_init, parent=None):
        super(DABNetParamDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.dabnet_input = self.dat['dabnet_input']
        icount = 0
        for item in self.dat['output_list']:
            icount += 1
            self.listWidget_OutputList.addItem("{0}. {1}".format(icount, item.key_sinter))
        self.listWidget_OutputList.setCurrentRow(0)
        icount = 0
        for item in self.dat['input_list']:
            icount += 1
            self.listWidget_InputList.addItem("{0}. {1}".format(icount, item.key_sinter))
        self.listWidget_InputList.setCurrentRow(0)
        if self.dabnet_input.ilinear_ann[0]==1:
            self.checkBox_LinearModel.setChecked(True)
            self.dabnet_input.nneuron_hid[0] = 1
            self.lineEdit_NumberOfNeurons.setText(str(1))
            self.lineEdit_NumberOfNeurons.setEnabled(False)
        else:
            self.checkBox_LinearModel.setChecked(False)
        self.lineEdit_NumberOfNeurons.setText(str(self.dabnet_input.nneuron_hid[0]))
        if self.dabnet_input.ipole_opt[0]==0:
            self.radioButton_UseSpecifiedPoleValue.setChecked(True)
        elif self.dabnet_input.ipole_opt[0]==1:
            self.radioButton_OptimizeBothPoles.setChecked(True)
        elif self.dabnet_input.ipole_opt[0]==2:
            self.radioButton_OptimizeFastPole.setChecked(True)
        else:
            self.radioButton_OptimizeSlowPole.setChecked(True)
        self.lineEdit_NumberOfDelays.setText(str(self.dabnet_input.ndelay_list[0][0]))
        self.lineEdit_NumberOfLaguerreStates.setText(str(self.dabnet_input.norder_list[0][0]))
        self.lineEdit_NumberOfLaguerreStates2.setText(str(self.dabnet_input.norder2_list[0][0]))
        self.lineEdit_EstimatedPoleValue.setText(str(self.dabnet_input.pole_list[0][0]))
        self.lineEdit_EstimatedPoleValue2.setText(str(self.dabnet_input.pole2_list[0][0]))
        if self.dabnet_input.ipole2_list[0][0]==1:
            self.checkBox_Use2Poles.setChecked(True)
        else:
            self.checkBox_Use2Poles.setChecked(False)
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(False)
            self.lineEdit_EstimatedPoleValue2.setEnabled(False)
        if self.dabnet_input.itrain_lag_opt==0:
            self.radioButton_LaguerreBP.setChecked(True)
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_lag))
        else:
            self.radioButton_LaguerreIPOPT.setChecked(True)
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_lag))
        if self.dabnet_input.itrain_red_opt==0:
            self.radioButton_BalancedBP.setChecked(True)
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_red))
        else:
            self.radioButton_BalancedIPOPT.setChecked(True)
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_red))
        self.lineEdit_InitialWeight.setText(str(self.dabnet_input.weight_init))
        # validators
        self.validator_NumberOfNeurons = CCSIIntValidator(1, 50, self.label_NumberOfNeurons.text())
        self.validator_NumberOfDelays = CCSIIntValidator(0, 10, self.label_NumberOfDelays.text())
        self.validator_NumberOfLaguerreStates = CCSIIntValidator(2, 20, self.label_NumberOfLaguerreStates.text())
        self.validator_NumberOfLaguerreStates2 = CCSIIntValidator(2, 20, self.label_NumberOfLaguerreStates2.text())
        self.validator_EstimatedPoleValue = CCSIDoubleValidator(0.001, 0.9999, self.label_EstimatedPoleValue.text())
        self.validator_EstimatedPoleValue2 = CCSIDoubleValidator(0.001, 0.9999, self.label_EstimatedPoleValue2.text())
        self.validator_LaguerreMaxIterations = CCSIIntValidator(100, 100000, self.label_LaguerreMaxIterations.text())
        self.validator_BalancedMaxIterations = CCSIIntValidator(100, 100000, self.label_BalancedMaxIterations.text())
        self.validator_InitialWeight = CCSIDoubleValidator(0.0001, 0.1, self.label_InitialWeight.text())
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.listWidget_OutputList.currentItemChanged.connect(self.on_output_list_item_changed)
        self.listWidget_InputList.currentItemChanged.connect(self.on_input_list_item_changed)
        self.checkBox_LinearModel.stateChanged.connect(self.on_checkbox_linearmodel_changed)
        self.lineEdit_NumberOfNeurons.editingFinished.connect(self.on_edit_number_of_neurons_changed)
        self.radioButton_UseSpecifiedPoleValue.clicked.connect(self.on_radio_use_specified_pole_value_clicked)
        self.radioButton_OptimizeBothPoles.clicked.connect(self.on_radio_optimize_both_poles_clicked)
        self.radioButton_OptimizeFastPole.clicked.connect(self.on_radio_optimize_fast_pole_clicked)
        self.radioButton_OptimizeSlowPole.clicked.connect(self.on_radio_optimize_slow_pole_clicked)
        self.checkBox_Use2Poles.stateChanged.connect(self.on_checkbox_use_two_poles)
        self.lineEdit_NumberOfDelays.editingFinished.connect(self.on_edit_number_of_delays_changed)
        self.lineEdit_NumberOfLaguerreStates.editingFinished.connect(self.on_edit_number_of_laguerre_states_changed)
        self.lineEdit_NumberOfLaguerreStates2.editingFinished.connect(self.on_edit_number_of_laguerre_states2_changed)
        self.lineEdit_EstimatedPoleValue.editingFinished.connect(self.on_edit_estimated_pole_value_changed)
        self.lineEdit_EstimatedPoleValue2.editingFinished.connect(self.on_edit_estimated_pole_value2_changed)
        self.radioButton_LaguerreBP.clicked.connect(self.on_radio_laguerre_bp_clicked)
        self.radioButton_LaguerreIPOPT.clicked.connect(self.on_radio_laguerre_ipopt_clicked)
        self.lineEdit_LaguerreMaxIterations.editingFinished.connect(self.on_edit_laguerre_max_iterations_changed)
        self.radioButton_BalancedBP.clicked.connect(self.on_radio_balanced_bp_clicked)
        self.radioButton_BalancedIPOPT.clicked.connect(self.on_radio_balanced_ipopt_clicked)
        self.lineEdit_BalancedMaxIterations.editingFinished.connect(self.on_edit_balanced_max_iterations_changed)
        self.lineEdit_InitialWeight.editingFinished.connect(self.on_edit_intial_weight_changed)
        self.pushButton_ResetToDefault.clicked.connect(self.on_button_reset_to_default_clicked)

    def on_output_list_item_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.dabnet_input.ipole_opt[index_output]==0:
            self.radioButton_UseSpecifiedPoleValue.setChecked(True)
        else:
            self.radioButton_OptimizeBothPoles.setChecked(True)
        if self.dabnet_input.ilinear_ann[index_output]==1:
            self.checkBox_LinearModel.setChecked(True)
            self.lineEdit_NumberOfNeurons.setText(str(1))
            self.dabnet_input.nneuron_hid[index_output] = 1
            self.lineEdit_NumberOfNeurons.setEnabled(False)
        else:
            self.checkBox_LinearModel.setChecked(False)
            self.lineEdit_NumberOfNeurons.setText(str(self.dabnet_input.nneuron_hid[index_output]))
            self.lineEdit_NumberOfNeurons.setEnabled(True)
        self.listWidget_InputList.setCurrentRow(0)
        if self.dabnet_input.ipole2_list[index_output][0]==1:
            self.checkBox_Use2Poles.setChecked(True)
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(True)
            self.lineEdit_EstimatedPoleValue2.setEnabled(True)
        else:
            self.checkBox_Use2Poles.setChecked(False)
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(False)
            self.lineEdit_EstimatedPoleValue2.setEnabled(False)
        self.lineEdit_NumberOfDelays.setText(str(self.dabnet_input.ndelay_list[index_output][0]))
        self.lineEdit_NumberOfLaguerreStates.setText(str(self.dabnet_input.norder_list[index_output][0]))
        self.lineEdit_NumberOfLaguerreStates2.setText(str(self.dabnet_input.norder2_list[index_output][0]))
        self.lineEdit_EstimatedPoleValue.setText(str(self.dabnet_input.pole_list[index_output][0]))
        self.lineEdit_EstimatedPoleValue2.setText(str(self.dabnet_input.pole2_list[index_output][0]))

    def on_input_list_item_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        if self.dabnet_input.ipole2_list[index_output][index_input]==1:
            self.checkBox_Use2Poles.setChecked(True)
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(True)
            self.lineEdit_EstimatedPoleValue2.setEnabled(True)
        else:
            self.checkBox_Use2Poles.setChecked(False)
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(False)
            self.lineEdit_EstimatedPoleValue2.setEnabled(False)
        self.lineEdit_NumberOfDelays.setText(str(self.dabnet_input.ndelay_list[index_output][index_input]))
        self.lineEdit_NumberOfLaguerreStates.setText(str(self.dabnet_input.norder_list[index_output][index_input]))
        self.lineEdit_NumberOfLaguerreStates2.setText(str(self.dabnet_input.norder2_list[index_output][index_input]))
        self.lineEdit_EstimatedPoleValue.setText(str(self.dabnet_input.pole_list[index_output][index_input]))
        self.lineEdit_EstimatedPoleValue2.setText(str(self.dabnet_input.pole2_list[index_output][index_input]))

    def on_checkbox_linearmodel_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.checkBox_LinearModel.isChecked():
            self.dabnet_input.nneuron_hid[index_output] = 1
            self.lineEdit_NumberOfNeurons.setText(str(1))
            self.dabnet_input.ilinear_ann[index_output] = 1
            self.lineEdit_NumberOfNeurons.setEnabled(False)
        else:
            self.dabnet_input.ilinear_ann[index_output] = 0
            self.lineEdit_NumberOfNeurons.setEnabled(True)
    
    def on_edit_number_of_neurons_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        txt = self.lineEdit_NumberOfNeurons.text()
        if self.validator_NumberOfNeurons.validate(txt) is False:
            self.lineEdit_NumberOfNeurons.selectAll()
            self.lineEdit_NumberOfNeurons.setFocus()
        else:
            self.dabnet_input.nneuron_hid[index_output] = int(txt)

    def on_radio_use_specified_pole_value_clicked(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.radioButton_UseSpecifiedPoleValue.isChecked():
            self.dabnet_input.ipole_opt[index_output] = 0

    def on_radio_optimize_both_poles_clicked(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.radioButton_OptimizeBothPoles.isChecked():
            self.dabnet_input.ipole_opt[index_output] = 1

    def on_radio_optimize_both_poles_clicked(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.radioButton_OptimizeBothPoles.isChecked():
            self.dabnet_input.ipole_opt[index_output] = 1

    def on_radio_optimize_fast_pole_clicked(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.radioButton_OptimizeFastPole.isChecked():
            self.dabnet_input.ipole_opt[index_output] = 2

    def on_radio_optimize_slow_pole_clicked(self):
        index_output = self.listWidget_OutputList.currentRow()
        if self.radioButton_OptimizeSlowPole.isChecked():
            self.dabnet_input.ipole_opt[index_output] = 3

    def on_checkbox_use_two_poles(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        if self.checkBox_Use2Poles.isChecked():
            self.dabnet_input.ipole2_list[index_output][index_input] = 1
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(True)
            self.lineEdit_EstimatedPoleValue2.setEnabled(True)
        else:
            self.dabnet_input.ipole2_list[index_output][index_input] = 0
            self.lineEdit_NumberOfLaguerreStates2.setEnabled(False)
            self.lineEdit_EstimatedPoleValue2.setEnabled(False)

    def on_edit_number_of_delays_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        txt = self.lineEdit_NumberOfDelays.text()
        if self.validator_NumberOfDelays.validate(txt) is False:
            self.lineEdit_NumberOfDelays.selectAll()
            self.lineEdit_NumberOfDelays.setFocus()
        else:
            self.dabnet_input.ndelay_list[index_output][index_input] = int(txt)

    def on_edit_number_of_laguerre_states_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        txt = self.lineEdit_NumberOfLaguerreStates.text()
        if self.validator_NumberOfLaguerreStates.validate(txt) is False:
            self.lineEdit_NumberOfLaguerreStates.selectAll()
            self.lineEdit_NumberOfLaguerreStates.setFocus()
        else:
            self.dabnet_input.norder_list[index_output][index_input] = int(txt)

    def on_edit_number_of_laguerre_states2_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        txt = self.lineEdit_NumberOfLaguerreStates2.text()
        if self.validator_NumberOfLaguerreStates2.validate(txt) is False:
            self.lineEdit_NumberOfLaguerreStates2.selectAll()
            self.lineEdit_NumberOfLaguerreStates2.setFocus()
        else:
            self.dabnet_input.norder2_list[index_output][index_input] = int(txt)

    def on_edit_estimated_pole_value_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        txt = self.lineEdit_EstimatedPoleValue.text()
        if self.validator_EstimatedPoleValue.validate(txt) is False:
            self.lineEdit_EstimatedPoleValue.selectAll()
            self.lineEdit_EstimatedPoleValue.setFocus()
        else:
            self.dabnet_input.pole_list[index_output][index_input] = float(txt)

    def on_edit_estimated_pole_value2_changed(self):
        index_output = self.listWidget_OutputList.currentRow()
        index_input = self.listWidget_InputList.currentRow()
        txt = self.lineEdit_EstimatedPoleValue2.text()
        if self.validator_EstimatedPoleValue2.validate(txt) is False:
            self.lineEdit_EstimatedPoleValue2.selectAll()
            self.lineEdit_EstimatedPoleValue2.setFocus()
        else:
            self.dabnet_input.pole2_list[index_output][index_input] = float(txt)

    def on_radio_laguerre_bp_clicked(self):
        if self.radioButton_LaguerreBP.isChecked():
            self.dabnet_input.itrain_lag_opt = 0
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_lag))

    def on_radio_laguerre_ipopt_clicked(self):
        if self.radioButton_LaguerreIPOPT.isChecked():
            self.dabnet_input.itrain_lag_opt = 1
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_lag))

    def on_edit_laguerre_max_iterations_changed(self):
        txt = self.lineEdit_LaguerreMaxIterations.text()
        if self.validator_LaguerreMaxIterations.validate(txt) is False:
            self.lineEdit_LaguerreMaxIterations.selectAll()
            self.lineEdit_LaguerreMaxIterations.setFocus()
        else:
            if self.dabnet_input.itrain_lag_opt==0:
                self.dabnet_input.nmax_iter_bp_lag = int(txt)
            else:
                self.dabnet_input.nmax_iter_ipopt_lag = int(txt)

    def on_radio_balanced_bp_clicked(self):
        if self.radioButton_BalancedBP.isChecked():
            self.dabnet_input.itrain_red_opt = 0
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_red))

    def on_radio_balanced_ipopt_clicked(self):
        if self.radioButton_BalancedIPOPT.isChecked():
            self.dabnet_input.itrain_red_opt = 1
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_red))

    def on_edit_balanced_max_iterations_changed(self):
        txt = self.lineEdit_BalancedMaxIterations.text()
        if self.validator_BalancedMaxIterations.validate(txt) is False:
            self.lineEdit_BalancedMaxIterations.selectAll()
            self.lineEdit_BalancedMaxIterations.setFocus()
        else:
            if self.dabnet_input.itrain_red_opt==0:
                self.dabnet_input.nmax_iter_bp_red = int(txt)
            else:
                self.dabnet_input.nmax_iter_ipopt_red = int(txt)

    def on_edit_intial_weight_changed(self):
        txt = self.lineEdit_InitialWeight.text()
        if self.validator_InitialWeight.validate(txt) is False:
            self.lineEdit_InitialWeight.selectAll()
            self.lineEdit_InitialWeight.setFocus()
        else:
            self.dabnet_input.weight_init = float(txt)

    def on_button_reset_to_default_clicked(self):
        self.dabnet_input.set_to_default_values()
        self.listWidget_OutputList.setCurrentRow(0)
        self.listWidget_InputList.setCurrentRow(0)
        self.lineEdit_NumberOfNeurons.setText(str(self.dabnet_input.nneuron_hid[0]))
        if self.dabnet_input.ipole_opt[0]==0:
            self.radioButton_UseSpecifiedPoleValue.setChecked(True)
        elif self.dabnet_input.ipole_opt[0]==1:
            self.radioButton_OptimizeBothPoles.setChecked(True)
        elif self.dabnet_input.ipole_opt[0]==2:
            self.radioButton_OptimizeFastPole.setChecked(True)
        else:
            self.radioButton_OptimizeSlowPole.setChecked(True)
        self.lineEdit_NumberOfLaguerreStates.setText(str(self.dabnet_input.norder_list[0][0]))
        self.lineEdit_NumberOfLaguerreStates2.setText(str(self.dabnet_input.norder2_list[0][0]))
        self.lineEdit_EstimatedPoleValue.setText(str(self.dabnet_input.pole_list[0][0]))
        self.lineEdit_EstimatedPoleValue2.setText(str(self.dabnet_input.pole2_list[0][0]))
        if self.dabnet_input.itrain_lag_opt==0:
            self.radioButton_LaguerreBP.setChecked(True)
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_lag))
        else:
            self.radioButton_LaguerreIPOPT.setChecked(True)
            self.lineEdit_LaguerreMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_lag))
        if self.dabnet_input.itrain_red_opt==0:
            self.radioButton_BalancedBP.setChecked(True)
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_bp_red))
        else:
            self.radioButton_BalancedIPOPT.setChecked(True)
            self.lineEdit_BalancedMaxIterations.setText(str(self.dabnet_input.nmax_iter_ipopt_red))
        self.lineEdit_InitialWeight.setText(str(self.dabnet_input.weight_init))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    dat = dict()
    dabnet_input = DABNetInput()
    dabnet_input.set_numbers_of_input_and_output(4,4)
    dat['dabnet_input'] = dabnet_input
    input_list = list()
    for i in xrange(4):
        input_list.append(InputVariable())
        input_list[i].name = "Input {}".format(i)
    dat['input_list'] = input_list
    output_list = list()
    for i in xrange(4):
        output_list.append(OutputVariable())
        output_list[i].name = "Outnput {}".format(i)
    dat['output_list'] = output_list
    form = DABNetParamDlg(dat)
    result = form.exec_()
    print result
    app.exec_()
