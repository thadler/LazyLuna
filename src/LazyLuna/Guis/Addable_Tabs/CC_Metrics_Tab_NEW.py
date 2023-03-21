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
import traceback
import pandas

from LazyLuna.Containers import Case_Comparison
from LazyLuna.Views   import *
from LazyLuna.loading_functions import *
from LazyLuna.Tables  import *
from LazyLuna.Figures import *


class CC_Metrics_Tab_NEW(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Metric Table and Figure'
        
    def make_tab(self, gui, view, cc):
        self.gui  = gui
        self.view = view
        self.cc   = cc
        gui.tabs.addTab(self, "Case Metrics: "+str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        print('In cc metrics tab: ', view, view.contour_names)
        
        self.combobox_select_contour = QComboBox()
        self.combobox_select_contour.setStatusTip('Choose a Contour')
        #self.combobox_select_contour.addItems(['Choose a Contour'])
        self.combobox_select_contour.addItems(['Choose a Contour'] + view.contour_names)
        self.combobox_select_contour.activated[str].connect(self.recalculate_metrics_table) 
        layout.addWidget(self.combobox_select_contour, 0,0, 1,3)

        if type(view) in [SAX_CINE_View, SAX_CS_View, SAX_LGE_View]:
            self.metrics_table  = SAX_CINE_CC_Metrics_Table()
        elif type(view) in [SAX_T1_PRE_View, SAX_T1_POST_View]:
            self.metrics_table  = T1_CC_Metrics_Table()
        elif type(view) in [SAX_T2_View]:
            self.metrics_table  = T2_CC_Metrics_Table()
        else: # type(view) is LAX_CINE_View:
            self.metrics_table  = LAX_CC_Metrics_Table()
            
        self.metrics_table.calculate(view, Case_Comparison(view.customize_case(cc.case1), view.customize_case(cc.case2)), view.contour_names[0])
        
        self.metrics_TableView = QTableView()
        self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
        self.metrics_TableView.resizeColumnsToContents()
        layout.addWidget(self.metrics_TableView, 1,0, 1,3)
        
        """
        self.annotation_comparison_figure = Annotation_Comparison()
        cat = cc.case1.categories[0]
        self.annotation_comparison_canvas = FigureCanvas(self.annotation_comparison_figure)
        self.annotation_comparison_figure.set_values(view, cc, self.annotation_comparison_canvas)
        self.annotation_comparison_figure.visualize(0, view.get_categories(cc.case1, view.contour_names[0])[0], view.contour_names[0])
        self.annotation_comparison_canvas.mpl_connect('key_press_event', self.annotation_comparison_figure.keyPressEvent)
        self.annotation_comparison_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.annotation_comparison_canvas.setFocus()
        self.annotation_comparison_toolbar = NavigationToolbar(self.annotation_comparison_canvas, gui)
        layout.addWidget(self.annotation_comparison_canvas,  2,0, 1,1)
        layout.addWidget(self.annotation_comparison_toolbar, 3,0, 1,1)
        """
        
        self.image_viewer1 = SideBySide_PlotWidget()
        self.image_viewer1.set_case(self.cc.case1) # for all cats and both cases
        self.image_viewer2 = SideBySide_PlotWidget()
        self.image_viewer2.set_case(self.cc.case2) # for all cats and both cases
        self.comparison_viewer = ContourComparison_PlotWidget()
        self.comparison_viewer.set_case_comparison(self.cc)
        layout.addWidget(self.image_viewer1,      2, 0, 1, 1)
        layout.addWidget(self.comparison_viewer,  2, 1, 1, 1)
        layout.addWidget(self.image_viewer2,      2, 2, 1, 1)
        
        self.image_viewer1.link_with_other(self.image_viewer2)
        self.image_viewer2.link_with_other(self.image_viewer1)
        self.image_viewer1.link_with_other(self.comparison_viewer)
        self.image_viewer2.link_with_other(self.comparison_viewer)
        self.comparison_viewer.link_with_other(self.image_viewer1)
        self.comparison_viewer.link_with_other(self.image_viewer2)
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

        
    def recalculate_metrics_table(self):
        cont_name = self.combobox_select_contour.currentText()
        if cont_name=='Choose a Contour': return
        view = self.view
        cat = view.get_categories(self.cc.case1, cont_name)[0]
        cc = Case_Comparison(view.customize_case(self.cc.case1), view.customize_case(self.cc.case2))
        try:
            self.metrics_table.calculate(view, cc, cont_name)
            self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
            self.metrics_TableView.resizeColumnsToContents()
        except Exception as e: print(traceback.format_exc())
        try: self.annotation_comparison_figure.visualize(0, cat, cont_name)
        except Exception as e: print(traceback.format_exc())
        
