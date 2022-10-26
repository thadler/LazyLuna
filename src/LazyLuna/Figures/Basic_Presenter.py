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


class Basic_Presenter(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
    
    def visualize(self, slice_nr, category, debug=False):
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category = slice_nr, category
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec   = gridspec.GridSpec(nrows=1, ncols=2, figure=self, hspace=0.0)
        ax1    = self.add_subplot(spec[0,0])
        ax2    = self.add_subplot(spec[0,1], sharex=ax1, sharey=ax1)
        img1   = cat1.get_img (slice_nr, cat1.get_phase())
        img2   = cat2.get_img (slice_nr, cat2.get_phase())
        anno1  = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2  = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w   = img1.shape
        extent = (0, w, h, 0)
        ax1.imshow(img1,'gray', extent=extent); ax2.imshow(img2,'gray', extent=extent)
        self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_contours(ax1) # looks like overlooked slices when different phases for RV and LV
            anno2.plot_contours(ax2)
            anno1.plot_points(ax1)
            anno2.plot_points(ax2)
        ax1.set_title(self.cc.case1.reader_name)
        ax2.set_title(self.cc.case2.reader_name)
        for ax in [ax1, ax2]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        slice_nr, category = self.slice_nr, self.category
        categories = self.cc.case1.categories
        idx = categories.index(category)
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : slice_nr = (slice_nr-1) % category.nr_slices
        if event.key == 'down' : slice_nr = (slice_nr+1) % category.nr_slices
        if event.key == 'left' : category = categories[(idx-1)%len(categories)]
        if event.key == 'right': category = categories[(idx+1)%len(categories)]
        #print('In key press: ', slice_nr, category)
        self.visualize(slice_nr, category)
