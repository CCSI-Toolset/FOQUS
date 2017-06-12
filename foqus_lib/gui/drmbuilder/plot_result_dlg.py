# plot_result_dlg.py
import copy
import sys
from PySide.QtGui import *
from plot_result_dlg_ui import Ui_plotResultDlg
from foqus_lib.framework.drmbuilder.input_variable import InputVariable
from foqus_lib.framework.drmbuilder.output_variable import OutputVariable
from foqus_lib.framework.drmbuilder.plotting_input import PlottingInput


class PlotResultDlg(QDialog, Ui_plotResultDlg):
    """
        The Dialog class for plotting results
    """

    def __init__(self, dat_init, parent=None):
        super(PlotResultDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.plotting_input = self.dat['plotting_input']
        for item in self.dat['input_list']:
            if item.bvaried:
                self.listWidget_Input.addItem("* {}".format(item.key_sinter))
            else:
                self.listWidget_Input.addItem("  {}".format(item.key_sinter))
        for item in self.dat['output_list']:
            if item.bvaried:
                self.listWidget_Output.addItem("* {}".format(item.key_sinter))
            else:
                self.listWidget_Output.addItem("  {}".format(item.key_sinter))
        self.checkBox_PlotRelativeErrors.setChecked(self.plotting_input.bplot_error)
        self.checkBox_PlotInputStepChanges.setChecked(self.plotting_input.bplot_step_change)
        self.checkBox_PlotCorrelationPoints.setChecked(self.plotting_input.bplot_correlation)
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_SelectAllInputs.clicked.connect(self.on_select_all_inputs_clicked)
        self.pushButton_SelectAllOutputs.clicked.connect(self.on_select_all_outputs_clicked)
        self.pushButton_DeselectAllInputs.clicked.connect(self.on_deselect_all_inputs_clicked)
        self.pushButton_DeselectAllOutputs.clicked.connect(self.on_deselect_all_outputs_clicked)
        self.checkBox_PlotRelativeErrors.clicked.connect(self.on_plot_relative_errors_clicked)
        self.checkBox_PlotInputStepChanges.clicked.connect(self.on_plot_input_step_changes_clicked)
        self.checkBox_PlotCorrelationPoints.clicked.connect(self.on_plot_correlation_points_clicked)

    def on_plot_relative_errors_clicked(self):
        self.plotting_input.bplot_error = self.checkBox_PlotRelativeErrors.isChecked()

    def on_plot_input_step_changes_clicked(self):
        self.plotting_input.bplot_step_change = self.checkBox_PlotInputStepChanges.isChecked()

    def on_plot_correlation_points_clicked(self):
        self.plotting_input.bplot_correlation = self.checkBox_PlotCorrelationPoints.isChecked()

    def on_select_all_inputs_clicked(self):
        self.listWidget_Input.selectAll()

    def on_select_all_outputs_clicked(self):
        self.listWidget_Output.selectAll()

    def on_deselect_all_inputs_clicked(self):
        self.listWidget_Input.setCurrentRow(-1)

    def on_deselect_all_outputs_clicked(self):
        self.listWidget_Output.setCurrentRow(-1)

    def accept(self):
        indexes_input = self.listWidget_Input.selectedIndexes()
        if len(indexes_input)<1:
            QMessageBox.warning(self, "Warning", "Please select at least on input variable.")
            return
        indexes_output = self.listWidget_Output.selectedIndexes()
        if len(indexes_output)<1:
            QMessageBox.warning(self, "Warning", "Please select at least on output variable.")
            return
        self.plotting_input.input_index_list = []
        for item in indexes_input:
            self.plotting_input.input_index_list.append(item.row())
        self.plotting_input.output_index_list = []
        for item in indexes_output:
            self.plotting_input.output_index_list.append(item.row())
        QDialog.accept(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dat = dict()
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
    dat['plotting_input'] = PlottingInput()
    form = PlotResultDlg(dat)
    result = form.exec_()
    if result==1:
        for i in form.indices_input:
            print i
    app.exec_()
