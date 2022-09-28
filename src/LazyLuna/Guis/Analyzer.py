from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QComboBox, QHeaderView, QLabel, QFileDialog, QDialog, QLineEdit
from PyQt5.QtGui import QIcon, QColor, QPalette
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
from LazyLuna.Mini_LL import Case_Comparison
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
        
        
    def get_paths_from_table(self):
        # if nothing selected, return all paths, else just the selected
        try:
            idxs = self.caseTableView.selectionModel().selectedIndexes()
            if len(idxs)==0: return self.get_paths()
            paths1, paths2 = [], []
            for idx in idxs:
                row, col = idx.row(), idx.column()
                #print(row)
                path1 = self.cc_table.df['Path1'].iloc[row]
                path2 = self.cc_table.df['Path2'].iloc[row]
                paths1.append(path1)
                paths2.append(path2)
            return paths1, paths2
        except Exception as e:
            print('Error in function get_paths_from_table: ', e)
        
    def load_case_comparisons(self):
        # get selected paths
        paths1, paths2 = self.get_paths_from_table()
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
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                basepath = dialog.selectedFiles()[0]
                self.case_folder_path.setText(basepath)
            print('Basepath: ', basepath)
            self.get_segmenters()
        except Exception as e:
            print(e)
    
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
        try:
            case_folder_path = self.case_folder_path.text()
            if not os.path.exists(case_folder_path): return
            paths   = [str(p) for p in Path(case_folder_path).glob('**/*.pickle')]
            cases   = [pickle.load(open(p,'rb')) for p in paths]
            self.cases_df = get_cases_table(cases, paths, False)
            readers = sorted(self.cases_df['Reader'].unique())
            self.combobox_select_segmenter .clear()
            self.combobox_select_segmenter2.clear()
            self.combobox_select_segmenter .addItems(['Select a Reader'] + readers)
            self.combobox_select_segmenter2.addItems(['Select a Reader'] + readers)
        except Exception as e:
            print('Get segmenters: ', e)
            pass
    

def main():
    app = QApplication(sys.argv)
    
    # Now use a palette to switch to dark colors:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(0,0,0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
    app.setPalette(palette)
    
    ex = Module_3()    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    






