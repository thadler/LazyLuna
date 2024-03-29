import os
from pathlib import Path
import pickle
import pydicom
from time import time
import pandas
import numpy as np
import traceback

def get_study_uid(imgs_path):
    """Returns StudyInstanceUID for Dicom folder
    
    Note: 
        Assumes that there is only one study in folder.
    
    Returns:
        str: StudyInstanceUID
    """
    for ip, p in enumerate(Path(imgs_path).glob('**/*.dcm')):
        try:
            dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
            study_uid = dcm.StudyInstanceUID
            return study_uid
        except: continue

def annos_to_table(annos_path):
    """Returns DataFrame with information on annotations in folder
    
    Notes:
        columns: (studyinstanceuid, sopinstanceuid, nr of geometries in annotation, path to annotation)
    
    Args:
        annos_path (str): folder path to annotations, folder name is StudyInstanceUID
    
    Returns:
        pandas.DataFrame: table of information on annotations in folder path
    """
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
    """Returns DataFrame with on available dicom datasets in folder
    
    Note:
        Columns = (casename, studyinstanceuid, sopinstanceuid, series description, seriesuid, LL_tag, path to dicom dataset)
    
    Args:
        imgs_path (str): folder path to dicom datasets
    
    Returns:
        pandas.DataFrame: table of information on dicom datasets in folder path
    """
    columns    = ['case', 'study_uid', 'sop_uid', 'series_descr', 'series_uid', 'LL_tag', 'dcm_path']
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
    """Returns DataFrame with on dicom datasets in folder
    
    Note:
        Columns = (casename, studyinstanceuid, sopinstanceuid, series description, (seriesuid), LL_tag, path to dicom dataset)
    
    Args:
        images_df (pandas.DataFrame):     taken from function LazyLuna.loading_functions.dicom_images_to_table
        annotation_df (pandas.DataFrame): taken from function LazyLuna.loading_functions.annos_to_table
        by_series (bool):                 if True differentiates rows by series_uid, if False by seriesDescription
    
    Returns:
        pandas.DataFrame: table of information on dicom datasets and annotations pertaining to them
    """
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
    """Returns DataFrame with information on available dicom datasets in folder
    
    Note: 
        Columns = (seriesDescription, (series_uid), LL_tag, nr_imgs)
    
    Args:
        images_df (pandas.DataFrame): taken from function LazyLuna.loading_functions.dicom_images_to_table
        by_series (bool):             if True differentiates rows by series_uid, if False by seriesDescription
    
    Returns:
        pandas.DataFrame: table of information on dicom datasets
    """
    if by_series: nr_imgs  = images_df[['series_descr','series_uid','LL_tag']].value_counts()
    else:         nr_imgs  = images_df[['series_descr','LL_tag']].value_counts()
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
    """Returns paths for dcms and annotations by series_descritpion (and seriesuid)
    
    Args:
        imgs_df (pandas.DataFrame):  taken from function LazyLuna.loading_functions.dicom_images_to_table
        annos_df (pandas.DataFrame): taken from function LazyLuna.loading_functions.annos_to_table
        series_description (str):    seriesDescription
        by_series (str):             SeriesUID (subselection if not None)
    
    Returns:
        (list of str, list of str): list of paths to dicom datasets, list of paths to annotation files
    """
    if series_uid is not None:
        imgs = imgs_df .loc[imgs_df ['series_descr'].isin([series_description]) & imgs_df ['series_uid'].isin([series_uid])]
    else:
        imgs  = imgs_df .loc[imgs_df ['series_descr'].isin([series_description])]
    annos = pandas.merge(imgs, annos_df, on=['study_uid','sop_uid'], how='inner')
    annos.fillna('', inplace=True)
    return imgs['dcm_path'].unique().tolist(), annos['anno_path'].unique().tolist()


def get_img_paths_for_series_descr(imgs_df, series_description, series_uid=None):
    """Returns paths for dcms by series_descritpion (and seriesuid)
    
    Args:
        imgs_df (pandas.DataFrame):  taken from function LazyLuna.loading_functions.dicom_images_to_table
        series_description (str):    seriesDescription
        by_series (str):             SeriesUID (subselection if not None)
    
    Returns:
        list of str: list of paths to dicom datasets
    """
    if series_uid is not None:
        imgs = imgs_df .loc[imgs_df ['series_descr'].isin([series_description]) & imgs_df ['series_uid'].isin([series_uid])]
    else:
        imgs  = imgs_df .loc[imgs_df ['series_descr'].isin([series_description])]
    return imgs['dcm_path'].unique().tolist()


