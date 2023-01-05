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


class LGE_Overview_BySlice(Visualization):
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        rows, columns   = 3, 2
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        titlesize=24
        labelsize=20
        ticksize=16
        
        mmDist = mmDistMetric()
        
        # Table
        rows = []
        cols = ['casename', 'studyuid', 'slice', 'Scar Area', 'No Reflow', 'Dice LVM', 'Dice Scar', 'Dice No Reflow', 'Reference Point Distance']
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                row = [cc.case1.case_name, cc.case1.studyinstanceuid, d]
                dcm1,  dcm2   = cat1.get_dcm(d,0),  cat2.get_dcm(d,0)
                anno1, anno2  = cat1.get_anno(d,0), cat2.get_anno(d,0)
                scar_area     = (anno1.get_contour('scar').area     - anno2.get_contour('scar').area) / 100.0
                noreflow_area = (anno1.get_contour('noreflow').area - anno2.get_contour('noreflow').area) / 100.0
                lvm_dice      = utils.dice(anno1.get_contour('lv_myo'), anno2.get_contour('lv_myo'))
                scar_dice     = utils.dice(anno1.get_contour('scar'), anno2.get_contour('scar'))
                noreflow_dice = utils.dice(anno1.get_contour('noreflow'), anno2.get_contour('noreflow'))
                ref_dist      = mmDist.get_val(anno1.get_point('sax_ref'), anno2.get_point('sax_ref'), dcm1)
                row.extend([scar_area, noreflow_area, lvm_dice, scar_dice, noreflow_dice, ref_dist])
                rows.append(row)
        df = DataFrame(rows, columns=cols)
        
        # Scar Area Plot
        ax = axes[0][0]
        ax.set_title(cols[3]+' [cm^2]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[3], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[3], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[3]].tolist())) + 1
        ax.set_xlim(-x_max, x_max)
        ax.set_xlabel('Scar Area', fontsize=labelsize)
        
        # Scar Area Plot
        ax = axes[0][1]
        ax.set_title(cols[4]+' [cm^2]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[4], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[4], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[4]].tolist())) + 1
        ax.set_xlim(-x_max, x_max)
        ax.set_xlabel('No Reflow Area', fontsize=labelsize)
        
        # Dice LV Myo
        ax = axes[1][0]
        ax.set_title(cols[5]+' [%]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[5], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[5], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[5]].tolist())) + 3
        ax.set_xlim(-1, x_max)
        ax.set_xlabel('Dice LV Myo', fontsize=labelsize)
        
        # Dice Scar
        ax = axes[1][1]
        ax.set_title(cols[6]+' [%]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[6], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[6], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[6]].tolist())) + 3
        ax.set_xlim(-1, x_max)
        ax.set_xlabel('Dice Scar', fontsize=labelsize)
        
        # Dice No Reflow
        ax = axes[2][0]
        ax.set_title(cols[7]+' [%]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[7], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[7], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[7]].tolist())) + 3
        ax.set_xlim(-1, x_max)
        ax.set_xlabel('Dice No Reflow', fontsize=labelsize)
        
        # Reference Point Distance
        ax = axes[2][1]
        ax.set_title(cols[8]+' [cm^2]', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x=cols[8], width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x=cols[8], palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df[cols[8]].tolist())) + 2
        ax.set_xlim(-1, x_max)
        ax.set_xlabel('Reference Point Distnace', fontsize=labelsize)
        
        
        for ax_ in axes:
            for ax in ax_:
                ax.tick_params(axis='both', which='major', labelsize=ticksize)
                ax.set_xlabel('', fontsize=labelsize); ax.set_ylabel('', fontsize=labelsize)
        
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='LGE_by_slice_boxplots_overview.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)