from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir

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
        connect_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database--plus.png')), "&Connect to DB", self)
        connect_action.setStatusTip("Connect to Lazy Luna's Database or create a new one by selecting a folder.")
        connect_action.triggered.connect(self.connect_to_or_create_database)

        add_tab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Add Tab to DB", self)
        add_tab_action.setStatusTip("This adds a tab below (like HCM or CS). A select subset of cases can be added to this tab for easier navigation.")
        add_tab_action.triggered.connect(self.add_new_tab)
        
        create_new_cases_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Create Cases for DB", self)
        create_new_cases_action.setStatusTip("Opens another tab to convert Images and Annotations to Lazy Luna Cases which are added to the DB.")
        create_new_cases_action.triggered.connect(self.open_case_converter)
        
        
        ##################################
        ## ADD FUNCTION FOR SINGLE CASE ##
        ##################################

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(connect_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(add_tab_action)
        self.toolbar.addWidget(b2)
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(create_new_cases_action)
        self.toolbar.addWidget(b3)
        
        self.db_path_label  = QLabel('Database Path: ')
        self.db_path_text   = QLabel('')
        self.tab1.layout.addWidget(self.db_path_label, 1, 0, 1,1)
        self.tab1.layout.addWidget(self.db_path_text,  1, 1, 1,1)
        
        # Table View on the right
        # set table view
        self.tableView = QTableView()
        self.tab1.layout.addWidget(self.tableView, 2, 0, 3,3)
        
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
            
    def connect_to_or_create_database(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                path = dialog.selectedFiles()[0]
                self.dbpath = os.path.join(path, 'LL_Database.db')
                self.case_folder_path = os.path.join(path, 'LL_Cases')
                if not os.path.exists(self.case_folder_path): os.mkdir(self.case_folder_path)
            self.db_connection = sqlite3.connect(self.dbpath)
            # if not exists, instantiate database!
            self.execute_query('CREATE TABLE IF NOT EXISTS Cases (casename TEXT, readername TEXT, age INT, gender TEXT, weight FLOAT, height FLOAT, creation_date TEXT, study_uid TEXT, casepath TEXT, UNIQUE(readername, study_uid) ON CONFLICT REPLACE)')
            self.execute_query('CREATE TABLE IF NOT EXISTS Tabnames (tab TEXT, UNIQUE(tab) ON CONFLICT IGNORE)')
            self.execute_query('CREATE TABLE IF NOT EXISTS Case_to_Tab (study_uid TEXT, readername TEXT, tab TEXT,  UNIQUE(study_uid, readername, tab) ON CONFLICT REPLACE)')
            self.execute_query('INSERT INTO Tabnames (tab) VALUES ("ALL");')
            # after connecting to database set path...
            self.db_path_text.setText(self.dbpath)
            self.present_all_table()
        except Exception as e: print(e)
    
    def add_new_tab(self):
        if not self.has_dbconnection(): return
        tabname, ok = QInputDialog().getText(self, "New Tabname", "Tabname:", QLineEdit.Normal, 'Enter Text')
        if not (ok and tabname):             return
        print(self.tabname_repitition((tabname,)))
        if self.tabname_repitition(tabname): return
        self.execute_query('INSERT INTO Tabnames (tab) VALUES ("' + tabname + '");')
        # CONTINUE HERE: ADD THE TAB TO THE TABS
        #rows = self.db_connection.cursor().execute("SELECT * FROM Tabnames").fetchall()
        
        
    
    def open_case_converter(self):
        if not self.has_dbconnection(): return
        self.parent.add_caseconverter_tab(self.case_folder_path, self.dbpath, self.db_connection)
        
    
    def present_all_table(self):
        rows = self.db_connection.cursor().execute("SELECT * FROM Cases").fetchall()
        columns = ['Case Name','Reader','Age (Y)','Gender (M/F)','Weight (kg)','Height (m)','Creation Date','StudyUID','Path']
        t  = Table()
        t.df = pandas.DataFrame(rows, columns=columns)
        self.tableView.setModel(t.to_pyqt5_table_model())
        for i in range(len(columns)): self.tableView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
    
    
    def execute_query(self, query):
        try: 
            self.db_connection.cursor().execute(query)
            self.db_connection.commit()
        except Error as e: print(f"The error '{e}' occurred")
        
    def has_dbconnection(self):
        # Information Message for User
        print('In has db: ', hasattr(self, 'db_connection'))
        if hasattr(self, 'db_connection'): return True
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Missing DB Connection.")
        msg.setInformativeText("Select a database path first.")
        retval = msg.exec_()
        return False
    
    def tabname_repitition(self, tabname):
        # Information Message for User
        rows = self.db_connection.cursor().execute("SELECT * FROM Tabnames").fetchall()
        if tabname not in rows: return False
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Tabname already exists.")
        msg.setInformativeText("No repeated Tabnames")
        retval = msg.exec_()
        return True