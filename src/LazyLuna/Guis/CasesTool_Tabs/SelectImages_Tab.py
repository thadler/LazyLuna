from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QAbstractItemView, QComboBox, QToolButton, QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import os
from pathlib import Path
import sys
import pandas
import traceback
import pydicom

from LazyLuna.Tables import Table
from LazyLuna.Figures import Image_List_Presenter
from LazyLuna.loading_functions import *

from catch_converter.parse_contours import parse_cvi42ws


class SelectImages_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        # Add tabs
        self.tabs.addTab(self.tab1, "Image Selection")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        
        # initializing some variables
        self.by_seriesUID = False
        
        # Actions for Toolbar
        select_dcm_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','blue-folder-open-slide.png')), '&Select DCM Folder', self)
        select_dcm_folder_action.setStatusTip("Select Folder with Dicom files.")
        select_dcm_folder_action.triggered.connect(self.select_dcm_folder)
        
        load_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','blue-folder-open-table.png')), "&Load Table", self)
        load_action.setStatusTip("Load Table.")
        load_action.triggered.connect(self.load_table)
        
        
        # First Toolbar for Loading the Table
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,5)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(select_dcm_folder_action)
        self.toolbar.addWidget(b1)
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(load_action)
        self.toolbar.addWidget(b3)
        
        
        # Table View on the Left
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        self.tab1.layout.addWidget(self.tableView, 5, 0, 1,10)
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        #self.tab1.layout.setColumnStretch(5,20)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)
        
        
    def select_dcm_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.dicom_folder_path = dialog.selectedFiles()[0]
                self.dicom_folder_text.setText(os.path.basename(self.dicom_folder_path))
        except Exception as e: print(e)
        
        
    def load_table(self):
        try:
            if not self.is_dicom_folder_path_set(): return
            self.imgs_df   = dicom_images_to_table(self.dicom_folder_path)
            study_uid      = get_study_uid(self.dicom_folder_path)
            try:
                annos_path       = os.path.join(self.reader_folder_path, study_uid)
                annos_df         = annos_to_table(annos_path)
            except: annos_df     = None
            if annos_df is not None:
                self.information_df = present_nrimages_nr_annos_table(self.imgs_df, annos_df, by_series=self.by_seriesUID)
            else:
                self.information_df = present_nrimages_table(self.imgs_df, by_series=self.by_seriesUID)
            t  = Table()
            t.df = self.information_df
            self.tableView.setModel(t.to_pyqt5_table_model())
            for i in range(len(self.tableView.horizontalHeader())):
                self.tableView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            self.overriding_dict = dict()
        except Exception as e: print(e)

    def get_dcms(self):
        rows = []
        indexes = self.tableView.selectionModel().selectedRows()
        for index in sorted(indexes): rows.append(index.row())
        #print(self.imgs_df.columns); print(self.information_df.columns)
        key = 'series_uid' if 'series_uid' in self.information_df.columns else 'series_descr'
        values = self.information_df[key].iloc[rows].values
        image_paths = self.imgs_df[self.imgs_df[key].isin(values)]['dcm_path'].values
        #print('image_paths: '); print(image_paths)
        dcms = [pydicom.dcmread(p) for p in image_paths]
        # attempt at sorting
        try:
            sortable = sorted([[dcm, dcm.SliceLocation] for dcm in dcms], key=lambda x: x[1])
            dcms = [a[0] for a in sortable]
        except: pass
        try:
            sortable = sorted([[dcm, dcm.InstanceNumber] for dcm in dcms], key=lambda x: x[1])
            dcms = [a[0] for a in sortable]
        except: pass
        try:
            sortable = sorted([[dcm, dcm.SliceLocation, dcm.InstanceNumber] for dcm in dcms], key=lambda x: (x[1],x[2]))
            dcms = [a[0] for a in sortable]
        except: pass
        return dcms
    
    def is_dicom_folder_path_set(self):
        if hasattr(self, 'dicom_folder_path'): return True
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("You must select a folder containing dicom files first.")
        msg.setInformativeText("Use the above button to select such a folder.")
        retval = msg.exec_()
        return False
    
    def is_table_loaded(self):
        if hasattr(self, 'information_df'): return True
        msg = QMessageBox() # Information Message for User
        msg.setIcon(QMessageBox.Information)
        msg.setText("You must select and load a folder containing dicom files first.")
        msg.setInformativeText("Use the above button to select such a folder.")
        retval = msg.exec_()
        return False
    
        