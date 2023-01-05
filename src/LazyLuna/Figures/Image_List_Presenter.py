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


class Image_List_Presenter(Visualization):
    def set_values(self, images, canvas):
        self.imgs = images
        self.canvas = canvas
        self.add_annotation = True
        self.nr = 0
    
    def visualize(self, nr, debug=False):
        """Presents an instance of a list images
        
        Note:
            requires setting values first:
            - self.set_values(images, canvas)
        
        Args:
            nr (int): the n-th image to visualize
        """
        if debug: print('Start'); st = time()
        self.clf()
        ax = self.add_subplot(111)
        img = self.imgs[nr]
        h, w   = img.shape
        extent = (0, w, h, 0)
        ax.imshow(img, 'gray', extent=extent)
        #self.suptitle('Image: ' + str(nr))
        """
        if self.add_annotation:
            anno1.plot_all_contour_outlines(ax) # looks like overlooked slices when different phases for RV and LV
            anno2.plot_all_points(ax)
        """
        ax.set_xticks([]); ax.set_yticks([])
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : self.nr = (self.nr - 1) %len(self.imgs)
        if event.key == 'down' : self.nr = (self.nr + 1) %len(self.imgs)
        if event.key == 'left' : self.nr = (self.nr - 1) %len(self.imgs)
        if event.key == 'right': self.nr = (self.nr + 1) %len(self.imgs)
        self.visualize(self.nr)

