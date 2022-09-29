
## INSPIRED BY:

##############
## https://www.delftstack.com/de/tutorial/pyqt5/pyqt5-menubar/
##############


import os
from pathlib import Path
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        bp = Path(__file__).parent.absolute()

        
        # Define Actions 
        
        # Action 1
        action1 = QAction(QIcon(os.path.join(bp, 'Icons','database--plus.png')), "&Your button", self)
        action1.setStatusTip("This is your button")
        action1.triggered.connect(self.onMyToolBarButtonClick)
        action1.setCheckable(True)
        
        # Action 2
        action2 = QAction(QIcon(os.path.join(bp, 'Icons','database-import.png')), "Your &button2", self)
        action2.setStatusTip("This is your button2")
        action2.triggered.connect(self.onMyToolBarButtonClick)
        action2.setCheckable(True)
        
        # MENU BAR
        # For adding specific tabs (like cvi42converter, image labeler (LLtags), case converter)
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(action1)
        
        
        
        # CENTRAL WIDGET - can this be replaced with a widget container?
        label = QLabel("Hello!")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

        toolbar = QToolBar("My main toolbar")
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)

        
        toolbar.addWidget(QLabel("Hello"))
        toolbar.addSeparator()
        toolbar.addAction(action1)

        toolbar.addSeparator()

        
        toolbar.addAction(action2)

        toolbar.addSeparator()
        
        toolbar.addWidget(QLabel("Hello"))
        toolbar.addWidget(QCheckBox())

        self.setStatusBar(QStatusBar(self))


    def onMyToolBarButtonClick(self, s):
        print("click", s)
        
        
def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()