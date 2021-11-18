import os
from pathlib import Path
from operator import itemgetter
import pickle
import pydicom
from time import time
import pandas

def get_study_uid(imgs_path):
    for ip, p in enumerate(Path(imgs_path).glob('**/*.dcm')):
        try:
            dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
            study_uid = dcm.StudyInstanceUID
            return study_uid
        except: continue

def annos_to_table(annos_path):
    rows = []
    study_uid = os.path.basename(annos_path)
    columns = ['study_uid', 'sop_uid', 'annotated', 'anno_path']
    for i_f, f in enumerate(Path(annos_path).glob('**/*.pickle')):
        pickle_anno = pickle.load(open(str(f), 'rb'))
        sop_uid = os.path.basename(str(f)).replace('.pickle','')
        row = [study_uid, sop_uid, int(len(pickle_anno.keys())>0), str(f)]
        rows.append(row)
    df = pandas.DataFrame(rows, columns=columns)
    return df

def dicom_images_to_table(imgs_path):
    columns    = ['case', 'study_uid', 'sop_uid', 'series_descr', 
                  'series_uid', 'LL_tag', 'dcm_path']
    rows, case = [], os.path.basename(imgs_path)
    for ip, p in enumerate(Path(imgs_path).glob('**/*.dcm')):
        try:
            p = str(p)
            dcm = pydicom.dcmread(p, stop_before_pixels=False)
            try:    tag = dcm[0x0b, 0x10].value
            except: tag = 'None'
            row = [case, dcm.StudyInstanceUID, dcm.SOPInstanceUID, 
                   dcm.SeriesDescription, dcm.SeriesInstanceUID, tag, p]
            rows.append(row)
        except: continue
    df = pandas.DataFrame(rows, columns=columns)
    return df

def present_nrimages_nr_annos_table(images_df, annotation_df, by_series=False):
    combined = pandas.merge(images_df, annotation_df, on=['sop_uid', 'study_uid'], how='left')
    combined.fillna(0, inplace=True)
    if by_series:
        nr_imgs  = combined[['series_descr','series_uid','LL_tag']].value_counts()
        nr_annos = combined.groupby(['series_descr','series_uid','LL_tag']).sum()
    else:
        nr_imgs  = combined[['series_descr','LL_tag']].value_counts()
        nr_annos = combined.groupby(['series_descr','LL_tag']).sum()
    nr_imgs   = nr_imgs.to_dict()
    nr_annos  = nr_annos.to_dict()['annotated']
    imgs_keys, anno_keys = list(nr_imgs.keys()), list(nr_annos.keys())
    for k in imgs_keys: 
        if not isinstance(k, tuple): nr_imgs[(k,)] = nr_imgs.pop(k)
    for k in anno_keys: 
        if not isinstance(k, tuple): nr_annos[(k,)] = nr_annos.pop(k)
    if by_series: cols = ['series_descr', 'series_uid','LL_tag', 'nr_imgs', 'nr_annos']
    else:         cols = ['series_descr','LL_tag', 'nr_imgs', 'nr_annos']
    keys = set(nr_imgs.keys()).union(set(nr_annos.keys()))
    rows = [[*k, nr_imgs[k], int(nr_annos[k])] for k in keys]
    df = pandas.DataFrame(rows, columns=cols)
    df.sort_values(by='series_descr', key=lambda x: x.str.lower(), inplace=True, ignore_index=True)
    df['Change LL_tag'] = df['LL_tag']
    return df

def present_nrimages_table(images_df, by_series=False):
    if by_series:
        nr_imgs  = images_df[['series_descr','series_uid','LL_tag']].value_counts()
    else:
        nr_imgs  = images_df[['series_descr','LL_tag']].value_counts()
    nr_imgs   = nr_imgs.to_dict()
    imgs_keys = list(nr_imgs.keys())
    for k in imgs_keys: 
        if not isinstance(k, tuple): nr_imgs[(k,)] = nr_imgs.pop(k)
    if by_series: cols = ['series_descr', 'series_uid','LL_tag', 'nr_imgs']
    else:         cols = ['series_descr','LL_tag', 'nr_imgs']
    keys = set(nr_imgs.keys())
    rows = [[*k, nr_imgs[k]] for k in keys]
    df = pandas.DataFrame(rows, columns=cols)
    df.sort_values(by='series_descr', key=lambda x: x.str.lower(), inplace=True, ignore_index=True)
    df['Change LL_tag'] = df['LL_tag']
    return df


def get_paths_for_series_descr(imgs_df, annos_df, series_description, series_uid=None):
    if series_uid is not None:
        imgs = imgs_df .loc[imgs_df ['series_descr'].isin([series_description]) & imgs_df ['series_uid'].isin([series_uid])]
    else:
        imgs  = imgs_df .loc[imgs_df ['series_descr'].isin([series_description])]
    annos = pandas.merge(imgs, annos_df, on=['study_uid','sop_uid'], how='inner')
    annos.fillna('', inplace=True)
    return imgs['dcm_path'].unique().tolist(), annos['anno_path'].unique().tolist()

def get_img_paths_for_series_descr(imgs_df, series_description, series_uid=None):
    if series_uid is not None:
        imgs = imgs_df .loc[imgs_df ['series_descr'].isin([series_description]) & imgs_df ['series_uid'].isin([series_uid])]
    else:
        imgs  = imgs_df .loc[imgs_df ['series_descr'].isin([series_description])]
    return imgs['dcm_path'].unique().tolist()


def add_LL_tag(store_path, dcm, tag='Lazy Luna: None'): # Lazy Luna: SAX CS
    try:    dcm[0x0b, 0x10].value = tag
    except: dcm.private_block(0x000b, tag, create=True)
    dcm.save_as(filename=store_path, write_like_original=False)

def add_and_store_LL_tags(imgs_df, key2LLtag):
    # key2LLtag: {(sd,ser_uid):'Lazy Luna: tag name'} or
    # key2LLtag: {(sd,):'Lazy Luna: tag name'}
    sdAndSeriesUID = isinstance(list(key2LLtag.keys())[0], tuple) and len(list(key2LLtag.keys())[0])>1
    for ip, p in enumerate(imgs_df['dcm_path'].values):
        dcm = pydicom.dcmread(p, stop_before_pixels=False)
        #print(dcm.SeriesDescription)
        try:
            k = (dcm.SeriesDescription,dcm.SeriesInstanceUID) if sdAndSeriesUID else dcm.SeriesDescription
            if k not in key2LLtag.keys(): continue
            add_LL_tag(p, dcm, tag=key2LLtag[k])
        except:
            print('Failed at: Case', c, '/nDCM', dcm)
            continue

