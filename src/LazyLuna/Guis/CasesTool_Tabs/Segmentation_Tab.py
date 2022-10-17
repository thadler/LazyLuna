from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QApplication, QLabel, QToolBar, QAction, QStatusBar, qApp, QStyle, QCheckBox, QGridLayout, QPushButton, QLineEdit, QFrame, QFileSystemModel, QTreeView, QDirModel, QTableView, QHeaderView, QFileDialog, QDialog, QToolButton, QSizePolicy, QInputDialog, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QDir, QSortFilterProxyModel, pyqtSignal

import pyqtgraph as pg

import os
from pathlib import Path
import sys
import copy
import inspect
from operator import itemgetter
import traceback

import pandas
import numpy as np

from LazyLuna.loading_functions import get_case_info
from LazyLuna.Tables import Table
from LazyLuna import Views

        
class Segmentation_TabWidget(QWidget):
    def __init__(self, parent, dicomfolder_path, dcms):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.layout.setSpacing(7)
        
        # Setting some variables
        self.dicomfolder_path = dicomfolder_path
        self.dcms = dcms
        self.current_cont_type = 'other'
        
        
        rv_endo_action = QAction(QIcon('eye.png'), "&Set RV ENDO", self)
        rv_endo_action.setStatusTip("RV Contours")
        rv_endo_action.triggered.connect(self.set_rv_endo)
        
        lv_endo_action = QAction(QIcon('eye.png'), "&Set LV ENDO", self)
        lv_endo_action.setStatusTip("LV Endo Contours")
        lv_endo_action.triggered.connect(self.set_lv_endo)
        
        lv_epi_action = QAction(QIcon('eye.png'), "&Set LV EPI", self)
        lv_epi_action.setStatusTip("LV Epi Contours")
        lv_epi_action.triggered.connect(self.set_lv_epi)
        
        ##############
        ## Toolbar  ##
        ##############
        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setIconSize(QSize(28, 28))
        self.layout.addWidget(self.toolbar, 0,0, 1,3)
        fontsize = 13
        b1 = QToolButton(); b1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b1.setFont(QFont('', fontsize))
        b1.setDefaultAction(rv_endo_action)
        self.toolbar.addWidget(b1)
        b2 = QToolButton(); b2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b2.setFont(QFont('', fontsize))
        b2.setDefaultAction(lv_endo_action)
        self.toolbar.addWidget(b2)
        b3 = QToolButton(); b3.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding); b3.setFont(QFont('', fontsize))
        b3.setDefaultAction(lv_epi_action)
        self.toolbar.addWidget(b3)
        
        self.layout.addWidget(QHLine(), 1, 0, 1, 10)
        self.selected_view_lbl  = QLabel('Foldername: ')
        self.selected_view_text = QLabel(dicomfolder_path)
        self.layout.addWidget(self.selected_view_lbl,  2, 0, 1,1)
        self.layout.addWidget(self.selected_view_text, 2, 1, 1,1)
        self.layout.addWidget(QHLine(), 3, 0, 1, 10)
        
        
        self.image_viewer = CustomPlotWidget()
        
        org = Organizer(dcms)
        imgs = [[org.get_img(d,p) for p in range(org.nr_phases)] for d in range(org.nr_slices)]
        self.image_viewer.set_images(imgs)
        
        self.image_viewer.setAspectLocked()
        self.image_viewer.getPlotItem().hideAxis('bottom')
        self.image_viewer.getPlotItem().hideAxis('left')
        self.image_viewer.invertY(True)   # vertical axis counts top to bottom
        self.label = pg.TextItem(text="X: {} \nY: {}".format(0, 0))
        self.image_viewer.addItem(self.label)
        self.image_viewer.scene().sigMouseMoved.connect(self.mouse_moved)
        self.image_viewer.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.image_viewer.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.layout.addWidget(self.image_viewer,  4, 0, 10, 5)
        
        
        
    def mouse_moved(self, evt):
        vb = self.image_viewer.plotItem.vb
        if self.image_viewer.sceneBoundingRect().contains(evt):
            mouse_point = vb.mapSceneToView(evt)
            self.label.setHtml(f"<p style='color:white'>X： {mouse_point.x()} <br> Y: {mouse_point.y()}</p>")

    def mouse_clicked(self, evt):
        vb = self.image_viewer.plotItem.vb
        scene_coords = evt.scenePos()
        if self.image_viewer.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            self.image_viewer.curr_cont.append([mouse_point.x(),mouse_point.y()])
            self.image_viewer.plot_all(self.current_cont_type)
        if evt.double():
            self.image_viewer.curr_cont.append(self.image_viewer.curr_cont[0])
            self.image_viewer.anno[self.current_cont_type].append(self.image_viewer.curr_cont)
            self.image_viewer.plot_all(self.current_cont_type)
            self.image_viewer.curr_cont = []
        
        
    def calculate_table(self):
        rows = []
        columns = ['Casename', 'Readername']+[cr.name for cr in self.case.crs]
        rows = [[self.case.case_name, self.case.reader_name]+[cr.get_val(string=True) for cr in self.case.crs]]
        self.t  = Table()
        self.t.df = pandas.DataFrame(rows, columns=columns)
        self.tableView.setModel(self.t.to_pyqt5_table_model())
        
        
    def set_rv_endo(self): self.current_cont_type = 'rv_endo'
    def set_lv_endo(self): self.current_cont_type = 'lv_endo'
    def set_lv_epi(self):  self.current_cont_type = 'lv_epi'
    

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

        
class CustomPlotWidget(pg.PlotWidget):
    keyPressed = pyqtSignal(int)
    def __init__(self):
        super().__init__()

    def set_images(self, imgs):
        self.images = imgs
        self.d, self.p = 0, 0
        self.nr_slices, self.nr_phases = len(imgs), len(imgs[0])
        self.annotations = [[None for i in range(self.nr_phases)] for j in range(self.nr_slices)]
        self.set_annotation()
        self.show()
        
    def keyPressEvent(self, event):
        event = event.key()
        left, right, up, down = 16777234, 16777236, 16777235, 16777237
        if event == left:  self.p = (self.p-1)%self.nr_phases
        if event == right: self.p = (self.p+1)%self.nr_phases
        if event == up:    self.d = (self.d-1)%self.nr_slices
        if event == down:  self.d = (self.d+1)%self.nr_slices
        self.curr_cont = []
        self.set_annotation()
        self.show()
        self.plot_all('other')
        
    def show(self):
        self.clear()
        img = self.images[self.d][self.p]
        img = pg.ImageItem(img, levels=(np.min(img),np.max(img)))
        self.addItem(img) 
        
    def set_annotation(self):
        d, p = self.d, self.p
        self.anno = self.annotations[d][p]
        self.curr_cont = []
        if self.anno is None:
            self.annotations[d][p] = {'rv_endo': [],'lv_endo': [],'lv_epi': [], 'other':[]}
            self.anno = self.annotations[d][p]
            
    def plot_all(self, conttype):
        for k in self.anno.keys():
            c = 'r' if k=='rv_endo' else 'y' if k=='lv_endo' else 'g' if k=='lv_epi' else 'w'
            pen = pg.mkPen(c, width=3, style=Qt.DashLine)
            for cont in self.anno[k]:
                xs = [c[0] for c in cont]; ys = [c[1] for c in cont]
                self.plot(xs, ys, symbol='o', pen=pen)
        k = conttype
        c = 'r' if k=='rv_endo' else 'y' if k=='lv_endo' else 'g' if k=='lv_epi' else 'w'
        pen = pg.mkPen(c, width=3, style=Qt.DashLine)
        xs = [c[0] for c in self.curr_cont]; ys = [c[1] for c in self.curr_cont]
        self.plot(xs, ys, symbol='o', pen=pen)
    
            
        
