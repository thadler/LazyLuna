
## INSPIRED BY:

##############
## https://www.delftstack.com/de/tutorial/pyqt5/pyqt5-menubar/
##############


import os
from pathlib import Path
import sys
import traceback

from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QSize

from LazyLuna.Guis.DataPreparation_Tabs.cvi42converter_tab import CVI42Converter_TabWidget
from LazyLuna.Guis.DataPreparation_Tabs.centralintroductory_tab import CentralIntroductory_TabWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lazy Luna - Data Preparation")
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
        
        cvi42converter_action = QAction(QIcon(os.path.join(self.bp, 'Icons','wand--arrow.png')), "&Convert CVI42 Workspaces", self)
        cvi42converter_action.setStatusTip("Convert CVI42Workspaces into LL Format.")
        cvi42converter_action.triggered.connect(self.open_cvi42converter_tab)
        
        labeler_action = QAction(QIcon(os.path.join(self.bp, 'Icons','tag--pencil.png')), "&Label Images with LL Types", self)
        labeler_action.setStatusTip("Identify and Label Case Images with LL Tags.")
        labeler_action.triggered.connect(self.open_labeler_tab)
        
        # MENU BAR
        menu = self.menuBar()
        file_menu = menu.addMenu("&Select Tools")
        file_menu.addAction(introduction_action)
        file_menu.addAction(cvi42converter_action)
        file_menu.addAction(labeler_action)
        
        # Central Tab - is replaced with other tabs as selected
        self.tab = CentralIntroductory_TabWidget(self)
        self.setCentralWidget(self.tab)

        # Set Statusbar for information display during use / mouse hovering
        self.setStatusBar(QStatusBar(self))

    def open_introduction_tab(self, s):
        try: self.removeToolBar(self.tab.toolbar)
        except Exception as e: print(traceback.format_exc())
        self.tab = CentralIntroductory_TabWidget(self)
        self.setCentralWidget(self.tab)
        

    def open_cvi42converter_tab(self, s):
        try: self.removeToolBar(self.tab.toolbar)
        except Exception as e: print(traceback.format_exc())
        self.tab = CVI42Converter_TabWidget(self)
        self.setCentralWidget(self.tab)
        
    def open_labeler_tab(self, s):
        try: self.removeToolBar(self.tab.toolbar)
        except Exception as e: print(traceback.format_exc())
        print("click", s)

        
        
        
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