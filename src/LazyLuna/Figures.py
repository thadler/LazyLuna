import os
import traceback

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import gridspec, colors, cm
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection
import matplotlib.pyplot as plt
import seaborn as sns

import shapely
from descartes import PolygonPatch
from shapely.geometry import Polygon
import numpy as np
from scipy.stats import wilcoxon, probplot
from statsmodels.graphics.gofplots import qqplot
import pandas

from LazyLuna import Mini_LL
from LazyLuna.Tables import *
from LazyLuna import utils
        
from mpl_interactions import ioff, panhandler, zoom_factory


class Visualization(Figure):
    def __init__(self):
        super().__init__()
        pass
    
    def visualize(self):
        pass
    
    def keyPressEvent(self, event):
        pass

    # overwrite figure name
    def store(self, storepath, figurename='visualization.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")

        
class SAX_BlandAltman(Visualization):
    def visualize(self, case_comparisons):
        cases1   = [cc.case1 for cc in case_comparisons]
        cases2   = [cc.case2 for cc in case_comparisons]
        rows, columns   = 4, 2
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        cr_table = CC_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_dices=False)
        cr_table.add_bland_altman_dataframe(case_comparisons)
        table = cr_table.df
        j = 0
        crvs = ['LVESV', 'LVEDV', 'LVEF', 'LVM', 'RVESV', 'RVEDV', 'RVEF']
        for i, crv in enumerate(crvs):
            if i >= (rows*columns): continue
            while i >= rows: i-=rows
            avg_n  = crv + ' avg'
            diff_n = crv + ' difference'
            axes[i][j].set_title(crv.replace('YOMASS','') + ' Bland Altman', fontsize=16)
            sns.scatterplot(ax=axes[i][j], x=avg_n, y=diff_n, data=table, markers='o', 
                            palette=swarm_palette, size=np.abs(table[diff_n]), 
                            s=10, legend=False)
            avg_difference = table[diff_n].mean()
            std_difference = table[diff_n].std()
            axes[i][j].axhline(avg_difference, ls="-", c=".2")
            axes[i][j].axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
            axes[i][j].axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
            axes[i][j].set_xlabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]', fontsize=14)
            axes[i][j].set_ylabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]', fontsize=14)
            yabs_max = abs(max(axes[i][j].get_ylim(), key=abs))
            axes[i][j].set_ylim(ymin=-yabs_max, ymax=yabs_max)
            if 'EF' in crv: axes[i][j].set_ylim(ymin=-20, ymax=20)
            if 'ESV' in crv or 'EDV' in crv: axes[i][j].set_ylim(ymin=-45, ymax=45)
            if 'MYOMASS' in crv: axes[i][j].set_ylim(ymin=-30, ymax=30)
            if i == (rows-1): j+=1
        dice_table = CC_SAX_DiceTable()
        dice_table.calculate(case_comparisons)
        d_table = dice_table.df
        ax = axes[3][1]
        ax.set_title('Dice', fontsize=16)
        dicebp = sns.boxplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table, width=0.8)
        sns.swarmplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table,
                      palette=swarm_palette, dodge=True)
        handles, labels = ax.get_legend_handles_labels()
        handles[0].set(color=custom_palette[3])
        handles[1].set(color=custom_palette2[3])
        ax.legend(handles[:2], labels[:2], title="Segmented by both", fontsize=14)
        ax.set_ylabel('[%]', fontsize=14)
        ax.set_xlabel("", fontsize=14)
        ax.set_ylim(ymin=65, ymax=101)
        for i, boxplot in enumerate(dicebp.artists):
            if i%2 == 0: boxplot.set_facecolor(custom_palette[i//2])
            else:        boxplot.set_facecolor(custom_palette2[i//2])
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='clinical_results_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
    
    
class SAX_Candlelight(Visualization):
    def visualize(self, case_comparisons):
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
    
    def store(self, storepath, figurename='clinical_results_candlelights.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")

        
class SAXCINE_Confidence_Intervals_Tolerance_Ranges(Visualization):
    def visualize(self, case_comparisons, with_swarmplot=True):
        ccs = case_comparisons
        vals = {cr.name:[] for cr in ccs[0].case1.crs}
        for cc in ccs:
            c1,  c2  = cc.case1, cc.case2
            for name in [cr.name for cr in c1.crs]:
                cr1 = [cr for cr in c1.crs if cr.name==name][0] 
                cr2 = [cr for cr in c2.crs if cr.name==name][0]
                vals[cr1.name].append(cr1.get_val_diff(cr2))

        self.set_size_inches(w=15, h=15)
        axes = self.subplots(3,3)
        for i, ax_ in enumerate(axes):
            for j, ax in enumerate(ax_):
                cr = ccs[0].case1.crs[i*3+j]
                name = cr.name
                ax.set_title(name)
                ax.axhspan(-cr.tol_range, cr.tol_range, facecolor='0.6', alpha=0.5)
                alpha = 0.5 if with_swarmplot else 0.0
                sns.swarmplot(ax=ax, y=vals[name], palette=sns.color_palette("Blues")[4:], 
                              dodge=True, size=5, alpha=alpha)
                ci = 1.96 * np.std(vals[name]) / np.sqrt(len(vals[name]))
                ax.errorbar([name], [np.mean(vals[name])], yerr=ci, fmt ='o', c='r')
                maxx = np.max([np.abs(np.min(vals[name])), np.abs(np.max(vals[name])),
                               np.abs(np.mean(vals[name])-ci), np.abs(np.mean(vals[name])+ci), 
                               cr.tol_range])
                ax.set_ylim(ymin=-maxx-2, ymax=maxx+2)
                ax.set_ylabel(name + ' ' + cr.unit)
                ax.set_xlabel(name)
        self.tight_layout()
    
    def store(self, storepath, figurename='confidence_intervals_tolerance_ranges.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=300, facecolor="#FFFFFF")

"""
from matplotlib.patches import Rectangle

# make figure
def tol_ranges_saxcine(ccs, with_swarmplot=True):
    vals = {cr.name:[] for cr in ccs[0].case1.crs}
    for cc in ccs:
        c1,  c2  = cc.case1, cc.case2
        for name in [cr.name for cr in c1.crs]:
            cr1, cr2 = [cr for cr in c1.crs if cr.name==name][0], [cr for cr in c2.crs if cr.name==name][0]
            vals[cr1.name].append(cr1.get_val_diff(cr2))
    
    fig, axes = plt.subplots(3,3, figsize=(15,15))
    for i, ax_ in enumerate(axes):
        for j, ax in enumerate(ax_):
            cr = ccs[0].case1.crs[i*3+j]
            name = cr.name
            ax.set_title(name)
            ax.axhspan(-cr.tol_range, cr.tol_range, facecolor='0.6', alpha=0.5)
            alpha = 0.5 if with_swarmplot else 0.0
            sns.swarmplot(ax=ax, y=vals[name], palette=sns.color_palette("Blues")[4:], dodge=True, size=5, alpha=alpha)
            ci = 1.96 * np.std(vals[name]) / np.sqrt(len(vals[name]))
            ax.errorbar([name], [np.mean(vals[name])], yerr=ci, fmt ='o', c='r')
            maxx = np.max([np.abs(np.min(vals[name])), np.abs(np.max(vals[name])),
                           np.abs(np.mean(vals[name])-ci), np.abs(np.mean(vals[name])+ci), cr.tol_range])
            ax.set_ylim(ymin=-maxx-2, ymax=maxx+2)
            ax.set_ylabel(name + ' ' + cr.unit)
            ax.set_xlabel(name)
    
    fig.tight_layout()
    plt.show()

print(tol_ranges_saxcine(ccs, True))
"""
        

class Annotation_Comparison(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
    
    def visualize(self, slice_nr, category, contour_name, debug=False):
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category, self.contour_name = slice_nr, category, contour_name
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec = gridspec.GridSpec(nrows=1, ncols=4, figure=self, hspace=0.0)
        ax1  = self.add_subplot(spec[0,0])
        ax2  = self.add_subplot(spec[0,1], sharex=ax1, sharey=ax1)
        ax3  = self.add_subplot(spec[0,2], sharex=ax1, sharey=ax1)
        ax4  = self.add_subplot(spec[0,3], sharex=ax1, sharey=ax1)
        img1  = cat1.get_img (slice_nr, cat1.get_phase())
        img2  = cat2.get_img (slice_nr, cat2.get_phase())
        anno1 = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2 = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w  = img1.shape
        extent=(0, w, h, 0)
        ax1.imshow(img1,'gray', extent=extent); ax2.imshow(img1,'gray', extent=extent)
        ax3.imshow(img2,'gray', extent=extent); ax4.imshow(img1,'gray', extent=extent)
        self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_contour_face   (ax1,        contour_name, alpha=0.4, c='r')
            anno1.plot_cont_comparison(ax2, anno2, contour_name, alpha=0.4)
            anno2.plot_contour_face   (ax3,        contour_name, alpha=0.4, c='b')
            #anno1.plot_all_contour_outlines(ax1) # looks like overlooked slices when different phases for RV and LV
            #anno2.plot_all_contour_outlines(ax3)
            anno1.plot_all_points(ax1)
            anno2.plot_all_points(ax3)
        for ax in [ax1, ax2, ax3]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        
        patches = [PolygonPatch(d,facecolor=c, edgecolor=c,  alpha=0.4) for c in ['red', 'green', 'blue']]
        handles = [self.cc.case1.reader_name,
                   self.cc.case1.reader_name+' & '+self.cc.case2.reader_name,
                   self.cc.case2.reader_name]
        ax4.legend(patches, handles)
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        slice_nr, category, contour_name = self.slice_nr, self.category, self.contour_name
        categories = self.view.get_categories(self.cc.case1, self.contour_name)
        idx = categories.index(category)
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : slice_nr = (slice_nr-1) % category.nr_slices
        if event.key == 'down' : slice_nr = (slice_nr+1) % category.nr_slices
        if event.key == 'left' : category = categories[(idx-1)%len(categories)]
        if event.key == 'right': category = categories[(idx+1)%len(categories)]
        self.visualize(slice_nr, category, contour_name)


class Basic_Presenter(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
    
    def visualize(self, slice_nr, category, debug=False):
        if debug: print('Start'); st = time()
        self.clear()
        self.slice_nr, self.category = slice_nr, category
        cat1, cat2 = self.cc.get_categories_by_example(category)
        spec   = gridspec.GridSpec(nrows=1, ncols=2, figure=self, hspace=0.0)
        ax1    = self.add_subplot(spec[0,0])
        ax2    = self.add_subplot(spec[0,1], sharex=ax1, sharey=ax1)
        img1   = cat1.get_img (slice_nr, cat1.get_phase())
        img2   = cat2.get_img (slice_nr, cat2.get_phase())
        anno1  = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2  = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w   = img1.shape
        extent = (0, w, h, 0)
        ax1.imshow(img1,'gray', extent=extent); ax2.imshow(img2,'gray', extent=extent)
        self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_all_contour_outlines(ax1) # looks like overlooked slices when different phases for RV and LV
            anno2.plot_all_contour_outlines(ax2)
            anno1.plot_all_points(ax1)
            anno2.plot_all_points(ax2)
        ax1.set_title(self.cc.case1.reader_name)
        ax2.set_title(self.cc.case2.reader_name)
        for ax in [ax1, ax2]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        
        self.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()
        if debug: print('Took: ', time()-st)
        
    def keyPressEvent(self, event):
        slice_nr, category = self.slice_nr, self.category
        categories = self.cc.case1.categories
        idx = categories.index(category)
        if event.key == 'shift': self.add_annotation = not self.add_annotation
        if event.key == 'up'   : slice_nr = (slice_nr-1) % category.nr_slices
        if event.key == 'down' : slice_nr = (slice_nr+1) % category.nr_slices
        if event.key == 'left' : category = categories[(idx-1)%len(categories)]
        if event.key == 'right': category = categories[(idx+1)%len(categories)]
        print('In key press: ', slice_nr, category)
        self.visualize(slice_nr, category)


class Angle_Segment_Comparison(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.switch_to_image = False
    
    def visualize(self, d, category, nr_segments, byreader=None):
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
            if byreader is not None: refpoint = anno1.get_point('sacardialRefPoint') if byreader==1 else anno2.get_point('sacardialRefPoint')
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
                row = ['R1-R2', '('+str(int(np.round(k[0])))+'°, '+str(int(np.round(k[1])))+'°)', np.mean(myo_vals1[k])-np.mean(myo_vals2[k])]
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
            anno1.plot_all_contour_outlines(axes[0])
            anno1.plot_cont_comparison(axes[1], anno2, 'lv_myo')
            anno2.plot_all_contour_outlines(axes[2])
            if byreader is None:
                anno1.plot_point(axes[0], 'sacardialRefPoint')
                anno2.plot_point(axes[2], 'sacardialRefPoint')
            elif byreader == 1:
                for j in [0,2]: anno1.plot_point(axes[j], 'sacardialRefPoint')
            elif byreader == 2:
                for j in [0,2]: anno2.plot_point(axes[j], 'sacardialRefPoint')
        
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


        
        
##########################################################################################
##########################################################################################
##########################################################################################

class Failed_Annotation_Comparison_Yielder(Visualization):
    def set_values(self, view, ccs):
        self.ccs     = ccs
        self.view    = view
        self.yielder = self.initialize_yeild_next()
        self.add_annotation = True
    
    def visualize(self, cc, slice_nr, category, contour_name, debug=False):
        if debug: print('Start'); st = time()
        self.clear()
        self.cc, self.slice_nr, self.category, self.contour_name = cc, slice_nr, category, contour_name
        rows, columns = 1, 4
        self.set_size_inches(w=columns*11.0, h=rows*11.0)
        axes = self.subplots(rows, columns)
        axes[0].get_shared_x_axes().join(*axes); axes[0].get_shared_y_axes().join(*axes)
        cat1, cat2 = self.cc.get_categories_by_example(category)
        img1  = cat1.get_img (slice_nr, cat1.get_phase())
        img2  = cat2.get_img (slice_nr, cat2.get_phase())
        anno1 = cat1.get_anno(slice_nr, cat1.get_phase())
        anno2 = cat2.get_anno(slice_nr, cat2.get_phase())
        h, w  = img1.shape
        extent=(0, w, h, 0)
        axes[0].imshow(img1,'gray', extent=extent); axes[1].imshow(img1,'gray', extent=extent)
        axes[2].imshow(img2,'gray', extent=extent); axes[3].imshow(img1,'gray', extent=extent)
        self.suptitle('Case: ' + cc.case1.case_name + ', Contour: ' + contour_name + ', category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_contour_face   (axes[0],        contour_name, alpha=0.4, c='r')
            anno1.plot_cont_comparison(axes[1], anno2, contour_name, alpha=0.4)
            anno2.plot_contour_face   (axes[2],        contour_name, alpha=0.4, c='b')
        for ax in axes: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        patches = [PolygonPatch(d,facecolor=c, edgecolor=c,  alpha=0.4) for c in ['red', 'green', 'blue']]
        handles = [self.cc.case1.reader_name,
                   self.cc.case1.reader_name+' & '+self.cc.case2.reader_name,
                   self.cc.case2.reader_name]
        axes[3].legend(patches, handles)
        self.tight_layout()
        if debug: print('Took: ', time()-st)
        
    def initialize_yeild_next(self, rounds=None):
        dsc, hd, mld = Mini_LL.DiceMetric(), Mini_LL.HausdorffMetric(), Mini_LL.mlDiffMetric()
        count = 0
        while (rounds is None) or (count<rounds):
            for cc in self.ccs:
                c1, c2    = cc.case1, cc.case2
                nr_slices = c1.categories[0].nr_slices
                case_name = c1.case_name
                for sl_nr in range(nr_slices):
                    for contname in self.view.contour_names:
                        cats1 = self.view.get_categories(c1, contname)
                        cats2 = self.view.get_categories(c2, contname)
                        for cat1, cat2 in zip(cats1, cats2):
                            p1, p2 = cat1.phase, cat2.phase
                            dcm    = cat1.get_dcm(sl_nr, p1)
                            cont1  = cat1.get_anno(sl_nr, p1).get_contour(contname)
                            cont2  = cat2.get_anno(sl_nr, p2).get_contour(contname)
                            dice   = dsc.get_val(cont1, cont2, dcm)
                            mldiff = np.abs(mld.get_val(cont1, cont2, dcm))
                            hdm    = hd.get_val(cont1, cont2, dcm)
                            if dice<70 and mldiff>1.2:
                                yield cc, sl_nr, cat1, contname
                            if contname in ['la','ra'] and (hdm>3.5 or dice<60):
                                yield cc, sl_nr, cat1, contname
            count += 1
                
    def store(self, storepath):
        self.yielder = self.initialize_yeild_next(rounds=1)
        for cc, slice_nr, category, contour_name in self.yielder:
            figname = cc.case1.case_name+'_'+str(slice_nr)+'_'+category.name+'_'+contour_name
            print(figname)
            self.visualize(cc, slice_nr, category, contour_name)
            self.savefig(os.path.join(storepath, figname+'.png'), dpi=100, facecolor="#FFFFFF")
    
        
class BlandAltman(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
        self.cr_name = cr_name
        cr = [cr for cr in case_comparisons[0].case1.crs if cr.name==cr_name][0]
        self.clf()
        ax = self.add_subplot(111, position=[0.16, 0.16, 0.68, 0.68])
        #self.set_size_inches(w=15, h=7.5)
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        rows = []
        for cc in case_comparisons:
            cr1 = [cr.get_val() for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr.get_val() for cr in cc.case2.crs if cr.name==cr_name][0]
            rows.append([(cr1+cr2)/2.0, cr1-cr2])
        df = DataFrame(rows, columns=[cr_name, cr_name+' difference'])
        sns.scatterplot(ax=ax, x=cr_name, y=cr_name+' difference', data=df, markers='o', 
                        palette=swarm_palette, size=np.abs(df[cr_name+' difference']), 
                        s=10, legend=False)
        ax.axhline(df[cr_name+' difference'].mean(), ls="-", c=".2")
        ax.axhline(df[cr_name+' difference'].mean()+1.96*df[cr_name+' difference'].std(), ls=":", c=".2")
        ax.axhline(df[cr_name+' difference'].mean()-1.96*df[cr_name+' difference'].std(), ls=":", c=".2")

        ax.set_title(cr_name+' Bland Altman', fontsize=14)
        ax.set_ylabel(cr.unit, fontsize=12)
        ax.set_xlabel(cr.unit, fontsize=12)
        ax.set_xlabel(cr.name+' '+cr.unit, fontsize=12)
        sns.despine()
        
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
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=100, facecolor="#FFFFFF")
    
    
class PairedBoxplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
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
        for cc in case_comparisons:
            cr1 = [cr.get_val() for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr.get_val() for cr in cc.case2.crs if cr.name==cr_name][0]
            if np.isnan(cr1) or np.isnan(cr2): continue
            rows.extend([[readername1, cr1], [readername2, cr2]])
        df = DataFrame(rows, columns=['Reader', cr_name])
        print(df)
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
        
        texts = [cc.case1.case_name for cc in case_comparisons]
        
        # sorts cr names by cr value
        ccs1 = sorted([cc for cc in case_comparisons], key=lambda cc: [cr for cr in cc.case1.crs if cr.name==cr_name][0].get_val())
        ccs2 = sorted([cc for cc in case_comparisons], key=lambda cc: [cr for cr in cc.case2.crs if cr.name==cr_name][0].get_val())
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
                for i, collection in enumerate(ax.collections):
                    cont, ind = collection.contains(event)
                    if cont:
                        cc = ccs[i][ind['ind'][0]]
                        for tab_name, tab in self.view.case_tabs.items(): 
                            t = tab()
                            t.make_tab(self.gui, self.view, cc)
                            self.gui.tabs.addTab(t, tab_name+': '+cc.case1.case_name)

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=100, facecolor="#FFFFFF")


class Boxplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
        self.cr_name = cr_name
        cr = [cr for cr in case_comparisons[0].case1.crs if cr.name==cr_name][0]
        self.clf()
        ax = self.add_subplot(111, position=[0.16, 0.16, 0.68, 0.68])
        #self.set_size_inches(w=15, h=7.5)
        custom_palette  = sns.color_palette([sns.color_palette("Blues")[2], sns.color_palette("Purples")[2]])
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        rows = []
        for cc in case_comparisons:
            cr1 = [cr for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr for cr in cc.case2.crs if cr.name==cr_name][0]
            rows.append([cc.case1.reader_name+'-'+cc.case2.reader_name, cr1.get_val_diff(cr2)])
        df = DataFrame(rows, columns=['Reader', cr_name+' difference'])

        # Plot
        sns.boxplot  (ax=ax, data=df, y='Reader', x=cr_name+' difference', orient='h', width=0.3, palette=custom_palette)
        sns.swarmplot(ax=ax, data=df, y='Reader', x=cr_name+' difference', orient='h', palette=swarm_palette)
        ax.set_title(cr_name+' Boxplot', fontsize=14)
        ax.set_xlabel(cr_name+' '+cr.unit, fontsize=12)
        ax.set_ylabel('')
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
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=100, facecolor="#FFFFFF")

        
class QQPlot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def visualize(self, case_comparisons, cr_name):
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
        
        
class Qualitative_Correlationplot(Visualization):
    def set_view(self, view):
        self.view   = view
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        
    def set_gui(self, gui):
        self.gui = gui
        
    def all_cases_metrics_table(self, ccs):
        all_dfs = []
        for i, cc in enumerate(ccs):
            st=time(); print(i, ' of ', len(ccs), end=', ')
            analyzer = Mini_LL.SAX_CINE_analyzer(cc)
            df = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader=False)
            df.drop(columns=['sop1','sop2','reader1','reader2','position2','has_contour1','has_contour2',
                             'depth_perc','max_slices','phase1','phase2'], inplace=True)
            df = df[df['contour name'].isin(['lv_endo','lv_myo','rv_endo'])]
            all_dfs.append(df)
            print('took: ', time()-st)
        df = pandas.concat(all_dfs, axis=0, ignore_index=True)
        return df
    
    def visualize(self, case_comparisons, metric='ml diff', hue='contour name'):
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
        sns.scatterplot(ax=ax_corr, data=df, x=metric, y='DSC', size='abs ml diff', hue=hue, picker=True, palette=customPalette)
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


        
class T1_bullseye_plot(Visualization):
    def set_values(self, view, case, canvas):
        self.case   = case
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        #v        = SAX_T1_View()
        self.clear()
        cat      = self.case.categories[0]
        means, stds = cat.calc_mapping_aha_model()

        means = np.concatenate((means[0],means[1],means[2]))
        stds  = np.concatenate((stds[0], stds[1], stds[2]))
        
        #ax = self.subplots(1,1)
        ax = self.subplots(1,1, subplot_kw=dict(projection='polar'))
        # requires polar projection: fig,ax = plt.subplots(1,1), subplot_kw=dict(projection='polar'))
        #cmap = plt.cm.viridis
        cmap = plt.cm.gnuplot # ??? which colormap?
        cmap = plt.cm.bwr
        
        print(minv, maxv)
        if minv is None: minv=np.min(means)
        if maxv is None: maxv=np.max(means)
        print(minv, maxv)
        
        minv, maxv = min([minv, 995]), max([maxv, 1005])
        minv = min([minv, 1000 - (maxv-1000)])
        maxv = max([maxv, 1000 + (1000 - minv)])
        norm = colors.Normalize(vmin=minv, vmax=maxv)
        means = np.array(means).ravel()
        stds  = np.array(stds) .ravel()
        theta = np.linspace(0, 2*np.pi, 768)
        r = np.linspace(0.2, 1, 4)
        linewidth = 2
        for i in range(r.shape[0]): ax.plot(theta, np.repeat(r[i], theta.shape), '-k', lw=linewidth)
        for i in range(6):
            theta_i = i * 60 * np.pi/180
            ax.plot([theta_i, theta_i], [r[1], 1], '-k', lw=linewidth)
        for i in range(4):
            theta_i = i * 90 * np.pi/180 - 45*np.pi/180
            ax.plot([theta_i, theta_i], [r[0], r[1]], '-k', lw=linewidth)
        r0 = r[2:4]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i], stds[i], i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+1 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[2],r[3]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[2],r[3]], '-k', lw=linewidth+1)
        r0 = r[1:3]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i+6], stds[i+6],  i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i+6]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+7 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[1],r[2]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[1],r[2]], '-k', lw=linewidth+1)
        r0 = r[0:2]
        r0 = np.repeat(r0[:,np.newaxis], 192, axis=1).T
        for i in range(4):
            theta0 = theta[i*192:i*192+192] + 45*np.pi/180  #+ 90*np.pi/180 
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax,means[i+12], stds[i+12], i*90*np.pi/180 + 90*np.pi/180, np.mean(r0[0]))
            z = np.ones((192,2)) * means[i+12]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+13 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[0],r[1]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[0],r[1]], '-k', lw=linewidth+1)
        ax.set_ylim([0, 1])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        axp    = ax.imshow(np.random.randint(0, 100, (100, 100)))
        cbaxes = self.add_axes([0.78, 0.1, 0.03, 0.8])  # This is the position for the colorbar
        cb     = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=axp, cax=cbaxes)
        ax.set_title('AHA Model: '+self.case.reader_name)
        self.canvas.draw()

    def write_val(self, ax, mean, std, angle, y):
        mean = "{:.1f}".format(float(mean))
        std  = "{:.1f}".format(float(std))
        ax.annotate(str(mean) + '\n(' + str(std) + ')',
                xy                  = (angle, y), # theta, radius
                xytext              = (angle, y), # fraction, fraction
                textcoords          = 'data',     #'figure fraction',
                bbox                = dict(boxstyle="round", fc="1.0", edgecolor="1.0"),
                horizontalalignment = 'center',
                size                = 10,
                verticalalignment   = 'center',
                )


