# output_variable_dlg.py
import copy
import sys
from PySide.QtGui import *
from foqus_lib.framework.drmbuilder.output_variable import OutputVariable
from output_variable_dlg_ui import Ui_outputVariableDlg
from ccsi_double_validator import CCSIDoubleValidator


class OutputVariableDlg(QDialog, Ui_outputVariableDlg):
    """
        The Dialog class for the specification of input variables
    """

    def __init__(self, dat_init, parent=None):
        super(OutputVariableDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.update_number_of_varied_outputs()
        self.lineEdit_NumberOfVariedVariables.setText(str(self.nvaried))
        icount = 0
        for item in self.dat['output_list']:
            icount += 1
            self.listWidget_OutputList.addItem("{0}. {1}".format(icount, item.key_sinter))
        self.listWidget_OutputList.setCurrentRow(0)
        self.lineEdit_Name.setText(self.dat['output_list'][0].name)
        self.lineEdit_Description.setText(self.dat['output_list'][0].desc)
        self.lineEdit_Unit.setText(self.dat['output_list'][0].unit)
        self.checkBox_VariesWithTime.setChecked(self.dat['output_list'][0].bvaried)
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.listWidget_OutputList.currentItemChanged.connect(self.on_list_item_changed)
        self.lineEdit_Description.editingFinished.connect(self.on_edit_description_changed)
        self.checkBox_VariesWithTime.clicked.connect(self.on_varied_checked)
        self.pushButton_Up.clicked.connect(self.on_move_up)
        self.pushButton_Down.clicked.connect(self.on_move_down)

    def update_number_of_varied_outputs(self):
        self.nvaried = 0
        for item in self.dat['output_list']:
            if item.bvaried:
                self.nvaried += 1

    def on_list_item_changed(self):
        index = self.listWidget_OutputList.currentRow()
        self.lineEdit_Name.setText(self.dat['output_list'][index].name)
        self.lineEdit_Description.setText(self.dat['output_list'][index].desc)
        self.lineEdit_Unit.setText(self.dat['output_list'][index].unit)
        self.checkBox_VariesWithTime.setChecked(self.dat['output_list'][index].bvaried)

    def on_edit_description_changed(self):
        txt = self.lineEdit_Description.text()
        index = self.listWidget_OutputList.currentRow()
        self.dat['output_list'][index].desc = txt

    def on_varied_checked(self):
        bvaried = self.checkBox_VariesWithTime.isChecked()
        index = self.listWidget_OutputList.currentRow()
        self.dat['output_list'][index].bvaried = bvaried
        self.update_number_of_varied_outputs()
        self.lineEdit_NumberOfVariedVariables.setText(str(self.nvaried))

    def on_move_up(self):
        index = self.listWidget_OutputList.currentRow()
        if index==0:
            return
        curItem = self.listWidget_OutputList.currentItem()
        upItem = self.listWidget_OutputList.item(index-1)
        tmp = self.dat['output_list'][index]
        self.dat['output_list'][index] = self.dat['output_list'][index-1]
        self.dat['output_list'][index-1] = tmp
        curItem.setText("{0}. {1}".format(index+1, self.dat['output_list'][index].key_sinter))
        upItem.setText("{0}. {1}".format(index, self.dat['output_list'][index-1].key_sinter))
        self.listWidget_OutputList.setCurrentRow(index-1)

    def on_move_down(self):
        index = self.listWidget_OutputList.currentRow()
        if index==self.listWidget_OutputList.count()-1:
            return
        curItem = self.listWidget_OutputList.currentItem()
        downItem = self.listWidget_OutputList.item(index+1)
        tmp = self.dat['output_list'][index]
        self.dat['output_list'][index] = self.dat['output_list'][index+1]
        self.dat['output_list'][index+1] = tmp
        curItem.setText("{0}. {1}".format(index+1, self.dat['output_list'][index].key_sinter))
        downItem.setText("{0}. {1}".format(index+2, self.dat['output_list'][index+1].key_sinter))
        self.listWidget_OutputList.setCurrentRow(index+1)

    def accept(self):
        if self.nvaried==0:
            QMessageBox.warning(self, "Warning", "No output variable is selected to vary with time and included in the D-RM!")
            return
        QDialog.accept(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dat = dict()
    output_list = list()
    for i in xrange(4):
        output_list.append(OutputVariable())
    dat['output_list'] = output_list
    form = OutputVariableDlg(dat)
    result = form.exec_()
    print result
    app.exec_()
