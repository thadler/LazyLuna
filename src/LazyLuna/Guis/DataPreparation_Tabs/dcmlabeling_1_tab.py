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
        self.overriding_dict = dict()
        
        # Actions for Toolbar
        select_dcm_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','blue-folder-open-slide.png')), '&Select DCM Folder', self)
        select_dcm_folder_action.setStatusTip("Select Folder with Dicom files.")
        select_dcm_folder_action.triggered.connect(self.select_dcm_folder)
        
        load_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','blue-folder-open-table.png')), "&Load Table", self)
        load_action.setStatusTip("Load Table.")
        load_action.triggered.connect(self.load_table)
        
        select_reader_folder_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','users.png')), "&Select Reader", self)
        select_reader_folder_action.setStatusTip("Select Folder with Annotation files.")
        select_reader_folder_action.triggered.connect(self.select_reader_folder)
        
        suggest_labels_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','wand--pencil.png')), "&Suggest Labels", self)
        suggest_labels_action.setStatusTip("Suggest LL Labels for Dicom series.")
        suggest_labels_action.triggered.connect(self.suggest_ll_labels)
        
        manual_select_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','tag--plus.png')), "&Manual Label Selection", self)
        manual_select_action.setStatusTip("Manually select LL Labels for Dicom series.")
        manual_select_action.triggered.connect(self.select_ll_labels)
        
        remove_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','tag--minus.png')), "&Remove Label Selection", self)
        remove_action.setStatusTip("Remove selected LL Labels for Dicom series.")
        remove_action.triggered.connect(self.remove_ll_labels)
        
        store_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','disk-return.png')), "&Store Labels", self)
        store_action.setStatusTip("Store LL Labels for all Dicoms.")
        store_action.triggered.connect(self.store_ll_labels)
        
        
        # First Toolbar for Loading the Table
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar, 0,0, 1,5)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(select_dcm_folder_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(select_reader_folder_action)
        self.toolbar.addWidget(b2)
        self.cb = QCheckBox()
        self.cb.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); self.cb.setLayoutDirection(Qt.RightToLeft)
        self.cb.setText('By Series: '); self.cb.setFont(QFont('', fontsize))
        self.cb.setStatusTip("If selected, separates Dicoms by SeriesUID instead of SeriesDescription.")
        self.cb.stateChanged.connect(self.set_by_seriesUID)
        self.toolbar.addWidget(self.cb)
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(load_action)
        self.toolbar.addWidget(b3)
        b4 = QToolButton(); b4.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b4.setFont(QFont('', fontsize))
        b4.setDefaultAction(store_action)
        self.toolbar.addWidget(b4)
        
        self.tab1.layout.addWidget(QHLine(), 1, 0, 1, 10)
        self.dicom_folder_label  = QLabel('Dicom  Folder: ')
        self.dicom_folder_text   = QLabel('')
        self.reader_folder_label = QLabel('Reader Folder: ')
        self.reader_folder_text  = QLabel('')
        self.tab1.layout.addWidget(self.dicom_folder_label,  2, 0, 1,1)
        self.tab1.layout.addWidget(self.dicom_folder_text,   2, 1, 1,1)
        self.tab1.layout.addWidget(self.reader_folder_label, 2, 2, 1,1)
        self.tab1.layout.addWidget(self.reader_folder_text,  2, 3, 1,1)
        self.tab1.layout.addWidget(QHLine(), 3, 0, 1, 10)
        
        # Second Toolbar for Table Manipulation
        self.toolbar2 = QToolBar("My main toolbar")
        self.toolbar2.setIconSize(QSize(28, 28))
        self.tab1.layout.addWidget(self.toolbar2, 4,0, 1,5)
        b5 = QToolButton(); b5.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b5.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b5.setFont(QFont('', fontsize))
        b5.setDefaultAction(suggest_labels_action)
        self.toolbar2.addWidget(b5)
        b6 = QToolButton(); b6.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b6.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b6.setFont(QFont('', fontsize))
        b6.setDefaultAction(manual_select_action)
        self.toolbar2.addWidget(b6)
        b7 = QToolButton(); b7.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b7.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b7.setFont(QFont('', fontsize))
        b7.setDefaultAction(remove_action)
        self.toolbar2.addWidget(b7)
        
        
        # Table View on the Left
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.select_ll_labels)
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
    
    def store_ll_labels(self):
        # Information Message for User
        if not self.is_table_loaded(): return
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("LL Tag storage can take a minute.")
        msg.setInformativeText("Are you sure you want to procede?")
        msg.setWindowTitle("Storage Warning")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval==65536: return # Return value for NO button
        try:
            self.key2LLtag = self.set_key2LLtag()
            add_and_store_LL_tags(self.imgs_df, self.key2LLtag, self.overriding_dict)
            self.information_df['LL_tag'] = self.information_df['Change LL_tag']
            t  = Table(); t.df = self.information_df
            self.tableView.setModel(t.to_pyqt5_table_model())
        except Exception as e: print(e)
    
    def acceptable_orientation(self, dcm):
        try: 
            if sum(dcm.ImageOrientationPatient)==2: return False
        except Exception as e: pass
        return True
        
    def suggest_ll_labels(self):
        try:
            if not self.is_table_loaded(): return
            table = self.information_df
            sax_cine_sds = []
            for row in range(table.shape[0]):
                try:
                    sd = table.at[row, 'series_descr']
                    if '2cv' in sd: continue
                    if '3cv' in sd: continue
                    if '4cv' in sd: continue
                    if 'pre_MOLLI' in sd and 'MOCO_T1' in sd and not 'T1S' in sd:
                        table.at[row,'Change LL_tag'] = 'Lazy Luna: SAX T1 PRE'
                    if sd.startswith('T2') and 'MOCO_T2' in sd:
                        table.at[row,'Change LL_tag'] = 'Lazy Luna: SAX T2'
                    if not self.by_seriesUID:
                        # check number of annotations # check orientation != 2 (removes axial images) # check larger > 7*25
                        try:
                            if int(table.at[row,'nr_annos'])==0:   continue
                            if int(table.at[row,'nr_imgs' ])<7*25: continue
                            dcm_paths = get_img_paths_for_series_descr(self.imgs_df, table.at[row,'series_descr'])
                            if not self.acceptable_orientation(pydicom.dcmread(dcm_paths[0], stop_before_pixels=True)): continue
                            sax_cine_sds.append(sd)
                        except Exception as e: print('Failed in suggesting SAX CINE: ', e)
                except Exception as e: pass
            # set sax cine tag
            if not self.by_seriesUID and len(sax_cine_sds)==1:
                sax_cine_sd = sax_cine_sds[0]
                for row in range(table.shape[0]):
                    sd = table.at[row,'series_descr']
                    if sd==sax_cine_sd:
                        table.at[row,'Change LL_tag'] = 'Lazy Luna: SAX CINE'
            t  = Table(); t.df = table
            self.tableView.setModel(t.to_pyqt5_table_model())
            self.color_rows()
        except Exception as e: print('Failed suggesting labels: ', e)
        
    def select_ll_labels(self, item):
        try:
            if not self.is_table_loaded(): return
            self.popup1 = ManualInterventionPopup(self)
            self.popup1.show()
        except Exception as e: pass
        
    def remove_ll_labels(self):
        if not self.is_table_loaded(): return
        try: self.set_LL_tags('Lazy Luna: None')
        except Exception as e: pass
        

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
    
    def set_LL_tags(self, name):
        try:
            idxs  = self.tableView.selectionModel().selectedIndexes()
            for idx in sorted(idxs):
                self.information_df.at[idx.row(), 'Change LL_tag'] = name
            t  = Table(); t.df = self.information_df
            self.tableView.setModel(t.to_pyqt5_table_model())
        except Exception as e: print(e)
        
    def set_key2LLtag(self):
        key2LLtag = dict()
        columns = ['series_descr', 'series_uid', 'Change LL_tag'] if self.by_seriesUID else ['series_descr', 'Change LL_tag']
        rows = self.information_df[columns].to_dict(orient='split')['data']
        for r in rows: key2LLtag[tuple(r[:-1])] = r[-1]
        return key2LLtag
    
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
        self.open_intervention_tab_button.clicked.connect(self.open_intervention_tab)
        self.optional_suffix = QLineEdit('')
        self.layout.addWidget(self.optional_suffix)
        
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
        
    def open_intervention_tab(self):
        dcms = self.parent.get_dcms()
        self.parent.parent.add_labeler_2_tab(dcms, self.parent.overriding_dict)
        self.close()
        

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
        
        
class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)