# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
    
class MplWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.figure      = Figure()
        self.canvas      = FigureCanvas(self.figure)
        vertical_layout  = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.setLayout(vertical_layout)
        
    def set_dcms(self, dcms):
        self.dcms = dcms
        self.n    = 0
        self.visualize()
        
    def keyPressEvent(self, event):
        if event.key() == 16777235: self.n=(self.n-1)  % len(self.dcms)
        if event.key() == 16777237: self.n=(self.n+1)  % len(self.dcms)
        if event.key() == 16777234: self.n=(self.n-1)  % len(self.dcms)
        if event.key() == 16777236: self.n=(self.n+1)  % len(self.dcms)
        if event.key() ==       32: self.n=(self.n+15) % len(self.dcms)
        self.visualize()
        self.canvas.draw()
        
    def visualize(self):
        img = self.dcms[self.n].pixel_array
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.imshow(img, cmap='gray')
        self.figure.suptitle('Image: ' + str(self.n) + ' of ' + str(len(self.dcms)))