class Organizer:
    def __init__(self, dcms):
        self.sop2depthandtime = self.get_sop2depthandtime(dcms)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.identify_missing_slices()

    def get_sop2depthandtime(self, dcms):
        # returns dict sop --> (depth, time)
        self.imgs = {dcm.SOPInstanceUID : dcm for dcm in dcms}
        sortable  = [[k,v.SliceLocation,v.InstanceNumber] for k,v in self.imgs.items()]
        slice_nrs = {x:i for i,x in enumerate(sorted(list(set([x[1] for x in sortable]))))}
        sortable  = [s+[slice_nrs[s[1]]] for s in sortable]
        sortable_by_slice = {d:[] for d in slice_nrs.values()}
        for s in sortable: sortable_by_slice[s[-1]].append(s)
        for d in range(len(sortable_by_slice.keys())):
            sortable_by_slice[d] = sorted(sortable_by_slice[d], key=lambda s:s[2])
            for p in range(len(sortable_by_slice[d])):
                sortable_by_slice[d][p].append(p)
        sop2depthandtime = dict()
        for d in range(len(sortable_by_slice.keys())):
            for s in sortable_by_slice[d]:
                sop2depthandtime[s[0]] = (s[-2],s[-1])
        # potentially flip slice direction: base top x0<x1, y0>y1, z0>z1, apex top x0>x1, y0<y1, z0<z1
        depthandtime2sop = {v:k for k,v in sop2depthandtime.items()}
        img1, img2 = self.imgs[depthandtime2sop[(0,0)]], self.imgs[depthandtime2sop[(1,0)]]
        img1x,img1y,img1z = list(map(float,img1.ImagePositionPatient))
        img2x,img2y,img2z = list(map(float,img2.ImagePositionPatient))
        if img1x<img2x and img1y>img2y and img1z>img2z: pass
        else: #img1x>img2x or img1y<img2y or img1z<img2z:
            max_depth = max(sortable_by_slice.keys())
            for sop in sop2depthandtime.keys():
                sop2depthandtime[sop] = (max_depth-sop2depthandtime[sop][0], sop2depthandtime[sop][1])
        return sop2depthandtime

    def set_image_height_width_depth(self):
        dcm = self.get_dcm(0,0)
        self.height, self.width    = dcm.pixel_array.shape
        self.pixel_h, self.pixel_w = list(map(float, dcm.PixelSpacing))
        try: self.spacing_between_slices = dcm.SpacingBetweenSlices
        except Exception as e: self.spacing_between_slices = dcm.SliceThickness; print(traceback.print_exc())
        try: self.slice_thickness = dcm.SliceThickness
        except Exception as e: print(traceback.print_exc())
            
    def identify_missing_slices(self):
        self.missing_slices = []
        for d in range(self.nr_slices-1): # if only one slice range is empty
            dcm1, dcm2 = self.get_dcm(d,   0), self.get_dcm(d+1, 0)
            curr_spacing = round(np.abs(dcm1.SliceLocation - dcm2.SliceLocation), 2)
            if round(curr_spacing / self.spacing_between_slices) != 1:
                for m in range(int(round(curr_spacing / self.spacing_between_slices))-1):
                    self.missing_slices += [(d + m)]
        
    def set_nr_slices_phases(self):
        dat = list(self.depthandtime2sop.keys())
        self.nr_phases = max(dat, key=itemgetter(1))[1]+1
        self.nr_slices = max(dat, key=itemgetter(0))[0]+1
        
    def get_dcm(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.imgs[sop]

    def get_img(self, slice_nr, phase_nr, value_normalize=True, window_normalize=True):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.imgs[sop].pixel_array

