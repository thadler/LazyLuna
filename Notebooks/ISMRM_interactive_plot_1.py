import os
from pathlib import Path
import pickle
from time import time
import pandas as pd

import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import seaborn as sns

from catch_converter.parse_contours import parse_cvi42ws
from LazyLuna.Mini_LL import *
from LazyLuna.CATCH_utils import *
from LazyLuna.network_comparison_utils import *


"""
bp       = '/media/omega/Daten1/CATCH/CS'
bp_annos = '/media/omega/Daten1/CATCH/CS/Preds/FCN'
bp_cases = '/media/omega/Daten1/CATCH/CS/Cases'
bp_imgs  = '/media/omega/Daten1/CATCH/CS/Imgs'
"""
bp       = '/Users/dietrichhadler/Desktop/Daten/CS_ESED_Cases'
bp_annos = '/Users/dietrichhadler/Desktop/Daten/CS_ESED_Cases/Annos'
bp_cases = '/Users/dietrichhadler/Desktop/Daten/CS_ESED_Cases/Cases'
bp_imgs  = '/Users/dietrichhadler/Desktop/Daten/CS_ESED_Cases/Imgs'


# load cases
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'Annos' in p]
cases1 = [pickle.load(open(p, 'rb')) for p in case_paths]
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'UNet' in p and 'MRUNet' not in p]
cases2 = [pickle.load(open(p, 'rb')) for p in case_paths]
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'FCN' in p]
cases3 = [pickle.load(open(p, 'rb')) for p in case_paths]
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'MRUNet' in p]
cases4 = [pickle.load(open(p, 'rb')) for p in case_paths]
cases1 = sorted(cases1, key=lambda c: c.case_name)
cases2 = sorted(cases2, key=lambda c: c.case_name)
cases3 = sorted(cases3, key=lambda c: c.case_name)
cases4 = sorted(cases4, key=lambda c: c.case_name)
names = set([c.case_name for c in cases2])
cases1 = [c for c in cases1 if c.case_name in names]

#cases1 = cases1[:3]
#cases2 = cases2[:3]


metric_names  = ['dice', 'hd', 'ml diff', 'by reader1', 'by reader2', 'position1', 'position2']
contour_names = ['lv_endo', 'lv_myo', 'rv_endo']
ph_names      = ['ES', 'ED']

column_names  = ['case name', 'reader1', 'reader2', 'slice']
column_names += [cn+' '+p+' '+mn for cn in contour_names for p in ph_names for mn in metric_names]

def get_position(case, d, p, cont_name):
    cat  = case.categories[0]
    anno = cat.get_anno(d, p)
    has_cont = anno.has_contour(cont_name)
    if not has_cont:                    return 'outside'
    if has_cont and d==0:               return 'basal'
    if has_cont and d==cat.nr_slices-1: return 'apical'
    prev_has_cont = cat.get_anno(d-1, p).has_contour(cont_name)
    next_has_cont = cat.get_anno(d+1, p).has_contour(cont_name)
    if prev_has_cont and next_has_cont: return 'midv'
    if prev_has_cont and not next_has_cont: return 'apical'
    if not prev_has_cont and next_has_cont: return 'basal'

    
