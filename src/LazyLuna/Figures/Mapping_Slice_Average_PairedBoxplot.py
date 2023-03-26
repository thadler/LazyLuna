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

from LazyLuna.utils import findMainWindow, findCCsOverviewTab

class Mapping_Slice_Average_PairedBoxplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
    
    def visualize(self, case_comparisons, mapping_type='T1'):
        """Takes a list of case_comparisons and presents a paired boxplot for myocardial pixel averages per slice
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        self.mapping_type = mapping_type
        figtype = 'paired boxplot'
        rows, columns   = 1, 1
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        ax = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        titlesize = 16
        labelsize = 14
        ticksize  = 12
        
        # Paired Boxplot for slice ms
        readername1 = case_comparisons[0].case1.reader_name
        readername2 = case_comparisons[0].case2.reader_name
        rows = []
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                try:    val1 = np.nanmean(cat1.get_anno(d,0).get_pixel_values('lv_myo', cat1.get_img(d,0)).tolist())
                except: val1 = np.nan
                try:    val2 = np.nanmean(cat2.get_anno(d,0).get_pixel_values('lv_myo', cat2.get_img(d,0)).tolist())
                except: val2 = np.nan
                if np.isnan(val1) or np.isnan(val2): continue
                else: rows.extend([[cc.case1.case_name, cc.case1.studyinstanceuid, d, cc.case1.reader_name, val1], 
                                   [cc.case2.case_name, cc.case2.studyinstanceuid, d, cc.case2.reader_name, val2]])
        name = mapping_type + 'Slice Average'
        unit = '[ms]'
        df = DataFrame(rows, columns=['casename', 'studyuid', 'slice', 'Reader', name])
        sns.boxplot  (ax=ax, data=df, y='Reader', x=name, width=0.4, palette=custom_palette, orient='h', linewidth=1)
        sns.swarmplot(ax=ax, data=df, y='Reader', x=name, palette=swarm_palette, orient='h')
        ax.set_title(mapping_type +' Paired Boxplot (by slice)', fontsize=titlesize)
        ax.set_ylabel('')
        ax.set_xlabel(mapping_type + ' ' + unit, fontsize=labelsize)
        # Now connect the dots
        children = [c for c in ax.get_children() if isinstance(c, PathCollection)]
        locs1 = children[0].get_offsets()
        locs2 = children[1].get_offsets()
        set1 = df[df['Reader']==case_comparisons[0].case1.reader_name][name]
        set2 = df[df['Reader']==case_comparisons[0].case2.reader_name][name]
        sort_idxs1 = np.argsort(set1)
        sort_idxs2 = np.argsort(set2)
        # revert "ascending sort" through sort_idxs2.argsort(),
        # and then sort into order corresponding with set1
        locs2_sorted = locs2[sort_idxs2.argsort()][sort_idxs1]
        for i in range(locs1.shape[0]):
            x = [locs1[i, 0], locs2_sorted[i, 0]]
            y = [locs1[i, 1], locs2_sorted[i, 1]]
            ax.plot(x, y, color="black", alpha=0.4, linewidth=0.3)
        
        
        df_sorted_r1 = df[df['Reader']==case_comparisons[0].case1.reader_name].sort_values(name)
        df_sorted_r2 = df[df['Reader']==case_comparisons[0].case2.reader_name].sort_values(name)
        suids1 = df_sorted_r1['studyuid'].tolist()
        suids2 = df_sorted_r2['studyuid'].tolist()
        texts1 = [t+', slice: '+str(d) for t,d in zip(df_sorted_r1['casename'].tolist(), df_sorted_r1['slice'].tolist())]
        texts2 = [t+', slice: '+str(d) for t,d in zip(df_sorted_r2['casename'].tolist(), df_sorted_r2['slice'].tolist())]
        suids = [suids1, suids2]
        texts = [texts1, texts2]
        
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        if not hasattr(self, 'canvas'): return
        
        def update_annot(collection, i, ind):
            pos = collection.get_offsets()[ind["ind"][0]]
            annot.xy = pos
            annot.set_text(texts[i][ind['ind'][0]])
        
        def hover(event):
            vis = annot.get_visible()
            if event.inaxes==ax:
                for i, collection in enumerate(ax.collections):
                    cont, ind = collection.contains(event)
                    if cont:
                        update_annot(collection, i, ind)
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
                    for i, collection in enumerate(ax.collections):
                        cont, ind = collection.contains(event)
                        if cont:
                            suid = suids[i][ind['ind'][0]]
                            cc = [cc for cc in case_comparisons if cc.case1.studyinstanceuid][0]
                            for tab_name, tab in self.view.case_tabs.items(): 
                                t = tab()
                                t.make_tab(self.gui, self.view, cc)
                                self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)
                except: print(traceback.format_exc()); pass
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name='T1_average_paired_boxplot')
                except: print(traceback.format_exc()); pass

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.subplots_adjust(top=0.90, bottom=0.15, left=0.15, right=0.93)
        self.canvas.draw()
        self.canvas.flush_events()
    
        
    
    def store(self, storepath, figurename='paired_boxplot_mapping_slice_average.png'):
        self.savefig(os.path.join(storepath, self.mapping_type+figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)