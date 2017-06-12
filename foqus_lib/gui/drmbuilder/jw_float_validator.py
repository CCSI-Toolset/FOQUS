from PySide import QtGui
import sys
class CCSIFloatValidator(QtGui.QValidator):
    def __init__(self, parent=None, min_=0.0, max_=100.0):
        QtGui.QValidator.__init__(self, parent)

        self.min_ = min_
        self.max_ = max_
        
        self.states = {'invalid':       QtGui.QValidator.Invalid,
                       'intermediate':  QtGui.QValidator.Intermediate,
                       'acceptable':    QtGui.QValidator.Acceptable,
                       }

    def returnState(self, state, text, pos):
        if state == 'acceptable':
            color = '#00cc00' # green
        elif state == 'intermediate':
            color = '#fff79a' # yellow
        else:
            color = '#f6989d' # red
        self.parent().setStyleSheet('QLineEdit {{ background-color: {} }}'.format(color))
        return (self.states[state], text, pos)

    def validate(self, textInput, pos):
        # Check text, return state
        if len(textInput) == 0:
            return self.returnState('intermediate', textInput, pos)

        try:
            num = float(textInput)
        except:
            return self.returnState('invalid', textInput, pos)

        if num < self.min_:
            self.parent().setToolTip('Value needs to be greater than {}'.format(self.min_))
            return self.returnState('invalid', textInput, pos)
        elif num > self.max_:
            self.parent().setToolTip('Value needs to be less than {}'.format(self.max_))
            return self.returnState('invalid', textInput, pos)
        else:
            return self.returnState('acceptable', textInput, pos)

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    #app.setStyle('GTK')
    mainWindow = QtGui.QMainWindow()

    lineEdit = QtGui.QLineEdit()
    validator = CCSIFloatValidator(lineEdit, 0.0, 100.0)
    lineEdit.setValidator(validator)

    mainWindow.setCentralWidget(lineEdit)
    mainWindow.show()

    app.exec_()

    app.deleteLater()
    sys.exit()
