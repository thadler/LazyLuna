import os
import traceback

from matplotlib import gridspec, colors, cm
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection
from mpl_interactions import ioff, panhandler, zoom_factory
import matplotlib.pyplot as plt
import seaborn as sns

from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg

import numpy as np

from LazyLuna.Metrics import *
from LazyLuna import utils
from LazyLuna.Figures.Visualization import *

from LazyLuna.utils import findMainWindow, findCCsOverviewTab


class ContourComparison_PlotWidget(pg.PlotWidget):
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
        
    def set_case_comparison(self, cc):
        self.cc = cc
        self.cat1  = cc.case1.categories[0]
        self.cat1  = cc.case2.categories[0]
        self.d, self.p     = 0, 0
        self.show()
        
    def keyPressEvent(self, event):
        self.switch(event.key())
        for o in self.others: o.switch(event.key())
        
    def switch(self, key):
        left, right, up, down = 16777234, 16777236, 16777235, 16777237
        if key == up:   self.d = (self.d-1)%self.cat1.nr_slices
        if key == down: self.d = (self.d+1)%self.cat1.nr_slices
        if not self.reader_phases:
            if key == left:  self.p = (self.p-1)%self.cat1.nr_phases
            if key == right: self.p = (self.p+1)%self.cat1.nr_phases
        else:
            idx = self.cc.case1.categories.index(self.cat)
            if key == left:  
                self.cat1 = self.cc.case1.categories[(idx-1)%len(self.cc.case1.categories)]
                self.cat2 = self.cc.case2.categories[(idx-1)%len(self.cc.case2.categories)]
            if key == right: 
                self.cat1 = self.cc.case1.categories[(idx+1)%len(self.cc.case1.categories)]
                self.cat2 = self.cc.case2.categories[(idx+1)%len(self.cc.case2.categories)]
            self.p1 = self.cat1.phase
            self.p2 = self.cat2.phase
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