def metrics_phase_slice_table(cases1, cases2, fixed_phase_first_reader=False):
    dsc, hd, mld = DiceMetric(), HausdorffMetric(), mlDiffMetric()
    metrics = [dsc.get_val, hd.get_val, mld.get_val, lambda g1,g2,_: not g1.is_empty, lambda g1,g2,_: not g2.is_empty]
    view = SAX_CINE_View()
    row_dict = {}
    row_counter = 0
    for c1,c2 in zip(cases1, cases2):
        cc = Case_Comparison(c1,c2)
        nr_slices = c1.categories[0].nr_slices
        for sl_nr in range(nr_slices):
            row = [c1.case_name, c1.reader_name, c2.reader_name,  sl_nr]
            for cont in contour_names:
                cat_es1, cat_ed1 = view.get_categories(c1, cont)
                cat_es2, cat_ed2 = view.get_categories(c2, cont)
                p_es1, p_ed1 = cat_es1.phase, cat_ed1.phase 
                p_es2, p_ed2 = (p_es1, p_ed1) if fixed_phase_first_reader else (cat_es2.phase, cat_ed2.phase)
                for cat1, cat2 in zip([cat_es1, cat_ed1],[cat_es2, cat_ed2]):
                    p1, p2 = cat1.phase, cat1.phase if fixed_phase_first_reader else cat2.phase
                    dcm = cat1.get_dcm(sl_nr, p1)
                    cont1, cont2 = cat1.get_anno(sl_nr, p1).get_contour(cont), cat2.get_anno(sl_nr, p2).get_contour(cont)
                    for m in metrics: 
                        if p1 is None or p2 is None: row.append('')
                        else: row.append(m(cont1, cont2, dcm))
                    row.extend([get_position(c1, sl_nr, p1, cont), get_position(c2, sl_nr, p2, cont)])
            row_dict['row_'+str(row_counter).zfill(5)] = row
            row_counter +=1 
    df = pandas.DataFrame.from_dict(row_dict, orient='index', columns=column_names)
    return df
unet_table   = metrics_phase_slice_table(cases1, cases2, fixed_phase_first_reader=True)
fcn_table    = metrics_phase_slice_table(cases1, cases3, fixed_phase_first_reader=True)
mrunet_table = metrics_phase_slice_table(cases1, cases4, fixed_phase_first_reader=True)


def contour_subset(table, cont_name):
    names = column_names[:4] + [c for c in column_names if cont_name in c]
    ret_table = table.copy()
    ret_table = ret_table[names]
    # sort by phase
    es_names = column_names[:4] + [c for c in column_names if cont_name in c and 'ES' in c]
    ed_names = column_names[:4] + [c for c in column_names if cont_name in c and 'ED' in c]

    es_table = ret_table[es_names]
    #es_table = pd.concat([es_table, pd.DataFrame([['es', cont_name] for _ in range(len(es_table))], columns=['phase', 'cont_type'])], axis=1)
    es_table['phase'] = 'es'
    es_table['cont_type'] = cont_name
    
    ed_table = ret_table[ed_names]
    #ed_table = pd.concat([ed_table, pd.DataFrame([['ed', cont_name] for _ in range(len(ed_table))], columns=['phase', 'cont_type'])], axis=1)
    ed_table['phase'] = 'ed'
    ed_table['cont_type'] = cont_name
    
    es_table.columns = [n.replace('ES ', '') for n in es_table.columns]
    ed_table.columns = [n.replace('ED ', '') for n in ed_table.columns]
    combined = es_table.append(ed_table)
    return combined

def add_absolute_mldiff(table):
    names = [c for c in table.columns if 'ml diff' in c]
    new_names  = [n.replace('ml diff', 'abs ml diff') for n in names]
    ret_table  = table.copy()
    absmldiffs = np.abs(ret_table[names].values)
    ret_table[new_names] = absmldiffs
    return ret_table


unet_lv_endo_table = add_absolute_mldiff(contour_subset(unet_table, 'lv_endo'))
unet_lv_myo_table  = add_absolute_mldiff(contour_subset(unet_table, 'lv_myo' ))
unet_rv_endo_table = add_absolute_mldiff(contour_subset(unet_table, 'rv_endo'))

fcn_lv_endo_table = add_absolute_mldiff(contour_subset(fcn_table, 'lv_endo'))
fcn_lv_myo_table  = add_absolute_mldiff(contour_subset(fcn_table, 'lv_myo' ))
fcn_rv_endo_table = add_absolute_mldiff(contour_subset(fcn_table, 'rv_endo'))

mrunet_lv_endo_table = add_absolute_mldiff(contour_subset(mrunet_table, 'lv_endo'))
mrunet_lv_myo_table  = add_absolute_mldiff(contour_subset(mrunet_table, 'lv_myo' ))
mrunet_rv_endo_table = add_absolute_mldiff(contour_subset(mrunet_table, 'rv_endo'))


fig, axes = plt.subplots(3,3,figsize=(10,10))
for i in range(3): 
    for j in range(3): 
        axes[i][j].set_title(['UNet', 'FCN', 'MRUNet'][i] +' '+ ['lv_endo', 'lv_myo', 'rv_endo'][j] + ' Ml Diff vs Dice')
