from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QSize

import os
from pathlib import Path
import sys
import pandas
import traceback

from LazyLuna.Tables import Table

from catch_converter.parse_contours import parse_cvi42ws


class CVI42Converter_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
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
        select_cvi42_files_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Show CVI42 Files", self)
        select_cvi42_files_action.setStatusTip("Present Files to be Converted.")
        select_cvi42_files_action.triggered.connect(self.select_cvi42_files)
        
        cvi42converter_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','wand--arrow.png')), "&Convert CVI42 Workspaces", self)
        cvi42converter_action.setStatusTip("Convert CVI42Workspaces into LL Format.")
        cvi42converter_action.triggered.connect(self.convert_cvi42workspaces)

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar)
        self.toolbar.addWidget(QLabel("Select CVI42 Filepaths"))
        self.toolbar.addAction(select_cvi42_files_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Convert CVI42 Workspaces"))
        self.toolbar.addAction(cvi42converter_action)
        self.toolbar.addSeparator()
        
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
        
        self.tab1.layout.addWidget(self.tree, 0,0, 1,1)
        
        # Buttons below
        self.select_cviws_button = QPushButton('Select CVI42 Workspaces')
        self.tab1.layout.addWidget(self.select_cviws_button, 2,0)
        self.select_cviws_button.clicked.connect(self.select_cvi42_files)
        
        self.with_figs = False
        self.with_figs_checkbox = QCheckBox("With figures for failed contours?", self)
        self.tab1.layout.addWidget(self.with_figs_checkbox, 3,0)
        self.with_figs_checkbox.stateChanged.connect(self.set_with_figs)
        
        self.convert_button = QPushButton('Convert CVI42 Workspaces')
        self.tab1.layout.addWidget(self.convert_button, 4,0)
        self.convert_button.clicked.connect(self.convert_cvi42workspaces)
        
        # Table View on the right
        # set table view
        self.tableView = QTableView()
        self.tab1.layout.addWidget(self.tableView, 0, 2, 5,2)
        
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
        
    def select_cvi42_files(self):
        try:
            items = [self.fileSystemModel.filePath(index) for index in self.tree.selectedIndexes()]
            self.folder_paths = list(set(items))
            cvi42_convertibles = []
            for path in self.folder_paths:
                path = Path(path)
                for p in path.glob("*.dcm"):     cvi42_convertibles.append(['--', str(p)])
                for p in path.glob("*.cvi42ws"): cvi42_convertibles.append(['--', str(p)])
            t  = Table()
            t.df = pandas.DataFrame(cvi42_convertibles, columns=['Converted', 'Paths to CVI42 Convertibles'])
            self.tableView.setModel(t.to_pyqt5_table_model())
            self.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        except Exception as e: print(traceback.format_exc())
    
    def convert_cvi42workspaces(self):
        try:
            for path in self.folder_paths:
                parse_cvi42ws(path, path, process=True, debug=False, noFigs=(not self.with_figs))
        except Exception as e: print(traceback.format_exc())
        

