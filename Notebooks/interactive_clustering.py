import os
from pathlib import Path
import pickle
from time import time
import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import seaborn as sns

from catch_converter.parse_contours import parse_cvi42ws
from LazyLuna.Mini_LL import *
from LazyLuna.CATCH_utils import *
from LazyLuna.network_comparison_utils import *

bp       = '/media/omega/Daten1/CATCH/CS'
bp_annos = '/media/omega/Daten1/CATCH/CS/Preds/FCN'
bp_cases = '/media/omega/Daten1/CATCH/CS/Cases'
bp_imgs  = '/media/omega/Daten1/CATCH/CS/Imgs'


# load cases
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'Annos' in p]
cases1 = [pickle.load(open(p, 'rb')) for p in case_paths]
case_paths = [os.path.join(bp_cases,p) for p in os.listdir(bp_cases) if p.endswith('.pickle') and 'UNet' in p and 'MRUNet' not in p]
cases2 = [pickle.load(open(p, 'rb')) for p in case_paths]
cases1 = sorted(cases1, key=lambda c: c.case_name)
cases2 = sorted(cases2, key=lambda c: c.case_name)
names = set([c.case_name for c in cases2])
cases1 = [c for c in cases1 if c.case_name in names]

#cases1 = cases1[:3]
#cases2 = cases2[:3]

crs1 = [(cr.name, cr.get_cr()) for c in cases1 for cr in c.crs]
crs2 = [(cr.name, cr.get_cr()) for c in cases2 for cr in c.crs]
print(crs1)
print(crs2)

def contour_subset(table, cont_name):
    ret_table = table.copy()
    return ret_table[ret_table['contour name']==cont_name]

def several_contour_subset(table, cont_names):
    ret_table = table.copy()
    return ret_table[ret_table['contour name'].isin(cont_names)]

def dice_subset_segmentation_failures(table, low_value=0, high_value=80.0):
    ret_table = table.copy()
    ret_table = ret_table[ret_table['DSC']<high_value]
    ret_table = ret_table[low_value < ret_table['DSC']]
    return ret_table

def hd_subset_segmentation_failures(table, value=2.0):
    ret_table = table.copy()
    return ret_table[ret_table['HD']>value]

def absmldiff_subset_segmentation_failures(table, value=2.0):
    ret_table = table.copy()
    return ret_table[ret_table['abs ml diff']>value]

def add_normalized_values(table):
    ret_table = table.copy()
    names = ['DSC', 'HD', 'ml diff', 'abs ml diff']
    data = ret_table[names].values.astype(np.float64)
    print('In add normalized values:')
    print('Length of data: ', data.shape)
    data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
    ret_table[[n+' normalized' for n in names]] = pd.DataFrame(data).values
    return ret_table

def add_pca_whitened_values(table):
    ret_table = table.copy()
    #names = ['DSC', 'HD', 'ml diff', 'abs ml diff']
    names = ['DSC', 'HD', 'ml diff', 'depth_perc']
    data = ret_table[names].values.astype(np.float64)
    pca = PCA(whiten=True)
    whitened = pca.fit_transform(data)
    ret_table[['pca_whitened_'+str(n_i) for n_i in range(len(names))]] = pd.DataFrame(whitened).values
    return ret_table
    return ret_table

case_comps = [Case_Comparison(cases1[i], cases2[i]) for i in range(len(cases1))]
tables = [SAX_CINE_analyzer(cc).get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader=False) for cc in case_comps]
master_table = pd.concat([t for t in tables])
#print('len(master_table): ', len(master_table))
table = master_table.copy()


# Get myocardium subset
#table = contour_subset(table, 'lv_myo')
#table = several_contour_subset(table, ['rv_endo', 'lv_endo', 'lv_myo'])
table = several_contour_subset(table, ['lv_myo'])

# Get segmentation failures
#print('All myos: ', len(table))
table = dice_subset_segmentation_failures(table, low_value=0, high_value=90.0)
#print('Poor myos: ', len(table))

# Normalize this data
table = add_normalized_values(table)
table = add_pca_whitened_values(table)
print('New table columns: ', table.columns)


fig, axes = plt.subplots(1,1,figsize=(32,32))
axes.set_title('PCA c1 vs PCA c2')
sns.scatterplot(ax=axes, data=table, x='pca_whitened_1', y='pca_whitened_2', 
                size='abs ml diff', hue='position1', picker=4)

def onpick(event):
    ind = event.ind
    print('onpick: ', ind)
    case_name  = table.iloc[ind]['case'].values[0]
    phase      = table.iloc[ind]['category'].values[0]
    reader1    = table.iloc[ind]['reader1'].values[0]
    reader2    = table.iloc[ind]['reader2'].values[0]
    slice_nr   = table.iloc[ind]['slice'].values[0]
    cont_name  = table.iloc[ind]['contour name'].values[0]
    sop1, sop2 = table.iloc[ind]['sop1'].values[0], table.iloc[ind]['sop2'].values[0]
    
    cc     = [cc for cc in case_comps if cc.case1.case_name==case_name][0]
    c1, c2 = cc.case1, cc.case2
    img    = c1.load_dcm(sop1).pixel_array
    cont1, cont2 = c1.load_anno(sop1).get_contour(cont_name), c2.load_anno(sop2).get_contour(cont_name)
    
    fig, ax = plt.subplots(1,3, sharex=True, sharey=True)
    fig.suptitle(case_name + ', Phase: ' + str(phase) + ', Slice: ' + str(slice_nr))
    for i in range(3): ax[i].imshow(img, cmap='gray'); ax[i].axis('off')
    ax[0].set_title(reader1); ax[2].set_title(reader2)
    if not cont1.is_empty: CATCH_utils.plot_outlines(ax[0], cont1); 
    if not cont2.is_empty: CATCH_utils.plot_outlines(ax[2], cont2)
    if not cont1.is_empty and not cont2.is_empty: CATCH_utils.plot_geo_face_comparison(ax[1], cont1, cont2)
    fig.tight_layout()
    plt.show()
    
fig.canvas.mpl_connect('pick_event', onpick)
plt.show()