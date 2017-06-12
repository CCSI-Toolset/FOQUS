# ccsi_double_validator.py
from PySide.QtGui import QMessageBox


class CCSIDoubleValidator(object):
    def __init__(self, lower=0.0, upper=1.0, name=""):
        self._lower = lower
        self._upper = upper
        self._name = name
        self._msgbox = False

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self, lower):
        self._lower = lower

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self, upper):
        self._upper = upper

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def validate(self, text_input, parent=None):
        if self._msgbox:
            return False
        if len(text_input) == 0:
            if len(self._name):
                msg = "The input for {0} is empty! Please enter a number between {1} and {2}".format(self._name, self._lower, self._upper)
            else:
                msg = "The input is empty! Please enter a number between {0} and {1}".format(self._lower, self._upper)
            self._msgbox = True
            QMessageBox.warning(parent, "Warning", msg)
            self._msgbox = False
            return False
        try:
            num = float(text_input)
        except ValueError:
            if len(self._name):
                msg = "Invalid input for {0}! Please enter a number between {1} and {2}".format(self._name, self._lower, self._upper)
            else:
                msg = "Invalid input! Please enter a number between {0} and {1}".format(self._lower, self._upper)
            self._msgbox = True
            QMessageBox.warning(parent, "Warning", msg)
            self._msgbox = False
            return False

        if num < self._lower:
            if len(self._name):
                msg = "Invalid input for {0}! Please enter a number greater or equal to {1}".format(self._name, self._lower)
            else:
                msg = "Invalid input! Please enter a number greater or equal to {0}".format(self._lower)
            self._msgbox = True
            QMessageBox.warning(parent, "Warning", msg)
            self._msgbox = False
            return False
        elif num > self._upper:
            if len(self._name):
                msg = "Invalid input for {0}! Please enter a number less or equal to {1}".format(self._name, self._upper)
            else:
                msg = "Invalid input! Please enter a number less or equal to {0}".format(self._upper)
            self._msgbox = True
            QMessageBox.warning(parent, "Warning", msg)
            self._msgbox = False
            return False
        else:
            return True
