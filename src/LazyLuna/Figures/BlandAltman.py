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

        
class BlandAltman(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
        """Takes a case_comparison and presents the annotations of both readers side by side
        
        Note:
            requires setting values first:
            - self.set_view(View)
            - self.set_canvas(canvas)
            - self.set_gui(gui)
        
        Args:
            case_comparisons (list of Case_Comparison): list of case comparisons to calculate the bland altman for
            cr_name (str): the name of the Clinical Result
        """
        self.cr_name = cr_name
        cr = [cr for cr in case_comparisons[0].case1.crs if cr.name==cr_name][0]
        self.clf()
        ax = self.add_subplot(111, position=[0.16, 0.16, 0.68, 0.68])
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        rows = []
        self.failed_cr_rows = []
        for cc in case_comparisons:
            cr1 = [cr.get_val() for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr.get_val() for cr in cc.case2.crs if cr.name==cr_name][0]
            if np.isnan(cr1) or np.isnan(cr2): self.failed_cr_rows.append([cc.case1.case_name, cc.case1.studyinstanceuid])
            else: rows.append([cc.case1.case_name, cc.case1.studyinstanceuid, (cr1+cr2)/2.0, cr1-cr2])
        df = DataFrame(rows, columns=['case_name', 'studyuid', cr_name, cr_name+' difference'])
        sns.scatterplot(ax=ax, x=cr_name, y=cr_name+' difference', data=df, markers='o', 
                        palette=swarm_palette, size=np.abs(df[cr_name+' difference']), s=10, legend=False)
        ax.axhline(df[cr_name+' difference'].mean(), ls="-", c=".2")
        ax.axhline(df[cr_name+' difference'].mean()+1.96*df[cr_name+' difference'].std(), ls=":", c=".2")
        ax.axhline(df[cr_name+' difference'].mean()-1.96*df[cr_name+' difference'].std(), ls=":", c=".2")
        ax.set_title(cr_name+' Bland Altman', fontsize=14)
        ax.set_ylabel(cr.unit, fontsize=12)
        ax.set_xlabel(cr.unit, fontsize=12)
        ax.set_xlabel(cr.name+' '+cr.unit, fontsize=12)
        sns.despine()
        texts = df['case_name'].tolist()
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
                    overviewtab.open_title_and_comments_popup(self, fig_name=self.cr_name+'_bland_altman')
                except: pass

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.tight_layout()
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=300, facecolor="#FFFFFF")
        return os.path.join(storepath, self.cr_name+figurename)
    