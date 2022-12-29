from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

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

import copy

import pandas as pd

from LazyLuna.Containers import Case_Comparison
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CCs_MappingSliceAnalysis_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Mapping Slice Analysis'
        
    def make_tab(self, gui, view, ccs):
        self.gui = gui
        gui.tabs.addTab(self, "Mapping Slice Analysis")
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.ccs = ccs
        
        self.fig1    = Mapping_Slice_Average_PairedBoxplot()
        self.canvas1 = FigureCanvas(self.fig1)
        self.fig1.set_view(view); self.fig1.set_canvas(self.canvas1); self.fig1.set_gui(gui)
        self.canvas1.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas1.setFocus()
        self.toolbar1 = NavigationToolbar(self.canvas1, gui)
        self.fig1.visualize(self.ccs, mapping_type='T1')
        layout.addWidget(self.canvas1,  2,0, 1,1)
        layout.addWidget(self.toolbar1, 3,0, 1,1)
        
        self.fig2    = Mapping_DiceBySlice()
        self.canvas2 = FigureCanvas(self.fig2)
        self.fig2.set_view(view); self.fig2.set_canvas(self.canvas2); self.fig2.set_gui(gui)
        self.canvas2.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas2.setFocus()
        self.toolbar2 = NavigationToolbar(self.canvas2, gui)
        self.fig2.visualize(self.ccs, mapping_type='T1')
        layout.addWidget(self.canvas2,  2,1, 1,1)
        layout.addWidget(self.toolbar2, 3,1, 1,1)
        
        self.fig3 = Mapping_ReferencePointAngleDiff_Boxplot()
        self.canvas3 = FigureCanvas(self.fig3)
        self.fig3.set_view(view); self.fig3.set_canvas(self.canvas3); self.fig3.set_gui(gui)
        self.canvas3.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas3.setFocus()
        self.toolbar3 = NavigationToolbar(self.canvas3, gui)
        self.fig3.visualize(self.ccs)
        layout.addWidget(self.canvas3,  4,0, 1,1)
        layout.addWidget(self.toolbar3, 5,0, 1,1)
        
        self.fig4 = Mapping_ReferencePointDistance_Boxplot()
        self.canvas4 = FigureCanvas(self.fig4)
        self.fig4.set_view(view); self.fig4.set_canvas(self.canvas4); self.fig4.set_gui(gui)
        self.canvas4.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas4.setFocus()
        self.toolbar4 = NavigationToolbar(self.canvas4, gui)
        self.fig4.visualize(self.ccs)
        layout.addWidget(self.canvas4,  4,1, 1,1)
        layout.addWidget(self.toolbar4, 5,1, 1,1)
        
        #layout.setRowStretch(0, 3)
        self.setLayout(layout)
        