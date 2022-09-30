import os
from pathlib import Path
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QSize

        
class CentralIntroductory_TabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs  = QTabWidget()
        self.tab1  = QWidget()
        self.tabs.resize(self.parent.width, self.parent.height)
        #######################
        ## NOT CLOSABLE HERE ##
        #######################
        # Closable Tabs
        #self.tabs.setTabsClosable(True)
        #self.tabs.tabCloseRequested.connect(lambda index: self.tabs.removeTab(index))
        # Add tabs
        self.tabs.addTab(self.tab1, "Introductory Information")
        
        ##################
        ## Create TAB 1 ##
        ##################
        self.tab1.layout = QGridLayout(self)
        self.tab1.layout.setSpacing(7)
        self.infoLbl = QLabel()
        self.infoLbl.setTextFormat(Qt.RichText)
        self.infoLbl.setFrameShape(QFrame.StyledPanel)
        self.infoTxt = '<!DOCTYPE html><html><head><style> ol.c{  list-style-type: upper-roman;  margin: 20;  padding: 20;}</style></head><body>\
        <p style="font-size:30pt" >Lazy Luna - Data Preparation includes:</p> \
        <ol class="c"> \
        <li><p style="font-size:20pt"> CVI42 Converter          </p></li> \
        <li><p style="font-size:20pt"> Image Type Labeler       </p></li> \
        <li><p style="font-size:20pt"> Lazy Luna Cases Database </p></li> \
        </ol> \
        <p style="font-size:20pt" >These tools can be opened by selecting them from the menu item "Select Tools".</p>\
        </body></html>'
        self.infoLbl.setText(self.infoTxt)
        self.infoLbl.setStatusTip('The menu item "Select Tools" is on the top. Select a tool there!')
        self.infoLbl.setMaximumHeight(1000)
        self.infoLbl.setMaximumWidth(2000)
        self.tab1.layout.addWidget(self.infoLbl, 0,0)

        # set layout
        self.tab1.setLayout(self.tab1.layout)
        
        ########################
        ## Add Tabs to Widget ##
        ########################
        self.layout.addWidget(self.tabs)