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
from LazyLuna.Annotation import *


class DCMs_list_Annos_Presenter(Visualization):
    def set_values(self, canvas, dcms, annos=None):
        self.canvas = canvas
        self.dcms = dcms
        self.annos = annos
        self.nr = 0
        self.add_annotation = True
    
    def visualize(self, nr, debug=False):
        """Presents an instance of a list images
        
        Note:
            requires setting values first:
            - self.set_values(images, canvas)
        
        Args:
            nr (int): the n-th image to visualize
        """
        self.clf()
        ax  = self.add_subplot(111)
        dcm = self.dcms[nr]
        sop = dcm.SOPInstanceUID
        img = dcm.pixel_array
        try:    h, w    = img.shape
        except: h, w, _ = img.shape
        extent = (0, w, h, 0)
        ax.imshow(img, 'gray', extent=extent)
        if self.annos is not None and sop in self.annos.keys() and self.add_annotation:
            anno = Annotation(self.annos[sop])
            anno.plot_contours(ax)
            anno.plot_points(ax)
        ax.set_xticks([]); ax.set_yticks([])
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        
    def keyPressEvent(self, event):
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : self.nr = (self.nr - 1) %len(self.dcms)
        if event.key == 'down' : self.nr = (self.nr + 1) %len(self.dcms)
        if event.key == 'left' : self.nr = (self.nr - 1) %len(self.dcms)
        if event.key == 'right': self.nr = (self.nr + 1) %len(self.dcms)
        self.visualize(self.nr)

