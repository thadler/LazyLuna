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

from LazyLuna.Mini_LL import Case_Comparison, SAX_CINE_View, SAX_CS_View
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CCs_ClinicalResults_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Clinical Results and Backtracking'
        
    def make_tab(self, gui, view, ccs):
        self.gui = gui
        gui.tabs.addTab(self, "Clinical Results")
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        cr_name = 'LVESV'
        
        
        """
        TODO GET HOVER TO WORK
        """
        self.ba = BlandAltman()
        self.ba.visualize(ccs, cr_name)
        self.ba_canvas = FigureCanvas(self.ba)
        self.ba_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.ba_canvas.setFocus()
        self.ba_toolbar = NavigationToolbar(self.ba_canvas, gui)
        layout.addWidget(self.ba_canvas,  0,0, 1,1)
        layout.addWidget(self.ba_toolbar, 1,0, 1,1)
        
        self.setLayout(layout)
        layout.setRowStretch(0, 3)
        
        