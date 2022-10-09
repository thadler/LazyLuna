from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

import os
from pathlib import Path
import sys
import pandas
import traceback

from LazyLuna.Tables import Table

from catchConverter import catchConverter


class CVI42Converter_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Add tabs
        self.tabs.addTab(self.tab1, "CVI42Converter")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        
        # Actions
        present_cvi42_files_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Show CVI42 Files", self)
        present_cvi42_files_action.setStatusTip("Presents a Table with the found CVI42 workspaces.")
        present_cvi42_files_action.triggered.connect(self.present_cvi42_files)
        
        cvi42converter_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','wand--arrow.png')), "&Convert CVI42 Workspaces", self)
        cvi42converter_action.setStatusTip("Convert CVI42 Workspaces. Updates the table with success information for workspaces.")
        cvi42converter_action.triggered.connect(self.convert_cvi42workspaces)

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(present_cvi42_files_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(cvi42converter_action)
        self.toolbar.addWidget(b2)
        
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
        self.tree.setStatusTip('Find and select folders with CVI42 workspaces (file extension: ".cvi42ws" or ".dcm") to unpack.')
        self.tab1.layout.addWidget(self.tree, 1,0, 1,1)
        
        # Buttons below
        self.select_cviws_button = QPushButton('Present CVI42 Workspaces')
        self.tab1.layout.addWidget(self.select_cviws_button, 3,0)
        self.select_cviws_button.setStatusTip('Presents a Table with the found CVI42 workspaces.')
        self.select_cviws_button.clicked.connect(self.present_cvi42_files)
        
        self.with_figs = True
        self.with_figs_checkbox = QCheckBox("With figures for repaired contours?", self)
        self.tab1.layout.addWidget(self.with_figs_checkbox, 4,0)
        self.with_figs_checkbox.setStatusTip('If selected: presents contours that are difficult to convert.')
        self.with_figs_checkbox.stateChanged.connect(self.set_with_figs)
        
        self.convert_button = QPushButton('Convert CVI42 Workspaces')
        self.convert_button.setStatusTip('Convert CVI42 Workspaces. Updates the table with success information for workspaces.')
        self.tab1.layout.addWidget(self.convert_button, 5,0)
        self.convert_button.clicked.connect(self.convert_cvi42workspaces)
        
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
        
        
    def set_with_figs(self):
        self.with_figs = not self.with_figs
        
    def present_cvi42_files(self):
        try:
            items = [self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]
            self.folder_paths = list(set(items))
            cvi42_convertibles = []
            for path in self.folder_paths:
                path = Path(path)
                for p in path.glob("*.cvi42ws"): cvi42_convertibles.append(['--', str(p)])
                for p in path.glob("*.dcm"):     cvi42_convertibles.append(['--', str(p)])
            t  = Table()
            t.df = pandas.DataFrame(cvi42_convertibles, columns=['Converted', 'Paths to CVI42 Convertibles'])
            self.tableView.setModel(t.to_pyqt5_table_model())
            self.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        except Exception as e: print(traceback.format_exc())
    
    def convert_cvi42workspaces(self):
        try:
            c = catchConverter()
            cvi42_convertibles = []
            converted = []
            for path in self.folder_paths:
                path = Path(path)
                for p in path.glob("*.cvi42ws"): cvi42_convertibles.append(str(p))
                for p in path.glob("*.dcm"):     cvi42_convertibles.append(str(p))
            for p in cvi42_convertibles:
                try:
                    c.read(p); c.process(noFigs=self.with_figs); c.save(os.path.dirname(p))
                    converted.append(['Yes', p])
                except Exception as e: 
                    print(traceback.format_exc())
                    converted.append(['! FAILED !', p])    
            t  = Table()
            t.df = pandas.DataFrame(converted, columns=['Converted', 'Paths to CVI42 Convertibles'])
            self.tableView.setModel(t.to_pyqt5_table_model())
            self.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        except Exception as e: print(traceback.format_exc())
        

