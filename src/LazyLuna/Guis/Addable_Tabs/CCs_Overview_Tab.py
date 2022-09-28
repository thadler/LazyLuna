from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog, QMessageBox
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from pathlib import Path
import pickle
import copy
import sys
import os
import inspect
import traceback

import pandas

from LazyLuna.Mini_LL import Case_Comparison
from LazyLuna.loading_functions import *
from LazyLuna.Tables  import *
from LazyLuna.Figures import *
from LazyLuna         import Views


class StoreInfoWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    def __init__(self, view, case_comparisons, view_folder_path):
        super().__init__()
        self.view = view
        self.case_comparisons = case_comparisons
        self.view_folder_path = view_folder_path
    def run(self):
        self.view.store_information(self.case_comparisons, self.view_folder_path)
        self.finished.emit()


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
        print('In overview tab: Nr CCs: ', len(case_comparisons))
        self.all_case_comparisons = case_comparisons
        self.threads = []
        self.workers = []

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
        self.overview_table.calculate(case_comparisons)
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
        try:
            dialog = QFileDialog(self.gui, '')
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_()==QDialog.Accepted:
                self.export_storage_folder_path.setText(dialog.selectedFiles()[0])
        except Exception as e:
            print(traceback.format_exc())
    
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
        except Exception as e:
            print(traceback.format_exc())
        try:
            self.gui.cc_table.store(os.path.join(export_folder_path, 'table.csv'))
            self.overview_table.store(os.path.join(view_folder_path, 'overview_table.csv'))
        except Exception as e:
            print(traceback.format_exc())
        try:
            self.threads.append(QThread())
            self.workers.append(StoreInfoWorker(view, self.case_comparisons, view_folder_path))
            thread, worker = self.threads[-1], self.workers[-1]
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.start()
        except Exception as e:
            print(traceback.format_exc())
        
    def create_stats_tab(self):
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("You're opening a statistical tab for "+str(len(self.case_comparisons))+" cases.\n!!! Calculations may take up to a minute !!!")
            msg.setInformativeText("Are you sure you want to procede?")
            msg.setWindowTitle("Statistical Tab Reminder")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            # Return value for NO button
            if retval==65536: return
            tab_name  = self.combobox_stats_tab  .currentText()
            view_name = self.combobox_select_view.currentText()
            if tab_name=='Choose a Tab' or view_name=='Choose a View': return
            view = self.get_view(self.combobox_select_view.currentText())
            tab  = [v for k,v in view.stats_tabs.items() if k==tab_name][0]()
            tab.make_tab(self.gui, view, self.case_comparisons)
            self.gui.tabs.addTab(tab, 'Clinical Results')
        except Exception as e:
            print(traceback.format_exc())
        return
    
    def create_case_tab(self):
        try:
            case_name = self.combobox_case       .currentText()
            tab_name  = self.combobox_case_tab   .currentText()
            view_name = self.combobox_select_view.currentText()
            if case_name=='Choose a Case' or tab_name=='Choose a Tab' or view_name=='Choose a View': return
            view = self.get_view(self.combobox_select_view.currentText())
            cc   = [cc for cc in self.case_comparisons if cc.case1.case_name==case_name][0]
            #tab  = [v for k,v in view.case_tabs.items()][0]()
            tab  = [v for k,v in view.case_tabs.items() if k==tab_name][0]()
            tab.make_tab(self.gui, view, cc)
            self.gui.tabs.addTab(tab, 'Metrics and Figure: '+cc.case1.case_name)
        except Exception as e:
            print(traceback.format_exc())
        return
    
    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]==vname][0]
        return view()
    
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]!='View']
        return v_names
    
    def select_view(self):
        try:
            view_name = self.combobox_select_view.currentText()
            v = self.get_view(view_name)
            new_ccs = []
            for i in range(len(self.all_case_comparisons)):
                cc = copy.deepcopy(self.all_case_comparisons[i])
                try:
                    new_cc = Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2))
                    new_ccs.append(new_cc)
                except Exception as e:
                    print('Failed customize at: ', i, cc.case1.case_name, '/n', traceback.format_exc())
            self.case_comparisons = new_ccs
            self.combobox_case_tab.clear(); self.combobox_case_tab.addItems(['Choose a Tab']+[str(tab) for tab in v.case_tabs])
            self.combobox_stats_tab.clear(); self.combobox_stats_tab.addItems(['Choose a Tab']+[str(tab) for tab in v.stats_tabs])
            self.overview_table.calculate(new_ccs)
            self.overview_TableView.setModel(self.overview_table.to_pyqt5_table_model())
            self.case_comparisons = [Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2)) for cc in self.case_comparisons]
        except Exception as e:
            print(traceback.format_exc())

    