class T1_diff_bullseye_plot(Visualization):
    def set_values(self, view, cc, canvas):
        self.cc     = cc
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        #v   = SAX_T1_View()
        self.clear()
        cat1 = self.cc.case1.categories[0]
        cat2 = self.cc.case2.categories[0]
        means1, stds1 = cat1.calc_mapping_aha_model()
        means2, stds2 = cat2.calc_mapping_aha_model()

        means = np.concatenate((means1[0]-means2[0],
                                means1[1]-means2[1],
                                means1[2]-means2[2]))
        stds  = np.concatenate((stds1[0]-stds2[0], 
                                stds1[1]-stds2[1], 
                                stds1[2]-stds2[2]))
        
        ax = self.subplots(1,1, subplot_kw=dict(projection='polar'))
        cmap = plt.cm.PRGn
        if minv is None: minv=np.min(means)-5
        if maxv is None: maxv=np.max(means)+5
        minv, maxv = min([minv, -maxv]), max([maxv, -minv])
        norm = colors.Normalize(vmin=minv, vmax=maxv)
        means = np.array(means).ravel()
        stds  = np.array(stds) .ravel()
        theta = np.linspace(0, 2*np.pi, 768)
        r = np.linspace(0.2, 1, 4)
        linewidth = 2
        for i in range(r.shape[0]): ax.plot(theta, np.repeat(r[i], theta.shape), '-k', lw=linewidth)
        for i in range(6):
            theta_i = i * 60 * np.pi/180
            ax.plot([theta_i, theta_i], [r[1], 1], '-k', lw=linewidth)
        for i in range(4):
            theta_i = i * 90 * np.pi/180 - 45*np.pi/180
            ax.plot([theta_i, theta_i], [r[0], r[1]], '-k', lw=linewidth)
        r0 = r[2:4]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i], stds[i], i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+1 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[2],r[3]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[2],r[3]], '-k', lw=linewidth+1)
        r0 = r[1:3]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i+6], stds[i+6],  i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i+6]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+7 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[1],r[2]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[1],r[2]], '-k', lw=linewidth+1)
        r0 = r[0:2]
        r0 = np.repeat(r0[:,np.newaxis], 192, axis=1).T
        for i in range(4):
            theta0 = theta[i*192:i*192+192] + 45*np.pi/180  #+ 90*np.pi/180 
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax,means[i+12], stds[i+12], i*90*np.pi/180 + 90*np.pi/180, np.mean(r0[0]))
            z = np.ones((192,2)) * means[i+12]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+13 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[0],r[1]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[0],r[1]], '-k', lw=linewidth+1)
        ax.set_ylim([0, 1])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        axp    = ax.imshow(np.random.randint(0, 100, (100, 100)))
        cbaxes = self.add_axes([0.78, 0.1, 0.03, 0.8])  # This is the position for the colorbar
        cb     = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=axp, cax=cbaxes)
        
        self.canvas.draw()

    def write_val(self, ax, mean, std, angle, y):
        mean = "{:.1f}".format(float(mean))
        std  = "{:.1f}".format(float(std))
        ax.annotate(str(mean) + '\n(' + str(std) + ')',
                xy                  = (angle, y), # theta, radius
                xytext              = (angle, y), # fraction, fraction
                textcoords          = 'data',     #'figure fraction',
                bbox                = dict(boxstyle="round", fc="1.0", edgecolor="1.0"),
                horizontalalignment = 'center',
                size                = 10,
                verticalalignment   = 'center',
                )



        
        

