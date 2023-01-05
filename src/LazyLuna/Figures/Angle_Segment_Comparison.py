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


class Angle_Segment_Comparison(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.switch_to_image = False
    
    def visualize(self, d, category, nr_segments, byreader=None):
        """Takes one case_comparison customized by a mapping view and divides the myocardium by slices and segments
        
        Note:
            requires setting values first:
            - self.set_values(View, Case_Comparison, canvas)
        
        Args:
            d (int): slice depth
            category (LazyLuna.Categories.Category): a case's mapping category
            nr_segments (int): number of segments the myocardium is divided into
            byreader (None|1|2): (optional) if None then the insertion point is reader specific, otherwise it is taken from reader1 or reader 2.
        """
        self.clear()
        r1, r2 = self.cc.case1.reader_name, self.cc.case2.reader_name
        self.d,           self.category = d,           category
        self.nr_segments, self.byreader = nr_segments, byreader
        cat1,  cat2  = self.cc.get_categories_by_example(category)
        img1,  img2  = cat1.get_img (d,0, True, False), cat2.get_img (d,0, True, False)
        anno1, anno2 = cat1.get_anno(d,0), cat2.get_anno(d,0)
        
        axes = self.subplots(1, 3)
        self.suptitle('Slice '+str(d))
        for i in range(3): axes[i].set_title([r1,r1+'-'+r2,r2][i])
        
        if not self.switch_to_image:
            refpoint = None
            if byreader is not None: refpoint = anno1.get_point('sax_ref') if byreader==1 else anno2.get_point('sax_ref')
            myo_vals1 = anno1.get_myo_mask_by_angles(img1, nr_segments, refpoint)
            myo_vals2 = anno2.get_myo_mask_by_angles(img2, nr_segments, refpoint)
            # make vals to pandas table
            rows = []
            for k in myo_vals1.keys():
                for v in myo_vals1[k]:
                    row = ['R1', '('+str(int(np.round(k[0])))+'°, '+str(int(np.round(k[1])))+'°)', v]
                    rows.append(row)
                for v in myo_vals2[k]:
                    row = ['R2', '('+str(int(np.round(k[0])))+'°, '+str(int(np.round(k[1])))+'°)', v]
                    rows.append(row)
                row = ['R1-R2', '('+str(int(np.round(k[0])))+'°, '+str(int(np.round(k[1])))+'°)', np.nanmean(myo_vals1[k])-np.nanmean(myo_vals2[k])]
                rows.append(row)
            columns = ['Reader', 'Angle Bins', 'Value']
            df = pandas.DataFrame(rows, columns=columns)
            custom_palette  = sns.color_palette([sns.color_palette("Blues")[3], sns.color_palette("Purples")[3]])
            try:
                sns.barplot(x='Angle Bins', y='Value', data=df[df['Reader']=='R1'],   ax=axes[0], capsize=.2, palette=custom_palette)
            except Exception: print(traceback.format_exc())
            try:
                sns.barplot(x='Angle Bins', y='Value', data=df[df['Reader']=='R1-R2'],ax=axes[1], capsize=.2, palette=custom_palette)
            except Exception: print(traceback.format_exc())
            try:
                sns.barplot(x='Angle Bins', y='Value', data=df[df['Reader']=='R2'],   ax=axes[2], capsize=.2, palette=custom_palette)
            except Exception: print(traceback.format_exc())
            try:
                ymax = df['Value'].mean() + df['Value'].std()*2
                axes[0].set_ylim([0, ymax]); axes[0].tick_params(rotation=45)
            except Exception: print(traceback.format_exc())
            try:
                axes[2].set_ylim([0, ymax]); axes[2].tick_params(rotation=45)
                ymin = df[df['Reader']=='R1-R2']['Value'].min()
                ymax = df[df['Reader']=='R1-R2']['Value'].max()
                ymin, ymax = min(ymin, -ymax)*1.05, max(-ymin, ymax)*1.05
                axes[1].tick_params(rotation=45)
                axes[1].set_ylim([ymin, ymax])
            except Exception: print(traceback.format_exc())
            try:
                textstr = 'Angle [°] counterclockwise from\n'#the reference point.'
                if byreader is None: textstr += "each reader's reference point."
                if byreader == 1   : textstr += r1+"'s reference point."
                if byreader == 2   : textstr += r2+"'s reference point."
                props = dict(boxstyle='round', facecolor='w', alpha=0.5)
            except Exception: print(traceback.format_exc())
            try:
                axes[2].text(0.05, 0.05, textstr, transform=axes[2].transAxes, fontsize=10,
                verticalalignment='bottom', bbox=props)
            except Exception: print(traceback.format_exc())
        
        else:
            h, w  = img1.shape; extent=(0, w, h, 0)
            for j in range(3): axes[j].imshow(img1,'gray', extent=extent); axes[j].axis('off')
            b   = 15
            bb1 = anno1.get_contour('lv_myo').envelope; bb2 = anno2.get_contour('lv_myo').envelope
            bb  = bb1 if hasattr(bb1, 'exterior') else bb2
            if hasattr(bb, 'exterior'):
                x, y = np.array(bb.exterior.xy)
                lx, ly, ux, uy = x.min()-b-5, y.min()-b, x.max()+b, y.max()+b
                for ax in axes: ax.set_xlim([lx, ux]); ax.set_ylim([ly, uy]); ax.invert_yaxis()
            anno1.plot_contours(axes[0])
            anno1.plot_cont_comparison(axes[1], anno2, 'lv_myo')
            anno2.plot_contours(axes[2])
            if byreader is None:
                anno1.plot_points(axes[0], 'sax_ref')
                anno2.plot_points(axes[2], 'sax_ref')
            elif byreader == 1:
                for j in [0,2]: anno1.plot_points(axes[j], 'sax_ref')
            elif byreader == 2:
                for j in [0,2]: anno2.plot_points(axes[j], 'sax_ref')
        
        def onclick(event):
            if event.dblclick:
                try:
                    overviewtab = findCCsOverviewTab()
                    overviewtab.open_title_and_comments_popup(self, fig_name='Case: ' + self.cc.case1.case_name + ', slice: ' + str(self.d))
                except: print(traceback.format_exc()); pass
        self.canvas.mpl_connect('button_press_event', onclick)
        
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        
    def keyPressEvent(self, event):
        d, category = self.d, self.category
        categories = self.cc.case1.categories
        idx = categories.index(category)
        if event.key == 'shift': self.switch_to_image = not self.switch_to_image
        if event.key == 'up'   : d = (d-1) % category.nr_slices
        if event.key == 'down' : d = (d+1) % category.nr_slices
        if event.key == 'left' : category = categories[(idx-1)%len(categories)]
        if event.key == 'right': category = categories[(idx+1)%len(categories)]
        #print('In key press: ', d, category, self.nr_segments, self.byreader)
        self.visualize(d, category, self.nr_segments, self.byreader)


    def store(self, storepath, figurename='_angle_segment_comparison.png'):
        self.tight_layout()
        figname = self.cc.case1.case_name + '_slice_' + str(self.d) + '_img_' + str(self.switch_to_image) + figurename
        self.savefig(os.path.join(storepath, figname), dpi=300, facecolor="#FFFFFF")
        return os.path.join(storepath, figname)