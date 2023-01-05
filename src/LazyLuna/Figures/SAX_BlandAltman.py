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


class SAX_BlandAltman(Visualization):
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        cases1   = [cc.case1 for cc in case_comparisons]
        cases2   = [cc.case2 for cc in case_comparisons]
        rows, columns   = 4, 2
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        cr_table = CC_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_dices=False)
        cr_table.add_bland_altman_dataframe(case_comparisons)
        table = cr_table.df
        j = 0
        crvs = ['LVESV', 'LVEDV', 'LVEF', 'LVM', 'RVESV', 'RVEDV', 'RVEF']
        for i, crv in enumerate(crvs):
            if i >= (rows*columns): continue
            while i >= rows: i-=rows
            avg_n  = crv + ' avg'
            diff_n = crv + ' difference'
            axes[i][j].set_title(crv.replace('YOMASS','') + ' Bland Altman', fontsize=16)
            sns.scatterplot(ax=axes[i][j], x=avg_n, y=diff_n, data=table, markers='o', 
                            palette=swarm_palette, size=np.abs(table[diff_n]), 
                            s=10, legend=False)
            avg_difference = table[diff_n].mean()
            std_difference = table[diff_n].std()
            axes[i][j].axhline(avg_difference, ls="-", c=".2")
            axes[i][j].axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
            axes[i][j].axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
            axes[i][j].set_xlabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]', fontsize=14)
            axes[i][j].set_ylabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]', fontsize=14)
            yabs_max = abs(max(axes[i][j].get_ylim(), key=abs))
            axes[i][j].set_ylim(ymin=-yabs_max, ymax=yabs_max)
            if 'EF' in crv: axes[i][j].set_ylim(ymin=-20, ymax=20)
            if 'ESV' in crv or 'EDV' in crv: axes[i][j].set_ylim(ymin=-45, ymax=45)
            if 'MYOMASS' in crv: axes[i][j].set_ylim(ymin=-30, ymax=30)
            if i == (rows-1): j+=1
        dice_table = CC_SAX_DiceTable()
        dice_table.calculate(case_comparisons)
        d_table = dice_table.df
        ax = axes[3][1]
        ax.set_title('Dice', fontsize=16)
        dicebp = sns.boxplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table, width=0.8)
        sns.swarmplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table,
                      palette=swarm_palette, dodge=True)
        handles, labels = ax.get_legend_handles_labels()
        handles[0].set(color=custom_palette[3])
        handles[1].set(color=custom_palette2[3])
        ax.legend(handles[:2], labels[:2], title="Segmented by both", fontsize=14)
        ax.set_ylabel('[%]', fontsize=14)
        ax.set_xlabel("", fontsize=14)
        ax.set_ylim(ymin=65, ymax=101)
        for i, boxplot in enumerate(dicebp.patches):
            if i%2 == 0: boxplot.set_facecolor(custom_palette[i//2])
            else:        boxplot.set_facecolor(custom_palette2[i//2])
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='clinical_results_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)