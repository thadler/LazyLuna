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


class Mapping_DiceBySlice(Visualization):
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
        
        rows = []
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                for conttype in ['lv_endo', 'lv_myo']:
                    try:
                        if not cat1.get_anno(d,0).has_contour(conttype) or not cat2.get_anno(d,0).has_contour(conttype): continue
                        cont1 = cat1.get_anno(d,0).get_contour(conttype)
                        cont2 = cat2.get_anno(d,0).get_contour(conttype)
                        dice, hd = utils.dice(cont1, cont2), utils.hausdorff(cont1, cont2)
                        rows.append([cc.case1.case_name, cc.case1.studyinstanceuid, d, conttype, dice, hd])
                    except Exception as e: print(cc.case1.case_name, d, e)
        df = DataFrame(rows, columns=['casename', 'studyuid', 'slice', 'conttype', 'Dice', 'HD'])
        ax.set_title('Dice (by slice)', fontsize=titlesize)
        sns.boxplot  (ax=ax, x="Dice", y="conttype", data=df, palette=custom_palette, width=0.4, orient='h')
        sns.swarmplot(ax=ax, x="Dice", y="conttype", data=df, palette=swarm_palette, dodge=True, orient='h')
        ax.set_ylabel('Dice [%]', fontsize=labelsize)
        ax.set_xlabel("", fontsize=labelsize)
        xmin = np.max([np.min(df['Dice']) - 5, 0])
        ax.set_xlim(xmin=xmin, xmax=101)
        ax.tick_params(axis='both', which='major', labelsize=ticksize)
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
        
        print(df)
        
        studyuids  = list(set(df['studyuid'].tolist()))
        suids_myo  = df[df['conttype']=='lv_myo' ].sort_values('Dice')['studyuid'].tolist()
        suids_endo = df[df['conttype']=='lv_endo'].sort_values('Dice')['studyuid'].tolist()
        texts_myo  = [t+', slice: '+str(d) for t,d in zip(df[df['conttype']=='lv_myo' ].sort_values('Dice')['casename'].tolist(), df[df['conttype']=='lv_myo' ].sort_values('Dice')['slice'].tolist())]
        texts_endo = [t+', slice: '+str(d) for t,d in zip(df[df['conttype']=='lv_endo'].sort_values('Dice')['casename'].tolist(), df[df['conttype']=='lv_endo'].sort_values('Dice')['slice'].tolist())]
        texts = [texts_endo, texts_myo]
        suids = [suids_endo, suids_myo]
        
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
                            cc = [cc for cc in case_comparisons if cc.case1.studyinstanceuid==suid][0]
                            for tab_name, tab in self.view.case_tabs.items(): 
                                t = tab()
                                t.make_tab(self.gui, self.view, cc)
                                self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)
                except: print(traceback.format_exc()); pass
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name=self.cr_name+'_paired_boxplot')
                except: print(traceback.format_exc()); pass

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
        
        self.tight_layout()
    
        
    
    def store(self, storepath, figurename='mapping_slice_average_blandaltman.png'):
        self.savefig(os.path.join(storepath, self.mapping_type+figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)