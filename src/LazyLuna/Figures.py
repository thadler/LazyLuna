import os

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import gridspec
import seaborn as sns

import shapely
from descartes import PolygonPatch
import numpy as np
import pandas
from scipy.stats import wilcoxon

from LazyLuna import Mini_LL
from LazyLuna.Tables import *
        


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
        ax.set_ylim(ymin=70, ymax=100)
        for i, boxplot in enumerate(dicebp.artists):
            if i%2 == 0: boxplot.set_facecolor(custom_palette[i//2])
            else:        boxplot.set_facecolor(custom_palette2[i//2])
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    
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
        ax1.imshow(img1,'gray'); ax2.imshow(img1,'gray'); ax3.imshow(img2,'gray'); ax4.imshow(img1,'gray')
        self.suptitle('Category: ' + cat1.name + ', slice: ' + str(slice_nr))
        if self.add_annotation:
            anno1.plot_contour_face   (ax1,        contour_name, alpha=0.4, c='r')
            anno1.plot_cont_comparison(ax2, anno2, contour_name, alpha=0.4)
            anno2.plot_contour_face   (ax3,        contour_name, alpha=0.4, c='b')
            anno1.plot_all_contour_outlines(ax1)
            anno2.plot_all_contour_outlines(ax3)
        for ax in [ax1, ax2, ax3]: ax.set_xticks([]); ax.set_yticks([])
        d = shapely.geometry.Polygon([[0,0],[1,1],[1,0]])
        patches = [PolygonPatch(d,facecolor='blue', edgecolor='blue',  alpha=0.4),
                   PolygonPatch(d,facecolor='green',edgecolor='green', alpha=0.4),
                   PolygonPatch(d,facecolor='red',  edgecolor='red',   alpha=0.4)]
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
        
    

        
class BlandAltman(Visualization):
    def visualize(self, case_comparisons, cr_name):
        self.cr_name = cr_name
        cases1   = [cc.case1 for cc in case_comparisons]
        cases2   = [cc.case2 for cc in case_comparisons]
        #self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        ax = self.subplots(111)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        crs1 = []; crs2 = []
        for cc in case_comparisons:
            crs1.append([cr for cr in cc.case1.crs if cr.name==cr_name][0])
            crs2.append([cr for cr in cc.case2.crs if cr.name==cr_name][0])
        avgs  = (np.array(crs1) + np.array(crs2)) / 2.0
        diffs =  np.array(crs1) - np.array(crs2)
        
        sns.scatterplot(ax=ax, x=avgs, y=diffs, markers='o', palette=swarm_palette, 
                        size=np.abs(table[diff_n]), s=10, legend=False)
        ax.axhline(np.mean(diffs), ls="-", c=".2")
        ax.axhline(np.mean(diffs)+1.96*np.std(diffs), ls=":", c=".2")
        ax.axhline(np.mean(diffs)-1.96*np.std(diffs), ls=":", c=".2")


        handles, labels = ax.get_legend_handles_labels()
        handles[0].set(color=custom_palette[3])
        handles[1].set(color=custom_palette2[3])
        ax.legend(handles[:2], labels[:2], title="Segmented by both", fontsize=14)
        ax.set_ylabel('[%]', fontsize=14)
        ax.set_xlabel("", fontsize=14)
        ax.set_ylim(ymin=70, ymax=100)
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    
    def store(self, storepath, figurename='_bland_altman.png'):
        self.savefig(os.path.join(storepath, self.cr_name+figurename), dpi=100, facecolor="#FFFFFF")
    
    
    
    
