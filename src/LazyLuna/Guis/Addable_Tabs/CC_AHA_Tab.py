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

from LazyLuna.Mini_LL import Case_Comparison, SAX_CINE_View, SAX_CS_View, LAX_CINE_View, SAX_T1_View, SAX_T2_View
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CC_AHA_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'AHA Figure'
        
    def make_tab(self, gui, view, cc):
        self.gui  = gui
        self.view = view
        self.cc   = cc
        gui.tabs.addTab(self, "Case AHA: "+str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)
        
        self.figure1 = T1_bullseye_plot()
        self.canvas1 = FigureCanvas(self.figure1)
        self.figure1.set_values(view, cc.case1, self.canvas1)
        self.figure1.visualize()
        self.canvas1.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas1.setFocus()
        self.toolbar1 = NavigationToolbar(self.canvas1, gui)
        layout.addWidget(self.canvas1,  0,0, 1,1)
        layout.addWidget(self.toolbar1, 1,0, 1,1)
        
        self.figure2 = T1_diff_bullseye_plot()
        self.canvas2 = FigureCanvas(self.figure2)
        self.figure2.set_values(view, cc, self.canvas2)
        self.figure2.visualize()
        self.canvas2.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas2.setFocus()
        self.toolbar2 = NavigationToolbar(self.canvas2, gui)
        layout.addWidget(self.canvas2,  0,1, 1,1)
        layout.addWidget(self.toolbar2, 1,1, 1,1)
        
        self.figure3 = T1_bullseye_plot()
        self.canvas3 = FigureCanvas(self.figure3)
        self.figure3.set_values(view, cc.case2, self.canvas3)
        self.figure3.visualize()
        self.canvas3.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas3.setFocus()
        self.toolbar3 = NavigationToolbar(self.canvas3, gui)
        layout.addWidget(self.canvas3,  0,2, 1,1)
        layout.addWidget(self.toolbar2, 1,2, 1,1)
        
        self.setLayout(layout)

        
    def recalculate_metrics_table(self):
        cont_name = self.combobox_select_contour.currentText()
        if cont_name=='Choose a Contour': return
        cat = self.view.get_categories(self.cc.case1, cont_name)[0]
        try:
            self.metrics_table.present_contour_df(cont_name)
            self.metrics_table.present_contour_df(cont_name)
            self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
        except Exception as e: print(e); pass
        try: self.annotation_comparison_figure.visualize(0, cat, cont_name)
        except Exception as e: print(e); pass
        