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


    
class SAX_Candlelight(Visualization):
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents candlelights for several clinical results
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        cases1 = [cc.case1 for cc in case_comparisons]
        cases2 = [cc.case2 for cc in case_comparisons]
        rows, columns    = 2, 4
        self.set_size_inches(w=columns*7.5/2, h=(rows*7.5))
        axes = self.subplots(rows, columns)
        boxplot_palette  = sns.color_palette("Blues")
        boxplot_palette2 = sns.color_palette("Purples")
        swarm_palette = sns.color_palette(["#061C36", "#061C36"])
        ax_list = [axes[0][0], axes[0][1], axes[0][2], axes[0][3]]
        ax_list[0].get_shared_y_axes().join(*ax_list)
        ax_list = [axes[1][1], axes[1][2]]
        ax_list[0].get_shared_y_axes().join(*ax_list)
        cr_table = CC_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_dices=True)
        table = cr_table.df
        j = 0
        crvs = ['LVESV', 'LVEDV', 'RVESV', 'RVEDV', 'LVMYOMASS', 'LVEF', 'RVEF']
        crvs = [crv+' difference' for crv in crvs]
        for i in range(rows):
            for j in range(columns):
                n = i*columns+j
                if n==7: break
                axes[i][j].set_title(crvs[n].replace(' difference','').replace('YOMASS','') + " Error")
                sns.boxplot(ax=axes[i][j], data=table, x='reader2', y=crvs[n], palette=boxplot_palette, saturation=1, width=0.3)
                sns.swarmplot(ax=axes[i][j], data=table, x='reader2', y=crvs[n], color="#061C36", alpha=1)
                axes[i][j].set_xlabel("")
        ax = axes[1][3]
        ax.set_title('Dice')
        dicebp = sns.boxplot(ax=ax, x="reader2", y="avg dice", data=table, width=0.3)
        sns.swarmplot(ax=ax, x="reader2", y="avg dice", data=table, palette=swarm_palette, dodge=True)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[:2], labels[:2], title="Segmented by both")
        ax.set_ylabel('[%]')
        ax.set_xlabel("")
        ax.set_ylim(ymin=75, ymax=100)
        for i, boxplot in enumerate(dicebp.artists):
            if i%2 == 0: boxplot.set_facecolor(boxplot_palette[i//2])
            else:        boxplot.set_facecolor(boxplot_palette2[i//2])
        sns.despine()
        self.tight_layout()
        plt.flush_events()
    
    def store(self, storepath, figurename='clinical_results_candlelights.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)