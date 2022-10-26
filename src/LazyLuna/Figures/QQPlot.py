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

        
class QQPlot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
        """Takes a list of case_comparisons and presents a QQ for a Clinical Result
        
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
        #self.set_size_inches(w=15, h=7.5)
        custom_palette  = sns.color_palette([sns.color_palette("Blues")[1], sns.color_palette("Purples")[1]])
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        rows = []
        for cc in case_comparisons:
            cr1 = [cr for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr for cr in cc.case2.crs if cr.name==cr_name][0]
            rows.append([cc.case1.reader_name+'-'+cc.case2.reader_name, cr1.get_val_diff(cr2)])
        df = DataFrame(rows, columns=['Reader', cr_name+' difference'])

        # Plot
        probplot(df[cr_name+' difference'].to_numpy(), dist="norm", plot=ax)
        
        ax.set_title(cr_name+' QQplot', fontsize=14)
        #ax.set_ylabel('')
        #ax.get_yticklabels()
        #ax.set_yticklabels([case_comparisons[0].case1.reader_name+'-'+case_comparisons[0].case2.reader_name], rotation=90)
        texts = [cc.case1.case_name for cc in case_comparisons]
        
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
                cont, ind = ax.collections[0].contains(event)
                name = [cc.case1.case_name for cc in case_comparisons][ind['ind'][0]]
                cc = [cc for cc in case_comparisons][ind['ind'][0]]
                for tab_name, tab in self.view.case_tabs.items(): 
                    t = tab()
                    t.make_tab(self.gui, self.view, cc)
                    self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
        #self.tight_layout()
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=100, facecolor="#FFFFFF")
        