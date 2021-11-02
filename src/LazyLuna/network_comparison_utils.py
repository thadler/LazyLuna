import matplotlib.pyplot as plt
import seaborn as sb
import pandas

import numpy as np
from scipy.stats import wilcoxon

from LazyLuna import Mini_LL


def clinical_result_pandas_table(cases1, cases2, with_dices=True, contour_names=['lv_endo','lv_myo','rv_endo']):
    row_dict = dict()
    row_counter = 0
    columns=['case']
    for cr in cases1[0].crs: columns += [cr.name+' '+cases1[0].reader_name, cr.name+' '+cases2[0].reader_name, cr.name+' difference']
    for c1,c2 in zip(cases1, cases2):
        row = [c1.case_name]
        for cr1, cr2 in zip(c1.crs, c2.crs):
            row += [cr1.get_cr(), cr2.get_cr(), cr1.get_cr_diff(cr2)]
        row_dict['row_'+str(row_counter).zfill(5)] = row
        row_counter += 1
    df = pandas.DataFrame.from_dict(row_dict,  orient='index', columns=columns)
    if with_dices: df = pandas.concat([df, dices_pandas_table(cases1, cases2, contour_names)], axis=1, join="outer")
    wilcox_tests = {n:wilcoxon(df[n],zero_method='zsplit') for n in df.columns if 'difference' in n and len(df[n].values.shape)==1}
    return df, df.describe(), wilcox_tests

def dices_pandas_table(cases1, cases2, contour_names=['lv_endo','lv_myo','rv_endo']):
    row_dict = dict()
    row_counter = 0
    for c1,c2 in zip(cases1, cases2):
        analyzer = Mini_LL.SAX_CINE_analyzer(Mini_LL.Case_Comparison(c1,c2))
        row = [c1.case_name]
        df = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader=True)
        all_dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0] in contour_names]
        row.append(np.mean(all_dices)); row.append(np.mean([d for d in all_dices if 0<d<100]))
        for cname in contour_names:
            dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0]==cname]
            row.append(np.mean(dices)); row.append(np.mean([d for d in dices if 0<d<100]))
        row_dict['row_'+str(row_counter).zfill(5)] = row
        row_counter += 1
    columns = ['case', 'avg dice', 'avg dice cont by both']
    for c in contour_names: columns.extend([c+' avg dice', c+' avg dice cont by both'])
    df = pandas.DataFrame.from_dict(row_dict, orient='index', columns=columns)
    return df


def SAX_candlelight_plot(gs_cases, name2cases):
    columns, rows    = 2, 4
    boxplot_palette  = sb.color_palette("Blues")
    boxplot_palette2 = sb.color_palette("Purples")
    swarm_palette = sb.color_palette(["#061C36", "#061C36"])
    font = {'family' : 'DejaVu Sans',
            'weight' : 'normal',
            'size'   : 18}
    plt.rc('font', **font)
    fig, axes = plt.subplots(rows, columns, figsize=(columns*11,(rows*7.5)))
    
    name2tables = dict()
    for n in name2cases.keys(): name2tables[n] = clinical_result_pandas_table(gs_cases, name2cases[n])
    
    j = 0
    for i, crv in enumerate(crvs_data):
        if i >= (rows*columns): continue
        while i >= rows: i-=rows
        axes[i][j].set_title(crv + " Error")
        sb.boxplot   (ax=axes[i][j], data=crvs_data[crv], palette=boxplot_palette, saturation=1, width=0.6)
        sb.swarmplot (ax=axes[i][j], data=crvs_data[crv], color="#061C36", alpha=1)
        axes[i][j].set_xticklabels([name2cases.keys()])
        axes[i][j].set_ylabel('[%]' if 'EF' in crv else '[ml]' if 'ESV' in crv or 'EDV' in crv else '[g]' )
        yabs_max = abs(max(axes[i][j].get_ylim(), key=abs))
        axes[i][j].set_ylim(ymin=-yabs_max, ymax=yabs_max)
        if i == (rows-1): j+=1

    ax = axes[3][1]
    ax.set_title('Dice')
    dicebp = sb.boxplot   (ax=ax, x="NetName", y="Dice", data=dice_data, hue="Segmented by both", width=0.8)
    sb.swarmplot (ax=ax, x="NetName", y="Dice", data=dice_data, hue="Segmented by both", palette=swarm_palette, dodge=True)
    handles, labels = ax.get_legend_handles_labels()
    handles[0].set_fc(boxplot_palette[3])
    handles[1].set_fc(boxplot_palette2[3])
    ax.legend(handles[:2], labels[:2], title="Segmented by both")
    ax.set_ylabel('[%]')
    ax.set_xlabel("")
    ax.set_ylim(ymin=70, ymax=95)

    for i, boxplot in enumerate(dicebp.artists):
        if i%2 == 0: boxplot.set_facecolor(boxplot_palette[i//2])
        else:        boxplot.set_facecolor(boxplot_palette2[i//2])

    sb.despine()
    plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.25, hspace=0.35)
    fig.savefig("candlelight_test.png", dpi=100, facecolor="#FFFFFF")