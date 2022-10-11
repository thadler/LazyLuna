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

        add_tab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database--plus.png')), "&Add Tab to DB", self)
        add_tab_action.setStatusTip("This adds a tab below (like HCM or CS). A select subset of cases can be added to this tab for easier navigation.")
        add_tab_action.triggered.connect(self.add_new_tab)
        
        remove_tab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database--minus.png')), "&Remove Tab from DB", self)
        remove_tab_action.setStatusTip("Select a Tabname and remove it from the database.")
        remove_tab_action.triggered.connect(self.remove_tab)
        
        add_cases_to_tab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','tag--plus.png')), "&Add Cases to Tab", self)
        add_cases_to_tab_action.setStatusTip("Take selected cases from selected tab and add them to another.")
        add_cases_to_tab_action.triggered.connect(self.add_cases_to_tab)
        
        remove_cases_from_tab_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','tag--minus.png')), "&Remove Cases from Tab", self)
        remove_cases_from_tab_action.setStatusTip("Remove the Cases from Current Tab.")
        remove_cases_from_tab_action.triggered.connect(self.remove_cases_from_tab)
        
        import_new_cases_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','database-import.png')), "&Import Cases to DB", self)
        import_new_cases_action.setStatusTip("Opens another tab to import Lazy Luna Cases or convert Images and Annotations to Lazy Luna Cases which are added to the DB.")
        import_new_cases_action.triggered.connect(self.open_case_converter)

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(connect_action)
        self.toolbar.addWidget(b1)
        self.toolbar.addSeparator()
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(import_new_cases_action)
        self.toolbar.addWidget(b2)
        
        self.tab1.layout.addWidget(QHLine(), 1, 0, 1, 3)
        self.db_path_label  = QLabel('Database Path: ')
        self.db_path_text   = QLabel('')
        self.tab1.layout.addWidget(self.db_path_label, 2, 0, 1,1)
        self.tab1.layout.addWidget(self.db_path_text,  2, 1, 1,1)
        self.tab1.layout.addWidget(QHLine(), 3, 0, 1, 3)
        
        self.toolbar2 = QToolBar("My main toolbar")
        self.toolbar2.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar2, 4,0, 1,3)
        
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(add_tab_action)
        self.toolbar2.addWidget(b3)
        b4 = QToolButton(); b4.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b4.setFont(QFont('', fontsize))
        b4.setDefaultAction(remove_tab_action)
        self.toolbar2.addWidget(b4)
        b5 = QToolButton(); b5.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b5.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b5.setFont(QFont('', fontsize))
        b5.setDefaultAction(add_cases_to_tab_action)
        self.toolbar2.addWidget(b5)
        b6 = QToolButton(); b6.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b6.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b6.setFont(QFont('', fontsize))
        b6.setDefaultAction(remove_cases_from_tab_action)
        self.toolbar2.addWidget(b6)
        
        self.tableview_tabs = QTabWidget()
        self.tableview_tabs.setStatusTip("Table of cases belonging to tabs. Here the assortments of cases to tabs can be viewed.")
        self.tab1.layout.addWidget(self.tableview_tabs, 5,0, 1,3)
        
        # add searchbar
        self.searchbar = QLineEdit()
        self.searchbar.setFixedWidth(200); self.searchbar.setFixedHeight(20)
        self.searchbar.setStatusTip("Use the searchbar to search for individual cases or subsets of cases.")
        self.tab1.layout.addWidget(self.searchbar, 6,0, 1,1)
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setRowStretch(5, 5)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
            
    def connect_to_or_create_database(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted: path = dialog.selectedFiles()[0]
            ## USER warning and folder making...
            if not os.path.exists(os.path.join(path, 'LL_Cases')):
                msg = QMessageBox() # Information Message for User
                msg.setIcon(QMessageBox.Information)
                msg.setText("There is no DB in this Folder.")
                msg.setInformativeText("Are you sure you want to create a Database here?")
                msg.setWindowTitle("Non-Reversable Action Warning")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                retval = msg.exec_()
                if retval==65536: return # Return value for NO button
                self.case_folder_path = os.path.join(path, 'LL_Cases')
                os.mkdir(self.case_folder_path)
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
    
    def add_new_tab(self):
        if not self.has_dbconnection(): return
        tabname, ok = QInputDialog().getText(self, "New Tabname", "Tabname:", QLineEdit.Normal, 'Enter Text')
        if not (ok and tabname):             return
        print(self.tabname_repitition((tabname,)))
        if self.tabname_repitition(tabname): return
        self.execute_query('INSERT INTO Tabnames (tab) VALUES ("' + tabname + '");')
        self.update_tableview_tabs()
    
    def open_case_converter(self):
        if not self.has_dbconnection(): return
        self.parent.add_caseconverter_tab(self.case_folder_path, self.dbpath, self.db_connection)
    
    def remove_tab(self):
        if not self.has_dbconnection(): return
        try: self.popup1 = RemoveTabPopup(self); self.popup1.show()
        except Exception as e: print(e); pass
        self.update_tableview_tabs()
    
    def add_cases_to_tab(self):
        if not self.has_dbconnection(): return
        tabname = self.tableview_tabs.tabText(self.tableview_tabs.currentIndex())
        rows = [i.row() for i in self.tableview_tabs.currentWidget().selectionModel().selectedRows()]
        proxy = self.tabname_to_proxy[tabname]
        insertion_keys = [[proxy.index(row,7).data(), proxy.index(row,1).data()] for row in rows]
        try: self.popup1 = AddCasesToTabPopup(self, insertion_keys); self.popup1.show()
        except Exception as e: print(e); pass
        self.update_tableview_tabs()
    
    def remove_cases_from_tab(self):
        if not self.has_dbconnection(): return
        tabname = self.tableview_tabs.tabText(self.tableview_tabs.currentIndex())
        rows = [i.row() for i in self.tableview_tabs.currentWidget().selectionModel().selectedRows()]
        df = self.tabname_to_table[tabname].df
        removal_keys = [df[['StudyUID', 'Reader']].iloc[row].tolist() for row in rows]
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("You are removing Cases from this tab.")
        msg.setInformativeText("Are you sure you want to procede?")
        msg.setWindowTitle("Non-Reversable Action Warning")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval==65536: return # Return value for NO button
        if tabname=='ALL':
            # remove from all
            for suid, readername in removal_keys:
                self.execute_query('DELETE FROM Case_to_Tab WHERE (study_uid="'+suid+'" AND readername="' + readername + '");')
                self.execute_query('DELETE FROM Cases       WHERE (study_uid="'+suid+'" AND readername="' + readername + '");')
        else:
            for suid, readername in removal_keys:
                q = 'DELETE FROM Case_to_Tab WHERE (study_uid="'+suid+'" AND readername="'+readername+'" AND tab="'+tabname+'");'
                self.execute_query(q)
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
        self.searchbar.textChanged.connect(self.tabname_to_proxy[tabname].setFilterFixedString)
    
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
    
    def tabname_repitition(self, tabname):
        # Information Message for User
        rows = self.db_connection.cursor().execute('SELECT * FROM Tabnames').fetchall()
        if tabname not in rows: return False
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Tabname already exists.")
        msg.setInformativeText("Repeated Tabnames are forbidden. Action prohibited.")
        retval = msg.exec_()
        return True


class RemoveTabPopup(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Tab Removal')
        self.setGeometry(800, 200, 300, 120)
        self.layout = QVBoxLayout(self)
        self.initUI()

    def initUI(self):
        self.choose_tag = QComboBox()
        self.choose_tag.setFixedHeight(50)
        tabnames = [name[0] for name in self.parent.db_connection.cursor().execute("SELECT * FROM Tabnames").fetchall()]
        self.choose_tag.addItems(['Select Tab'] + [t for t in tabnames if t!='ALL'])
        self.choose_tag.activated.connect(self.remove_tab)
        self.layout.addWidget(self.choose_tag)
        
    def remove_tab(self):
        tabname = self.choose_tag.currentText()
        if tabname=='Select Tab': return
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("Removing Tab below from Database.")
        msg.setInformativeText("Are you sure you want to procede?")
        msg.setWindowTitle("Non-Reversable Action Warning")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval==65536: return # Return value for NO button
        self.parent.execute_query('DELETE FROM Tabnames WHERE tab="' + tabname + '";')    # Remove tab name from Tabnames
        self.parent.execute_query('DELETE FROM Case_to_Tab WHERE tab="' + tabname + '";') # Remove all connections in Case_to_Tab
        self.parent.update_tableview_tabs()
        self.close()
        
        
class AddCasesToTabPopup(QWidget):
    def __init__(self, parent, insertion_keys):
        super().__init__()
        self.parent = parent
        self.insertion_keys = insertion_keys
        self.setWindowTitle('Add Selected Cases To another Tab')
        self.setGeometry(800, 200, 300, 120)
        self.layout = QVBoxLayout(self)
        self.initUI()

    def initUI(self):
        self.choose_tag = QComboBox()
        self.choose_tag.setFixedHeight(50)
        tabnames = [name[0] for name in self.parent.db_connection.cursor().execute("SELECT * FROM Tabnames").fetchall()]
        self.choose_tag.addItems(['Select Tab'] + tabnames)
        self.choose_tag.activated.connect(self.add_to_tab)
        self.layout.addWidget(self.choose_tag)
        
    def add_to_tab(self):
        tabname = self.choose_tag.currentText()
        if tabname=='Select Tab': return
        for (suid, readername) in self.insertion_keys:
            q = 'INSERT OR REPLACE INTO Case_to_Tab (study_uid, readername, tab) VALUES'
            q += '("' + suid + '", "' + readername + '", "' + tabname + '");'
            self.parent.execute_query(q)
        self.parent.update_tableview_tabs()
        self.close()
        
        
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
