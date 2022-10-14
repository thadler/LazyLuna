from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir, QSortFilterProxyModel, pyqtSignal

import pyqtgraph as pg

import os
from pathlib import Path
import sys
import copy
import inspect

import pandas
import numpy as np

from LazyLuna.loading_functions import get_case_info
from LazyLuna.Tables import Table
from LazyLuna import Views

        
class SingleCase_TabWidget(QWidget):
    def __init__(self, parent, view, viewname, case, case_path):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        
        # Setting some variables
        self.view = copy.deepcopy(view)
        self.viewname = viewname
        self.case = copy.deepcopy(case)
        self.case_paths = copy.deepcopy(case_path)
        
        
        self.layout.addWidget(QHLine(), 0, 0, 1, 10)
        self.selected_view_lbl  = QLabel('View: ')
        self.selected_view_text = QLabel(viewname)
        self.nr_cases_lbl       = QLabel('Casename: ')
        self.nr_cases_text      = QLabel(case.case_name)
        self.layout.addWidget(self.selected_view_lbl,  1, 0, 1,1)
        self.layout.addWidget(self.selected_view_text, 1, 1, 1,1)
        self.layout.addWidget(self.nr_cases_lbl,       1, 2, 1,1)
        self.layout.addWidget(self.nr_cases_text,      1, 3, 1,1)
        self.layout.addWidget(QHLine(), 2, 0, 1, 10)
        
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        #self.tableView.doubleClicked.connect(self.manual_intervention)
        self.tableView.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout.addWidget(self.tableView, 3, 0, 1,10)
        
        self.image_viewer = CustomPlotWidget()
        #self.image_viewer.invertY(True)   # vertical axis counts top to bottom
        #self.image_viewer.showGrid(x=True, y=True)
        self.image_viewer.setAspectLocked()
        self.image_viewer.getPlotItem().hideAxis('bottom')
        self.image_viewer.getPlotItem().hideAxis('left')
        cat = case.categories[0]
        self.layout.addWidget(self.image_viewer,  4, 0, 10, 5)
        
        imgs = [[cat.get_img(d,p) for p in range(cat.nr_phases)] for d in range(cat.nr_slices)]
        self.image_viewer.set_images(imgs)
        self.calculate_table()
        
        
    
    def calculate_table(self):
        rows = []
        columns = ['Casename', 'Readername']+[cr.name for cr in self.case.crs]
        rows = [[self.case.case_name, self.case.reader_name]+[cr.get_val(string=True) for cr in self.case.crs]]
        self.t  = Table()
        self.t.df = pandas.DataFrame(rows, columns=columns)
        self.tableView.setModel(self.t.to_pyqt5_table_model())
    
    

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

        
class CustomPlotWidget(pg.PlotWidget):
    keyPressed = pyqtSignal(int)
    def __init__(self):
        super().__init__()

    def set_images(self, imgs):
        self.images = imgs
        self.d, self.p = 0, 0
        self.nr_slices, self.nr_phases = len(imgs), len(imgs[0])
        self.show()
        
    def keyPressEvent(self, event):
        event = event.key()
        left, right, up, down = 16777234, 16777236, 16777235, 16777237
        if event == left:  self.p = (self.p-1)%self.nr_phases
        if event == right: self.p = (self.p+1)%self.nr_phases
        if event == up:    self.d = (self.d-1)%self.nr_slices
        if event == down:  self.d = (self.d+1)%self.nr_slices
        self.show()
        
    def show(self):
        self.clear()  # add ImageItem to PlotItem
        img = self.images[self.d][self.p]
        img = pg.ImageItem(img, levels=(np.min(img),np.max(img)))
        self.addItem(img)  # add ImageItem to PlotItem