sns.scatterplot(ax=axes[0,0], data=unet_lv_endo_table, x='lv_endo ml diff', y='lv_endo dice', 
                size='lv_endo abs ml diff', hue='lv_endo position1', picker=4)
sns.scatterplot(ax=axes[0,1], data=unet_lv_myo_table, x='lv_myo ml diff', y='lv_myo dice', 
                size='lv_myo abs ml diff', hue='lv_myo position1', picker=4)
sns.scatterplot(ax=axes[0,2], data=unet_rv_endo_table, x='rv_endo ml diff', y='rv_endo dice', 
                size='rv_endo abs ml diff', hue='rv_endo position1', picker=4)

sns.scatterplot(ax=axes[1,0], data=fcn_lv_endo_table, x='lv_endo ml diff', y='lv_endo dice', 
                size='lv_endo abs ml diff', hue='lv_endo position1', picker=4)
sns.scatterplot(ax=axes[1,1], data=fcn_lv_myo_table, x='lv_myo ml diff', y='lv_myo dice', 
                size='lv_myo abs ml diff', hue='lv_myo position1', picker=4)
sns.scatterplot(ax=axes[1,2], data=fcn_rv_endo_table, x='rv_endo ml diff', y='rv_endo dice', 
                size='rv_endo abs ml diff', hue='rv_endo position1', picker=4)

sns.scatterplot(ax=axes[2,0], data=mrunet_lv_endo_table, x='lv_endo ml diff', y='lv_endo dice', 
                size='lv_endo abs ml diff', hue='lv_endo position1', picker=4)
sns.scatterplot(ax=axes[2,1], data=mrunet_lv_myo_table, x='lv_myo ml diff', y='lv_myo dice', 
                size='lv_myo abs ml diff', hue='lv_myo position1', picker=4)
sns.scatterplot(ax=axes[2,2], data=mrunet_rv_endo_table, x='rv_endo ml diff', y='rv_endo dice', 
                size='rv_endo abs ml diff', hue='rv_endo position1', picker=4)


def onpick(event):
    ind = event.ind
    print('onpick: ', ind)
    table = unet_lv_endo_table
    c1s, c2s = cases1, cases2
    
    case_name  = table.iloc[ind]['case name'].values[0]
    phase      = table.iloc[ind]['phase'].values[0]
    reader1    = table.iloc[ind]['reader1'].values[0]
    reader2    = table.iloc[ind]['reader2'].values[0]
    slice_nr   = table.iloc[ind]['slice'].values[0]
    cont_type  = table.iloc[ind]['cont_type'].values[0]
    
    c1, c2 = [c for c in c1s if c.case_name==case_name][0], [c for c in c2s if c.case_name==case_name][0]
    cat1, cat2 = [cat for cat in c1.categories if phase in cat.name.lower()][0], [cat for cat in c2.categories if phase in cat.name.lower()][0]
    img   = cat1.get_img(slice_nr, cat1.phase)
    cont1 = cat1.get_anno(slice_nr, cat1.phase).get_contour(cont_type)
    cont2 = cat2.get_anno(slice_nr, cat1.phase).get_contour(cont_type)
    
    fig, ax = plt.subplots(1,1)
    fig.suptitle(case_name + ', Phase: ' + str(phase) + ', Slice: ' + str(slice_nr))
    ax.imshow(img, cmap='gray'); ax.axis('off')
    if not cont1.is_empty and not cont2.is_empty: CATCH_utils.plot_geo_face_comparison(ax, cont1, cont2)
    pst = Polygon([[0,0],[1,1],[1,0]])
    patches = [PolygonPatch(pst,facecolor='red', edgecolor='red',  alpha=0.4),
               PolygonPatch(pst,facecolor='green',edgecolor='green', alpha=0.4),
               PolygonPatch(pst,facecolor='blue',  edgecolor='blue',   alpha=0.4)]
    handles = [reader1,reader1+' & '+reader2,reader2]
    ax.legend(patches, handles)
    fig.tight_layout()
    plt.show()
    
    
fig.canvas.mpl_connect('pick_event', onpick)
fig.tight_layout()
plt.show()


