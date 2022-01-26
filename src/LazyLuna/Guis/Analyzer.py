from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QComboBox, QHeaderView, QLabel, QFileDialog, QDialog, QLineEdit
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from pathlib import Path
import pickle
import sys
import os

import numpy as np

from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Mini_LL import Case_Comparison, SAX_CS_View, SAX_CINE_View
from LazyLuna.Guis.Addable_Tabs.CCs_Overview_Tab import CCs_Overview_Tab
from LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab import CC_Metrics_Tab




class Module_3(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title  = 'Lazy Luna - Analyzer'
        shift       = 30
        self.left   = 0
        self.top    = shift
        self.width  = 1200
        self.height = 800  + shift
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.table_widget = MyTabWidget(self)
        self.setCentralWidget(self.table_widget)
        self.show()
    
class MyTabWidget(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Closable Tabs
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda index: self.tabs.removeTab(index))
        # Add tabs
        self.tabs.addTab(self.tab1, "Data Loader")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        # choose basepath
        self.case_folder_button = QPushButton('Select Case Folder')
        self.case_folder_button.clicked.connect(self.set_case_folder)
        self.tab1.layout.addWidget(self.case_folder_button, 0, 0)
        self.case_folder_path = QLineEdit('')
        self.tab1.layout.addWidget(self.case_folder_path, 1, 0)
        # segmenter chooser
        self.combobox_select_segmenter = QComboBox()
        self.combobox_select_segmenter.setStatusTip('Choose a segmenter to load.')
        self.combobox_select_segmenter.addItems(['Select a Reader'])
        self.combobox_select_segmenter.activated[str].connect(self.set_segmenter) 
        self.tab1.layout.addWidget(self.combobox_select_segmenter, 2, 0)
        # segmenter chooser
        self.combobox_select_segmenter2 = QComboBox()
        self.combobox_select_segmenter2.setStatusTip('Choose a segmenter to load.')
        self.combobox_select_segmenter2.addItems(['Select a Reader'])
        self.combobox_select_segmenter2.activated[str].connect(self.set_segmenter) 
        self.tab1.layout.addWidget(self.combobox_select_segmenter2, 3, 0)
        #load all cases button
        self.button_load_cases = QPushButton("Load All Cases")
        self.button_load_cases.clicked.connect(self.load_case_comparisons)
        self.tab1.layout.addWidget(self.button_load_cases, 4,0)
        
        # set table view
        self.caseTableView = QTableView()
        self.tab1.layout.addWidget(self.caseTableView, 0, 1, 10,1)
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setColumnStretch(1, 2)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
        
    def load_case_comparisons(self):
        paths1, paths2 = self.get_paths()
        if paths1==[]: return
        cases1 = [pickle.load(open(p,'rb')) for p in paths1]
        cases2 = [pickle.load(open(p,'rb')) for p in paths2]
        case_names = set([c.case_name for c in cases1]).intersection(set([c.case_name for c in cases2]))
        cases1 = [c for c in cases1 if c.case_name in case_names]
        cases2 = [c for c in cases2 if c.case_name in case_names]
        cases1 = sorted(cases1, key=lambda c:c.case_name)
        cases2 = sorted(cases2, key=lambda c:c.case_name)
        self.case_comparisons = [Case_Comparison(cases1[i],cases2[i]) for i in range(len(cases1))]
        # remove all failed CCs
        self.case_comparisons = [cc for cc in self.case_comparisons if len(cc.case1.available_types)>0]
        self.case_comparisons = sorted(self.case_comparisons, key=lambda cc:cc.case1.case_name)
        tab = CCs_Overview_Tab()
        tab.make_tab(self, self.case_comparisons)
        self.tabs.addTab(tab, "Case Comparisons Overview")
        
        
    def set_case_folder(self):
        dialog = QFileDialog(self, '')
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_() == QDialog.Accepted:
            basepath = dialog.selectedFiles()[0]
            self.case_folder_path.setText(basepath)
        self.get_segmenters()
    
    def set_segmenter(self):
        paths1, paths2 = self.get_paths()
        self.fill_case_table()
    
    def get_paths(self):
        reader1 = self.combobox_select_segmenter .currentText()
        reader2 = self.combobox_select_segmenter2.currentText()
        if reader1=='Select a Reader' or reader2=='Select a Reader': return [], []
        case_folder_path = self.case_folder_path.text()
        paths1 = self.cases_df[self.cases_df['Reader']==reader1]['Path'].tolist()
        paths2 = self.cases_df[self.cases_df['Reader']==reader2]['Path'].tolist()
        return paths1, paths2
        
    def fill_case_table(self):
        self.reader1 = self.combobox_select_segmenter .currentText()
        self.reader2 = self.combobox_select_segmenter2.currentText()
        if self.reader1=='Select a Reader' or self.reader2=='Select a Reader': return [], []
        self.cc_table = CC_OverviewTable()
        self.cc_table.calculate(self.cases_df, self.reader1, self.reader2)
        self.caseTableView.setModel(self.cc_table.to_pyqt5_table_model())
        
    def get_segmenters(self):
        case_folder_path = self.case_folder_path.text()
        if not os.path.exists(case_folder_path): return
        try:
            paths   = [str(p) for p in Path(case_folder_path).glob('**/*.pickle')]
            cases   = [pickle.load(open(p,'rb')) for p in paths]
            self.cases_df = get_cases_table(cases, paths, False)
            readers = sorted(self.cases_df['Reader'].unique())
            self.combobox_select_segmenter .clear()
            self.combobox_select_segmenter2.clear()
            self.combobox_select_segmenter .addItems(['Select a Reader'] + readers)
            self.combobox_select_segmenter2.addItems(['Select a Reader'] + readers)
        except:
            pass
    

def main():
    app = QApplication(sys.argv)
    ex = Module_3()    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    






