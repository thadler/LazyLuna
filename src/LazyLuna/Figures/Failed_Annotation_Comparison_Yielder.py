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

from LazyLuna.utils import PolygonPatch


class Failed_Annotation_Comparison_Yielder(Visualization):
    def set_values(self, view, ccs):
        self.ccs     = ccs
        self.view    = view
        self.yielder = self.initialize_yeild_next()
        self.add_annotation = True
    
    def visualize(self, cc, slice_nr, category, contour_name, debug=False):
        """Takes a list of case_comparisons and presents a Boxplot for a Clinical Result
        
        Note:
            requires setting values first:
            - self.set_values(View, list of Case_Comparisons)
        
        Args:
            cc (LazyLuna.Containers.Case_Comparison): - current - case comparison for visualization
            slice_nr (int): slice depth
            category (LazyLuna.Categories.Category): a case's category
            contour_type (str): contour type
        """
        if debug: print('Start'); st = time()
        self.clear()
        self.cc, self.slice_nr, self.category, self.contour_name = cc, slice_nr, category, contour_name
        rows, columns = 1, 4
        self.set_size_inches(w=columns*11.0, h=rows*11.0)
        axes = self.subplots(rows, columns)
        axes[0].get_shared_x_axes().join(*axes); axes[0].get_shared_y_axes().join(*axes)
        cat1, cat2 = self.cc.get_categories_by_example(category)
        img1  = cat1.get_img (slice_nr, cat1.get_phase())
        img2  = cat2.get_img (slice_nr, cat2.get_phase())
        anno1 = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2 = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w  = img1.shape
        extent=(0, w, h, 0)
        axes[0].imshow(img1,'gray', extent=extent); axes[1].imshow(img1,'gray', extent=extent)
        axes[2].imshow(img2,'gray', extent=extent); axes[3].imshow(img1,'gray', extent=extent)
        self.suptitle('Case: ' + cc.case1.case_name + ', Contour: ' + contour_name + ', category: ' + cat1.name + ', slice: ' + str(slice_nr), fontsize=30)
        if self.add_annotation:
            anno1.plot_face   (axes[0],        contour_name, alpha=0.4, c='r')
            anno1.plot_cont_comparison(axes[1], anno2, contour_name, alpha=0.4)
            anno2.plot_face   (axes[2],        contour_name, alpha=0.4, c='b')
        for ax in axes: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        patches = [PolygonPatch(d, c=c, alpha=0.4) for c in ['red', 'green', 'blue']]
        handles = [self.cc.case1.reader_name,
                   self.cc.case1.reader_name+' & '+self.cc.case2.reader_name,
                   self.cc.case2.reader_name]
        axes[3].legend(patches, handles, fontsize=20)
        self.tight_layout()
        if debug: print('Took: ', time()-st)
        
    def initialize_yeild_next(self, rounds=None):
        dsc, hd, mld = DiceMetric(), HausdorffMetric(), mlDiffMetric()
        count = 0
        while (rounds is None) or (count<rounds):
            for cc in self.ccs:
                c1, c2    = cc.case1, cc.case2
                nr_slices = c1.categories[0].nr_slices
                case_name = c1.case_name
                for sl_nr in range(nr_slices):
                    for contname in self.view.contour_names:
                        cats1 = self.view.get_categories(c1, contname)
                        cats2 = self.view.get_categories(c2, contname)
                        for cat1, cat2 in zip(cats1, cats2):
                            p1, p2 = cat1.phase, cat2.phase
                            dcm    = cat1.get_dcm(sl_nr, p1)
                            cont1  = cat1.get_anno(sl_nr, p1).get_contour(contname)
                            cont2  = cat2.get_anno(sl_nr, p2).get_contour(contname)
                            dice   = dsc.get_val(cont1, cont2, dcm)
                            mldiff = np.abs(mld.get_val(cont1, cont2, dcm))
                            hdm    = hd.get_val(cont1, cont2, dcm)
                            if dice<70 and mldiff>1.2:
                                yield cc, sl_nr, cat1, contname
                            if contname in ['la','ra'] and (hdm>3.5 or dice<60):
                                yield cc, sl_nr, cat1, contname
            count += 1
                
    def store(self, storepath):
        self.yielder = self.initialize_yeild_next(rounds=1)
        for cc, slice_nr, category, contour_name in self.yielder:
            figname = cc.case1.case_name+'_'+str(slice_nr)+'_'+category.name+'_'+contour_name
            self.visualize(cc, slice_nr, category, contour_name)
            self.savefig(os.path.join(storepath, figname+'.png'), dpi=100, facecolor="#FFFFFF")
    