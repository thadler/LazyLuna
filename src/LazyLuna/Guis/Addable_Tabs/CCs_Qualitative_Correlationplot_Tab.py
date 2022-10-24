from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5 import QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from pathlib import Path
import pickle
import copy
import sys
import os
import inspect

import pandas

from LazyLuna.Containers import Case_Comparison
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CCs_Qualitative_Correlationplot_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Clinical Results and Backtracking'
        
    def make_tab(self, gui, view, ccs):
        self.gui = gui
        gui.tabs.addTab(self, "Qualitative Correlationplot")
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.ccs = ccs
        
        self.qc = Qualitative_Correlationplot()
        self.qc_canvas = FigureCanvas(self.qc)
        self.qc.set_view(view); self.qc.set_canvas(self.qc_canvas); self.qc.set_gui(gui)
        self.qc.visualize(ccs)
        self.qc_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.qc_canvas.setFocus()
        self.qc_toolbar = NavigationToolbar(self.qc_canvas, gui)
        layout.addWidget(self.qc_canvas,  0,0, 1,1)
        layout.addWidget(self.qc_toolbar, 1,0, 1,1)
        
        #layout.setRowStretch(0, 3)
        self.setLayout(layout)