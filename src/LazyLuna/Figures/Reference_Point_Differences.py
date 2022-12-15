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


class Reference_Point_Differences(Visualization):
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        rows, columns   = 1, 2
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        titlesize = 24
        labelsize = 20
        ticksize  = 16
        
        mmDist = mmDistMetric()
        
        # Bland Altman
        ref_distances = []
        angle_differences = []
        for cc in case_comparisons:
            case1, case2 = cc.case1, cc.case2
            cat1,  cat2  = case1.categories[0], case2.categories[0]
            for d in range(cat1.nr_slices):
                anno1, anno2 = cat1.get_anno(d,0), cat2.get_anno(d,0)
                dcm = cat1.get_dcm(d,0)
                try:
                    a1 = anno1.get_reference_angle()
                    a2 = anno2.get_reference_angle()
                    ad = (a1 - a2)
                    angle_differences.append(ad)
                    ref1 = anno1.get_point('sax_ref')
                    ref2 = anno2.get_point('sax_ref')
                    ref_distances.append(mmDist.get_val(ref1, ref2, dcm))
                except: print(traceback.print_exc()); pass
        
        ax = axes[0]
        ax.set_title('Reference Point Angle Difference Boxplot', fontsize=titlesize)
        sns.boxplot  (ax=ax, x=angle_differences, width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, x=angle_differences, palette=swarm_palette, s=10, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(angle_differences)) + 3
        ax.set_xlim(-x_max, x_max)
        ax.set_xlabel('Angle Difference [%]', fontsize=labelsize)
                                         
        ax = axes[1]
        ax.set_title('Reference Point Distance Boxplot', fontsize=titlesize)
        sns.boxplot  (ax=ax, x=ref_distances, width=0.4,   palette=custom_palette[2:])
        sns.stripplot(ax=ax, x=ref_distances, palette=swarm_palette, s=10, jitter=False, dodge=True)
        ax.set_xlabel('Millimeter Distance [mm]', fontsize=labelsize)
        
        for ax in axes: ax.tick_params(axis='both', which='major', labelsize=ticksize)
        
        self.tight_layout()
        
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='_reference_point_differences.png'):
        self.tight_layout()
        self.savefig(os.path.join(storepath, figurename), dpi=200, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)