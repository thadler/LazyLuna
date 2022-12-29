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

from LazyLuna.utils import findMainWindow, findCCsOverviewTab


class Mapping_Slice_Average_BlandAltman(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
    
    def visualize(self, case_comparisons, mapping_type='T1'):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        self.mapping_type = mapping_type
        rows, columns   = 1, 1
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        ax = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        titlesize = 16
        labelsize = 14
        ticksize  = 12
        
        # Bland Altman for slice ms
        rows = []
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                try:
                    val1 = np.nanmean(cat1.get_anno(d,0).get_pixel_values('lv_myo', cat1.get_img(d,0)).tolist())
                    val2 = np.nanmean(cat2.get_anno(d,0).get_pixel_values('lv_myo', cat2.get_img(d,0)).tolist())
                    avg, diff = (val1+val2)/2.0, val1-val2
                    if np.isnan(val1) or np.isnan(val2): continue
                    else: rows.append([cc.case1.case_name, cc.case1.studyinstanceuid, d, avg, diff])
                except Exception as e: print(cc.case1.case_name,  d, e)
        avg_n  = mapping_type + 'average [ms]'
        diff_n = mapping_type + 'difference [ms]'
        df = DataFrame(rows, columns=['casename', 'studyuid', 'slice', avg_n, diff_n])
        ax.set_title(mapping_type + ' Bland Altman (by slice & segmented by both)', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=avg_n, y=diff_n, data=df, markers='o', 
                        palette=swarm_palette, size=np.abs(df[diff_n]), 
                        s=10, legend=False)
        avg_difference = df[diff_n].mean()
        std_difference = df[diff_n].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        ax.set_xlabel(avg_n, fontsize=labelsize)
        ax.set_ylabel(diff_n, fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        
        ax.tick_params(axis='both', which='major', labelsize=ticksize)
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
        
        texts     = df['casename'].tolist()
        slices    = df['slice'].tolist()
        texts     = [t+', slice '+str(d) for t,d in zip(texts, slices)]
        studyuids = df['studyuid'].tolist()
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        if not hasattr(self, 'canvas'): return
        def update_annot(ind):
            pos = ax.collections[0].get_offsets()[ind["ind"][0]]
            annot.xy = pos
            annot.set_text(texts[ind['ind'][0]])
        
        def hover(event):
            vis = annot.get_visible()
            if event.inaxes==ax:
                cont, ind = ax.collections[0].contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    self.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        self.canvas.draw_idle()
        
        def onclick(event):
            vis = annot.get_visible()
            if event.inaxes==ax:
                try:
                    cont, ind = ax.collections[0].contains(event)
                    name = texts[ind['ind'][0]]
                    studyuid = studyuids[ind['ind'][0]]
                    cc = [cc for cc in case_comparisons if cc.case1.studyinstanceuid==studyuid][0]
                    for tab_name, tab in self.view.case_tabs.items():
                        try:
                            t = tab()
                            t.make_tab(self.gui, self.view, cc)
                            self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)
                        except: pass
                except: pass
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name=mapping_type + '_bland_altman')
                except: pass

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
        
        self.tight_layout()
    
        
    
    def store(self, storepath, figurename='mapping_slice_average_blandaltman.png'):
        self.savefig(os.path.join(storepath, self.mapping_type+figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)