class Statistical_T1_bullseye_plot(Visualization):
    def set_values(self, view, cases, canvas):
        self.cases  = cases
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        #v        = SAX_T1_View()
        self.clear()
        collecting_means = []
        collecting_stds  = []
        for case in self.cases:
            cat         = case.categories[0]
            means, stds = cat.calc_mapping_aha_model()
            means = np.concatenate((means[0],means[1],means[2]))
            stds  = np.concatenate((stds[0], stds[1], stds[2]))
            collecting_means.append(means)
            collecting_stds .append(stds)
        means = np.mean(np.asarray(collecting_means), axis=0)
        stds  = np.mean(np.asarray(collecting_stds),  axis=0)
        
        #ax = self.subplots(1,1)
        ax = self.subplots(1,1, subplot_kw=dict(projection='polar'))
        # requires polar projection: fig,ax = plt.subplots(1,1), subplot_kw=dict(projection='polar'))
        #cmap = plt.cm.viridis
        cmap = plt.cm.gnuplot # ??? which colormap?
        cmap = plt.cm.bwr
        
        print(minv, maxv)
        if minv is None: minv=np.min(means)
        if maxv is None: maxv=np.max(means)
        print(minv, maxv)
        
        minv, maxv = min([minv, 995]), max([maxv, 1005])
        minv = min([minv, 1000 - (maxv-1000)])
        maxv = max([maxv, 1000 + (1000 - minv)])
        norm = colors.Normalize(vmin=minv, vmax=maxv)
        means = np.array(means).ravel()
        stds  = np.array(stds) .ravel()
        theta = np.linspace(0, 2*np.pi, 768)
        r = np.linspace(0.2, 1, 4)
        linewidth = 2
        for i in range(r.shape[0]): ax.plot(theta, np.repeat(r[i], theta.shape), '-k', lw=linewidth)
        for i in range(6):
            theta_i = i * 60 * np.pi/180
            ax.plot([theta_i, theta_i], [r[1], 1], '-k', lw=linewidth)
        for i in range(4):
            theta_i = i * 90 * np.pi/180 - 45*np.pi/180
            ax.plot([theta_i, theta_i], [r[0], r[1]], '-k', lw=linewidth)
        r0 = r[2:4]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i], stds[i], i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+1 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[2],r[3]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[2],r[3]], '-k', lw=linewidth+1)
        r0 = r[1:3]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i+6], stds[i+6],  i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i+6]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+7 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[1],r[2]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[1],r[2]], '-k', lw=linewidth+1)
        r0 = r[0:2]
        r0 = np.repeat(r0[:,np.newaxis], 192, axis=1).T
        for i in range(4):
            theta0 = theta[i*192:i*192+192] + 45*np.pi/180  #+ 90*np.pi/180 
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax,means[i+12], stds[i+12], i*90*np.pi/180 + 90*np.pi/180, np.mean(r0[0]))
            z = np.ones((192,2)) * means[i+12]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+13 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[0],r[1]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[0],r[1]], '-k', lw=linewidth+1)
        ax.set_ylim([0, 1])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        axp    = ax.imshow(np.random.randint(0, 100, (100, 100)))
        cbaxes = self.add_axes([0.78, 0.1, 0.03, 0.8])  # This is the position for the colorbar
        cb     = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=axp, cax=cbaxes)
        ax.set_title('Averaged AHA Model: '+self.cases[0].reader_name)
        self.canvas.draw()

    def write_val(self, ax, mean, std, angle, y):
        mean = "{:.1f}".format(float(mean))
        std  = "{:.1f}".format(float(std))
        ax.annotate(str(mean) + '\n(' + str(std) + ')',
                xy                  = (angle, y), # theta, radius
                xytext              = (angle, y), # fraction, fraction
                textcoords          = 'data',     #'figure fraction',
                bbox                = dict(boxstyle="round", fc="1.0", edgecolor="1.0"),
                horizontalalignment = 'center',
                size                = 10,
                verticalalignment   = 'center',
                )