def add_LL_tag(store_path, dcm, tag='Lazy Luna: None'): # Lazy Luna: SAX CS
    """Adds a LazyLuna name tag to a dicom dataset and stores it
    
    Args:
        store_path (str):    dicom dataset path
        dcm (dicom dataset): dicom file to which the tag is added
        tag (str):           tag label text
    """
    try:    dcm[0x0b, 0x10].value = tag
    except: dcm.private_block(0x000b, tag, create=True)
    dcm.save_as(filename=store_path, write_like_original=False)

def get_LL_tag(dcm): # Lazy Luna: SAX CS
    """Returns LL tag if available, else 'None' (str)"""
    try:    return dcm[0x0b, 0x10].value
    except: return 'None'

def add_and_store_LL_tags(imgs_df, key2LLtag, overriding_dict=None):
    """Stores LL Tags for all images
    
    Args:
        imgs_df (pandas.DataFrame):           taken from function LazyLuna.loading_functions.dicom_images_to_table
        key2LLtag (dict of (str,(str)): str): mapping of (seriesDescription, (seriesUID)) to LL tag
        overriding_dict (dict of str: str):   mapping of SOPInstanceUID to LL tag
    """
    # key2LLtag: {(sd,ser_uid):'Lazy Luna: tag name'} or
    # key2LLtag: {(sd,):'Lazy Luna: tag name'}
    sdAndSeriesUID = isinstance(list(key2LLtag.keys())[0], tuple) and len(list(key2LLtag.keys())[0])>1
    for ip, p in enumerate(imgs_df['dcm_path'].values):
        dcm = pydicom.dcmread(p, stop_before_pixels=False)
        try:
            if overriding_dict is not None and dcm.SOPInstanceUID in overriding_dict.keys():
                add_LL_tag(p, dcm, tag=overriding_dict[dcm.SOPInstanceUID])
            else:
                k = (dcm.SeriesDescription,dcm.SeriesInstanceUID) if sdAndSeriesUID else (dcm.SeriesDescription,)
                if k in key2LLtag.keys(): add_LL_tag(p, dcm, tag=key2LLtag[k])
                else:                     add_LL_tag(p, dcm, tag='Lazy Luna: None')
        except:
            print('Failed at case: ', c, '/nDCM', dcm)
            continue

def get_cases_table(cases, paths, return_dataframe=True, debug=False):
    """Returns a table for Case presentation
    
    Note:
        Columns = [Casename, Readername, Age, Gender, Weight, Height, SAX CINE, SAX CS, LAX CINE, SAX T1 PRE, SAX T1 POST, SAX T2, SAX LGE', Path]
    
    Args:
        cases (list of Case):    List of Case objects
        paths (list of str):     List of Case filepaths
        return_dataframe (bool): if True make pandas.DataFrame, else returns list
        
    Returns:
        list | pandas.DataFrame: table to present Cases
    """
    def get_dcm(case):
        for k in case.all_imgs_sop2filepath.keys():
            try: sop = next(iter(case.all_imgs_sop2filepath[k]))
            except: continue
            return pydicom.dcmread(case.all_imgs_sop2filepath[k][sop])
    def get_age(case):
        try:
            age = get_dcm(case).data_element('PatientAge').value
            age = float(age[:-1]) if age!='' else np.nan
        except: age=np.nan
        return age
    def get_gender(case):
        try:
            gender = get_dcm(case).data_element('PatientSex').value
            gender = gender if gender in ['M','F'] else np.nan
        except: gender=np.nan
        return gender
    def get_weight(case):
        try:
            weight = get_dcm(case).data_element('PatientWeight').value
            weight = float(weight) if weight is not None else np.nan
        except: weight=np.nan
        return weight
    def get_height(case):
        try:
            h = get_dcm(case).data_element('PatientSize').value
            h = np.nan if h is None else float(h)/100 if float(h)>3 else float(h)
        except: h=np.nan
        return h
    if debug: st = time()
    columns = ['Case Name', 'Reader', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 
               'LAX CINE', 'SAX T1 PRE', 'SAX T1 POST', 'SAX T2', 'SAX LGE', 'Path']
    #print([c.available_types for c in cases])
    rows    = sorted([[c.case_name, c.reader_name, get_age(c), get_gender(c), get_weight(c), get_height(c), 
                       'SAX CINE' in c.available_types, 'SAX CS' in c.available_types, 'LAX CINE' in c.available_types, 
                       'SAX T1 PRE' in c.available_types, 'SAX T1 POST' in c.available_types, 'SAX T2' in c.available_types, 
                       'SAX LGE' in c.available_types, paths[i]] 
                      for i, c in enumerate(cases)],
                     key=lambda p: str(p[0]))
    if not return_dataframe: return rows
    df      = pandas.DataFrame(rows, columns=columns)
    if debug: print('Took: ', time()-st)
    return df



########################
# Loaders from Mini_LL #
########################

