import os
import traceback

from matplotlib import gridspec, colors, cm
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection
from mpl_interactions import ioff, panhandler, zoom_factory
import matplotlib.pyplot as plt
import seaborn as sns

import shapely
from shapely.geometry import Polygon
from scipy.stats import probplot
import numpy as np
import pandas

from LazyLuna.Tables import *
from LazyLuna.Metrics import *
from LazyLuna import utils
from LazyLuna.Figures.Visualization import *

from LazyLuna.utils import findMainWindow, findCCsOverviewTab


class Basic_Presenter(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        self.cmap           = 'gray'
        self.dcm_tags       = False
        self.info           = True
        self.zoom           = False
        self.all_phases     = False
        self.p1, self.p2    = 0, 0
    
    def visualize(self, slice_nr, category, debug=False):
        """Takes a case_comparison and presents the annotations of both readers side by side
        
        Note:
            requires setting values first:
            - self.set_values(View, Case_Comparison, canvas)
        
        Args:
            slice_nr (int): slice depth
            p1 (int): phase of first case
            p2 (int): phase of second case
        """
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category = slice_nr, category
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec   = gridspec.GridSpec(nrows=1, ncols=2, figure=self, hspace=0.0)
        self.ax1    = self.add_subplot(spec[0,0])
        self.ax2    = self.add_subplot(spec[0,1], sharex=self.ax1, sharey=self.ax1)
        p1, p2 = (self.p1, self.p2) if self.all_phases else (cat1.get_phase(), cat2.get_phase())
        img1   = cat1.get_img (slice_nr, p1)
        img2   = cat2.get_img (slice_nr, p2)
        anno1  = cat1.get_anno(slice_nr, p1)
        anno2  = cat2.get_anno(slice_nr, p2)
        h, w   = img1.shape
        extent = (0, w, h, 0)
        vmin, vmax = (min(np.min(img1), np.min(img2)), max(np.max(img1), np.max(img2))) if self.cmap=='gray' else (0, 2000)
        self.ax1.imshow(img1, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        self.ax2.imshow(img2, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        if self.add_annotation:
            anno1.plot_contours(self.ax1) # looks like overlooked slices when different phases for RV and LV
            anno2.plot_contours(self.ax2)
            anno1.plot_points(self.ax1)
            anno2.plot_points(self.ax2)
        for ax in [self.ax1, self.ax2]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        
        if self.zoom: 
            for ax in [self.ax1, self.ax2]: ax.set_xlim(self.xlims); ax.set_ylim(self.ylims); ax.invert_yaxis()
        
        self.ax1.text(x=w//2, y=5+(self.ylims[0]-3 if self.zoom else 0), 
                      s=self.cc.case1.reader_name, c='w', fontsize=8, bbox=dict(facecolor='k'))
        self.ax2.text(x=w//2, y=5+(self.ylims[0]-3 if self.zoom else 0), 
                      s=self.cc.case2.reader_name, c='w', fontsize=8, bbox=dict(facecolor='k'))
        
        if self.info:
            xx, yy = (self.xlims[0] if self.zoom else 2), (self.ylims[0]+3 if self.zoom else 0)
            s  = 'Slice: ' + str(slice_nr) + '\nPhase: ' + str(p1)
            self.ax1.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k'),
                          horizontalalignment='left', verticalalignment='top')
            s  = 'Slice: ' + str(slice_nr) + '\nPhase: ' + str(p2)
            self.ax2.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k'),
                          horizontalalignment='left', verticalalignment='top')
        
        if self.dcm_tags:
            dcm = cat1.get_dcm(slice_nr, p1)
            xx, yy = (self.xlims[0] if self.zoom else 2), (self.ylims[1]-3 if self.zoom else h)
            s  = 'Series Descr.:   ' + dcm.SeriesDescription+'\n'
            s += 'Slice Thickness: ' + f"{dcm.SliceThickness:.2f}"+'\n'
            s += 'Slice Position:  ' + f"{dcm.SliceLocation:.2f}"+'\n'
            s += 'Pixel Size:      ' + str([float(f"{ps:.2f}") for ps in dcm.PixelSpacing])
            self.ax1.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k', edgecolor='w', linewidth=1),
                          horizontalalignment='left', verticalalignment='bottom')

        
        def onclick(event):
            if event.dblclick: # image storing ("tracing") with LL
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name=self.cc.case1.case_name+' category: ' + cat1.name + ', slice: ' + str(slice_nr) + ' annotation comparison')
                except: print(traceback.format_exc()); pass
            if event.button == 3: # right click
                try:
                    if not hasattr(self,'menu'):
                        from PyQt5.QtGui import QCursor
                        from PyQt5 import QtWidgets
                        pos = QCursor.pos()
                        self.menu = QtWidgets.QMenu()
                        self.menu.addAction("Show Dicom Tags", self.present_dicom_tags)
                        self.menu.addAction("Zoom", self.set_zoom)
                        self.menu.addSeparator()
                        self.menu.addAction("Select Colormap", self.select_cmap)
                        self.menu.addAction("Reader / All Phases", self.set_phase_choice)
                        self.menu.move(pos)
                    self.menu.show()
                except: print(traceback.format_exc()); pass
                
        self.canvas.mpl_connect('button_press_event', onclick)
        self.patch.set_facecolor('black')
        self.subplots_adjust(top=1, bottom=0, wspace=0.02)
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        slice_nr, category = self.slice_nr, self.category
        categories = self.cc.case1.categories
        idx = categories.index(category)
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'z'    : self.set_zoom()
        if event.key == 'up'   : slice_nr = (slice_nr-1) % category.nr_slices
        if event.key == 'down' : slice_nr = (slice_nr+1) % category.nr_slices
        if not self.all_phases:
            if event.key == 'left' : category = categories[(idx-1)%len(categories)]
            if event.key == 'right': category = categories[(idx+1)%len(categories)]
            cat1, cat2 = self.cc.get_categories_by_example(category)
            self.p1, self.p2 = cat1.get_phase(), cat2.get_phase()
        else:
            if event.key == 'left' : self.p1 = self.p2 = (self.p1-1)%category.nr_phases
            if event.key == 'right': self.p1 = self.p2 = (self.p1+1)%category.nr_phases
        self.visualize(slice_nr, category)
    
    def select_cmap(self):
        if self.cmap != 'gray': self.cmap = 'gray'
        else:                   self.cmap = self.view.cmap
        self.visualize(self.slice_nr, self.category)
        
    def present_dicom_tags(self):
        self.dcm_tags = not self.dcm_tags
        self.visualize(self.slice_nr, self.category)
        
    def set_zoom(self):
        self.zoom = not self.zoom
        if not self.zoom: self.visualize(self.slice_nr, self.category); return
        bounds = []
        for cat1,cat2 in zip(self.cc.case1.categories, self.cc.case2.categories):
            for d in range(cat1.nr_slices):
                anno = cat1.get_anno(d,cat1.get_phase())
                for cname in anno.available_contour_names(): bounds.append(anno.get_contour(cname).bounds)
                anno = cat2.get_anno(d,cat2.get_phase())
                for cname in anno.available_contour_names(): bounds.append(anno.get_contour(cname).bounds)
        bounds = np.asarray(bounds)
        xmin, ymin, _, _ = np.min(bounds, axis=0); _, _, xmax, ymax = np.max(bounds, axis=0)
        h,w = cat1.get_img(d,cat1.get_phase()).shape
        self.xlims, self.ylims = (max(xmin-10,0), min(xmax+10,w)), (max(ymin-10,0), min(ymax+10,h))
        self.visualize(self.slice_nr, self.category)
        
    def set_phase_choice(self):
        self.all_phases = not self.all_phases
        if self.all_phases: self.p1 = self.p2 = 0
        else: self.p1, self.p2 = self.cc.case1.categories[0].get_phase(), self.cc.case2.categories[0].get_phase()
        self.visualize(self.slice_nr, self.category)

    def store(self, storepath, figurename='_basic_presentation.png'):
        self.patch.set_facecolor('black')
        self.subplots_adjust(top=1, bottom=0, wspace=0.02)
        figname = self.cc.case1.case_name+'_Category_' + self.category.name + '_slice_' + str(self.slice_nr)+figurename
        self.savefig(os.path.join(storepath, figname), dpi=300, facecolor="#000000")
        return os.path.join(storepath, figname)
    