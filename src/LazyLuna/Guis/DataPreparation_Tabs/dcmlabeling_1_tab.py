from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QAbstractItemView, QComboBox, QToolButton, QSizePolicy
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize
#from PyQt5.Qt.Qt.Qt import ClickFocus


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


class DcmLabeling_1_TabWidget(QWidget):
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
        
        # initializing some variables
        self.by_seriesUID = False
        
        # Actions for Toolbar
        select_dcm_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','folder-open-image.png')), '&Select Folder', self)
        select_dcm_folder_action.setStatusTip("Select Folder with Dicom files.")
        select_dcm_folder_action.triggered.connect(self.select_dcm_folder)
        
        load_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Load Table", self)
        load_action.setStatusTip("Load Table.")
        load_action.triggered.connect(self.load_table)
        
        select_reader_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','notebook.png')), "&Select Reader", self)
        select_reader_folder_action.setStatusTip("Select Folder with Annotation files.")
        select_reader_folder_action.triggered.connect(self.select_reader_folder)
        
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
        
        
        # First Toolbar for Loading the Table
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar)
        
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', 15))
        b1.setDefaultAction(select_dcm_folder_action)
        self.toolbar.addWidget(b1)
        
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', 15))
        b2.setDefaultAction(select_reader_folder_action)
        self.toolbar.addWidget(b2)
        
        #self.toolbar.addSeparator()
        #self.toolbar.addWidget(QLabel("Select Reader"))
        #self.toolbar.addAction(select_reader_folder_action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("By Series"))
        self.toolbar.addSeparator()
        self.cb = QCheckBox()
        self.cb.stateChanged.connect(self.set_by_seriesUID)
        self.toolbar.addWidget(self.cb)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Load Table"))
        self.toolbar.addAction(load_action)
        self.toolbar.addSeparator(); self.toolbar.addSeparator(); self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Store Labels"))
        self.toolbar.addAction(store_action)
        self.toolbar.addSeparator()
        
        
        
        # Second Toolbar for Table Manipulation
        self.toolbar2 = QToolBar("My main toolbar")
        self.toolbar2.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar2)
        self.toolbar2.addWidget(QLabel("Suggest Labels"))
        self.toolbar2.addAction(suggest_labels_action)
        self.toolbar2.addSeparator()
        self.toolbar2.addWidget(QLabel("Manual Label Selection"))
        self.toolbar2.addAction(manual_select_action)
        self.toolbar2.addSeparator()
        self.toolbar2.addWidget(QLabel("Remove Label"))
        self.toolbar2.addAction(remove_action)
        self.toolbar2.addSeparator()
        
        # User Info on Image and Reader Folder
        self.dicom_folder_label  = QLabel('Dicom  Folder: ')
        self.dicom_folder_text   = QLabel('')
        self.reader_folder_label = QLabel('Reader Folder: ')
        self.reader_folder_text  = QLabel('')
        self.tab1.layout.addWidget(self.dicom_folder_label,  0, 0, 1,1)
        self.tab1.layout.addWidget(self.dicom_folder_text,   0, 1, 1,1)
        self.tab1.layout.addWidget(self.reader_folder_label, 0, 2, 1,1)
        self.tab1.layout.addWidget(self.reader_folder_text,  0, 3, 1,1)
        
        # Table View on the Left
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        self.tableView.clicked.connect(self.present_series_in_figure)
        self.tableView.doubleClicked.connect(self.select_ll_labels)
        self.tab1.layout.addWidget(self.tableView, 1, 0, 1,5)
        
        # set layout
        self.tab1.setLayout(self.tab1.layout)
        self.tab1.layout.setColumnStretch(4,20)
        
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
        
    def select_reader_folder(self):
        try:
            dialog = QFileDialog(self, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                self.reader_folder_path = dialog.selectedFiles()[0]
                self.reader_folder_text.setText(os.path.basename(self.reader_folder_path))
        except Exception as e: print(e)
        
    def set_by_seriesUID(self):
        self.by_seriesUID = not self.by_seriesUID
        
    def load_table(self):
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
    
    def store_ll_labels(self):
        ##################################################################
        ## Add a window to inform the user and give the option to abort ##
        ##################################################################
        self.store_LL_tags()
        
    def suggest_ll_labels(self):
        print('D')
        
    def select_ll_labels(self, item):
        self.popup1 = ManualInterventionPopup(self)
        self.popup1.show()
        
    def remove_ll_labels(self): 
        self.set_LL_tags('Lazy Luna: None')
        

    def get_dcms(self):
        rows = []
        indexes = self.tableView.selectionModel().selectedRows()
        for index in sorted(indexes): rows.append(index.row())
        print(self.imgs_df.columns); print(self.information_df.columns) # TODO Remove
        key = 'series_uid' if 'series_uid' in self.information_df.columns else 'series_descr'
        values = self.information_df[key].iloc[rows].values
        image_paths = self.imgs_df[self.imgs_df[key].isin(values)]['dcm_path'].values
        print('image_paths: '); print(image_paths) # TODO Remove
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
                                   
    
    
    def present_series_in_figure(self):
        print('Presenting in Figure')
        # Add sorted images to Figure
        # Present first image
        dcms = self.get_dcms()
    
    def set_LL_tags(self, name):
        idxs  = self.tableView.selectionModel().selectedIndexes()
        for idx in sorted(idxs):
            self.information_df.at[idx.row(), 'Change LL_tag'] = name
        t  = Table(); t.df = self.information_df
        self.tableView.setModel(t.to_pyqt5_table_model())
        
    def store_LL_tags(self):
        self.key2LLtag = self.set_key2LLtag()
        add_and_store_LL_tags(self.imgs_df, self.key2LLtag)
        
    def set_key2LLtag(self):
        key2LLtag = dict()
        columns = ['series_descr', 'series_uid', 'Change LL_tag'] if self.by_seriesUID else ['series_descr', 'Change LL_tag']
        rows = self.information_df[columns].to_dict(orient='split')['data']
        for r in rows: key2LLtag[tuple(r[:-1])] = r[-1]
        return key2LLtag

        
class ManualInterventionPopup(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Manual Intervention')
        self.setGeometry(800, 200, 300, 120)
        self.layout = QVBoxLayout(self)
        self.initUI()

    def initUI(self):
        self.choose_tag = QComboBox()
        self.choose_tag.setFixedHeight(50)
        self.choose_tag.addItems(['Select Tag', 'SAX CINE', 'SAX CS', 'LAX CINE 2CV', 'LAX CINE 3CV', 'LAX CINE 4CV', 
                                  'SAX T1 PRE', 'SAX T1 POST', 'SAX T2', 'SAX LGE', 'None'])
        self.choose_tag.activated.connect(self.set_LL_tags)
        self.layout.addWidget(self.choose_tag)
        self.remove_tags_button = QPushButton('Remove LL Tags')
        self.layout.addWidget(self.remove_tags_button)
        self.remove_tags_button.clicked.connect(self.remove_LL_tags)
        self.viewer_button = QPushButton('Show in Viewer')
        self.layout.addWidget(self.viewer_button)
        self.viewer_button.clicked.connect(self.open_viewer)
        self.open_intervention_tab_button = QPushButton('Open Intervention Tab')
        self.layout.addWidget(self.open_intervention_tab_button)
        #self.open_intervention_tab_button.clicked.connect(self.select_cvi42_files)
        self.optional_suffix = QLineEdit('')
        self.layout.addWidget(self.optional_suffix)
        #self.optional_suffix.clicked.connect(self.select_cvi42_files)
        
    def set_LL_tags(self):
        name = self.choose_tag.currentText()
        if name=='Select Tag': return
        suffix = self.optional_suffix.text()
        self.parent.set_LL_tags('Lazy Luna: ' + name + suffix)
        self.close()
        
    def remove_LL_tags(self):
        self.parent.set_LL_tags('Lazy Luna: None')
        self.close()
        
    def open_viewer(self):
        dcms = self.parent.get_dcms()
        self.parent.popup2 = SeriesFigurePopup(self, dcms)
        self.parent.popup2.show()
        

class SeriesFigurePopup(QWidget):
    def __init__(self, parent, dcms=None):
        super().__init__()
        self.parent = parent
        self.dcms   = dcms
        self.images = [dcm.pixel_array for dcm in dcms]
        self.setWindowTitle('Series Visualization')
        self.setGeometry(1100, 200, 300, 300)
        self.layout = QVBoxLayout(self)
        self.initUI()

    def initUI(self):
        self.figure = Image_List_Presenter()
        self.canvas = FigureCanvas(self.figure)
        if self.images is None: self.images = [np.arange(25).reshape(5,5)]
        self.figure.set_values(self.images, self.canvas)
        self.figure.visualize(0)
        self.canvas.mpl_connect('key_press_event', self.figure.keyPressEvent)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()
        self.fig_toolbar = NavigationToolbar(self.canvas, self.parent)
        self.layout.addWidget(self.canvas)
        