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


class LGE_Overview(Visualization):
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
        
        # Table
        rows = []
        cols = ['Scar Mass', 'Scar Fraction', 'No Reflow Mass', 'No Reflow Fraction', 'LV Volume', 'LVM Mass']
        cols = [s + ' ' + t for s in cols for t in ['avg', 'diff']]
        cols = ['casename', 'studyuid'] + cols
        cr_names = ['SCARM', 'SCARF', 'NOREFLOWVOL', 'NOREFLOWF', 'LVV', 'LVMMASS']
        for cc in case_comparisons:
            row = [cc.case1.case_name, cc.case1.studyinstanceuid]
            for crname in cr_names:
                try:
                    cr1 = [cr for cr in cc.case1.crs if cr.name==crname][0]
                    cr2 = [cr for cr in cc.case2.crs if cr.name==crname][0]
                    row.extend([(cr1.get_val()+cr2.get_val())/2.0, cr1.get_val_diff(cr2)])
                except:
                    print('Failed in case: ',cc.case1.casename, traceback.print_exc())
                    row.extend([(np.nan, np.nan)])
            rows.append(row)
        df = DataFrame(rows, columns=cols)
        
        # Scar Mass Plot
        ax = axes[0][0]
        ax.set_title(cols[2].replace(' avg','') + ' Bland Altman [g]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[2], y=cols[3], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[3]].mean()
        std_difference = df[cols[3]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[2]+' [g]', fontsize=labelsize)
        #ax.set_ylabel(cols[3]+' [g]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        # Scar Fraction Plot
        ax = axes[0][1]
        ax.set_title(cols[4].replace(' avg','') + ' Bland Altman [%]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[4], y=cols[5], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[5]].mean()
        std_difference = df[cols[5]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[4]+' [%]', fontsize=labelsize)
        #ax.set_ylabel(cols[5]+' [%]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        # No Reflow Plot
        ax = axes[1][0]
        ax.set_title(cols[6].replace(' avg','') + ' Bland Altman [g]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[6], y=cols[7], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[7]].mean()
        std_difference = df[cols[7]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[6]+' [g]', fontsize=labelsize)
        #ax.set_ylabel(cols[7]+' [g]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        
        # No Reflow Fraction Plot
        ax = axes[1][1]
        ax.set_title(cols[8].replace(' avg','') + ' Bland Altman [%]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[8], y=cols[9], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[9]].mean()
        std_difference = df[cols[9]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[8]+' [%]', fontsize=labelsize)
        #ax.set_ylabel(cols[9]+' [%]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        # LV Volume Plot
        ax = axes[2][0]
        ax.set_title(cols[10].replace(' avg','') + ' Bland Altman [ml]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[10], y=cols[11], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[11]].mean()
        std_difference = df[cols[11]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[10]+' [ml]', fontsize=labelsize)
        #ax.set_ylabel(cols[11]+' [ml]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        # LV Myo Mass Plot
        ax = axes[2][1]
        ax.set_title(cols[12].replace(' avg','') + ' Bland Altman [g]', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=cols[10], y=cols[11], data=df, markers='o', palette=swarm_palette, s=20, legend=False)
        avg_difference = df[cols[13]].mean()
        std_difference = df[cols[13]].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        #ax.set_xlabel(cols[12]+' [g]', fontsize=labelsize)
        #ax.set_ylabel(cols[13]+' [g]', fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        for ax_ in axes:
            for ax in ax_:
                ax.tick_params(axis='both', which='major', labelsize=ticksize)
                ax.set_xlabel('', fontsize=labelsize); ax.set_ylabel('', fontsize=labelsize)
        
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='clinical_results_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)