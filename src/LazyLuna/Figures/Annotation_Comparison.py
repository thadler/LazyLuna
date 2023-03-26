import os
import traceback

from matplotlib import gridspec, colors, cm
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection
from mpl_interactions import ioff, panhandler, zoom_factory
import matplotlib.pyplot as plt
import seaborn as sns

import matplotlib
from matplotlib.patches import PathPatch
from matplotlib.path import Path

import shapely
from shapely.geometry import Polygon
from scipy.stats import probplot
import numpy as np
import pandas

from LazyLuna.Tables import *
from LazyLuna.Metrics import *
from LazyLuna import utils
from LazyLuna.Figures.Visualization import *

from LazyLuna.utils import findMainWindow, findCCsOverviewTab, PolygonPatch
    

class Annotation_Comparison(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        self.cmap           = 'gray'
        self.dcm_tags       = False
        self.info           = True
        self.zoom           = False
    
    def visualize(self, slice_nr, category, contour_name, debug=False):
        """Takes a case_comparison and presents a colourful annotation comparison on their respective images
        
        Note:
            requires setting values first:
            - self.set_values(View, Case_Comparison, canvas)
        
        Args:
            slice_nr (int): slice depth
            category (LazyLuna.Categories.Category): a case's category
            contour_name (str): countour type
        """
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category, self.contour_name = slice_nr, category, contour_name
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec = gridspec.GridSpec(nrows=1, ncols=4, figure=self, hspace=0.0)
        self.ax1  = self.add_subplot(spec[0,0])
        self.ax2  = self.add_subplot(spec[0,1], sharex=self.ax1, sharey=self.ax1)
        self.ax3  = self.add_subplot(spec[0,2], sharex=self.ax1, sharey=self.ax1)
        self.ax4  = self.add_subplot(spec[0,3], sharex=self.ax1, sharey=self.ax1)
        img1  = cat1.get_img (slice_nr, cat1.get_phase())
        img2  = cat2.get_img (slice_nr, cat2.get_phase())
        anno1 = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2 = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w  = img1.shape
        extent=(0, w, h, 0)
        vmin, vmax = (min(np.min(img1), np.min(img2)), max(np.max(img1), np.max(img2))) if self.cmap=='gray' else (0, 2000)
        self.ax1.imshow(img1, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        self.ax2.imshow(img1, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        self.ax3.imshow(img2, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        self.ax4.imshow(img1, self.cmap, extent=extent, vmin=vmin, vmax=vmax)
        #self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            if self.cmap=='gray':
                anno1.plot_face           (self.ax1,        contour_name, alpha=0.4, c='r')
                anno1.plot_cont_comparison(self.ax2, anno2, contour_name, alpha=0.4)
                anno2.plot_face           (self.ax3,        contour_name, alpha=0.4, c='b')
            else:
                anno1.plot_contours       (self.ax1,        contour_name, c='w')
                anno1.plot_cont_comparison(self.ax2, anno2, contour_name, colors=['g','white','black'], alpha=1.0)
                anno2.plot_contours       (self.ax3,        contour_name, c='k')
            anno1.plot_points(self.ax1)
            anno2.plot_points(self.ax3)
        for ax in [self.ax1, self.ax2, self.ax3]: ax.set_xticks([]); ax.set_yticks([])
        
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        if self.cmap=='gray': patches = [PolygonPatch(d, c=c, alpha=0.4) for c in ['red', 'green', 'blue']]
        else:                 patches = [PolygonPatch(d, c=c, alpha=1.0) for c in ['white', 'green', 'black']]
        handles = [self.cc.case1.reader_name,
                   self.cc.case1.reader_name+' & '+self.cc.case2.reader_name,
                   self.cc.case2.reader_name]
        self.ax4.legend(patches, handles)
        
        if self.zoom: 
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]: 
                ax.set_xlim(self.xlims); ax.set_ylim(self.ylims); ax.invert_yaxis()
                
        if self.info:
            xx, yy = (self.xlims[0] if self.zoom else 2), (self.ylims[0]+3 if self.zoom else 0)
            s  = 'Label: ' + cat1.name + '\nSlice: ' + str(slice_nr) + '\nPhase: ' + str(cat1.get_phase())
            self.ax1.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k'),
                          horizontalalignment='left', verticalalignment='top')
            s  = 'Label: ' + cat2.name + '\nSlice: ' + str(slice_nr) + '\nPhase: ' + str(cat2.get_phase())
            self.ax3.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k'),
                          horizontalalignment='left', verticalalignment='top')
        
        if self.dcm_tags:
            dcm = cat1.get_dcm(slice_nr, cat1.get_phase())
            xx, yy = (self.xlims[1] if self.zoom else w-2), (self.ylims[1]-3 if self.zoom else h)
            s  = 'Series Descr.:   ' + dcm.SeriesDescription+'\n'
            s += 'Slice Thickness: ' + f"{dcm.SliceThickness:.2f}"+'\n'
            s += 'Slice Position:  ' + f"{dcm.SliceLocation:.2f}"+'\n'
            s += 'Pixel Size:      ' + str([float(f"{ps:.2f}") for ps in dcm.PixelSpacing])
            self.ax4.text(x=xx, y=yy, s=s, c='w', fontsize=8, bbox=dict(facecolor='k', edgecolor='w', linewidth=1),
                          horizontalalignment='right', verticalalignment='bottom')
        
        def onclick(event):
            if event.dblclick:
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
                        self.menu.addAction("Reader / All Phases")
                        self.menu.move(pos)
                    self.menu.show()
                except: print(traceback.format_exc()); pass
                
        self.canvas.mpl_connect('button_press_event', onclick)
        self.patch.set_facecolor('black')
        self.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0.005)
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        slice_nr, category, contour_name = self.slice_nr, self.category, self.contour_name
        categories = self.view.get_categories(self.cc.case1, self.contour_name)
        idx = categories.index(category)
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : slice_nr = (slice_nr-1) % category.nr_slices
        if event.key == 'down' : slice_nr = (slice_nr+1) % category.nr_slices
        if event.key == 'left' : category = categories[(idx-1)%len(categories)]
        if event.key == 'right': category = categories[(idx+1)%len(categories)]
        if event.key == 'z'    : self.set_zoom()
        self.visualize(slice_nr, category, contour_name)
        
    def select_cmap(self):
        if self.cmap != 'gray': self.cmap = 'gray'
        else:                   self.cmap = self.view.cmap
        self.visualize(self.slice_nr, self.category, self.contour_name)
        
    def present_dicom_tags(self):
        self.dcm_tags = not self.dcm_tags
        self.visualize(self.slice_nr, self.category, self.contour_name)
        
    def set_zoom(self):
        self.zoom = not self.zoom
        if not self.zoom: self.visualize(self.slice_nr, self.category, self.contour_name); return
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
        self.visualize(self.slice_nr, self.category, self.contour_name)

    
    def store(self, storepath, figurename='_annotation_comparison.png'):
        self.tight_layout()
        figname = self.cc.case1.case_name+'_Category_' + self.category.name + '_slice_' + str(self.slice_nr)+figurename
        self.savefig(os.path.join(storepath, figname), dpi=300, facecolor="#000000")
        return os.path.join(storepath, figname)
    