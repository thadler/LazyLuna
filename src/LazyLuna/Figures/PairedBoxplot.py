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

class PairedBoxplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
        """Takes a list of case_comparisons and presents a Paired Boxplot for a Clinical Result
        
        Note:
            requires setting values first:
            - self.set_view(View)
            - self.set_canvas(canvas)
            - self.set_gui(gui)
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
            cr_name (str): name of Clinical Result
        """
        self.cr_name = cr_name
        cr = [cr for cr in case_comparisons[0].case1.crs if cr.name==cr_name][0]
        self.clf()
        ax = self.add_subplot(111, position=[0.16, 0.16, 0.68, 0.68])
        #self.set_size_inches(w=7.5, h=10)
        readername1 = case_comparisons[0].case1.reader_name
        readername2 = case_comparisons[0].case2.reader_name
        if readername1==readername2: readername2=' '+readername2
        custom_palette  = sns.color_palette([sns.color_palette("Blues")[1], sns.color_palette("Purples")[1]])
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        rows = []
        self.failed_cr_rows = []
        for cc in case_comparisons:
            cr1 = [cr.get_val() for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr.get_val() for cr in cc.case2.crs if cr.name==cr_name][0]
            casename, studyuid = cc.case1.case_name, cc.case1.studyinstanceuid
            if np.isnan(cr1) or np.isnan(cr2): self.failed_cr_rows.append([casename, studyuid])
            else: rows.extend([[casename, studyuid, readername1, cr1], [casename, studyuid, readername2, cr2]])
        df = DataFrame(rows, columns=['casename', 'studyuid', 'Reader', cr_name])
        # Plot
        sns.boxplot  (ax=ax, data=df, y='Reader', x=cr_name, width=0.4, palette=custom_palette, orient='h', linewidth=1)
        sns.swarmplot(ax=ax, data=df, y='Reader', x=cr_name, palette=swarm_palette, orient='h')
        ax.set_title(cr_name+' Paired Boxplot', fontsize=14)
        ax.set_ylabel('')
        ax.set_xlabel(cr.name+' '+cr.unit, fontsize=12)
        # Now connect the dots
        children = [c for c in ax.get_children() if isinstance(c, PathCollection)]
        locs1 = children[0].get_offsets()
        locs2 = children[1].get_offsets()
        set1 = df[df['Reader']==case_comparisons[0].case1.reader_name][cr_name]
        set2 = df[df['Reader']==case_comparisons[0].case2.reader_name][cr_name]
        sort_idxs1 = np.argsort(set1)
        sort_idxs2 = np.argsort(set2)
        # revert "ascending sort" through sort_idxs2.argsort(),
        # and then sort into order corresponding with set1
        locs2_sorted = locs2[sort_idxs2.argsort()][sort_idxs1]
        for i in range(locs1.shape[0]):
            x = [locs1[i, 0], locs2_sorted[i, 0]]
            y = [locs1[i, 1], locs2_sorted[i, 1]]
            ax.plot(x, y, color="black", alpha=0.4, linewidth=0.3)
        studyuids = df['studyuid'].tolist()[::2]
        # sorts cr names by cr value
        ccs1 = sorted([cc for cc in case_comparisons if cc.case1.studyinstanceuid in studyuids], key=lambda cc: [cr for cr in cc.case1.crs if cr.name==cr_name][0].get_val())
        ccs2 = sorted([cc for cc in case_comparisons if cc.case2.studyinstanceuid in studyuids], key=lambda cc: [cr for cr in cc.case2.crs if cr.name==cr_name][0].get_val())
        texts1 = [cc.case1.case_name for cc in ccs1]
        texts2 = [cc.case1.case_name for cc in ccs2]
        
        ccs   = [ccs1, ccs2]
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
                            cc = ccs[i][ind['ind'][0]]
                            for tab_name, tab in self.view.case_tabs.items(): 
                                t = tab()
                                t.make_tab(self.gui, self.view, cc)
                                self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)
                except: pass
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name=self.cr_name+'_paired_boxplot')
                except: print(traceback.format_exc()); pass
                            
        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.tight_layout()
        self.canvas.draw()
    
    def store(self, storepath, figurename='_paired_boxplot.png'):
        self.tight_layout()
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=300, facecolor="#FFFFFF")
        return os.path.join(storepath, self.cr_name+figurename)
