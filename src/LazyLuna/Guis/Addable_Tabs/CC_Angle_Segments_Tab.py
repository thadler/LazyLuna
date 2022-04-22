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

from LazyLuna.Mini_LL import Case_Comparison
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CC_Angle_Segments_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Angle Segments Comparison'
        
    def make_tab(self, gui, view, cc):
        self.gui     = gui
        self.base_cc = self.cc = cc
        gui.tabs.addTab(self, self.name + ': ' + str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.nr_angle_text   = QLineEdit('6')
        self.nr_angle_button = QPushButton('Update Angles')
        self.nr_angle_button.clicked.connect(self.update)
        self.byref_combobox = QComboBox()
        self.byref_combobox.addItems(['Individual', 'R1', 'R2'])
        self.byref_combobox.activated[str].connect(self.update)
        layout.addWidget(self.nr_angle_text,   0,0, 1,1)
        layout.addWidget(self.nr_angle_button, 0,1, 1,1)
        layout.addWidget(self.byref_combobox,  0,2, 1,1)

        self.table = CC_AngleAvgT1ValuesTable()
        self.table.calculate(cc, category=cc.case1.categories[0], nr_segments=6, byreader=None)
        self.tableView = QTableView()
        self.tableView.setModel(self.table.to_pyqt5_table_model())
        #self.tableView.selectionModel().selectionChanged.connect(self.update_figures)
        layout.addWidget(self.tableView, 1,0, 1,3)
        
        
        self.fig    = Angle_Segment_Comparison()
        self.canvas = FigureCanvas(self.fig)
        self.fig.set_values(view, cc, self.canvas)
        self.canvas.mpl_connect('key_press_event', self.fig.keyPressEvent)
        self.canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.canvas.setFocus()
        self.toolbar = NavigationToolbar(self.canvas, gui)
        layout.addWidget(self.canvas,  2,0, 1,3)
        layout.addWidget(self.toolbar, 3,0, 1,3)
        
        self.update()
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

    def update(self):
        t = self.nr_angle_text.text()
        if t=='': t = 6
        self.nr_angles = int(str(t))
        self.nr_angles = max(2, min(self.nr_angles, 60)) # between 0 and 30
        self.nr_angle_text.setText(str(self.nr_angles))
        byref = self.byref_combobox.currentText()
        byref = ['Individual', 'R1', 'R2'].index(byref)
        cat = self.cc.case1.categories[0]
        self.fig.visualize(0, cat, self.nr_angles, [None, 1, 2][byref])
        self.canvas.draw()
        self.table.calculate(self.cc, cat, nr_segments=self.nr_angles, byreader=[None, 1, 2][byref])
        self.tableView.setModel(self.table.to_pyqt5_table_model())
        
        
    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Mini_LL, inspect.isclass) if issubclass(c[1], Mini_LL.View) if c[0]==vname][0]
        return view()
    
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Mini_LL, inspect.isclass) if issubclass(c[1], Mini_LL.View) if c[0]!='View']
        return v_names
    
    def select_view(self):
        view_name = self.combobox_select_view.currentText()
        v         = self.get_view(view_name)
        cc        = copy.deepcopy(self.base_cc)
        self.cc   = Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2))
        cat       = self.cc.case1.categories[0]
        # recalculate CRs and reinitialize Figure
        self.cr_table.calculate([self.cc])
        self.cr_tableView.setModel(self.cr_table.to_pyqt5_table_model())
        self.img_fig.set_values(v, self.cc, self.img_canvas)
        self.img_fig.visualize(0, cat)


