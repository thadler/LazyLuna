from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

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


class LL_CaseConverter_TabWidget(QWidget):
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
        select_bulk_dicoms_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Select Bulk Dicoms Folder", self)
        select_bulk_dicoms_action.setStatusTip("This is for bulk conversion. Select the folder in which one or several Dicom cases are contained.")
        select_bulk_dicoms_action.triggered.connect(self.select_dicoms_folder)
        
        select_readers_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Select Reader Folders", self)
        select_readers_action.setStatusTip("Click all folders with Annotations you want connected to the Dicom Images.")
        select_readers_action.triggered.connect(self.present_reader_folders)
        
        convert_llcases_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Convert to LL Cases", self)
        convert_llcases_action.setStatusTip("Converts Images and Annotations to Lazy Luna Cases.")
        convert_llcases_action.triggered.connect(self.convert_cases)
        
        case_path_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Select Case Path", self)
        case_path_action.setStatusTip("Select the folder in which all cases are contained.")
        case_path_action.triggered.connect(self.select_case_path)
        
        ##################################
        ## ADD FUNCTION FOR SINGLE CASE ##
        ##################################

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,10)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(select_bulk_dicoms_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(select_readers_action)
        self.toolbar.addWidget(b2)
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(convert_llcases_action)
        self.toolbar.addWidget(b3)
        b4 = QToolButton(); b4.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b4.setFont(QFont('', fontsize))
        b4.setDefaultAction(case_path_action)
        self.toolbar.addWidget(b4)
        
        
        self.dicoms_folder_label  = QLabel('Dicom  Folder: ')
        self.dicoms_folder_text   = QLabel('')
        self.tab1.layout.addWidget(self.dicoms_folder_label,  1, 0, 1,1)
        self.tab1.layout.addWidget(self.dicoms_folder_text,   2, 0, 1,1)
        
        # File System View
        self.fileSystemModel = QFileSystemModel()
        self.fileSystemModel.setRootPath('')
        self.tree = QTreeView()
        self.tree.setModel(self.fileSystemModel)
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.setWindowTitle("Dir View")
        self.tree.resize(480, 320)
        self.tree.setSelectionMode(self.tree.ExtendedSelection)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().resizeSection(0, 200)
        self.tree.setDragEnabled(True)
        self.tree.setStatusTip('Find and select reader folders you wish to connect to the images.')
        self.tab1.layout.addWidget(self.tree, 3,0, 1,2)
        
        
        # Table View on the right
        # set table view
        self.tableView = QTableView()
        self.tab1.layout.addWidget(self.tableView, 1, 2, 5,8)
        
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
        
    def select_dicoms_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.dicoms_folder_path = dialog.selectedFiles()[0]
                self.dicoms_folder_text.setText(self.dicoms_folder_path)
        except Exception as e: print(e)
            
    
    def present_reader_folders(self):
        try:
            self.reader_paths = list(set([self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]))
            imganno_paths = []
            for reader_path in self.reader_paths:
                try: 
                    ia_paths = get_imgs_and_annotation_paths(self.dicoms_folder_path, reader_path)
                    ia_paths = [['--', os.path.basename(ia[0]), os.path.basename(reader_path), ia[1]] for ia in ia_paths]
                    imganno_paths.extend(ia_paths)
                except Exception as e: print(e); pass
            self.imganno_paths = pandas.DataFrame(imganno_paths, columns=['Converted', 'Casename', 'Readername', 'Annotation Path'])
            t = Table(); t.df = self.imganno_paths
            self.tableView.setModel(t.to_pyqt5_table_model())
            for i in range(len(self.tableView.horizontalHeader())):
                self.tableView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        except Exception as e: print(traceback.format_exc())
            
    def select_case_path(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.case_folder_path = dialog.selectedFiles()[0]
        except Exception as e: print(e)
            
    #####################
    ## Make to QTHREAD ##
    #####################
    def convert_cases(self):
        
        ##############################
        ## warning window for:      ##
        ##   - case path not set    ##
        ##   - dicom path not set   ##
        ##   - readers no selected  ##
        ##############################
        
        if not hasattr(self, 'case_folder_path')
        
        # Information Message for User
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Fill with Information on casefolderpath and stuff.")
        msg.setInformativeText("Are you sure you want to succeed?")
        msg.setWindowTitle("Storage Warning")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval==65536: return # Return value for NO button
        
        try: 
            views = [v[1]() for v in inspect.getmembers(Views, inspect.isclass) if issubclass(v[1], Views.View) if v[0]!='View']
            self.reader_paths = list(set([self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]))
            imganno_paths = []
            for reader_path in self.reader_paths:
                try: 
                    ia_paths = get_imgs_and_annotation_paths(self.dicoms_folder_path, reader_path)
                    ia_paths = [['--', os.path.basename(ia[0]), ia[0], os.path.basename(reader_path), ia[1]] for ia in ia_paths]
                    imganno_paths.extend(ia_paths)
                except Exception as e: print(e); pass
            conversion_worked = []
            for i, (_, casename, imgp, readername, annop) in enumerate(imganno_paths):
                try:
                    print(i , ' of ', len(imganno_paths), ': ', imgp, annop)
                    if not os.path.exists(annop): 
                        print('No annotations available: ', annop)
                        conversion_worked.append(['! Failed !', casename, readername, annop])
                        continue
                    case = Case(imgp, annop, casename, readername)
                    for v in views:
                        try:
                            case = v.initialize_case(case)
                            print(str(v.__class__)+' worked for: '+case.case_name)
                        except Exception as e:
                            print(str(v.__class__)+' FAILED for: '+case.case_name+',  '+str(e))
                    case.store(self.case_folder_path)
                    conversion_worked.append(['Yes', casename, readername, annop])
                except Exception as e: 
                    conversion_worked.append(['! Failed !', casename, readername, annop])
                    print(e); pass
            print(conversion_worked)
            self.imganno_paths = pandas.DataFrame(conversion_worked, columns=['Converted', 'Casename', 'Readername', 'Annotation Path'])
            t = Table(); t.df = self.imganno_paths
            self.tableView.setModel(t.to_pyqt5_table_model())
        except Exception as e: print(e); pass