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


class LAX_Volumes_BlandAltman(Visualization):
    def visualize(self, view, ccs):
        """Takes a list of case_comparisons and presents several blandaltman plots for the different volumes
        
        Note:
            requires setting values first:
            - self.set_values(View, list of Case_Comparisons)
        
        Args:
            view (LazyLuna.Views.View): A LAX_CINE view object
            ccs (list of LazyLuna.Containers.Case_Comparison): the list of case comparisons for which the blandaltmans are calculated
        """
        cases1   = [cc.case1 for cc in ccs]
        cases2   = [cc.case2 for cc in ccs]
        rows, columns   = 4, 2
        #fig, axes = plt.subplots(rows, columns, figsize=(columns*11.0,rows*5.0))
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])

        cr_cols = ['case_name']+[cr.name+'_avg' for cr in ccs[0].case1.
                                 crs]+[cr.name+'_diff' for cr in ccs[0].case1.crs]
        cr_rows = []
        for cc in ccs:
            row = [cc.case1.case_name]
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append((cr1.get_val() + cr2.get_val())/ 2.0)
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append(cr1.get_val_diff(cr2))
            cr_rows.append(row)
        cr_table = DataFrame(cr_rows, columns=cr_cols)

        #display(cr_table)
        x_name, y_name = '4CV_RAESV_avg', '4CV_RAESV_diff'
        sns.scatterplot(ax=axes[0][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][0].set_xlabel(axes[0][0].xaxis.get_label().get_text() + ' [ml]')
        axes[0][0].set_ylabel(axes[0][0].yaxis.get_label().get_text() + ' [ml]')
        axes[0][0].axhline(mean, ls="-", c=".2")
        axes[0][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_RAEDV_avg', '4CV_RAEDV_diff'
        sns.scatterplot(ax=axes[0][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][1].set_xlabel(axes[0][1].xaxis.get_label().get_text() + ' [ml]')
        axes[0][1].set_ylabel(axes[0][1].yaxis.get_label().get_text() + ' [ml]')
        axes[0][1].axhline(mean, ls="-", c=".2")
        axes[0][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAESV_avg', '4CV_LAESV_diff'
        sns.scatterplot(ax=axes[1][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][0].set_xlabel(axes[1][0].xaxis.get_label().get_text() + ' [ml]')
        axes[1][0].set_ylabel(axes[1][0].yaxis.get_label().get_text() + ' [ml]')
        axes[1][0].axhline(mean, ls="-", c=".2")
        axes[1][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAEDV_avg', '4CV_LAEDV_diff'
        sns.scatterplot(ax=axes[1][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][1].set_xlabel(axes[1][1].xaxis.get_label().get_text() + ' [ml]')
        axes[1][1].set_ylabel(axes[1][1].yaxis.get_label().get_text() + ' [ml]')
        axes[1][1].axhline(mean, ls="-", c=".2")
        axes[1][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAESV_avg', '2CV_LAESV_diff'
        sns.scatterplot(ax=axes[2][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][0].set_xlabel(axes[2][0].xaxis.get_label().get_text() + ' [ml]')
        axes[2][0].set_ylabel(axes[2][0].yaxis.get_label().get_text() + ' [ml]')
        axes[2][0].axhline(mean, ls="-", c=".2")
        axes[2][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAEDV_avg', '2CV_LAEDV_diff'
        sns.scatterplot(ax=axes[2][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][1].set_xlabel(axes[2][1].xaxis.get_label().get_text() + ' [ml]')
        axes[2][1].set_ylabel(axes[2][1].yaxis.get_label().get_text() + ' [ml]')
        axes[2][1].axhline(mean, ls="-", c=".2")
        axes[2][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][1].axhline(mean-1.96*std, ls=":", c=".2")

        m_table = LAX_CCs_MetricsTable()
        m_table.calculate(view, ccs)

        ra_vals = m_table.df['ra LAX 4CV RAES DSC'].to_list() + m_table.df['ra LAX 4CV RAED DSC'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES DSC'].to_list() + m_table.df['la LAX 4CV LAED DSC'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES DSC'].to_list() + m_table.df['la LAX 2CV LAED DSC'].to_list()

        dicebp = sns.boxplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][0].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][0].set_ylabel('DSC [%]')

        for i, boxplot in enumerate(dicebp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        ra_vals = m_table.df['ra LAX 4CV RAES HD'].to_list() + m_table.df['ra LAX 4CV RAED HD'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES HD'].to_list() + m_table.df['la LAX 4CV LAED HD'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES HD'].to_list() + m_table.df['la LAX 2CV LAED HD'].to_list()

        hd_bp = sns.boxplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][1].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][1].set_ylabel('Hausdorff Distance [mm]')

        for i, boxplot in enumerate(hd_bp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    
    def store(self, storepath, figurename='clinical_volumes_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)