def read_annos_into_sop2filepaths(path, debug=False):
    """Returns dictionary mapping of SOPInstanceUIDs to filepaths
    
    Args:
        path (str): path to Annotation files
        
    Returns:
        (dict of str: str): Mapping of SOPInstanceUID to filepath
    """
    if debug: st = time()
    paths = [f for f in os.listdir(path) if 'case' not in f]
    anno_sop2filepath = dict()
    for p in paths:
        anno_sop2filepath[p.replace('.pickle','')] = os.path.join(path, p)
    if debug: print('Reading annos took: ', time()-st)
    return anno_sop2filepath

def read_dcm_images_into_sop2filepaths(path, debug=False):
    """Returns nested dictionary mapping of LL type to SOPInstanceUIDs to filepaths
    
    Args:
        path (str): path to dicom dataset files
        
    Returns:
        (dict of str: dict of str: str): Nested mapping of LL type to SOPInstanceUID to filepath
    """
    if debug: st = time()
    sop2filepath = dict()
    for n in ['SAX CINE', 'SAX CS', 'SAX T1 PRE', 'SAX T1 POST', 'SAX T2', 'LAX CINE 2CV', 'LAX CINE 3CV', 'LAX CINE 4CV', 'SAX LGE', 'None']:
        sop2filepath[n] = dict()
    for p in Path(path).glob('**/*.dcm'):
        try:
            dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
            name = str(dcm[0x0b, 0x10].value).replace('Lazy Luna: ', '') # LL Tag
            sop2filepath[name][dcm.SOPInstanceUID] = str(p)
        except Exception as e:
            if debug: print(dcm, '\nException: ', e)
    if debug: print('Reading images took: ', time()-st)
    return sop2filepath

# returns the base paths for Cases
def get_imgs_and_annotation_paths(bp_imgs, bp_annos):
    """Returns list of tuples, like (Case Dicom folder path, Annotation folder path)
    
    Note:
        Annotation folder path may not exist. The annotation folder is assumed to be named after the StudyInstanceUID
    
        bp_imgs is a folder structured like:
        bp_imgs
        |--> imgs folder 1 --> dicoms within
        |--> imgs folder 2 --> ...
        |--> ...
        bp_annos is a folder like:
        bp_annos
        |--> pickles folder 1 --> pickles within
        |--> pickles folder 2 ...
        
    Args:
        bp_imgs (str):  path to folder containing case folders of dicom datasets (see note)
        bp_annos (str): path to folder containing annotation folders (see note)
        
    Returns:
        list of (str, str): list of (Case Dicom folder path, Annotation folder path)
    """
    imgpaths_annopaths_tuples = []
    img_folders = os.listdir(bp_imgs)
    for i, img_f in enumerate(img_folders):
        case_path = os.path.join(bp_imgs, img_f)
        for p in Path(case_path).glob('**/*.dcm'):
            try: dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
            except Exception as e: print(traceback.format_exc()); continue
            if not hasattr(dcm, 'StudyInstanceUID'): continue
            imgpaths_annopaths_tuples += [(os.path.normpath(case_path), os.path.normpath(os.path.join(bp_annos, dcm.StudyInstanceUID)))]
            break
    return imgpaths_annopaths_tuples


def get_case_info(case, path):
    """Returns columns, rows
    
    Args:
        case (LazyLuna.Containers.Case): case for which information is sorted
        path (str): path to Case pickle file
        
    Returns:
        (list (str), list(str)): List of column names, list of case information pertaining to columns
    """
    def get_dcm(case):
        for k in case.all_imgs_sop2filepath.keys():
            try: 
                sop = next(iter(case.all_imgs_sop2filepath[k]))
                return pydicom.dcmread(case.all_imgs_sop2filepath[k][sop])
            except: continue
    def get_age(case):
        try:    age = get_dcm(case).PatientAge.repace('Y','')
        except: age = 'None'
        return  age
    def get_gender(case):
        try:    gender = get_dcm(case).PatientSex
        except: gender = 'None'
        return  gender
    def get_weight(case):
        try:    weight = str(get_dcm(case).PatientWeight)
        except: weight = 'None'
        return  weight
    def get_height(case):
        try:    h = str(get_dcm(case).PatientSize)
        except: h = 'None'
        return  h
    def get_creation_date(case):
        try:    cd = get_dcm(case).InstanceCreationDate
        except: cd = 'None'
        return  cd
    def get_studyuid(case):
        try:    uid = get_dcm(case).StudyInstanceUID
        except: uid = 'None'
        return  uid
    columns = ['Case Name', 'Reader', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 
               'Creation Date', 'StudyUID', 'Path']
    c       = case
    rows    = [c.case_name, c.reader_name, get_age(c), get_gender(c), get_weight(c), get_height(c), 
               get_creation_date(c), get_studyuid(c), path]
    return columns, rows