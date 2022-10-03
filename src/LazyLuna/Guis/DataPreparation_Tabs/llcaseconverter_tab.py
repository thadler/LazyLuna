from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

import os
from pathlib import Path
import sys
import pandas
import traceback

from LazyLuna.Tables import Table
from LazyLuna.loading_functions import *


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

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(select_bulk_dicoms_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(select_readers_action)
        self.toolbar.addWidget(b2)
        
        
        self.dicoms_folder_label  = QLabel('Dicom  Folder: ')
        self.dicoms_folder_text   = QLabel('')
        self.tab1.layout.addWidget(self.dicoms_folder_label,  1, 0, 1,1)
        self.tab1.layout.addWidget(self.dicoms_folder_text,   1, 1, 1,1)
        
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
        self.tab1.layout.addWidget(self.tree, 2,0, 1,2)
        
        
        # Table View on the right
        # set table view
        self.tableView = QTableView()
        self.tab1.layout.addWidget(self.tableView, 1, 2, 5,2)
        
        ###################
        ## TODO Populate ##
        ###################
        
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setColumnStretch(2, 5)
        
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
            items = [self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]
            self.folder_paths = list(set(items))
            print(self.folder_paths)
            
            bp_imgs  = self.dicoms_folder_path
            
            for annos_path in self.folder_paths:
                imgsanno_paths = get_imgs_and_annotation_paths(bp_imgs, annos_path)
                print(imgsanno_paths)
            """
            cvi42_convertibles = []
            for path in self.folder_paths:
                path = Path(path)
                for p in path.glob("*.cvi42ws"): cvi42_convertibles.append(['--', str(p)])
                for p in path.glob("*.dcm"):     cvi42_convertibles.append(['--', str(p)])
            t  = Table()
            t.df = pandas.DataFrame(cvi42_convertibles, columns=['Converted', 'Paths to CVI42 Convertibles'])
            self.tableView.setModel(t.to_pyqt5_table_model())
            self.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            """
        except Exception as e: print(traceback.format_exc())
            
            
    """
    def bulk_transform_cases(self):
        bp_imgs  = self.ui.bulk_case_images_folder_path
        bp_annos = self.case_reader_folder_path
        bp_cases = self.ui.cases_folder_path
        imgsanno_paths = get_imgs_and_annotation_paths(bp_imgs, bp_annos)
        cases = []
        views = [v[1]() for v in inspect.getmembers(Views, inspect.isclass) if issubclass(v[1], Views.View) if v[0]!='View']
        print('Views: ', views)
        for i, (imgp, annop) in enumerate(imgsanno_paths):
            print(i, imgp)
            self.ui.case_conversion_text_edit.append('Image and Annotation paths:/n'+imgp+'/n'+annop)
            if not os.path.exists(annop): 
                self.ui.case_conversion_text_edit.append('No annotations: '+annop)
                continue
            case = Case(imgp, annop, os.path.basename(imgp), os.path.basename(bp_annos))
            for v in views:
                try:
                    case = v.initialize_case(case)
                    self.ui.case_conversion_text_edit.append(str(v.__class__)+' worked for: '+case.case_name)
                except Exception as e:
                    self.ui.case_conversion_text_edit.append(str(v.__class__)+' FAILED for: '+case.case_name+',  '+str(e))
            case.store(bp_cases)
    """