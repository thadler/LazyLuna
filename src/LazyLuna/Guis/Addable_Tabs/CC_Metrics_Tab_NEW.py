from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QTextEdit, QTableView, QTableWidgetItem, QComboBox, QHeaderView, QLabel, QLineEdit, QFileDialog, QHBoxLayout, QDialog, QRadioButton, QButtonGroup, QInputDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import Qt
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg

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

from LazyLuna.Containers import Case_Comparison
from LazyLuna.Views   import *
from LazyLuna.loading_functions import *
from LazyLuna.Tables  import *
from LazyLuna.Figures import *


class CC_Metrics_Tab_NEW(QWidget):
    def __init__(self):
        super().__init__()
        self.name = 'Metric Table and Figure'
        
    def make_tab(self, gui, view, cc):
        self.gui  = gui
        self.view = view
        self.cc   = cc
        gui.tabs.addTab(self, "Case Metrics: "+str(cc.case1.case_name))
        layout = self.layout
        layout = QGridLayout(gui)
        layout.setSpacing(7)

        print('In cc metrics tab: ', view, view.contour_names)
        
        self.combobox_select_contour = QComboBox()
        self.combobox_select_contour.setStatusTip('Choose a Contour')
        #self.combobox_select_contour.addItems(['Choose a Contour'])
        self.combobox_select_contour.addItems(['Choose a Contour'] + view.contour_names)
        self.combobox_select_contour.activated[str].connect(self.recalculate_metrics_table) 
        layout.addWidget(self.combobox_select_contour, 0,0, 1,3)

        if type(view) in [SAX_CINE_View, SAX_CS_View, SAX_LGE_View]:
            self.metrics_table  = SAX_CINE_CC_Metrics_Table()
        elif type(view) in [SAX_T1_PRE_View, SAX_T1_POST_View]:
            self.metrics_table  = T1_CC_Metrics_Table()
        elif type(view) in [SAX_T2_View]:
            self.metrics_table  = T2_CC_Metrics_Table()
        else: # type(view) is LAX_CINE_View:
            self.metrics_table  = LAX_CC_Metrics_Table()
            
        self.metrics_table.calculate(view, Case_Comparison(view.customize_case(cc.case1), view.customize_case(cc.case2)), view.contour_names[0])
        
        self.metrics_TableView = QTableView()
        self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
        self.metrics_TableView.resizeColumnsToContents()
        layout.addWidget(self.metrics_TableView, 1,0, 1,3)
        
        """
        self.annotation_comparison_figure = Annotation_Comparison()
        cat = cc.case1.categories[0]
        self.annotation_comparison_canvas = FigureCanvas(self.annotation_comparison_figure)
        self.annotation_comparison_figure.set_values(view, cc, self.annotation_comparison_canvas)
        self.annotation_comparison_figure.visualize(0, view.get_categories(cc.case1, view.contour_names[0])[0], view.contour_names[0])
        self.annotation_comparison_canvas.mpl_connect('key_press_event', self.annotation_comparison_figure.keyPressEvent)
        self.annotation_comparison_canvas.setFocusPolicy(Qt.Qt.ClickFocus)
        self.annotation_comparison_canvas.setFocus()
        self.annotation_comparison_toolbar = NavigationToolbar(self.annotation_comparison_canvas, gui)
        layout.addWidget(self.annotation_comparison_canvas,  2,0, 1,1)
        layout.addWidget(self.annotation_comparison_toolbar, 3,0, 1,1)
        """
        
        self.image_viewer1 = SideBySide_PlotWidget()
        self.image_viewer1.set_case(self.cc.case1) # for all cats and both cases
        self.image_viewer2 = SideBySide_PlotWidget()
        self.image_viewer2.set_case(self.cc.case2) # for all cats and both cases
        self.image_viewer1.link_with_other(self.image_viewer2)
        self.image_viewer2.link_with_other(self.image_viewer1)
        layout.addWidget(self.image_viewer1,  2, 0, 1, 1)
        layout.addWidget(self.image_viewer2,  2, 1, 1, 1)
        
        self.setLayout(layout)
        layout.setRowStretch(2, 3)

        
    def recalculate_metrics_table(self):
        cont_name = self.combobox_select_contour.currentText()
        if cont_name=='Choose a Contour': return
        view = self.view
        cat = view.get_categories(self.cc.case1, cont_name)[0]
        cc = Case_Comparison(view.customize_case(self.cc.case1), view.customize_case(self.cc.case2))
        try:
            self.metrics_table.calculate(view, cc, cont_name)
            self.metrics_TableView.setModel(self.metrics_table.to_pyqt5_table_model())
            self.metrics_TableView.resizeColumnsToContents()
        except Exception as e: print(traceback.format_exc())
        try: self.annotation_comparison_figure.visualize(0, cat, cont_name)
        except Exception as e: print(traceback.format_exc())
        
        

class Metrics_PlotWidget(pg.PlotWidget):
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
        
        info = self.case.reader_name
        info += '\nPhase: ' + str(self.p)
        info += '\nSlice: ' + str(self.d)
        self.text_item.setText(info)
        
        dcmtags = ''
        if self.with_tags:
            dcmtags = 'Dicom Tags'
            dcm    = self.cat.get_dcm(self.d, self.p)
            dcmtags += '\nSeriesDescr: ' + str(dcm.SeriesDescription)
        self.tags.setText(dcmtags)