class Statistical_T1_diff_bullseye_plot(Visualization):
    def set_values(self, view, ccs, canvas):
        self.ccs    = ccs
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        #v   = SAX_T1_View()
        self.clear()
        
        collecting_means = []
        collecting_stds  = []
        for cc in self.ccs:
            cat1 = cc.case1.categories[0]
            cat2 = cc.case2.categories[0]
            means1, stds1 = cat1.calc_mapping_aha_model()
            means2, stds2 = cat2.calc_mapping_aha_model()
            means = np.concatenate((means1[0]-means2[0],
                                    means1[1]-means2[1],
                                    means1[2]-means2[2]))
            stds  = np.concatenate((stds1[0]-stds2[0], 
                                    stds1[1]-stds2[1], 
                                    stds1[2]-stds2[2]))
            collecting_means.append(means)
            collecting_stds.append(stds)
        means = np.mean(np.asarray(collecting_means), axis=0)
        stds  = np.mean(np.asarray(collecting_stds),  axis=0)
        
        ax = self.subplots(1,1, subplot_kw=dict(projection='polar'))
        cmap = plt.cm.PRGn
        if minv is None: minv=np.min(means)-5
        if maxv is None: maxv=np.max(means)+5
        minv, maxv = min([minv, -maxv]), max([maxv, -minv])
        norm = colors.Normalize(vmin=minv, vmax=maxv)
        means = np.array(means).ravel()
        stds  = np.array(stds) .ravel()
        theta = np.linspace(0, 2*np.pi, 768)
        r = np.linspace(0.2, 1, 4)
        linewidth = 2
        for i in range(r.shape[0]): ax.plot(theta, np.repeat(r[i], theta.shape), '-k', lw=linewidth)
        for i in range(6):
            theta_i = i * 60 * np.pi/180
            ax.plot([theta_i, theta_i], [r[1], 1], '-k', lw=linewidth)
        for i in range(4):
            theta_i = i * 90 * np.pi/180 - 45*np.pi/180
            ax.plot([theta_i, theta_i], [r[0], r[1]], '-k', lw=linewidth)
        r0 = r[2:4]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i], stds[i], i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+1 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[2],r[3]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[2],r[3]], '-k', lw=linewidth+1)
        r0 = r[1:3]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i+6], stds[i+6],  i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i+6]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+7 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[1],r[2]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[1],r[2]], '-k', lw=linewidth+1)
        r0 = r[0:2]
        r0 = np.repeat(r0[:,np.newaxis], 192, axis=1).T
        for i in range(4):
            theta0 = theta[i*192:i*192+192] + 45*np.pi/180  #+ 90*np.pi/180 
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax,means[i+12], stds[i+12], i*90*np.pi/180 + 90*np.pi/180, np.mean(r0[0]))
            z = np.ones((192,2)) * means[i+12]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+13 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[0],r[1]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[0],r[1]], '-k', lw=linewidth+1)
        ax.set_ylim([0, 1])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        axp    = ax.imshow(np.random.randint(0, 100, (100, 100)))
        cbaxes = self.add_axes([0.78, 0.1, 0.03, 0.8])  # This is the position for the colorbar
        cb     = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=axp, cax=cbaxes)
        ax.set_title('Averaged AHA Difference Model: '+self.ccs[0].case1.reader_name+' - '+self.ccs[0].case2.reader_name)
        
        self.canvas.draw()

    def write_val(self, ax, mean, std, angle, y):
        mean = "{:.1f}".format(float(mean))
        std  = "{:.1f}".format(float(std))
        ax.annotate(str(mean) + '\n(' + str(std) + ')',
                xy                  = (angle, y), # theta, radius
                xytext              = (angle, y), # fraction, fraction
                textcoords          = 'data',     #'figure fraction',
                bbox                = dict(boxstyle="round", fc="1.0", edgecolor="1.0"),
                horizontalalignment = 'center',
                size                = 10,
                verticalalignment   = 'center',
                )
        
        

