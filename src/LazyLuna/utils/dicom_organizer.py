import os
from pathlib import Path
import pydicom

from functools import reduce
from operator import getitem

import numpy as np

from LazyLuna.loading_functions import add_LL_tag


def get_values_from_nested_dict(d):
    for v in d.values():
        if isinstance(v, dict): yield from get_values_from_nested_dict(v)
        else:                   yield v

def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str): result.extend(flatten(el))
        else: result.append(el)
    return result


class Dicom_Organizer:
    def __init__(self, dcm_folder_path, reader_folder_path=None, by_series_description=True, by_series=False, load=True):
        self.dcm_folder_path    = dcm_folder_path
        self.by_seriesdescr     = by_series_description
        self.by_series          = by_series
        self.reader_folder_path = reader_folder_path
        self.anno_folder_path   = self.get_anno_folder_path()
        if load: self.load_images_and_annos()
            
    def get_anno_folder_path(self):
        if self.reader_folder_path is None: return None
        for p in Path(self.dcm_folder_path).glob('**/*.dcm'):
            try:
                dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
                study_uid = dcm.StudyInstanceUID
                break
            except: continue
        return os.path.join(self.reader_folder_path, study_uid)
            
    def load_images_and_annos(self):
        # GET ANNOS
        self.annos = dict()
        if self.anno_folder_path is not None:
            paths = [f for f in os.listdir(self.anno_folder_path) if 'case' not in f]
            for p in paths: 
                self.annos[p.replace('.pickle','')] = os.path.join(self.anno_folder_path, p)
        # GET DCMS
        self.dcms = dict()
        self.has_annotations = dict()
        for p in Path(self.dcm_folder_path).glob('**/*.dcm'):
            try:
                # LOAD DCM
                p = str(p)
                dcm   = pydicom.dcmread(p, stop_before_pixels=True)
                # GET RELEVANT KEYS
                try:    lltag = str(dcm[0x0b, 0x10].value).replace('Lazy Luna: ', '')
                except: lltag = 'None'
                seriessdescr = dcm.SeriesDescription
                series_uid   = dcm.SeriesInstanceUID
                # INITIATE KEYS IN DICT IN MISSING
                if lltag not in self.dcms.keys(): 
                    self.dcms[lltag] = dict()
                    self.has_annotations[lltag] = dict()
                if seriessdescr not in self.dcms[lltag].keys(): 
                    self.dcms[lltag][seriessdescr] = dict()
                    self.has_annotations[lltag][seriessdescr] = dict()
                if series_uid not in self.dcms[lltag][seriessdescr].keys(): 
                    self.dcms[lltag][seriessdescr][series_uid] = []
                    self.has_annotations[lltag][seriessdescr][series_uid] = False
                # ADD PATH TO DICT
                sop = dcm.SOPInstanceUID
                if sop in self.annos.keys():
                    self.has_annotations[lltag][seriessdescr][series_uid] = True
                self.dcms[lltag][seriessdescr][series_uid].append(p)
            except Exception as e: pass #print(dcm, '\nException: ', e)
        self.original_lltag2pathset = self.get_lltag_to_path_set()

    
    def get_section_keys(self, sort_by_has_anno=True):
        if not self.by_seriesdescr and not self.by_series: 
            keys = [(lltag,) for lltag in self.dcms.keys()]
            return sorted(keys, key=lambda k: self.section_has_annotations(k), reverse=True)
        if self.by_seriesdescr and not self.by_series:
            keys = []
            for lltag in self.dcms.keys():
                for seriesdescr in self.dcms[lltag].keys():
                    keys.append((lltag, seriesdescr))
            return sorted(keys, key=lambda k: self.section_has_annotations(k), reverse=True)
        keys = []
        for lltag in self.dcms.keys():
            for seriesdescr in self.dcms[lltag].keys():
                for seriesuid in self.dcms[lltag][seriesdescr].keys():
                    keys.append((lltag, seriesdescr, seriesuid))
        return sorted(keys, key=lambda k: self.section_has_annotations(k), reverse=True)
    
    def get_section(self, key): 
        return reduce(getitem, key, self.dcms)
        
    def get_paths_from_section(self, key):
        section = self.get_section(key)
        if isinstance(section, list): lists = section
        else: lists = [x for x in get_values_from_nested_dict(section)]
        return flatten(lists)
    
    def get_nr_of_paths_from_section(self, key):
        section = self.get_section(key)
        if isinstance(section, list): return len(section)
        lengths = [len(x) for x in get_values_from_nested_dict(section)]
        return sum(lengths)
    
    def get_first_path_from_section(self, key):
        section = self.get_section(key)
        if isinstance(section, list): return section[0]
        return next(get_values_from_nested_dict(section))[0]
    
    def get_first_path_all_sections(self):
        keys = self.get_section_keys()
        return [self.get_first_path_from_section(k) for k in keys]
    
    def get_firstpath_hasanno_nr(self, key):
        firstpath = self.get_first_path_from_section(key)
        has_anno  = self.section_has_annotations(key)
        nr = self.get_nr_of_paths_from_section(key)
        return firstpath, has_anno, nr
    
    def get_key_firstpath_hasanno_nr_all_sections(self):
        keys = self.get_section_keys()
        ret = []
        for k in keys:
            fpath, has_anno, nr = self.get_firstpath_hasanno_nr(k)
            ret.append((k, fpath, has_anno, nr))
        return ret
    
    def set_lltag_for_section(self, origin_key, lltag):
        if origin_key[0]==lltag: return # no change
        new_key = list(origin_key); new_key[0] = lltag; new_key = tuple(new_key)
        # make destination if not exists
        self.make_destination_from_origin_ifnotexists(new_key, origin_key)
        # INSERT into destination (append all lists on lowest level) 
        self.insert_section(new_key, origin_key)
        # Delete former section
        self.delete_section(origin_key)
    
    
    def insert_section(self, destination_key, origin_key):
        paths = self.get_paths_from_section(origin_key)
        lltag = destination_key[0]
        for i_p, p in enumerate(paths):
            dcm = pydicom.dcmread(p, stop_before_pixels=True)
            seriesdescr = dcm.SeriesDescription
            series_uid  = dcm.SeriesInstanceUID
            self.dcms[lltag][seriesdescr][series_uid].append(p)
            self.has_annotations[lltag][seriesdescr][series_uid] = True
        
        
    def make_destination_from_origin_ifnotexists(self, destination_key, origin_key):
        assert len(destination_key)==len(origin_key), print("Failed in Make Destination")
        dkey = destination_key
        okey = origin_key
        try:
            if dkey[0] not in self.dcms.keys():
                self.dcms[dkey[0]] = dict(); self.has_annotations[dkey[0]] = dict()
        except: pass
        try:
            if dkey[1] not in self.dcms[dkey[0]].keys():
                self.dcms[dkey[0]][dkey[1]] = dict(); self.has_annotations[dkey[0]][dkey[1]] = dict()
        except: pass
        try:
            if dkey[2] not in self.dcms[dkey[0]][dkey[1]].keys():
                self.dcms[dkey[0]][dkey[1]][dkey[2]]=[]
                self.has_annotations[dkey[0]][dkey[1]][dkey[2]] = False
        except: pass
        if len(origin_key)<3: # make the sub levels as well
            section = self.get_section(origin_key)
            for k in section.keys():
                ok = origin_key+(k,)
                dk = destination_key+(k,)
                self.make_destination_from_origin_ifnotexists(dk, ok)
    
    def delete_section(self, k):
        if len(k)==3: del self.dcms[k[0]][k[1]][k[2]]; del self.has_annotations[k[0]][k[1]][k[2]]
        if len(k)==2: del self.dcms[k[0]][k[1]];       del self.has_annotations[k[0]][k[1]]
        if len(k)==1: del self.dcms[k[0]];             del self.has_annotations[k[0]]
    
    def section_has_annotations(self, key):
        anno_section = reduce(getitem, key, self.has_annotations)
        if isinstance(anno_section, bool): return anno_section
        bools = [int(x) for x in get_values_from_nested_dict(anno_section)]
        return sum(bools)>0
    
    def get_lltag_to_path_set(self):
        lltag2paths = dict()
        for lltag in self.dcms.keys(): lltag2paths[lltag] = set()
        for key in self.get_section_keys():
            paths = self.get_paths_from_section(key)
            lltag2paths[key[0]] = lltag2paths[key[0]].union(set(paths))
        return lltag2paths
        
    def store_dicoms_with_tags(self):
        new_lltag2pathset = self.get_lltag_to_path_set()
        all_keys = set(new_lltag2pathset.keys()).union(self.original_lltag2pathset.keys())
        for k in all_keys:
            if k not in new_lltag2pathset:           new_lltag2pathset[k]           = set()
            if k not in self.original_lltag2pathset: self.original_lltag2pathset[k] = set()
        for lltag in all_keys:
            paths = new_lltag2pathset[lltag].difference(self.original_lltag2pathset[lltag])
            for p in paths:
                dcm = pydicom.dcmread(p, stop_before_pixels=False)
                add_LL_tag(p, dcm, lltag)
        
        
    
if __name__=="__main__":
    dcm_path  = '/Users/dietrichhadler/Desktop/Daten/Atria_Intra/Imgs/Atria_COV_34_'
    anno_path = '/Users/dietrichhadler/Desktop/Daten/Atria_Intra/HaOne'
    #org = Dicom_Organizer(dcm_path, anno_path, by_series_description=True, by_series=True)
    org = Dicom_Organizer(dcm_path, None, by_series_description=True, by_series=True)

    key = ('None', 'cine_tf2d12_retro_iPAT_Ao', '1.3.6.1.4.1.53684.1.1.3.1955809981.5808.1655727190.79028')
    #key = ('None', 'cine_tf2d12_retro_iPAT_Ao')
    org.set_lltag_for_section(key, 'BLABLABLA')


    #pprint([x[0] for x in org.get_section_keys()])
    #pprint(org.get_section_keys())
    print()
    for key in org.get_section_keys():
        print(org.section_has_annotations(key), key, len(org.get_paths_from_section(key)))

    fpaths = org.get_first_path_all_sections()
    print(fpaths)

