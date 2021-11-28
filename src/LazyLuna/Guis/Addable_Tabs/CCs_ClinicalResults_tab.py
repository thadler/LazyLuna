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


class CC_ClinicalResults_Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Clinical Results and Backtracking'
        
    def make_tab(self, gui, view, ccs):
        self.gui = gui
        gui.tabs.addTab(self, "Clinical Results")
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.metrics_table  = CC_Metrics_Table()
        self.metrics_table.calculate(Case_Comparison(view.customize_case(cc.case1), view.customize_case(cc.case2)))
        #self.metrics_table.present_contour_df('')
        self.metrics_table.present_contour_df(view.contour_names[0])
        
        self.metrics_TableView = QTableView()
        self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
        layout.addWidget(self.metrics_TableView, 1,0, 1,1)

        
        self.annotation_comparison_figure = Annotation_Comparison()
        cat = cc.case1.categories[0]
        self.annotation_comparison_canvas = FigureCanvas(self.annotation_comparison_figure)
        self.annotation_comparison_figure.set_values(view, cc, self.annotation_comparison_canvas)
        self.annotation_comparison_figure.visualize(3, cat, 'lv_endo')
        self.annotation_comparison_canvas.mpl_connect('key_press_event', self.annotation_comparison_figure.keyPressEvent)
        self.annotation_comparison_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.annotation_comparison_canvas.setFocus()
        self.annotation_comparison_toolbar = NavigationToolbar(self.annotation_comparison_canvas, gui)
        layout.addWidget(self.annotation_comparison_canvas,  2,0, 1,1)
        layout.addWidget(self.annotation_comparison_toolbar, 3,0, 1,1)
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

        
    def change_cr(self):
        cont_name = self.combobox_select_contour.currentText()
        if cont_name=='Choose a Contour': return
        self.metrics_table.present_contour_df(cont_name)
        
        