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


class DcmLabeling_2_TabWidget(QWidget):
    def __init__(self, parent, dcms, overriding_dict):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        
        # initializing some variables
        self.dcms = dcms
        self.overriding_dict = overriding_dict
        
        self.ui_init()
        
        
    def ui_init(self):
        
        # Actions for Toolbar
        manual_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','folder-open-image.png')), '&Manual Intervention', self)
        manual_action.setStatusTip("Manual Selection of Labels.")
        manual_action.triggered.connect(self.manual_intervention)
        
        # Actions for Toolbar
        store_and_return_action = QAction(QIcon(os.path.join(self.parent.bp, 'Icons','folder-open-image.png')), '&Store and Return', self)
        store_and_return_action.setStatusTip("Store Labels and Return to Former Tab.")
        store_and_return_action.triggered.connect(self.store_and_return)
        
        # First Toolbar for Loading the Table
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar, 0,0, 1,5)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(manual_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(store_and_return_action)
        self.toolbar.addWidget(b2)
        
        
        # User Info on Image and Reader Folder
        self.seriesdescr_label = QLabel('Series Description: ')
        self.seriesdescr_text  = QLabel('')
        self.seriesuid_label   = QLabel('SeriesUID: ')
        self.seriesuid_text    = QLabel('')
        self.layout.addWidget(self.seriesdescr_label, 1, 0, 1,1)
        self.layout.addWidget(self.seriesdescr_text,  1, 1, 1,1)
        self.layout.addWidget(self.seriesuid_label,   1, 2, 1,1)
        self.layout.addWidget(self.seriesuid_text,    1, 3, 1,1)
        self.set_labels()
        
        # Table View on the Left
        self.tableView = QTableView(self)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setEditTriggers(QTableView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.manual_intervention)
        self.layout.addWidget(self.tableView, 2, 0, 2,5)
        self.make_table()
        
        # Figure on the top right
        self.fig = Image_List_Presenter()
        self.canvas = FigureCanvas(self.fig)
        self.fig.set_values([dcm.pixel_array for dcm in self.dcms], self.canvas)
        self.fig.visualize(0)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()
        self.layout.addWidget(self.canvas,  2,5, 1,1)
        
        
        # set layout
        self.setLayout(self.layout)
        self.layout.setColumnStretch(4,20)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        #self.layout.addWidget(self.tabs)
        
        
    def set_labels(self):
        seriesUIDs         = list(set([dcm.SeriesDescription for dcm in self.dcms]))
        seriesDescriptions = list(set([dcm.SeriesInstanceUID for dcm in self.dcms]))
        lbl1 = 'multiple' if len(seriesDescriptions)!=1 else seriesDescriptions[0]
        lbl2 = 'multiple' if len(seriesUIDs)!=1 else seriesUIDs[0]
        self.seriesdescr_text.setText(lbl1)
        self.seriesuid_text.setText(lbl2)
        
        
    def make_table(self):
        columns = ['SOP Instance UID', 'Slice Position', 'LL_tag', 'Change LL_tag', 'series_descr', 'series_uid']
        rows = []
        for dcm in self.dcms:
            rows.append([dcm.SOPInstanceUID, "{:10.2f}".format(dcm.SliceLocation), get_LL_tag(dcm), get_LL_tag(dcm), dcm.SeriesDescription, dcm.SeriesInstanceUID])
        self.dcm_table = pandas.DataFrame(rows, columns=columns)
        t  = Table(); t.df = self.dcm_table
        self.tableView.setModel(t.to_pyqt5_table_model())
        self.tableView.selectionModel().selectionChanged.connect(self.update_figure)
        for i in range(2, len(self.tableView.horizontalHeader())):
            self.tableView.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
    def update_figure(self):
        row = self.tableView.selectionModel().selectedIndexes()[0].row()
        self.fig.visualize(row)

    def manual_intervention(self):
        try:
            self.popup1 = ManualInterventionPopup(self)
            self.popup1.show()
        except Exception as e: pass
        
    def store_and_return(self):
        # Information Message for User
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Individual Tags are stored.")
        msg.setInformativeText("Individual tag changes are not visible in table. Are you sure you want to close this window?")
        msg.setWindowTitle("Storage and Closure Warning")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        # Return value for NO button
        if retval==65536: return
        # Message end
        self.parent.tab.tabs.removeTab(1)
        

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
        self.optional_suffix = QLineEdit('')
        self.layout.addWidget(self.optional_suffix)
        ###########################################################
        ## Alternative ComboBox for Artefacts, Fat, Blurry, etc? ##
        ###########################################################
        
    def set_LL_tags(self):
        try:
            name = self.choose_tag.currentText()
            if name=='Select Tag': return
            row = self.parent.tableView.selectionModel().selectedIndexes()[0].row()
            sop = self.parent.dcm_table['SOP Instance UID'].iloc[row]
            suffix = self.optional_suffix.text()
            tag = 'Lazy Luna: ' + name + suffix
            self.parent.overriding_dict[sop] = tag
            self.parent.dcm_table['Change LL_tag'].iloc[row] = tag
            t  = Table(); t.df = self.parent.dcm_table
            self.parent.tableView.setModel(t.to_pyqt5_table_model())
            self.close()
        except Exception as e: pass
        
    def remove_LL_tags(self):
        try:
            tag = 'Lazy Luna: None'
            row = self.parent.tableView.selectionModel().selectedIndexes()[0].row()
            sop = self.parent.dcm_table['SOP Instance UID'].iloc[row]
            self.parent.overriding_dict[sop] = tag
            self.parent.dcm_table['Change LL_tag'].iloc[row] = tag
            t  = Table(); t.df = self.parent.dcm_table
            self.parent.tableView.setModel(t.to_pyqt5_table_model())
            self.close()
        except Exception as e: pass
        
        
        
        