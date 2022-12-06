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


        
class SAXCINE_Confidence_Intervals_Tolerance_Ranges(Visualization):
    def visualize(self, case_comparisons, with_swarmplot=True):
        """Takes a list of case_comparisons and plots confidence intervals for Clinical Results
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
            with_swarmplot (bool): whether to plot CRs of the individual case comparisons on top of the confidence intervals
        """
        ccs = case_comparisons
        vals = {cr.name:[] for cr in ccs[0].case1.crs}
        for cc in ccs:
            c1,  c2  = cc.case1, cc.case2
            for name in [cr.name for cr in c1.crs]:
                cr1 = [cr for cr in c1.crs if cr.name==name][0] 
                cr2 = [cr for cr in c2.crs if cr.name==name][0]
                vals[cr1.name].append(cr1.get_val_diff(cr2))
        self.set_size_inches(w=15, h=15)
        axes = self.subplots(3,3)
        for i, ax_ in enumerate(axes):
            for j, ax in enumerate(ax_):
                cr = ccs[0].case1.crs[i*3+j]
                name = cr.name
                ax.set_title(name)
                ax.axhspan(-cr.tol_range, cr.tol_range, facecolor='0.6', alpha=0.5)
                alpha = 0.5 if with_swarmplot else 0.0
                sns.swarmplot(ax=ax, y=vals[name], palette=sns.color_palette("Blues")[4:], 
                              dodge=True, size=5, alpha=alpha)
                ci = 1.96 * np.std(vals[name]) / np.sqrt(len(vals[name]))
                ax.errorbar([name], [np.mean(vals[name])], yerr=ci, fmt ='o', c='r')
                maxx = np.max([np.abs(np.min(vals[name])), np.abs(np.max(vals[name])),
                               np.abs(np.mean(vals[name])-ci), np.abs(np.mean(vals[name])+ci), 
                               cr.tol_range])
                ax.set_ylim(ymin=-maxx-2, ymax=maxx+2)
                ax.set_ylabel(name + ' ' + cr.unit)
                ax.set_xlabel(name)
        self.tight_layout()
    
    def store(self, storepath, figurename='confidence_intervals_tolerance_ranges.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=300, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)