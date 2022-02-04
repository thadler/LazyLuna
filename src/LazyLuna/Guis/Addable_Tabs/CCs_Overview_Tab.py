from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5 import QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from pathlib import Path
import pickle
import copy
import sys
import os
import inspect

import pandas

from LazyLuna.Mini_LL import Case_Comparison, SAX_CINE_View, SAX_CS_View
from LazyLuna.loading_functions import *
from LazyLuna.Tables import *
from LazyLuna.Figures import *


class CCs_Overview_Tab(QWidget):
    def __init__(self):
        super().__init__()
        
    def make_tab(self, gui, case_comparisons):
        self.gui = gui
        gui.tabs.addTab(self, "Overview")
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)
        
        #########################################
        ## Temporary: replace with Select view ##
        #########################################
        self.all_case_comparisons = case_comparisons

        ###########
        ## Row 1 ##
        ###########
        self.patient_overview_lbl = QLabel('Pick View on Data: ')
        layout.addWidget(self.patient_overview_lbl, 0,0, 1,1)
        self.combobox_select_view = QComboBox()
        self.combobox_select_view.addItems(['Choose a View'] + self.get_view_names())
        self.combobox_select_view.activated[str].connect(self.select_view)
        layout.addWidget(self.combobox_select_view, 1,0, 1,1)

        self.patient_overview_lbl = QLabel('Patient Overview: ')
        layout.addWidget(self.patient_overview_lbl, 0,2, 1,1)

        self.overview_table = CC_StatsOverviewTable()
        self.overview_table.calculate(gui.cc_table)
        self.overview_TableView = QTableView()
        self.overview_TableView.setModel(self.overview_table.to_pyqt5_table_model())
        layout.addWidget(self.overview_TableView, 1, 2, 10,1)

        ###########
        ## Row 2 ##
        ###########

        self.stats_lbl = QLabel('Pick Statistical Tab: ')
        layout.addWidget(self.stats_lbl, 2,0, 1,1)
        self.combobox_stats_tab = QComboBox()
        self.combobox_stats_tab.addItems(['Choose a Tab'])# + get_view_names())
        self.combobox_stats_tab.activated[str].connect(self.create_stats_tab)
        layout.addWidget(self.combobox_stats_tab, 3,0, 1,1)

        self.case_lbl = QLabel('Pick Case and Tab: ')
        layout.addWidget(self.case_lbl, 2,1, 1,1)
        self.combobox_case_tab = QComboBox()
        self.combobox_case_tab.addItems(['Choose a Tab'])
        self.combobox_case_tab.activated[str].connect(self.create_case_tab)
        layout.addWidget(self.combobox_case_tab, 3,1, 1,1)
        self.combobox_case = QComboBox()
        self.combobox_case.addItems(['Choose a Case']+[cc.case1.case_name for cc in case_comparisons])
        self.combobox_case.activated[str].connect(self.create_case_tab)
        layout.addWidget(self.combobox_case, 4,1, 1,1)

        ###########
        ## Row 3 ##
        ###########
        self.LLL_lbl = QLabel('Little Lazy Luna - Export (Select View first)')
        layout.addWidget(self.LLL_lbl, 5,0, 1,1)

        self.set_export_folder_path_button = QPushButton('Select Export Folder')
        self.set_export_folder_path_button.clicked.connect(self.set_export_storage_folder_path)
        layout.addWidget(self.set_export_folder_path_button, 6, 0)
        self.export_storage_folder_path = QLineEdit('')
        layout.addWidget(self.export_storage_folder_path, 6, 1)
        self.export_button = QPushButton('Export Figures and Tables')
        self.export_button.clicked.connect(self.store_all)
        layout.addWidget(self.export_button, 7, 0)

        layout.setColumnStretch(2, 2)
        self.setLayout(layout)

    def set_export_storage_folder_path(self):
        dialog = QFileDialog(self.gui, '')
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_()==QDialog.Accepted:
            self.export_storage_folder_path.setText(dialog.selectedFiles()[0])
    
    def store_all(self):
        try:
            path = self.export_storage_folder_path.text()
            reader1 = self.gui.reader1
            reader2 = self.gui.reader2
            export_folder_path = os.path.join(path, 'Export_comparison_'+reader1+'_'+reader2)
            if not os.path.exists(export_folder_path): os.mkdir(export_folder_path)
            view_name = self.combobox_select_view.currentText()
            view = self.get_view(view_name)
            view_folder_path = os.path.join(export_folder_path, view_name)
            if not os.path.exists(view_folder_path): os.mkdir(view_folder_path)
            self.gui.cc_table.store(os.path.join(export_folder_path, 'table1.csv'))
            self.overview_table.store(os.path.join(view_folder_path, 'overview_table.csv'))
            cr_table = CC_ClinicalResultsTable()
            cr_table.calculate(self.case_comparisons)
            cr_table.store(os.path.join(view_folder_path, 'clinical_results.csv'))
            cr_overview_figure = SAX_BlandAltman()
            cr_overview_figure.visualize(self.case_comparisons)
            cr_overview_figure.store(view_folder_path)
            metrics_table = CCs_MetricsTable()
            metrics_table.calculate(self.case_comparisons, self.get_view(view_name))
            metrics_table.store(os.path.join(view_folder_path, 'metrics_phase_slice_table.csv'))
            failed_segmentation_folder_path = os.path.join(view_folder_path, 'Failed_Segmentations')
            if not os.path.exists(failed_segmentation_folder_path): os.mkdir(failed_segmentation_folder_path)
            failed_annotation_comparison = Failed_Annotation_Comparison_Yielder()
            failed_annotation_comparison.set_values(view, self.case_comparisons)
            failed_annotation_comparison.store(failed_segmentation_folder_path)
            table = SAX_Cine_CCs_pretty_averageCRs_averageMetrics_Table()
            table.calculate(self.case_comparisons, view)
            table.present_metrics()
            table.store(os.path.join(view_folder_path, 'metrics_table_by_contour_position.csv'))
            table.present_crs()
            table.store(os.path.join(view_folder_path, 'crvs_and_metrics.csv'))
        except Exception as e:
            print(e)
        
        
        
    def create_stats_tab(self):
        tab_name  = self.combobox_stats_tab  .currentText()
        view_name = self.combobox_select_view.currentText()
        if tab_name=='Choose a Tab' or view_name=='Choose a View': return
        view = self.get_view(self.combobox_select_view.currentText())
        tab  = [v for k,v in view.stats_tabs.items() if k==tab_name][0]()
        tab.make_tab(self.gui, view, self.case_comparisons)
        self.gui.tabs.addTab(tab, 'Clinical Results')
        return
    
    def create_case_tab(self):
        case_name = self.combobox_case       .currentText()
        tab_name  = self.combobox_case_tab   .currentText()
        view_name = self.combobox_select_view.currentText()
        if case_name=='Choose a Case' or tab_name=='Choose a Tab' or view_name=='Choose a View': return
        view = self.get_view(self.combobox_select_view.currentText())
        cc   = [cc for cc in self.case_comparisons if cc.case1.case_name==case_name][0]
        tab  = [v for k,v in view.case_tabs.items()][0]()
        tab.make_tab(self.gui, view, cc)
        self.gui.tabs.addTab(tab, 'Metrics and Figure: '+cc.case1.case_name)
        return
    
    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Mini_LL, inspect.isclass) if issubclass(c[1], Mini_LL.View) if c[0]==vname][0]
        return view()
    
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Mini_LL, inspect.isclass) if issubclass(c[1], Mini_LL.View) if c[0]!='View']
        return v_names
    
    def select_view(self):
        view_name = self.combobox_select_view.currentText()
        v = self.get_view(view_name)
        new_ccs = []
        for i in range(len(self.all_case_comparisons)):
            cc = copy.deepcopy(self.all_case_comparisons[i])
            try:
                new_cc = Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2))
                new_ccs.append(new_cc)
            except Exception as e:
                print('Failed customize at: ', i, cc.case1.case_name, e)
        self.case_comparisons = new_ccs
        self.combobox_case_tab.clear(); self.combobox_case_tab.addItems(['Choose a Tab']+[str(tab) for tab in v.case_tabs])
        self.combobox_stats_tab.clear(); self.combobox_stats_tab.addItems(['Choose a Tab']+[str(tab) for tab in v.stats_tabs])
        self.overview_table.calculate(self.gui.cc_table, view_name.replace('_View','').replace('_',' '))
        self.overview_TableView.setModel(self.overview_table.to_pyqt5_table_model())
        self.case_comparisons = [Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2)) for cc in self.case_comparisons]

    