class LAX_BlandAltman(Visualization):
    def visualize(self, view, ccs):
        cases1   = [cc.case1 for cc in ccs]
        cases2   = [cc.case2 for cc in ccs]
        rows, columns   = 4, 2
        #fig, axes = plt.subplots(rows, columns, figsize=(columns*11.0,rows*5.0))
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])

        cr_cols = ['case_name']+[cr.name+'_avg' for cr in ccs[0].case1.
                                 crs]+[cr.name+'_diff' for cr in ccs[0].case1.crs]
        cr_rows = []
        for cc in ccs:
            row = [cc.case1.case_name]
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append((cr1.get_val() + cr2.get_val())/ 2.0)
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append(cr1.get_val_diff(cr2))
            cr_rows.append(row)
        cr_table = DataFrame(cr_rows, columns=cr_cols)

        #display(cr_table)
        x_name, y_name = '4CV_RAESAREA_avg', '4CV_RAESAREA_diff'
        sns.scatterplot(ax=axes[0][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][0].axhline(mean, ls="-", c=".2")
        axes[0][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_RAEDAREA_avg', '4CV_RAEDAREA_diff'
        sns.scatterplot(ax=axes[0][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][1].axhline(mean, ls="-", c=".2")
        axes[0][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAESAREA_avg', '4CV_LAESAREA_diff'
        sns.scatterplot(ax=axes[1][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][0].axhline(mean, ls="-", c=".2")
        axes[1][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAEDAREA_avg', '4CV_LAEDAREA_diff'
        sns.scatterplot(ax=axes[1][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][1].axhline(mean, ls="-", c=".2")
        axes[1][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAESAREA_avg', '2CV_LAESAREA_diff'
        sns.scatterplot(ax=axes[2][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][0].axhline(mean, ls="-", c=".2")
        axes[2][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAEDAREA_avg', '2CV_LAEDAREA_diff'
        sns.scatterplot(ax=axes[2][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][1].axhline(mean, ls="-", c=".2")
        axes[2][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][1].axhline(mean-1.96*std, ls=":", c=".2")

        m_table = LAX_CCs_MetricsTable()
        m_table.calculate(ccs, view)
        #display(m_table.df)

        ra_vals = m_table.df['ra LAX 4CV RAES DSC'].to_list() + m_table.df['ra LAX 4CV RAED DSC'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES DSC'].to_list() + m_table.df['la LAX 4CV LAED DSC'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES DSC'].to_list() + m_table.df['la LAX 2CV LAED DSC'].to_list()

        dicebp = sns.boxplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][0].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][0].set_ylabel('DSC [%]')

        for i, boxplot in enumerate(dicebp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        ra_vals = m_table.df['ra LAX 4CV RAES HD'].to_list() + m_table.df['ra LAX 4CV RAED HD'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES HD'].to_list() + m_table.df['la LAX 4CV LAED HD'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES HD'].to_list() + m_table.df['la LAX 2CV LAED HD'].to_list()

        hd_bp = sns.boxplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][1].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][1].set_ylabel('Hausdorff Distance [mm]')

        for i, boxplot in enumerate(hd_bp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
        #fig.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    
    def store(self, storepath, figurename='clinical_results_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
    

        

class LAX_Volumes_BlandAltman(Visualization):
    def visualize(self, view, ccs):
        cases1   = [cc.case1 for cc in ccs]
        cases2   = [cc.case2 for cc in ccs]
        rows, columns   = 4, 2
        #fig, axes = plt.subplots(rows, columns, figsize=(columns*11.0,rows*5.0))
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])

        cr_cols = ['case_name']+[cr.name+'_avg' for cr in ccs[0].case1.
                                 crs]+[cr.name+'_diff' for cr in ccs[0].case1.crs]
        cr_rows = []
        for cc in ccs:
            row = [cc.case1.case_name]
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append((cr1.get_val() + cr2.get_val())/ 2.0)
            for cr1, cr2 in zip(cc.case1.crs, cc.case2.crs):
                row.append(cr1.get_val_diff(cr2))
            cr_rows.append(row)
        cr_table = DataFrame(cr_rows, columns=cr_cols)

        #display(cr_table)
        x_name, y_name = '4CV_RAESV_avg', '4CV_RAESV_diff'
        sns.scatterplot(ax=axes[0][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][0].axhline(mean, ls="-", c=".2")
        axes[0][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_RAEDV_avg', '4CV_RAEDV_diff'
        sns.scatterplot(ax=axes[0][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[0][1].axhline(mean, ls="-", c=".2")
        axes[0][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[0][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAESV_avg', '4CV_LAESV_diff'
        sns.scatterplot(ax=axes[1][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][0].axhline(mean, ls="-", c=".2")
        axes[1][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '4CV_LAEDV_avg', '4CV_LAEDV_diff'
        sns.scatterplot(ax=axes[1][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[1][1].axhline(mean, ls="-", c=".2")
        axes[1][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[1][1].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAESV_avg', '2CV_LAESV_diff'
        sns.scatterplot(ax=axes[2][0], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][0].axhline(mean, ls="-", c=".2")
        axes[2][0].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][0].axhline(mean-1.96*std, ls=":", c=".2")

        x_name, y_name = '2CV_LAEDV_avg', '2CV_LAEDV_diff'
        sns.scatterplot(ax=axes[2][1], x=x_name, y=y_name,
                        data=cr_table, markers='o', palette=swarm_palette, 
                        size=np.abs(cr_table[y_name]), s=10, legend=False)
        mean = cr_table[y_name].mean()
        std = cr_table[y_name].std()
        axes[2][1].axhline(mean, ls="-", c=".2")
        axes[2][1].axhline(mean+1.96*std, ls=":", c=".2")
        axes[2][1].axhline(mean-1.96*std, ls=":", c=".2")

        m_table = LAX_CCs_MetricsTable()
        m_table.calculate(ccs, view)
        #display(m_table.df)

        ra_vals = m_table.df['ra LAX 4CV RAES DSC'].to_list() + m_table.df['ra LAX 4CV RAED DSC'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES DSC'].to_list() + m_table.df['la LAX 4CV LAED DSC'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES DSC'].to_list() + m_table.df['la LAX 2CV LAED DSC'].to_list()

        dicebp = sns.boxplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][0], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][0].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][0].set_ylabel('DSC [%]')

        for i, boxplot in enumerate(dicebp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        ra_vals = m_table.df['ra LAX 4CV RAES HD'].to_list() + m_table.df['ra LAX 4CV RAED HD'].to_list()
        la4vals = m_table.df['la LAX 4CV LAES HD'].to_list() + m_table.df['la LAX 4CV LAED HD'].to_list()
        la2vals = m_table.df['la LAX 2CV LAES HD'].to_list() + m_table.df['la LAX 2CV LAED HD'].to_list()

        hd_bp = sns.boxplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], width=0.4)
        sns.swarmplot(ax=axes[3][1], data=[ra_vals,la4vals,la2vals], 
                      palette=swarm_palette, dodge=True)
        axes[3][1].set_xticklabels(['RA 4CV', 'LA 4CV', 'LA 2CV'])
        axes[3][1].set_ylabel('Hausdorff Distance [mm]')

        for i, boxplot in enumerate(hd_bp.artists):
            if i==0: boxplot.set_facecolor(custom_palette [i])
            else:    boxplot.set_facecolor(custom_palette2[i])

        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    
    def store(self, storepath, figurename='clinical_volumes_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
    


