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
from descartes import PolygonPatch
from scipy.stats import probplot
import numpy as np
import pandas

from LazyLuna.Tables import *
from LazyLuna.Metrics import *
from LazyLuna import utils
from LazyLuna.Figures.Visualization import *


class Annotation_Comparison(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
    
    def visualize(self, slice_nr, category, contour_name, debug=False):
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category, self.contour_name = slice_nr, category, contour_name
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec = gridspec.GridSpec(nrows=1, ncols=4, figure=self, hspace=0.0)
        ax1  = self.add_subplot(spec[0,0])
        ax2  = self.add_subplot(spec[0,1], sharex=ax1, sharey=ax1)
        ax3  = self.add_subplot(spec[0,2], sharex=ax1, sharey=ax1)
        ax4  = self.add_subplot(spec[0,3], sharex=ax1, sharey=ax1)
        img1  = cat1.get_img (slice_nr, cat1.get_phase())
        img2  = cat2.get_img (slice_nr, cat2.get_phase())
        anno1 = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2 = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w  = img1.shape
        extent=(0, w, h, 0)
        ax1.imshow(img1,'gray', extent=extent); ax2.imshow(img1,'gray', extent=extent)
        ax3.imshow(img2,'gray', extent=extent); ax4.imshow(img1,'gray', extent=extent)
        self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_face           (ax1,        contour_name, alpha=0.4, c='r')
            anno1.plot_cont_comparison(ax2, anno2, contour_name, alpha=0.4)
            anno2.plot_face           (ax3,        contour_name, alpha=0.4, c='b')
            anno1.plot_points(ax1)
            anno2.plot_points(ax3)
        for ax in [ax1, ax2, ax3]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        
        patches = [PolygonPatch(d,facecolor=c, edgecolor=c,  alpha=0.4) for c in ['red', 'green', 'blue']]
        handles = [self.cc.case1.reader_name,
                   self.cc.case1.reader_name+' & '+self.cc.case2.reader_name,
                   self.cc.case2.reader_name]
        ax4.legend(patches, handles)
        self.tight_layout()
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
        self.visualize(slice_nr, category, contour_name)
