# step_change_dlg.py
import copy
import sys
from PySide.QtGui import *
from foqus_lib.framework.drmbuilder.step_change import StepChange
from step_change_dlg_ui import Ui_stepChangeDlg
from ccsi_int_validator import CCSIIntValidator


class StepChangeDlg(QDialog, Ui_stepChangeDlg):
    """
        The Dialog class for the specification of step change sequence
    """

    def __init__(self, dat_init, parent=None):
        super(StepChangeDlg, self).__init__(parent)
        self.setupUi(self)
        self.dat = copy.deepcopy(dat_init)
        self.lineEdit_SamplingTime.setText(str(self.dat['dt_sampling']))
        self.lineEdit_SolverMinTime.setText(str(self.dat['dt_min_solver']))
        self.lineEdit_UnitSamplingTime.setText(self.dat['unit_time'])
        self.lineEdit_UnitSolverMinTime.setText(self.dat['unit_time'])
        self.lineEdit_NumberOfLHSPoints.setText(str(self.dat['step_change'].npoint))
        self.lineEdit_NumberOfLHSSets.setText(str(self.dat['step_change'].nduration))
        self.checkBox_IncludeReverse.setChecked(self.dat['step_change'].ireverse==1)
        for icount in xrange(self.dat['step_change'].nduration):
            self.listWidget_SetList.addItem("LHS Set {0:d}".format(icount+1))
        self.listWidget_SetList.setCurrentRow(0);
        self.lineEdit_Duration.setText(str(self.dat['step_change'].vduration[0]))
        # validators
        self.validator_NumberOfLHSPoints = CCSIIntValidator(3, 20, self.label_NumberOfLHSPoints.text())
        self.validator_NumberOfLHSSets = CCSIIntValidator(1, 10, self.label_NumberOfLHSSets.text())
        self.validator_Duration = CCSIIntValidator(2, 500, self.label_Duration.text())
        # signals and slots
        self.pushButton_OK.clicked.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.listWidget_SetList.currentItemChanged.connect(self.on_list_item_changed)
        self.lineEdit_Duration.editingFinished.connect(self.on_edit_duration_changed)
        self.lineEdit_NumberOfLHSPoints.editingFinished.connect(self.on_edit_lhspoints_changed)
        self.lineEdit_NumberOfLHSSets.editingFinished.connect(self.on_edit_lhssets_changed)
        self.checkBox_IncludeReverse.clicked.connect(self.on_reverse_clicked)

    def on_list_item_changed(self):
        index = self.listWidget_SetList.currentRow()
        self.lineEdit_Duration.setText(str(self.dat['step_change'].vduration[index]))

    def on_edit_duration_changed(self):
        txt = self.lineEdit_Duration.text()
        if self.validator_Duration.validate(txt) is False:
            self.lineEdit_Duration.selectAll()
            self.lineEdit_Duration.setFocus()
        else:
            index = self.listWidget_SetList.currentRow()
            self.dat['step_change'].vduration[index] = int(txt)

    def on_edit_lhspoints_changed(self):
        txt = self.lineEdit_NumberOfLHSPoints.text()
        if self.validator_NumberOfLHSPoints.validate(txt) is False:
            self.lineEdit_NumberOfLHSPoints.selectAll()
            self.lineEdit_NumberOfLHSPoints.setFocus()
        else:
            self.dat['step_change'].npoint = int(txt)

    def on_edit_lhssets_changed(self):
        txt = self.lineEdit_NumberOfLHSSets.text()
        if self.validator_NumberOfLHSSets.validate(txt) is False:
            self.lineEdit_NumberOfLHSSets.selectAll()
            self.lineEdit_NumberOfLHSSets.setFocus()
        else:
            nduration_new = int(txt)
            self.dat['step_change'].nduration = nduration_new
            self.listWidget_SetList.clear()
            for icount in xrange(nduration_new):
                self.listWidget_SetList.addItem("LHS Set {0:d}".format(icount+1))
            # dynamically allocate the vduration list
            vduration = self.dat['step_change'].vduration
            nduration_old = len(vduration)
            if nduration_new > nduration_old:
                for i in xrange(nduration_new - nduration_old):
                    vduration.append(10)
            elif nduration_new < nduration_old:
                for i in xrange(nduration_old - nduration_new):
                    vduration.pop()
            self.listWidget_SetList.setCurrentRow(0)
            self.lineEdit_Duration.setText(str(self.dat['step_change'].vduration[0]))

    def on_reverse_clicked(self):
        breverse = self.checkBox_IncludeReverse.isChecked()
        if breverse:
            self.dat['step_change'].ireverse = 1
        else:
            self.dat['step_change'].ireverse = 0

    def accept(self):
        QDialog.accept(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    step_change = StepChange()
    dat = dict()
    dat['dt_sampling'] = 0.1
    dat['dt_min_solver'] = 0.001
    dat['unit_time'] = "sec"
    dat['step_change'] = step_change
    form = StepChangeDlg(dat)
    result = form.exec_()
    print result
    app.exec_()
