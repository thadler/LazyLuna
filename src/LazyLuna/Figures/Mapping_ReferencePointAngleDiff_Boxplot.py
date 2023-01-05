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


class Mapping_ReferencePointAngleDiff_Boxplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        ax = self.add_subplot(111, position=[0.16, 0.16, 0.68, 0.68])
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        titlesize = 16
        labelsize = 14
        ticksize  = 12
        
        rows = []
        for cc in case_comparisons:
            case1, case2 = cc.case1, cc.case2
            cat1,  cat2  = case1.categories[0], case2.categories[0]
            for d in range(cat1.nr_slices):
                anno1, anno2 = cat1.get_anno(d,0), cat2.get_anno(d,0)
                dcm = cat1.get_dcm(d,0)
                try:
                    ad = (anno1.get_reference_angle() - anno2.get_reference_angle())
                    rows.append([case1.case_name, case1.studyinstanceuid, d, ad])
                except: print(traceback.print_exc()); pass
        df = DataFrame(rows, columns=['casename', 'studyuid', 'slice', 'value'])
        
        ax.set_title('Reference Point Angle Difference Boxplot', fontsize=titlesize)
        sns.boxplot  (ax=ax, data=df, x='value', width=0.4, palette=custom_palette[2:])
        sns.stripplot(ax=ax, data=df, x='value', palette=swarm_palette, s=6, jitter=False, dodge=True)
        x_max = np.nanmax(np.abs(df['value'].tolist())) + 3
        ax.set_xlim(-x_max, x_max)
        ax.set_xlabel('Angle Difference [%]', fontsize=labelsize)
        
        suids = df['studyuid'].tolist()
        texts = [t+', slice: '+str(d) for t,d in zip(df['casename'].tolist(), df['slice'].tolist())]
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
                    if cont:
                        suid = suids[ind['ind'][0]]
                        cc = [cc for cc in case_comparisons if cc.case1.studyinstanceuid==suid][0]
                        for tab_name, tab in self.view.case_tabs.items(): 
                            t = tab()
                            t.make_tab(self.gui, self.view, cc)
                            self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)
                except: print(traceback.format_exc()); pass
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name='Reference_AngleDiff_Boxplot')
                except: print(traceback.format_exc()); pass

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
        
        ax.tick_params(axis='both', which='major', labelsize=ticksize)
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='Reference_AngleDiff_Boxplot.png'):
        self.tight_layout()
        self.savefig(os.path.join(storepath, figurename), dpi=200, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)