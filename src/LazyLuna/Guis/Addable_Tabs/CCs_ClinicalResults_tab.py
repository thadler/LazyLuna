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

        self.ccs = ccs
        
        self.crs_TableView = QTableView()
        layout.addWidget(self.crs_TableView, 0,0, 2,1)
        
        self.qq = QQPlot()
        self.qq_canvas = FigureCanvas(self.qq)
        self.qq.set_view(view); self.qq.set_canvas(self.qq_canvas); self.qq.set_gui(gui)
        self.qq_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.qq_canvas.setFocus()
        self.qq_toolbar = NavigationToolbar(self.qq_canvas, gui)
        layout.addWidget(self.qq_canvas,  2,0, 1,1)
        layout.addWidget(self.qq_toolbar, 3,0, 1,1)
        
        self.pair = PairedBoxplot()
        self.pair_canvas = FigureCanvas(self.pair)
        self.pair.set_view(view); self.pair.set_canvas(self.pair_canvas); self.pair.set_gui(gui)
        self.pair_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.pair_canvas.setFocus()
        self.pair_toolbar = NavigationToolbar(self.pair_canvas, gui)
        layout.addWidget(self.pair_canvas,  0,1, 1,1)
        layout.addWidget(self.pair_toolbar, 1,1, 1,1)
        
        self.ba = BlandAltman()                # instantiating visualization
        self.ba_canvas = FigureCanvas(self.ba) # wrapping visualization
        self.ba.set_view(view)                 # setting auxilliary information
        self.ba.set_canvas(self.ba_canvas)     # ""
        self.ba.set_gui(gui)                   # ""
        self.ba_canvas.setFocusPolicy(Qt.Qt.ClickFocus) # focus policy 
        self.ba_canvas.setFocus()                       # ""
        self.ba_toolbar = NavigationToolbar(self.ba_canvas, gui)
        layout.addWidget(self.ba_canvas,  2,1, 1,1) # adding vis to PyQt5 tab
        layout.addWidget(self.ba_toolbar, 3,1, 1,1) # ""
        
        #layout.setRowStretch(0, 3)
        self.setLayout(layout)
        
        self.CR_threadworker(ccs)
        
        
    def update_figures(self):
        try:
            idx = self.crs_TableView.selectionModel().selectedIndexes()[0]
            row, col = idx.row(), idx.column()
            cr_name = self.crs_table.df['Clinical Result (mean±std)'].iloc[row].split(' ')[0]
            self.qq.visualize(self.ccs, cr_name)
            #self.bp.visualize(self.ccs, cr_name)
            self.pair.visualize(self.ccs, cr_name)
            self.ba.visualize(self.ccs, cr_name)
        except Exception as e:
            print(traceback.format_exc())
        
    def CR_threadworker(self, ccs):
        self.worker = CR_Results_Worker(self, ccs)
        self.worker.start()
        self.worker.worksignal.connect(self.update_cr_avgs_table)
        
    def update_cr_avgs_table(self, crs_df):
        self.crs_table = CC_ClinicalResultsAveragesTable()
        self.crs_table.df = crs_df
        self.crs_TableView.setModel(self.crs_table.to_pyqt5_table_model())
        self.crs_TableView.selectionModel().selectionChanged.connect(self.update_figures)
        self.crs_TableView.resizeColumnsToContents()
        return
        
        
class CR_Results_Worker(QThread):
    worksignal = pyqtSignal(pd.DataFrame)

    def __init__(self, parent=None, ccs=None):
        super(QThread, self).__init__()
        self.set_ccs(ccs)

    @pyqtSlot(pd.DataFrame)
    def run(self):
        self.table = CC_ClinicalResultsAveragesTable()
        self.table.calculate(self.ccs)
        self.worksignal.emit(self.table.df)

    def set_ccs(self, ccs):
        self.ccs = copy.deepcopy(ccs)