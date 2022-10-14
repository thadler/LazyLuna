from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir, QSortFilterProxyModel

import os
from pathlib import Path
import sys
import copy
import inspect
import traceback

import pandas
import numpy as np

from LazyLuna.loading_functions import get_case_info
from LazyLuna.Tables import Table
from LazyLuna import Views

        
class CasesOverview_TabWidget(QWidget):
    def __init__(self, parent, cases, case_paths):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        
        
        # Setting some variables
        self.all_cases = cases
        self.cases = copy.deepcopy(cases)
        self.case_paths = case_paths
        
        
        # Actions
        statstab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Statistical Tab", self)
        statstab_action.setStatusTip("Connect to Lazy Luna's Database or create a new one by selecting a folder.")
        statstab_action.triggered.connect(self.stats_tab_selection)
        
        singletab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Single Case Tab", self)
        singletab_action.setStatusTip("Open Overview of all selected Cases.")
        singletab_action.triggered.connect(self.singletab_selection)
        
        

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        
        self.view_combo=QComboBox()
        self.view_combo.insertItems(1, ["Select View"]+self.get_view_names())
        self.view_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding);
        self.toolbar.addWidget(self.view_combo)
        self.view_combo.activated.connect(self.select_view)
        
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(statstab_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(singletab_action)
        self.toolbar.addWidget(b2)
        
        self.layout.addWidget(QHLine(), 1, 0, 1, 10)
        self.selected_view_lbl  = QLabel('View: ')
        self.selected_view_text = QLabel('None')
        self.nr_cases_lbl       = QLabel('Number of Cases: ')
        self.nr_cases_text      = QLabel(str(len(self.cases)))
        self.layout.addWidget(self.selected_view_lbl,  2, 0, 1,1)
        self.layout.addWidget(self.selected_view_text, 2, 1, 1,1)
        self.layout.addWidget(self.nr_cases_lbl,       2, 2, 1,1)
        self.layout.addWidget(self.nr_cases_text,      2, 3, 1,1)
        self.layout.addWidget(QHLine(), 3, 0, 1, 10)
        
        
        
        self.tableView_overview = QTableView(self)
        self.tableView_overview.setSelectionBehavior(QTableView.SelectRows)
        self.tableView_overview.setEditTriggers(QTableView.NoEditTriggers)
        #self.tableView_overview.doubleClicked.connect(self.manual_intervention)
        self.tableView_overview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addWidget(self.tableView_overview, 4, 0, 1,5)
        
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        #self.tableView.doubleClicked.connect(self.manual_intervention)
        self.tableView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.tableView, 5, 0, 20,10)
        
        self.calculate_table()
        self.calculate_table_overview()
        
        
        
    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]==vname][0]
        return view()
        
    def select_view(self):
        try:
            view_name = self.view_combo.currentText()
            v = self.get_view(view_name)
            self.selected_view_text.setText(view_name)
            new_cases = [copy.deepcopy(c) for c in self.all_cases]
            self.cases = []
            for c in new_cases:
                try: self.cases.append(v.customize_case(c))
                except Exception as e: print('Failed customize at: ', c.case_name)
            self.calculate_table()
            
        except Exception as e:
            print(traceback.format_exc())
        
    def stats_tab_selection(self):
        # currently simply add the clinical results tab # later add a user intervention with Tab selection
        try:
            view_name = self.view_combo.currentText()
            print(view_name)
            view = self.get_view(view_name)
            self.parent.add_clinical_results_tab(view, view_name, self.cases, self.case_paths)
        except Exception as e: print(traceback.format_exc())
        
        
    
    def singletab_selection(self):
        pass
    
    
    def calculate_table(self):
        try:
            rows = []
            for c, cp in zip(self.cases, self.case_paths):
                cols, row = get_case_info(c,cp)
                rows.append(row)
            t  = Table()
            t.df = pandas.DataFrame(rows, columns=cols)
            self.tableView.setModel(t.to_pyqt5_table_model())
        except Exception as e: print(traceback.format_exc())
    
    def calculate_table_overview(self):
        rows = []
        for c, cp in zip(self.cases, self.case_paths):
            cols, row = get_case_info(c,cp)
            row = row[2:-3]
            try: age = float(row[0])
            except: age = np.nan
            try: w = float(row[2])
            except: w = np.nan
            try: h = float(row[3])
            except: h = np.nan
            row = [age, row[1], w, h]
            rows.append(row)
        Fs, Ms = sum([1 for r in rows if r[2]=='F']), sum([1 for r in rows if r[2]=='M'])
        avgs = [[np.around(np.nanmean([r[0] for r in rows]), 2), str(Fs)+'/'+str(Ms), 
                 np.around(np.nanmean([r[2] for r in rows]), 2), np.around(np.nanmean([r[3] for r in rows]), 2)]]
        t  = Table(); t.df = pandas.DataFrame(avgs, columns=cols[2:-3])
        self.tableView_overview.setModel(t.to_pyqt5_table_model())
        
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]!='View']
        return v_names
    

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
