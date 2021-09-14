import sys  # We need sys so that we can pass argv to QApplication
from MainForm import MainForm
from PyQt5.QtWidgets import (QApplication)

app = QApplication(sys.argv)
w = MainForm()
sys.exit(app.exec_())#!/bin/python3


