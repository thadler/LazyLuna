from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg

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
from LazyLuna.Tables  import *
from LazyLuna.Figures import *
from LazyLuna         import Views


class CC_CRs_Images_Tab_NEW(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Clinical Results and Images/Annotations'
        
    def make_tab(self, gui, view, cc):
        self.gui     = gui
        self.base_cc = self.cc = cc
        gui.tabs.addTab(self, self.name + ': ' + str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.combobox_select_view = QComboBox()
        self.combobox_select_view.setStatusTip('Choose a View')
        self.combobox_select_view.addItems(['Choose a View'] + self.get_view_names())
        self.combobox_select_view.activated[str].connect(self.select_view) 
        layout.addWidget(self.combobox_select_view, 0, 0)

        self.cr_table = CC_ClinicalResultsAveragesTable()
        self.cr_table.calculate([self.cc])
        self.cr_tableView = QTableView()
        self.cr_tableView.setModel(self.cr_table.to_pyqt5_table_model())
        layout.addWidget(self.cr_tableView, 1, 0, 1,2)
        
        self.image_viewer1 = SideBySide_PlotWidget()
        self.image_viewer1.set_case(self.cc.case1) # for all cats and both cases
        self.image_viewer2 = SideBySide_PlotWidget()
        self.image_viewer2.set_case(self.cc.case2) # for all cats and both cases
        self.image_viewer1.link_with_other(self.image_viewer2)
        self.image_viewer2.link_with_other(self.image_viewer1)
        layout.addWidget(self.image_viewer1,  4, 0, 2, 2)
        layout.addWidget(self.image_viewer2,  4, 2, 2, 2)
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]==vname][0]
        return view()
    
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]!='View']
        return v_names
    
    def select_view(self):
        try:
            view_name = self.combobox_select_view.currentText()
            v         = self.get_view(view_name)
            cc        = copy.deepcopy(self.base_cc)
            self.cc   = Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2))
            cat       = self.cc.case1.categories[0]
            # recalculate CRs and reinitialize Figure
            self.cr_table.calculate([self.cc])
            self.cr_tableView.setModel(self.cr_table.to_pyqt5_table_model())
            #self.img_fig.set_values(v, self.cc, self.img_canvas)
            #self.img_fig.visualize(0, cat)
            self.image_viewer1.set_case(self.cc.case1)
            self.image_viewer2.set_case(self.cc.case2)
        except Exception as e:
            print('Exception in select_view: ', e)


        
        
        