from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir, QSortFilterProxyModel

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

        
class ClinicalResultsTable_TabWidget(QWidget):
    def __init__(self, parent, view, viewname, cases, case_paths):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        
        # Setting some variables
        self.view = copy.deepcopy(view)
        self.viewname = viewname
        self.cases = copy.deepcopy(cases)
        self.case_paths = copy.deepcopy(case_paths)
        
        # Actions
        inspectcases_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Open Cases", self)
        inspectcases_action.setStatusTip("Allows for a visual inspection of selected cases.")
        inspectcases_action.triggered.connect(self.open_cases)
        
        store_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Store Table", self)
        store_action.setStatusTip("Store the table.")
        store_action.triggered.connect(self.store_table)
        
        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(store_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(inspectcases_action)
        self.toolbar.addWidget(b2)
        
        self.layout.addWidget(QHLine(), 1, 0, 1, 10)
        self.selected_view_lbl  = QLabel('View: ')
        self.selected_view_text = QLabel(viewname)
        self.nr_cases_lbl       = QLabel('Number of Cases: ')
        self.nr_cases_text      = QLabel(str(len(self.cases)))
        self.layout.addWidget(self.selected_view_lbl,  2, 0, 1,1)
        self.layout.addWidget(self.selected_view_text, 2, 1, 1,1)
        self.layout.addWidget(self.nr_cases_lbl,       2, 2, 1,1)
        self.layout.addWidget(self.nr_cases_text,      2, 3, 1,1)
        self.layout.addWidget(QHLine(), 3, 0, 1, 10)
        
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        #self.tableView.doubleClicked.connect(self.manual_intervention)
        self.tableView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.tableView, 4, 0, 20,10)
        
        self.calculate_table()
        
        
        
    def store_table(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted: path = dialog.selectedFiles()[0]
            tablepath = os.path.join(path, self.viewname+'_Clinical_Results.csv')
            self.t.store(tablepath)
        except Exception as e: print(e)
    
        
    def open_cases(self):
        rows = [r.row() for r in self.tableView.selectionModel().selectedRows()]
        for r in rows:
            self.parent.add_single_case_tab(self.view, self.viewname, self.cases[r], self.case_paths[r])
    
    def calculate_table(self):
        rows = []
        columns = ['Casename', 'Readername']+[cr.name for cr in self.cases[0].crs]
        for c, cp in zip(self.cases, self.case_paths):
            row = [c.case_name, c.reader_name]
            for cr in c.crs: 
                try: row.append(cr.get_val(string=True))
                except Exception as e: print(e); row.append(np.nan)
            rows.append(row)
        self.t  = Table()
        self.t.df = pandas.DataFrame(rows, columns=columns)
        self.tableView.setModel(self.t.to_pyqt5_table_model())
    
        
    

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
