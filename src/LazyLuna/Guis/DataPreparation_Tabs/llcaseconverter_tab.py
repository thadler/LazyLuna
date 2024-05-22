from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QMessageBox
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
from LazyLuna.Containers import Case


class LL_CaseConverter_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        self.ui_init()
    
    def ui_init(self):
        # Actions
        select_bulk_dicoms_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','folder-open-image.png')), "&Select Bulk Dicoms Folder", self)
        select_bulk_dicoms_action.setStatusTip("This is for bulk conversion. Select the folder in which one or several Dicom cases are contained.")
        select_bulk_dicoms_action.triggered.connect(self.select_dicoms_folder)
        
        select_readers_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','eye.png')), "&Present Reader Folders", self)
        select_readers_action.setStatusTip("In folder-tree on the left, click all folders with Annotations you want connected to the Dicom Images.")
        select_readers_action.triggered.connect(self.present_reader_folders)
        
        convert_llcases_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','wand--arrow.png')), "&Convert to LL Cases", self)
        convert_llcases_action.setStatusTip("Converts Images and Annotations to Lazy Luna Cases.")
        convert_llcases_action.triggered.connect(self.convert_cases)
        
        
        select_casefolder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','folder-open-image.png')), "&Select Cases Folder", self)
        select_casefolder_action.setStatusTip("This is for bulk conversion. Select the folder where all relevant cases are to be stored.")
        select_casefolder_action.triggered.connect(self.select_cases_folder)
        
        
        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar, 0,0, 1,10)
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
        b4.setDefaultAction(select_casefolder_action)
        self.toolbar.addWidget(b4)
        
        
        self.dicoms_folder_label  = QLabel('Dicom  Folder: ')
        self.dicoms_folder_text   = QLabel('')
        self.case_folder_label    = QLabel('Cases  Folder: ')
        self.case_folder_text     = QLabel('')
        self.layout.addWidget(self.dicoms_folder_label,  1, 0, 1,1)
        self.layout.addWidget(self.dicoms_folder_text,   2, 0, 1,1)
        self.layout.addWidget(self.case_folder_label,    3, 0, 1,1)
        self.layout.addWidget(self.case_folder_text,     4, 0, 1,1)
        
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
        self.layout.addWidget(self.tree, 5,0, 1,2)
        
        
        # Table View on the right
        # set table view
        self.tableView = QTableView()
        self.layout.addWidget(self.tableView, 1, 2, 5,8)
        
        # set layout
        self.setLayout(self.layout)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        #self.layout.addWidget(self.tabs)
        
        
    
    def select_cases_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.case_folder_path = dialog.selectedFiles()[0]
                self.case_folder_text.setText(self.case_folder_path)
        except Exception as e: print(traceback.format_exc())
        
    def select_dicoms_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.dicoms_folder_path = dialog.selectedFiles()[0]
                self.dicoms_folder_text.setText(self.dicoms_folder_path)
        except Exception as e: print(traceback.format_exc())
            
    
    def present_reader_folders(self):
        try:
            self.reader_paths = list(set([self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]))
            if not self.has_selected_reader_folders(): return
            imganno_paths = []
            for reader_path in self.reader_paths:
                try: 
                    ia_paths = get_imgs_and_annotation_paths(self.dicoms_folder_path, reader_path)
                    ia_paths = [['--', os.path.basename(ia[0]), os.path.basename(reader_path), ia[1]] for ia in ia_paths]
                    imganno_paths.extend(ia_paths)
                except Exception as e: print(traceback.format_exc()); pass
            self.imganno_paths = pandas.DataFrame(imganno_paths, columns=['Converted', 'Casename', 'Readername', 'Annotation Path'])
            t = Table(); t.df = self.imganno_paths
            self.tableView.setModel(t.to_pyqt5_table_model())
            for i in range(len(self.tableView.horizontalHeader())):
                self.tableView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        except Exception as e: print(traceback.format_exc())
            
    def convert_cases(self):
        if not self.has_dicom_folder(): return
        if not self.has_selected_reader_folders(): return
        if not self.has_cases_folder(): return
        
        # Information Message for User
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("You are about to start a sequence of case conversions.")
        msg.setInformativeText("This can take some time. Are you sure you want to procede?")
        msg.setWindowTitle("Grab a coffee - Warning")
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
                except Exception as e: print(traceback.format_exc()); pass
            conversion_worked = []
            case_cpath_list_for_db = []
            for i, (_, casename, imgp, readername, annop) in enumerate(imganno_paths):
                try:
                    #print(i , ' of ', len(imganno_paths), ': ', imgp, annop)
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
                            print(str(v.__class__)+' FAILED for: '+case.case_name+',  '+str(e))#str(traceback.format_exc()))
                    cp = case.store(self.case_folder_path)
                    conversion_worked.append(['Yes', casename, readername, annop])
                    case_cpath_list_for_db.append([case, cp])
                except Exception as e: 
                    conversion_worked.append(['! Failed !', casename, readername, annop])
                    print(traceback.format_exc()); pass
            self.imganno_paths = pandas.DataFrame(conversion_worked, columns=['Converted', 'Casename', 'Readername', 'Annotation Path'])
            t = Table(); t.df = self.imganno_paths
            self.tableView.setModel(t.to_pyqt5_table_model())
            for c, cp in case_cpath_list_for_db:
                try:
                    col, row = get_case_info(c, cp)
                    self.insert_case(c, cp)
                except Exception as e: print(traceback.format_exc()); continue
        except Exception as e: print(traceback.format_exc()); pass
        
    def import_cases(self):
        try:
            import_cases_path = None
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                import_cases_path = dialog.selectedFiles()[0]
            if import_cases_path is None: return
            paths = [str(p) for p in Path(import_cases_path).glob('**/*.pickle')]
            for p in paths: c = pickle.load(open(p,'rb')); self.insert_case(c, p)
            self.parent.tab.update_tableview_tabs()
        except Exception as e: print(traceback.format_exc()); pass
        

            
    def has_selected_reader_folders(self):
        if len(list(set([self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()])))!=0: return True
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("Select reader folders with annotations first.")
        msg.setInformativeText("Open the folder tree on the left and select folders that contain annotations of the cases.")
        retval = msg.exec_()
        return False
    
    def has_dicom_folder(self):
        if hasattr(self, 'dicoms_folder_path'): return True
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("You must select a folder with patient folders containing dicom files first.")
        msg.setInformativeText("Use the above button to select such a folder.")
        retval = msg.exec_()
        return False
    
    def has_cases_folder(self):
        if hasattr(self, 'case_folder_path'): return True
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("You must select a folder to which the cases should be loaded first.")
        msg.setInformativeText("Use the above button to select such a folder.")
        retval = msg.exec_()
        return False
        
        
    