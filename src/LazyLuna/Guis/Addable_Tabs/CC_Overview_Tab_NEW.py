from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib

from pathlib import Path
import pickle
import copy
import sys
import os
import inspect

import pandas

from LazyLuna.Containers import Case_Comparison
from LazyLuna.loading_functions import *
from LazyLuna.Tables  import *
from LazyLuna.Figures import *
from LazyLuna         import Views


class CC_CRs_Images_Tab_NEW(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Clinical Results and Images/Annotations'
        
    def make_tab(self, gui, view, cc):
        self.gui     = gui
        self.base_cc = self.cc = cc
        gui.tabs.addTab(self, self.name + ': ' + str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        self.combobox_select_view = QComboBox()
        self.combobox_select_view.setStatusTip('Choose a View')
        self.combobox_select_view.addItems(['Choose a View'] + self.get_view_names())
        self.combobox_select_view.activated[str].connect(self.select_view) 
        layout.addWidget(self.combobox_select_view, 0, 0)

        self.cr_table = CC_ClinicalResultsAveragesTable()
        self.cr_table.calculate([self.cc])
        self.cr_tableView = QTableView()
        self.cr_tableView.setModel(self.cr_table.to_pyqt5_table_model())
        layout.addWidget(self.cr_tableView, 1, 0, 1,2)
        
        
        self.image_viewer1 = CustomPlotWidget()
        self.image_viewer1.set_case(self.cc.case1) # for all cats and both cases
        self.image_viewer2 = CustomPlotWidget()
        self.image_viewer2.set_case(self.cc.case2) # for all cats and both cases
        self.image_viewer1.link_with_other(self.image_viewer2)
        self.image_viewer2.link_with_other(self.image_viewer1)
        layout.addWidget(self.image_viewer1,  4, 0, 2, 2)
        layout.addWidget(self.image_viewer2,  4, 2, 2, 2)
        
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

    def get_view(self, vname):
        view = [c[1] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]==vname][0]
        return view()
    
    def get_view_names(self):
        v_names = [c[0] for c in inspect.getmembers(Views, inspect.isclass) if issubclass(c[1], Views.View) if c[0]!='View']
        return v_names
    
    def select_view(self):
        try:
            view_name = self.combobox_select_view.currentText()
            v         = self.get_view(view_name)
            cc        = copy.deepcopy(self.base_cc)
            self.cc   = Case_Comparison(v.customize_case(cc.case1), v.customize_case(cc.case2))
            cat       = self.cc.case1.categories[0]
            # recalculate CRs and reinitialize Figure
            self.cr_table.calculate([self.cc])
            self.cr_tableView.setModel(self.cr_table.to_pyqt5_table_model())
            #self.img_fig.set_values(v, self.cc, self.img_canvas)
            #self.img_fig.visualize(0, cat)
            self.image_viewer1.set_case(self.cc.case1)
            self.image_viewer2.set_case(self.cc.case2)
        except Exception as e:
            print('Exception in select_view: ', e)


        
        
        
class CustomPlotWidget(pg.PlotWidget):
    keyPressed = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.factory_settings()

    def factory_settings(self):
        pg.setConfigOption('imageAxisOrder', 'row-major') # best performance
        self.setAspectLocked()
        self.getPlotItem().hideAxis('bottom'); self.getPlotItem().hideAxis('left')
        #self.invertY(True) # vertical axis counts top to bottom
        self.pen = pg.mkPen('w', width=2)
        self.text_item = pg.TextItem(''); self.text_item.setPos(5, 5); self.text_item.setParentItem(self.getPlotItem())
        self.tags = pg.TextItem(''); self.tags.setPos(5, 85); self.tags.setParentItem(self.getPlotItem())
        for i in range(4): self.getPlotItem().vb.menu.removeAction(self.getPlotItem().vb.menu.actions()[0])
        # setting some variables
        self.cmap          = False
        self.with_anno     = True
        self.with_tags     = False
        self.reader_phases = False # if True then ES/EDs from category are used, otherwise phases and slices start at 0
        self.lutable       = None
        self.others = []
        # add right click actions
        cmapAction = self.getPlotItem().vb.menu.addAction('Switch CMap')
        self.getPlotItem().vb.menu.actions()[-1].triggered.connect(self.set_cmaps)
        tagsAction = self.getPlotItem().vb.menu.addAction('Dicom Tags')
        self.getPlotItem().vb.menu.actions()[-1].triggered.connect(self.set_tags)
        phasesAction = self.getPlotItem().vb.menu.addAction('Reader Phases')
        self.getPlotItem().vb.menu.actions()[-1].triggered.connect(self.set_reader_phases)
        
    def link_with_other(self, other):
        self.others = list(set(self.others+[other]))
        self.setXLink(other)
        self.setYLink(other)
        
    def set_reader_phases(self):
        self.set_reader_phase()
        for o in self.others: o.set_reader_phase()
        
    def set_reader_phase(self):
        self.reader_phases = not self.reader_phases
        self.p = self.cat.phase if self.reader_phases else 0
        self.show()
        
    def set_cmaps(self):
        self.set_cmap()
        for o in self.others: o.set_cmap()
            
    def set_cmap(self):
        self.cm = pg.colormap.get('CET-L3' if not self.cmap else 'CET-L1')
        self.lutable = self.cm.getLookupTable(0.0, 1.0)
        self.img_item.setLookupTable(self.lutable)
        self.cmap = not self.cmap
        
    def set_tags(self):
        self.set_tag()
        for o in self.others: o.set_tag()
            
    def set_tag(self):
        self.with_tags = not self.with_tags
        self.show()
        
    def set_case(self, case):
        self.case = case
        self.cat  = case.categories[0]
        self.d, self.p     = 0, 0
        self.show()
        
    def keyPressEvent(self, event):
        self.switch(event.key())
        for o in self.others: o.switch(event.key())
        
    def switch(self, key):
        left, right, up, down = 16777234, 16777236, 16777235, 16777237
        if key == up:   self.d = (self.d-1)%self.cat.nr_slices
        if key == down: self.d = (self.d+1)%self.cat.nr_slices
        if not self.reader_phases:
            if key == left:  self.p = (self.p-1)%self.cat.nr_phases
            if key == right: self.p = (self.p+1)%self.cat.nr_phases
        else:
            idx = self.case.categories.index(self.cat)
            if key == left:  self.cat = self.case.categories[(idx-1)%len(self.case.categories)]
            if key == right: self.cat = self.case.categories[(idx+1)%len(self.case.categories)]
            self.p = self.cat.phase
        self.show()
        
        
    def show(self):
        img = self.cat.get_img(self.d, self.p)
        self.img_item = pg.ImageItem(img, levels=(np.min(img),np.max(img)))
        self.img_item.setLookupTable(self.lutable)
        self.clear()
        self.addItem(self.img_item)
        
        if self.with_anno:
            anno = self.cat.get_anno(self.d, self.p)
            for cname in anno.available_contour_names():
                geo = anno.get_contour(cname)
                if geo.geom_type=='Polygon':
                    xx, yy = geo.exterior.coords.xy
                    self.plot(xx,yy, pen=self.pen)
                    for ring in geo.interiors:
                        xx, yy = ring.coords.xy
                        self.plot(xx,yy, pen=self.pen)
                if geo.geom_type=='MultiPolygon':
                    for poly in geo.geoms:
                        xx, yy = poly.exterior.coords.xy
                        self.plot(xx,yy, pen=self.pen)
                        for ring in poly.interiors:
                            xx, yy = ring.coords.xy
                            self.plot(xx,yy, pen=self.pen)
        
        info = ''
        info += '\nPhase: ' + str(self.p)
        info += '\nSlice: ' + str(self.d)
        self.text_item.setText(info)
        
        dcmtags = ''
        if self.with_tags:
            dcmtags = 'Dicom Tags'
            dcm    = self.cat.get_dcm(self.d, self.p)
            dcmtags += '\nSeriesDescr: ' + str(dcm.SeriesDescription)
        self.tags.setText(dcmtags)
        
        
        
        