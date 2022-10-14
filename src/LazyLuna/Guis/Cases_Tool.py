import os
from pathlib import Path
import sys
import traceback

from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QSize

from LazyLuna.Guis.CasesTool_Tabs.centralintroductory_tab import CentralIntroductory_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.Datenbank_Tab import LL_Database_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.CasesOverview_Tab import CasesOverview_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.ClinicalResultsTable_Tab import ClinicalResultsTable_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.SingleCase_Tab import SingleCase_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.SelectImages_Tab import SelectImages_TabWidget
from LazyLuna.Guis.CasesTool_Tabs.Segmentation_Tab import Segmentation_TabWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lazy Luna - Case(s) Analysis")
        shift       = 30
        self.left   = 0
        self.top    = shift
        self.width  = 1200
        self.height = 800  + shift
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()
        self.bp = Path(__file__).parent.absolute()
        self.ui_init()
        
    def ui_init(self):
        introduction_action = QAction(QIcon(os.path.join(self.bp, 'Icons','notebook.png')), "&Introduction", self)
        introduction_action.setStatusTip("General information about this tool.")
        introduction_action.triggered.connect(self.open_introduction_tab)
        
        cases_tab_action = QAction(QIcon(os.path.join(self.bp, 'Icons','notebook.png')), "&Case(s) Analysis", self)
        cases_tab_action.setStatusTip("Select Cases from the LL Database to inspect!‚")
        cases_tab_action.triggered.connect(self.open_cases_tab)
        
        segmentation_tab_action = QAction(QIcon(os.path.join(self.bp, 'Icons','notebook.png')), "&Segmentation Tool", self)
        segmentation_tab_action.setStatusTip("Load images for manual segmentation.")
        segmentation_tab_action.triggered.connect(self.open_segmentation_tab)
        
        
        
        # MENU BAR
        menu = self.menuBar()
        file_menu = menu.addMenu("&Select Tools")
        file_menu.addAction(introduction_action)
        file_menu.addAction(cases_tab_action)
        file_menu.addAction(segmentation_tab_action)
        
        # Central Tab - is replaced with other tabs as selected
        self.tab = CentralIntroductory_TabWidget(self)
        self.setCentralWidget(self.tab)

        # Set Statusbar for information display during use / mouse hovering
        self.setStatusBar(QStatusBar(self))

    def open_introduction_tab(self, s):
        self.tab = CentralIntroductory_TabWidget(self)
        self.setCentralWidget(self.tab)

    def open_cases_tab(self, s):
        self.tab = LL_Database_TabWidget(self)
        self.setCentralWidget(self.tab)
        
    def add_cases_overview_tab(self, cases, case_paths):
        t = CasesOverview_TabWidget(self, cases, case_paths)
        self.tab.tabs.addTab(t, 'Overview of Selected Cases')
        
    def add_clinical_results_tab(self, view, viewname, cases, case_paths):
        t = ClinicalResultsTable_TabWidget(self, view, viewname, cases, case_paths)
        self.tab.tabs.addTab(t, 'Clinical Results')
        
    def add_single_case_tab(self, view, viewname, case, casepath):
        t = SingleCase_TabWidget(self, view, viewname, case, casepath)
        self.tab.tabs.addTab(t, 'Case '+case.case_name)
        
    def open_segmentation_tab(self, s):
        self.tab = SelectImages_TabWidget(self)
        self.setCentralWidget(self.tab)
        
    def add_segmentation_tab(self, dicom_folder_path, dcms):
        t = Segmentation_TabWidget(self, dicom_folder_path, dcms)
        self.tab.tabs.addTab(t, 'Segmentation Tab')
        
        
def main():
    app = QApplication(sys.argv)
    
    # Now use a palette to switch to dark colors:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(0,0,0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
    app.setPalette(palette)
    
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()