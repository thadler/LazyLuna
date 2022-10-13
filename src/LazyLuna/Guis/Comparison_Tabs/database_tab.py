from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir, QSortFilterProxyModel

import sqlite3
from sqlite3 import Error

import os
from pathlib import Path
import sys
import pandas
import traceback
import inspect

from LazyLuna.Tables import Table
from LazyLuna import Views
from LazyLuna.loading_functions import *
from LazyLuna.Mini_LL import Case


class LL_Database_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Add tabs
        self.tabs.addTab(self.tab1, "Case Converter")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        
        # Actions
        connect_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Connect to DB", self)
        connect_action.setStatusTip("Connect to Lazy Luna's Database or create a new one by selecting a folder.")
        connect_action.triggered.connect(self.connect_to_or_create_database)
        
        open_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database.png')), "&Open Cases Overview", self)
        open_action.setStatusTip("Open Overview of all selected Cases.")
        open_action.triggered.connect(self.open_cases_overview)
        

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(connect_action)
        self.toolbar.addWidget(b1)
        self.combo=QComboBox()
        self.combo.insertItems(1,["Select Reader"])
        self.combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding);
        self.toolbar.addWidget(self.combo)
        self.combo.activated.connect(self.select_reader)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(open_action)
        self.toolbar.addWidget(b2)
        
        
        self.tab1.layout.addWidget(QHLine(), 1, 0, 1, 3)
        self.db_path_label  = QLabel('Database Path: ')
        self.db_path_text   = QLabel('')
        self.tab1.layout.addWidget(self.db_path_label, 2, 0, 1,1)
        self.tab1.layout.addWidget(self.db_path_text,  2, 1, 1,1)
        self.tab1.layout.addWidget(QHLine(), 3, 0, 1, 3)
        
        
        
        self.tableview_tabs = QTabWidget()
        self.tableview_tabs.setStatusTip("Table of cases belonging to tabs. Here the assortments of cases to tabs can be viewed.")
        self.tab1.layout.addWidget(self.tableview_tabs, 5,0, 1,3)
        self.tableview_tabs.currentChanged.connect(self.set_available_readers)
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setRowStretch(5, 5)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
        
    def set_available_readers(self):
        # use tabname for reader name extraction from database
        # add names to combobox
        print(self.tableview_tabs.currentIndex())
        tabname = self.tableview_tabs.tabText(self.tableview_tabs.currentIndex())
        print(tabname)
        q = 'SELECT DISTINCT Cases.readername FROM Cases INNER JOIN Case_to_Tab ON (Cases.study_uid=Case_to_Tab.study_uid AND Cases.readername=Case_to_Tab.readername AND Case_to_Tab.tab="' + tabname + '");'
        readernames = ['Select Reader']+[r[0] for r in self.db_connection.cursor().execute(q).fetchall()]
        self.combo.clear()
        self.combo.addItems(readernames)
        
        
    def select_reader(self):
        print('USE ME')
        pass
            
    def open_cases_overview(self):
        print('Opening all kinds of cases!')
        pass
        
    def connect_to_or_create_database(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted: path = dialog.selectedFiles()[0]
            ## USER warning and folder making...
            if not os.path.exists(os.path.join(path, 'LL_Cases')) or not os.path.exists(os.path.join(path, 'LL_Database.db')):
                msg = QMessageBox() # Information Message for User
                msg.setIcon(QMessageBox.Information)
                msg.setText("There is no DB in this Folder.")
                msg.setInformativeText("A Database must be instantiated before using this tool.")
                retval = msg.exec_()
                return # Return value for NO button
            self.case_folder_path = os.path.join(path, 'LL_Cases')
            self.dbpath = os.path.join(path, 'LL_Database.db')
            self.case_folder_path = os.path.join(path, 'LL_Cases')
            self.db_connection = sqlite3.connect(self.dbpath)
            # if not exists, instantiate database!
            self.execute_query('CREATE TABLE IF NOT EXISTS Cases (casename TEXT, readername TEXT, age INT, gender TEXT, weight FLOAT, height FLOAT, creation_date TEXT, study_uid TEXT, casepath TEXT, UNIQUE(readername, study_uid) ON CONFLICT REPLACE)')
            self.execute_query('CREATE TABLE IF NOT EXISTS Tabnames (tab TEXT, UNIQUE(tab) ON CONFLICT IGNORE)')
            self.execute_query('CREATE TABLE IF NOT EXISTS Case_to_Tab (study_uid TEXT, readername TEXT, tab TEXT,  UNIQUE(study_uid, readername, tab) ON CONFLICT REPLACE)')
            self.execute_query('INSERT INTO Tabnames (tab) VALUES ("ALL");')
            # after connecting to database set path...
            self.db_path_text.setText(self.dbpath)
            #self.present_all_table()
            self.update_tableview_tabs()
        except Exception as e: print(e)
    
    
    ### Perhaps useful to switch case location after inspection
    def add_new_tab(self):
        if not self.has_dbconnection(): return
        tabname, ok = QInputDialog().getText(self, "New Tabname", "Tabname:", QLineEdit.Normal, 'Enter Text')
        if not (ok and tabname):             return
        print(self.tabname_repitition((tabname,)))
        if self.tabname_repitition(tabname): return
        self.execute_query('INSERT INTO Tabnames (tab) VALUES ("' + tabname + '");')
        self.update_tableview_tabs()
    
        
    
    def update_tableview_tabs(self):
        if not self.has_dbconnection(): return
        tabnames = [name[0] for name in self.db_connection.cursor().execute('SELECT * FROM Tabnames').fetchall()]
        self.tabname_to_tableview = dict()
        self.tabname_to_table     = dict()
        self.tabname_to_proxy     = dict()
        try: 
            for i in range(len(self.tableview_tabs)): self.tableview_tabs.removeTab(0)
        except Exception as e: print(e); pass
        for tabname in tabnames:
            self.tabname_to_tableview[tabname] = QTableView()
            self.tabname_to_tableview[tabname].setSelectionBehavior(QTableView.SelectRows)
            self.tabname_to_tableview[tabname].setEditTriggers(QTableView.NoEditTriggers)
            self.tableview_tabs.addTab(self.tabname_to_tableview[tabname], tabname)
            self.present_table_view(tabname)
        
        
    def present_table_view(self, tabname):
        q = 'SELECT casename, Cases.readername, age, gender, weight, height, creation_date, Cases.study_uid, casepath FROM Cases INNER JOIN Case_to_Tab ON (Cases.study_uid=Case_to_Tab.study_uid AND Cases.readername=Case_to_Tab.readername AND Case_to_Tab.tab="' + tabname + '");'
        rows = self.db_connection.cursor().execute(q).fetchall()
        columns = ['Case Name','Reader','Age (Y)','Gender (M/F)','Weight (kg)','Height (m)','Creation Date','StudyUID','Path']
        t  = Table(); t.df = pandas.DataFrame(rows, columns=columns)
        self.tabname_to_tableview[tabname].setModel(t.to_pyqt5_table_model())
        self.tabname_to_table[tabname] = t
        self.tabname_to_tableview[tabname].resizeColumnsToContents()
        proxy_model = QSortFilterProxyModel() 
        proxy_model.setFilterKeyColumn(-1) # Search all columns.
        proxy_model.setSourceModel(t.to_pyqt5_table_model())
        self.tabname_to_proxy[tabname] = proxy_model
        self.tabname_to_tableview[tabname].setModel(self.tabname_to_proxy[tabname])
    
    def execute_query(self, query):
        try: self.db_connection.cursor().execute(query); self.db_connection.commit()
        except Error as e: print(f"The error '{e}' occurred")
        
    def has_dbconnection(self):
        # Information Message for User
        if hasattr(self, 'db_connection'): return True
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Missing DB Connection.")
        msg.setInformativeText("Select a database path first.")
        retval = msg.exec_()
        return False
    

        
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
