import os

import matplotlib.pyplot as plt
import seaborn as sns
import pandas

import numpy as np
from scipy.stats import wilcoxon

from LazyLuna import Mini_LL
from LazyLuna.Tables import *



def SAX_candlelight_plot(case_comparisons, store_path=''):
    cases1 = [cc.case1 for cc in case_comparisons]
    cases2 = [cc.case2 for cc in case_comparisons]
    columns, rows    = 4, 2
    boxplot_palette  = sns.color_palette("Blues")
    boxplot_palette2 = sns.color_palette("Purples")
    swarm_palette = sns.color_palette(["#061C36", "#061C36"])
    plt.rc('font', **{'family': 'DejaVu Sans', 'weight': 'normal', 'size': 12})
    fig, axes = plt.subplots(rows, columns, figsize=(columns*7.5/2,(rows*7.5)))
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
    plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    fig.savefig(os.path.join(store_path,'clinical_results_candlelights.png'), dpi=100, facecolor="#FFFFFF")
    

    
def SAX_candlelight_plot2(case_comparisons, store_path=''):
    cases1 = [cc.case1 for cc in case_comparisons]
    cases2 = [cc.case2 for cc in case_comparisons]
    columns, rows    = 2, 4
    boxplot_palette  = sns.color_palette("Blues")
    boxplot_palette2 = sns.color_palette("Purples")
    swarm_palette = sns.color_palette(["#061C36", "#061C36"])
    plt.rc('font', **{'family': 'DejaVu Sans', 'weight': 'normal', 'size': 18})
    fig, axes = plt.subplots(rows, columns, figsize=(columns*11.0,(rows*7.5)))
    
    cr_table = CC_ClinicalResultsTable()
    cr_table.calculate(case_comparisons, with_dices=True)
    table = cr_table.df
    j = 0
    crvs = ['LVESV', 'LVEDV', 'LVEF', 'LVMYOMASS', 'RVESV', 'RVEDV', 'RVEF']
    crvs = [crv+' difference' for crv in crvs]
    for i, crv in enumerate(crvs):
        if i >= (rows*columns): continue
        while i >= rows: i-=rows
        axes[i][j].set_title(crv.replace(' difference','').replace('YOMASS','') + " Error")
        sns.boxplot(ax=axes[i][j], data=table, x='reader2', y=crv, palette=boxplot_palette, saturation=1, width=0.6)
        sns.swarmplot (ax=axes[i][j], data=table, x='reader2', y=crv, color="#061C36", alpha=1)        
        axes[i][j].set_ylabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]' )
        yabs_max = abs(max(axes[i][j].get_ylim(), key=abs))
        #axes[i][j].set_ylim(ymin=-yabs_max, ymax=yabs_max)
        if 'EF' in crv: axes[i][j].set_ylim(ymin=-20, ymax=20)
        if 'ESV' in crv or 'EDV' in crv: axes[i][j].set_ylim(ymin=-45, ymax=45)
        if 'MYOMASS' in crv: axes[i][j].set_ylim(ymin=-30, ymax=30)
        axes[i][j].set_xlabel("")
        if i == (rows-1): j+=1
            
    ax = axes[3][1]
    ax.set_title('Dice')
    dicebp = sns.boxplot(ax=ax, x="reader2", y="avg dice", data=table, width=0.8)
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
    plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    fig.savefig(os.path.join(store_path,'candlelight_test.png'), dpi=100, facecolor="#FFFFFF")
    
    

def SAX_BlandAltman_plot(case_comparisons, store_path=''):
    cases1 = [cc.case1 for cc in case_comparisons]
    cases2 = [cc.case2 for cc in case_comparisons]
    columns, rows    = 2, 4
    custom_palette  = sns.color_palette("Blues")
    custom_palette2 = sns.color_palette("Purples")
    swarm_palette   = sns.color_palette(["#061C36", "#061C36"])
    plt.rc('font', **{'family': 'DejaVu Sans', 'weight': 'normal', 'size': 18})
    fig, axes = plt.subplots(rows, columns, figsize=(columns*11.0,(rows*6.0)))
    
    cr_table = CC_ClinicalResultsTable()
    cr_table.calculate(case_comparisons, with_dices=False)
    cr_table.add_bland_altman_dataframe(case_comparisons)
    table = cr_table.df
    j = 0
    crvs = ['LVESV', 'LVEDV', 'LVEF', 'LVMYOMASS', 'RVESV', 'RVEDV', 'RVEF']
    for i, crv in enumerate(crvs):
        if i >= (rows*columns): continue
        while i >= rows: i-=rows
        avg_n  = crv + ' avg'
        diff_n = crv + ' difference'
        axes[i][j].set_title(crv.replace('YOMASS','') + ' Bland Altman')
        sns.scatterplot(ax=axes[i][j], x=avg_n, y=diff_n, data=table, markers='o', 
                        palette=swarm_palette, size=np.abs(table[diff_n]), 
                        s=10, legend=False)
        avg_difference = table[diff_n].mean()
        std_difference = table[diff_n].std()
        axes[i][j].axhline(avg_difference, ls="-", c=".2")
        axes[i][j].axhline(avg_difference+1.96*std_difference, ls=":", c=".2")
        axes[i][j].axhline(avg_difference-1.96*std_difference, ls=":", c=".2")
        
        axes[i][j].set_xlabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]' )
        axes[i][j].set_ylabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]' )
        
        yabs_max = abs(max(axes[i][j].get_ylim(), key=abs))
        #axes[i][j].set_ylim(ymin=-yabs_max, ymax=yabs_max)
        if 'EF' in crv: axes[i][j].set_ylim(ymin=-20, ymax=20)
        if 'ESV' in crv or 'EDV' in crv: axes[i][j].set_ylim(ymin=-45, ymax=45)
        if 'MYOMASS' in crv: axes[i][j].set_ylim(ymin=-30, ymax=30)
        if i == (rows-1): j+=1
            
    dice_table = CC_SAX_DiceTable()
    dice_table.calculate(case_comparisons)
    d_table = dice_table.df
    ax = axes[3][1]
    ax.set_title('Dice')
    dicebp = sns.boxplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table, width=0.8)
    sns.swarmplot(ax=ax, x="cont type", y="avg dice", hue='cont by both', data=d_table,
                  palette=swarm_palette, dodge=True)
    handles, labels = ax.get_legend_handles_labels()
    handles[0].set(color=custom_palette[3])
    handles[1].set(color=custom_palette2[3])
    ax.legend(handles[:2], labels[:2], title="Segmented by both")
    ax.set_ylabel('[%]')
    ax.set_xlabel("")
    ax.set_ylim(ymin=70, ymax=100)
    for i, boxplot in enumerate(dicebp.artists):
        if i%2 == 0: boxplot.set_facecolor(custom_palette[i//2])
        else:        boxplot.set_facecolor(custom_palette2[i//2])
    sns.despine()
    plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    fig.savefig(os.path.join(store_path,'clinical_relevant_values_bland_altman.png'), dpi=100, facecolor="#FFFFFF")