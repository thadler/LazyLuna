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


class DcmLabeling_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Add tabs
        self.tabs.addTab(self.tab1, "Image Labeler")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        
        # Actions
        select_dcm_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Load Dicoms", self)
        select_dcm_folder_action.setStatusTip("Select Folder with Dicom files.")
        select_dcm_folder_action.triggered.connect(self.select_dcm_folder)
        
        select_reader_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Select Reader", self)
        select_reader_folder_action.setStatusTip("Select Folder with Annotation files.")
        select_reader_folder_action.triggered.connect(self.select_reader_folder)
        
        differentiate_series_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&By Series", self)
        select_reader_folder_action.setStatusTip("Select Checkmark to differentiate not by seriesDescription but by SeriesUID.")
        select_reader_folder_action.triggered.connect(self.set_by_seriesUID)
        
        suggest_labels_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Suggest Labels", self)
        suggest_labels_action.setStatusTip("Suggest LL Labels for Dicom series.")
        suggest_labels_action.triggered.connect(self.suggest_ll_labels)
        
        manual_select_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Manual Label Selection", self)
        manual_select_action.setStatusTip("Manually select LL Labels for Dicom series.")
        manual_select_action.triggered.connect(self.select_ll_labels)
        
        remove_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Remove Label Selection", self)
        remove_action.setStatusTip("Remove selected LL Labels for Dicom series.")
        remove_action.triggered.connect(self.remove_ll_labels)
        
        store_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Store Labels", self)
        store_action.setStatusTip("Store LL Labels for all Dicoms.")
        store_action.triggered.connect(self.store_ll_labels)
        
        

        # Toolbar
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(32, 32))
        self.layout.addWidget(self.toolbar)
        self.toolbar.addWidget(QLabel("Load Dicoms"))
        self.toolbar.addAction(select_dcm_folder_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Select Reader"))
        self.toolbar.addAction(select_reader_folder_action)
        self.toolbar.addSeparator()
        
        
        
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
        
        
    def select_dcm_folder(self):
        pass
    def select_reader_folder(self):
        pass
    def set_by_seriesUID(self):
        pass
    def suggest_ll_labels(self):
        pass
    def select_ll_labels(self):
        pass
    def remove_ll_labels(self):
        pass
    def store_ll_labels(self):
        pass
        

