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
import traceback

import pandas

from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *
        

class CCs_AHA_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Stats AHA Figure'
        
    def make_tab(self, gui, view, ccs):
        self.gui  = gui
        self.view = view
        self.ccs   = ccs
        gui.tabs.addTab(self, "Stats Cases AHA: "+str(ccs[0].case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)
        
        try:
            
            self.readerchoice_combobox = QComboBox()
            self.readerchoice_combobox.addItems(['Select Reader', 'R1', 'R2'])
            self.readerchoice_combobox.activated[str].connect(self.update)
            layout.addWidget(self.readerchoice_combobox, 0,0, 1,1)
        
            self.figure = Statistical_T1_bullseye_plot()
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setFocusPolicy(Qt.Qt.ClickFocus)
            self.canvas.setFocus()
            self.toolbar = NavigationToolbar(self.canvas, gui)
            layout.addWidget(self.canvas,   0, 1, 10,2)
            layout.addWidget(self.toolbar, 11, 1,  1,2)
            
        except Exception as e:
            print(traceback.format_exc())
        
        self.setLayout(layout)

        
    def update(self):
        try:
            reader = self.readerchoice_combobox.currentText()
            if reader=='Select Reader': return
            if reader=='R1':
                cases = [cc.case1 for cc in self.ccs]
                self.figure.set_values(self.view, cases, self.canvas)
                self.figure.visualize()
            if reader=='R2':
                cases = [cc.case2 for cc in self.ccs]
                self.figure.set_values(self.view, cases, self.canvas)
                self.figure.visualize()
        except Exception as e:
            print(traceback.format_exc())
        
            