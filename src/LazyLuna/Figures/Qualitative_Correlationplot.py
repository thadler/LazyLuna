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

        
class Qualitative_Correlationplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    
    def all_cases_metrics_table(self, ccs, contour_names=['lv_endo', 'lv_myo', 'rv_endo']):
        from LazyLuna.Views import SAX_CINE_View
        view = SAX_CINE_View()
        mlDiff_m, absmldiff_m, dsc_m = mlDiffMetric(), absMlDiffMetric(), DiceMetric()
        rows = []
        cols = ['case', 'category', 'slice', 'contour name', 'ml diff', 'abs ml diff', 'DSC']
        for i, cc in enumerate(ccs):
            case1, case2 = cc.case1, cc.case2
            for d in range(case1.categories[0].nr_slices):
                for cn in contour_names:
                    cats1, cats2 = view.get_categories(case1, cn), view.get_categories(case2, cn)
                    for cat1, cat2 in zip(cats1, cats2):
                        try:
                            p1, p2 = cat1.phase, cat2.phase
                            dcm = cat1.get_dcm(d, p1)
                            anno1, anno2 = cat1.get_anno(d, p1), cat2.get_anno(d, p2)
                            cont1, cont2 = anno1.get_contour(cn), anno2.get_contour(cn)
                            ml_diff   = mlDiff_m.get_val(cont1, cont2, dcm, string=False)
                            absmldiff = absmldiff_m.get_val(cont1, cont2, dcm, string=False)
                            dsc       = dsc_m.get_val(cont1, cont2, dcm, string=False)
                            rows.append([case1.case_name, cat1.name, d, cn, ml_diff, absmldiff, dsc])
                        except Exception as e: print(traceback.format_exc()); continue
        return DataFrame(rows, columns=cols)
    
    def visualize(self, case_comparisons):
        """Takes a list of case_comparisons and presents a Metrics correlation plot (for ml difference vs Dice) for different contour types. These can be investigated by interaction
        
        Note:
            requires setting values first:
            - self.set_view(View)
            - self.set_canvas(canvas)
            - self.set_gui(gui)
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        df = self.all_cases_metrics_table(case_comparisons)
        self.curr_fig = 0
        self.set_figwidth(20); self.set_figheight(9)
        gs   = self.add_gridspec(nrows=3, ncols=8)
        ax_corr  = self.add_subplot(gs[:,:4])
        ax_comps = []
        ax_comps.append([self.add_subplot(gs[0,4+i]) for i in range(4)])
        ax_comps.append([self.add_subplot(gs[1,4+i]) for i in range(4)])
        ax_comps.append([self.add_subplot(gs[2,4+i]) for i in range(4)])
        for axlist in ax_comps:
            axlist[0].get_shared_x_axes().join(*axlist); axlist[0].get_shared_y_axes().join(*axlist)
            for ax in axlist:
                ax.set_xticks([]); ax.set_yticks([])
                
        colors = ["#FF2020", "#00bd00", "#4d50ff"]# Set your custom color palette
        customPalette = sns.set_palette(sns.color_palette(colors))
        sns.scatterplot(ax=ax_corr, data=df, x='ml diff', y='DSC', size='abs ml diff', hue='contour name', picker=True, palette=customPalette)
        xmax = np.max(np.abs(ax_corr.get_xlim())); ymax = np.max(np.abs(ax_corr.get_ylim()))
        ax_corr.set_xlim([-xmax, xmax]); ax_corr.set_ylim([-5, ymax])
        
        texts = df['case'].tolist()
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        if not hasattr(self, 'canvas'): return
        
        def onclick(event):
            vis = annot.get_visible()
            if event.inaxes==ax_corr:
                cont, ind = ax_corr.collections[0].contains(event)
                cc_info = df.iloc[ind['ind'][0]]
                
                case_name = cc_info['case']
                cat_name  = cc_info['category']
                slice_nr  = cc_info['slice']
                dice      = cc_info['DSC']
                mldiff    = cc_info['ml diff']
                cont_type = cc_info['contour name']
                
                cc = [cc for cc in case_comparisons if cc.case1.case_name==case_name][0]
                cat1, cat2 = [cat for cat in cc.case1.categories if cat_name==cat.name][0], [cat for cat in cc.case2.categories if cat_name==cat.name][0]
                
                tmp_img     = cat1.get_img(slice_nr, cat1.phase)
                h,w         = tmp_img.shape
                img1        = np.zeros((max(h,w),max(h,w)))
                img1[:h,:w] = tmp_img
                tmp_img     = cat2.get_img(slice_nr, cat2.phase)
                h,w         = tmp_img.shape
                img2        = np.zeros((max(h,w),max(h,w)))
                img2[:h,:w] = tmp_img
                h, w    = img1.shape
                extent =(0, w, h, 0)
                cont1  = cat1.get_anno(slice_nr, cat1.phase).get_contour(cont_type)
                cont2  = cat2.get_anno(slice_nr, cat2.phase).get_contour(cont_type)
                axes = ax_comps[self.curr_fig]
                for ax_i, ax in enumerate(axes):
                    ax.clear()
                    ax.axis('off')
                    if ax_i!=2: ax.imshow(img1, cmap='gray', extent=extent)
                    else:       ax.imshow(img2, cmap='gray', extent=extent)
                axes[0].set_ylabel(case_name, rotation=90, labelpad=0.1)
                axes[0].set_title('Phase: '+cat_name.replace('SAX ',''));   axes[1].set_title('Slice: '+str(slice_nr))
                axes[2].set_title('ml Diff: {:.1f}'.format(mldiff)+'[ml]'); axes[3].set_title('Dice: {:.1f}'.format(dice)+'[%]')
                    
                if not cont1.is_empty: utils.plot_geo_face(axes[0], cont1, c='r')
                if not cont1.is_empty or not cont2.is_empty: utils.plot_geo_face_comparison(axes[1], cont1, cont2)
                if not cont2.is_empty: utils.plot_geo_face(axes[2], cont2, c='b')
                pst = Polygon([[0,0],[1,1],[1,0]]) 
                patches = [[PolygonPatch(pst, facecolor=c, edgecolor=c, alpha=0.4)] for c in ['red','green','blue']]
                handles = [[cc.case1.reader_name], [cc.case1.reader_name+' & '+cc.case2.reader_name], [cc.case2.reader_name]]
                for i in range(3): axes[i].legend(patches[i], handles[i])
                
                disconnect_zoom = zoom_factory(axes[0])
                pan_handler = panhandler(self)
                self.curr_fig = (self.curr_fig + 1)%3
                self.canvas.draw()
        
        self.tight_layout()
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
    
    def store(self, storepath, figurename='qualitative_correlationplot.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)
