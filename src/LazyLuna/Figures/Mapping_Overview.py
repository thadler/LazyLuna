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


class Mapping_Overview(Visualization):
    def visualize(self, case_comparisons, mapping_type='T1'):
        """Takes a list of case_comparisons and presents Blandaltmans for several Clinical Results in one figure
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons for calculation
        """
        rows, columns   = 4, 2
        self.set_size_inches(w=columns*11.0, h=(rows*6.0))
        axes = self.subplots(rows, columns)
        custom_palette  = sns.color_palette("Blues")
        custom_palette2 = sns.color_palette("Purples")
        swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
        
        cr  = [cr for cr in case_comparisons[0].case1.crs if 'GLOBAL' in cr.name][0]
        cr_name = cr.name
        
        titlesize=24
        labelsize=20
        ticksize=16
        
        # Bland Altman
        ax = axes[0][0]
        cr_table = CC_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_dices=False)
        cr_table.add_bland_altman_dataframe(case_comparisons)
        table = cr_table.df
        avg_n  = [c for c in table.columns if 'GLOBAL' in c and 'avg'  in c][0]
        diff_n = [c for c in table.columns if 'GLOBAL' in c and 'diff' in c][0]
        ax.set_title(avg_n.replace(' avg','') + ' Bland Altman', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=avg_n, y=diff_n, data=table, markers='o', 
                        palette=swarm_palette, size=np.abs(table[diff_n]), 
                        s=10, legend=False)
        avg_difference = table[diff_n].mean()
        std_difference = table[diff_n].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        ax.set_xlabel(cr.name+' '+cr.unit, fontsize=labelsize)
        ax.set_ylabel(cr.name+' '+cr.unit, fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        
        # Paired Boxplot
        ax = axes[0][1]
        readername1 = case_comparisons[0].case1.reader_name
        readername2 = case_comparisons[0].case2.reader_name
        rows = []
        for cc in case_comparisons:
            cr1 = [cr.get_val() for cr in cc.case1.crs if cr.name==cr_name][0]
            cr2 = [cr.get_val() for cr in cc.case2.crs if cr.name==cr_name][0]
            casename, studyuid = cc.case1.case_name, cc.case1.studyinstanceuid
            if np.isnan(cr1) or np.isnan(cr2): continue
            else: rows.extend([[casename, studyuid, readername1, cr1], [casename, studyuid, readername2, cr2]])
        df = DataFrame(rows, columns=['casename', 'studyuid', 'Reader', cr.name])
        # Plot
        sns.boxplot  (ax=ax, data=df, y='Reader', x=cr_name, width=0.4, palette=custom_palette, orient='h', linewidth=1)
        sns.swarmplot(ax=ax, data=df, y='Reader', x=cr_name, palette=swarm_palette, orient='h')
        ax.set_title(cr_name+' Paired Boxplot', fontsize=titlesize)
        ax.set_ylabel('')
        ax.set_xlabel(cr.name+' '+cr.unit, fontsize=22)
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
        
        
        # Bland Altman for slice ms
        ax = axes[1][0]
        rows = []
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                try:
                    val1 = np.nanmean(cat1.get_anno(d,0).get_pixel_values('lv_myo', cat1.get_img(d,0)).tolist())
                    val2 = np.nanmean(cat2.get_anno(d,0).get_pixel_values('lv_myo', cat2.get_img(d,0)).tolist())
                    avg, diff = (val1+val2)/2.0, val1-val2
                    if np.isnan(val1) or np.isnan(val2): continue
                    else: rows.append([avg, diff])
                except Exception as e:
                    print(cc.case1.case_name, d, e)
        table = DataFrame(rows, columns=[avg_n, diff_n])
        ax.set_title(mapping_type + ' Bland Altman (by slice & segmented by both)', fontsize=titlesize)
        sns.scatterplot(ax=ax, x=avg_n, y=diff_n, data=table, markers='o', 
                        palette=swarm_palette, size=np.abs(table[diff_n]), 
                        s=10, legend=False)
        avg_difference = table[diff_n].mean()
        std_difference = table[diff_n].std()
        ax.axhline(avg_difference, ls="-", c=".2")
        ax.axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        ax.axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        ax.set_xlabel(mapping_type+' '+cr.unit, fontsize=labelsize)
        ax.set_ylabel(mapping_type+' '+cr.unit, fontsize=labelsize)
        yabs_max = abs(max(ax.get_ylim(), key=abs)) + 10
        ax.set_ylim(ymin=-yabs_max, ymax=yabs_max)
        
        
        # Paired Boxplot for slice ms
        ax = axes[1][1]
        readername1 = case_comparisons[0].case1.reader_name
        readername2 = case_comparisons[0].case2.reader_name
        rows = []
        segm_by_both, segm_by_r1, segm_by_r2, segm_by_none = 0, 0, 0, 0
        for cc in case_comparisons:
            cat1, cat2 = cc.case1.categories[0], cc.case2.categories[0]
            for d in range(cat1.nr_slices):
                try:    val1 = np.nanmean(cat1.get_anno(d,0).get_pixel_values('lv_myo', cat1.get_img(d,0)).tolist())
                except: val1 = np.nan
                try:    val2 = np.nanmean(cat2.get_anno(d,0).get_pixel_values('lv_myo', cat2.get_img(d,0)).tolist())
                except: val2 = np.nan
                if not np.isnan(val1) and not np.isnan(val2): segm_by_both += 1
                if not np.isnan(val1) and np.isnan(val2):     segm_by_r1   += 1
                if np.isnan(val1) and not np.isnan(val2):     segm_by_r2   += 1
                if np.isnan(val1) and np.isnan(val2):         segm_by_none += 1
                if np.isnan(val1) or np.isnan(val2): continue
                else: rows.extend([[cc.case1.case_name, d, cc.case1.reader_name, val1], 
                                   [cc.case2.case_name, d, cc.case2.reader_name, val2]])
        df = DataFrame(rows, columns=['casename', 'slice', 'Reader', cr.name])
        sns.boxplot  (ax=ax, data=df, y='Reader', x=cr_name, width=0.4, palette=custom_palette, orient='h', linewidth=1)
        sns.swarmplot(ax=ax, data=df, y='Reader', x=cr_name, palette=swarm_palette, orient='h')
        ax.set_title(mapping_type +' Paired Boxplot (by slice & segmented by both)', fontsize=titlesize)
        ax.set_ylabel('')
        ax.set_xlabel(mapping_type + ' ' + cr.unit, fontsize=labelsize)
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
        
        
        # histogram of counts
        ax = axes[2][0]
        ax.set_ylabel('Count [#]')
        ax.set_title('Barplot of Annotated / Overlooked Images', fontsize=titlesize)
        sns.barplot(x=['Segm. by \nboth', 'Segm. only \nby '+readername1, 'Segm. only \nby '+readername2, 'Segm. by \nnone'], 
                    y=[segm_by_both, segm_by_r1, segm_by_r2, segm_by_none], 
                    ax=ax, palette=custom_palette2[2:])#, width=0.4)
        
        
        # Tolerance ranges
        ax = axes[2][1]
        ax.axhspan(-cr.tol_range, cr.tol_range, facecolor='0.6', alpha=0.5)
        alpha = 0.5 
        sns.swarmplot(ax=ax, y=table[diff_n], palette=sns.color_palette("Blues")[4:], 
                      dodge=True, size=5, alpha=alpha)
        ci = 1.96 * np.std(table[diff_n]) / np.sqrt(len(table[diff_n]))
        ax.errorbar([cr_name], [np.mean(table[diff_n])], yerr=ci, fmt ='o', c='r')
        maxx = np.max([np.abs(np.min(table[diff_n])), np.abs(np.max(table[diff_n])),
                       np.abs(np.mean(table[diff_n])-ci), np.abs(np.mean(table[diff_n])+ci), 
                       cr.tol_range])
        ax.set_title(mapping_type +' Tolerance Range (by slice & segmented by both)', fontsize=titlesize)
        ax.set_ylim(ymin=-maxx-10, ymax=maxx+10)
        ax.set_ylabel(cr_name + ' ' + cr.unit, fontsize=labelsize)
        ax.set_xlabel(cr_name, fontsize=labelsize)
        
        
        # Dice Values
        ax = axes[3][0]
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
                        rows.append([conttype, dice, hd])
                    except Exception as e:
                        print(cc.case1.case_name, d, e)
        table = DataFrame(rows, columns=['cont type', 'Dice', 'HD'])
        ax.set_title('Dice (by slice & segmented by both)', fontsize=titlesize)
        dicebp = sns.boxplot(ax=ax, x="cont type", y="Dice", data=table, palette=custom_palette, width=0.8)
        sns.swarmplot(ax=ax, x="cont type", y="Dice", data=table, palette=swarm_palette, dodge=True)
        ax.set_ylabel('Dice [%]', fontsize=labelsize)
        ax.set_xlabel("", fontsize=labelsize)
        ymin = np.max([np.min(table['Dice']) - 5, 0])
        ax.set_ylim(ymin=ymin, ymax=101)
        
        # HD Values
        ax = axes[3][1]
        ax.set_title('Hausdorff (by slice & segmented by both)', fontsize=titlesize)
        dicebp = sns.boxplot(ax=ax, x="cont type", y="HD", data=table, palette=custom_palette, width=0.8)
        sns.swarmplot(ax=ax, x="cont type", y="HD", data=table, palette=swarm_palette, dodge=True)
        ax.set_ylabel('HD [mm]', fontsize=labelsize)
        ax.set_xlabel("", fontsize=labelsize)
        ymax = np.max(table['HD']) + 2
        ax.set_ylim(ymin=0, ymax=ymax)
        
        for ax_ in axes:
            for ax in ax_:
                ax.tick_params(axis='both', which='major', labelsize=ticksize)

        
        sns.despine()
        self.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.25)
    
    def store(self, storepath, figurename='clinical_results_bland_altman.png'):
        self.savefig(os.path.join(storepath, figurename), dpi=100, facecolor="#FFFFFF")
        return os.path.join(storepath, figurename)