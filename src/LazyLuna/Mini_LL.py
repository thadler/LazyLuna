import os
from pathlib import Path
from time import time
from operator import itemgetter
import pickle
import pandas
from uuid import uuid4
import pydicom
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, GeometryCollection, Point, MultiPoint
from LazyLuna import CATCH_utils
from shapely.affinity import translate, scale

###########
# Loaders #
###########

def read_annos_into_sop2filepaths(path, debug=False):
    if debug: st = time()
    paths = [f for f in os.listdir(path) if 'case' not in f]
    anno_sop2filepath = dict()
    for p in paths:
        anno_sop2filepath[p.replace('.pickle','')] = os.path.join(path, p)
    if debug: print('Reading annos took: ', time()-st)
    return anno_sop2filepath

def read_dcm_images_into_sop2filepaths(path, debug=False):
    if debug: st = time()
    sop2filepath = dict()
    for n in ['SAX CINE', 'SAX CS', 'SAX T1', 'SAX T2', 'LAX 2CV', 'LAX 3CV', 'LAX 4CV', 'SAX LGE', 'None']:
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
    """
    bp_imgs is a folder structured like:
    bp_imgs
    |--> imgs folder 1 --> dicoms within
    |--> imgs folder 2 --> ...
    |--> ...
    bp_annos is a folder like:
    bp_annos
    |--> pickles folder 1 --> pickles within
    |--> pickles folder 2 ...
    """
    imgpaths_annopaths_tuples = []
    img_folders = os.listdir(bp_imgs)
    for i, img_f in enumerate(img_folders):
        case_path = os.path.join(bp_imgs, img_f)
        for p in Path(case_path).glob('**/*.dcm'):
            dcm = pydicom.dcmread(str(p), stop_before_pixels=True)
            if not hasattr(dcm, 'StudyInstanceUID'): continue
            imgpaths_annopaths_tuples += [(case_path, os.path.join(bp_annos, dcm.StudyInstanceUID))]
            break
    return imgpaths_annopaths_tuples

##############
# Annotation #
##############

class Annotation:
    def __init__(self, sop, filepath):
        self.sop = sop
        try:    self.anno = pickle.load(open(filepath, 'rb'))
        except: self.anno = dict()
        self.set_information()

    def plot_all_contour_outlines(self, ax):
        for c in self.available_contour_names():
            CATCH_utils.plot_outlines(ax, self.get_contour(c))

    def plot_all_points(self, ax):
        for p in self.available_point_names():
            self.plot_point(ax, p)

    def plot_contour_face(self, ax, cont_name, c='r', alpha=0.4):
        if not self.has_contour(cont_name): return
        CATCH_utils.plot_geo_face(ax, self.get_contour(cont_name), c=c, ec=c, alpha=alpha)

    def plot_point(self, ax, point_name):
        if not self.has_point(point_name): return
        CATCH_utils.plot_points(ax, self.get_point(point_name))

    def plot_cont_comparison(self, ax, other_anno, cont_name, alpha=0.4):
        cont1, cont2 = self.get_contour(cont_name), other_anno.get_contour(cont_name)
        CATCH_utils.plot_geo_face_comparison(ax, cont1, cont2, alpha=alpha)

    def available_contour_names(self):
        return [c for c in self.contour_names if self.has_contour(c)]

    def has_contour(self, cont_name):
        return cont_name in self.anno.keys()

    def get_contour(self, cont_name):
        if self.has_contour(cont_name): return self.anno[cont_name]['cont']
        else:                           return Polygon()

    def available_point_names(self):
        return [p for p in self.point_names if self.has_point(p)]

    def has_point(self, point_name):
        return point_name in self.anno.keys()

    def get_point(self, point_name):
        if self.has_point(point_name): return self.anno[point_name]['cont']
        else:                          return Point()

    def get_cont_as_mask(self, cont_name, h, w):
        if not self.has_contour(cont_name): return np.zeros((h,w))
        mp = MultiPolygon([self.get_contour(cont_name)])
        # TODO belongs in the contours
        mp = translate(mp, xoff=0.5, yoff=0.5)
        return CATCH_utils.to_mask(mp, h, w)

    def get_pixel_size(self):
        return (self.pixel_h, self.pixel_w)


class SAX_CINE_Annotation(Annotation):
    def __init__(self, sop, filepath):
        super().__init__(sop, filepath)

    def set_information(self):
        self.name = 'SAX CINE Annotation'
        self.contour_names = ['lv_endo', 'lv_epi', 'lv_myo', 'lv_pamu',
                              'rv_endo', 'rv_epi', 'rv_myo', 'rv_pamu']
        self.point_names   = ['sacardialRefPoint']
        self.pixel_h, self.pixel_w = self.anno['info']['pixelSize'] if 'info' in self.anno.keys() and 'pixelSize' in self.anno['info'].keys() else (-1,-1)#1.98,1.98
        self.h,       self.w       = self.anno['info']['imageSize'] if 'info' in self.anno.keys() and 'imageSize' in self.anno['info'].keys() else (-1,-1)


class LAX_CINE_Annotation(Annotation):
    def __init__(self, sop, filepath):
        super().__init__(sop, filepath)

    def set_information(self):
        self.name = 'LAX CINE Annotation'
        self.contour_names = ['lv_lax_endo', 'lv_lax_myo', 'rv_lax_endo', 'ra', 'la']
        self.point_names   = ['lv_lax_extent', 'laxRaExtentPoints', 'laxLaExtentPoints']
        self.pixel_h, self.pixel_w = self.anno['info']['pixelSize'] if 'info' in self.anno.keys() and 'pixelSize' in self.anno['info'].keys() else (-1,-1)#1.98,1.98
        self.h,       self.w       = self.anno['info']['imageSize'] if 'info' in self.anno.keys() and 'imageSize' in self.anno['info'].keys() else (-1,-1)
        
    def length_LV(self):
        if not self.has_point('lv_lax_extent'): return 0
        extent = self.get_point('lv_lax_extent')
        lv_ext1, lv_ext2, apex = scale(extent, xfact=self.pixel_w, yfact=self.pixel_h)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
    
    def length_LA(self):
        if not self.has_point('laxLaExtentPoints'): return 0
        extent = self.get_point('laxLaExtentPoints')
        lv_ext1, lv_ext2, apex = scale(extent, xfact=self.pixel_w, yfact=self.pixel_h)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
    
    def length_RA(self):
        if not self.has_point('laxRaExtentPoints'): return 0
        extent = self.get_point('laxRaExtentPoints')
        lv_ext1, lv_ext2, apex = scale(extent, xfact=self.pixel_w, yfact=self.pixel_h)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
        

############
# Category #
############

class SAX_slice_phase_Category:
    def __init__(self, case):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'none'
        self.phase = None

    def get_sop2depthandtime(self, sop2filepath, debug=False):
        if debug: st = time()
        if hasattr(self.case, 'categories'):
            for c in self.case.categories:
                if hasattr(c, 'sop2depthandtime'):
                    if debug: print('calculating sop2sorting takes: ', time()-st)
                    return c.sop2depthandtime
        # returns dict sop --> (depth, time)
        imgs = {k:pydicom.dcmread(sop2filepath[k]) for k in sop2filepath.keys()}
        sortable_slice_location_and_instance_number = [[float(v.SliceLocation), float(v.InstanceNumber)] for sopinstanceuid, v in imgs.items()]
        sl_len = len(set([elem[0] for elem in sortable_slice_location_and_instance_number]))
        in_len = len(set([elem[1] for elem in sortable_slice_location_and_instance_number]))
        sorted_slice_location_and_instance_number = sorted(sortable_slice_location_and_instance_number, key=itemgetter(0,1))
        sorted_slice_location_and_instance_number = np.array([sorted_slice_location_and_instance_number[i*in_len:(i+1)*in_len] for i in range(sl_len)])
        sop2depthandtime = dict()
        st_sort = time()
        for sopinstanceuid in imgs.keys():
            s_loc, i_nr = imgs[sopinstanceuid].SliceLocation, imgs[sopinstanceuid].InstanceNumber
            for i in range(len(sorted_slice_location_and_instance_number)):
                for j in range(len(sorted_slice_location_and_instance_number[i])):
                    curr_s_loc, curr_i_nr = sorted_slice_location_and_instance_number[i, j]
                    if not (s_loc==curr_s_loc and i_nr==curr_i_nr): continue
                    sop2depthandtime[sopinstanceuid] = (i,j)
        # potentially flip slice direction: base top x0<x1, y0>y1, z0>z1, apex top x0>x1, y0<y1, z0<z1
        depthandtime2sop = {v:k for k,v in sop2depthandtime.items()}
        img1, img2 = imgs[depthandtime2sop[(0,0)]], imgs[depthandtime2sop[(1,0)]]
        img1x,img1y,img1z = list(map(float,img1.ImagePositionPatient))
        img2x,img2y,img2z = list(map(float,img2.ImagePositionPatient))
        if img1x<img2x and img1y>img2y and img1z>img2z: pass
        else: #img1x>img2x and img1y<img2y and img1z<img2z:
            max_depth = sl_len-1
            for sop in sop2depthandtime.keys():
                sop2depthandtime[sop] = (max_depth-sop2depthandtime[sop][0], sop2depthandtime[sop][1])
        if debug: print('calculating sop2sorting takes: ', time()-st)
        return sop2depthandtime

    def set_image_height_width_depth(self, debug=False):
        if debug: st = time()
        nr_slices = self.nr_slices
        for slice_nr in range(nr_slices):
            sop = self.depthandtime2sop[(slice_nr, 0)]
            dcm = self.case.load_dcm(sop)
            self.height, self.width    = dcm.pixel_array.shape
            self.pixel_h, self.pixel_w = list(map(float, dcm.PixelSpacing))
            try: self.spacing_between_slices = dcm.SpacingBetweenSlices
            except Exception as e:
                self.spacing_between_slices = dcm.SliceThickness
                print('Exception in SAX_Slice_Phase_Category, ', e)
            try: self.slice_thickness = dcm.SliceThickness
            except Exception as e: print('Exception in SAX_Slice_Phase_Category, ', e)
        if debug: print('Setting stuff took: ', time()-st)

    def set_nr_slices_phases(self):
        dat = list(self.depthandtime2sop.keys())
        self.nr_phases = max(dat, key=itemgetter(1))[1]+1
        self.nr_slices = max(dat, key=itemgetter(0))[0]+1
        
    def get_dcm(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_dcm(sop)

    def get_anno(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_anno(sop)

    def get_img(self, slice_nr, phase_nr, value_normalize=True, window_normalize=True):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)

    def get_imgs_phase(self, phase_nr, value_normalize=True, window_normalize=True):
        return [self.get_img(d, phase_nr, value_normalize, window_normalize) for d in range(self.nr_slices)]

    def get_annos_phase(self, phase):
        return [self.get_anno(d,phase) for d in range(self.nr_slices)]

    def get_volume(self, cont_name, phase):
        if np.isnan(phase): return 0.0
        annos = self.get_annos_phase(phase)
        pixel_area = self.pixel_h * self.pixel_w
        areas = [a.get_contour(cont_name).area*pixel_area if a is not None else 0.0 for a in annos]
        has_conts = [a!=0 for a in areas]
        if True not in has_conts: return 0
        base_idx, apex_idx  = has_conts.index(True), has_conts[::-1].index(True)
        vol = 0
        for d in range(self.nr_slices):
            pixel_depth = (self.spacing_between_slices + self.slice_thickness)/2.0 if d in [base_idx, apex_idx] else self.spacing_between_slices
            vol += areas[d] * pixel_depth
        return vol / 1000.0

    def get_volume_curve(self, cont_name):
        return [self.get_volume(cont_name, p) for p in range(self.nr_phases)]


class SAX_RV_ES_Category(SAX_slice_phase_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'SAX RVES'
        self.phase = self.get_phase()

    def get_phase(self):
        rvendo_vol_curve = self.get_volume_curve('rv_endo')
        rvpamu_vol_curve = self.get_volume_curve('rv_pamu')
        vol_curve = np.array(rvendo_vol_curve) - np.array(rvpamu_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class SAX_RV_ED_Category(SAX_slice_phase_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'SAX RVED'
        self.phase = self.get_phase()

    def get_phase(self):
        rvendo_vol_curve = self.get_volume_curve('rv_endo')
        rvpamu_vol_curve = self.get_volume_curve('rv_pamu')
        vol_curve = np.array(rvendo_vol_curve) - np.array(rvpamu_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        return np.argmax(vol_curve)

class SAX_LV_ES_Category(SAX_slice_phase_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'SAX LVES'
        self.phase = self.get_phase()

    def get_phase(self):
        lvendo_vol_curve = self.get_volume_curve('lv_endo')
        lvpamu_vol_curve = self.get_volume_curve('lv_pamu')
        vol_curve = np.array(lvendo_vol_curve) - np.array(lvpamu_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class SAX_LV_ED_Category(SAX_slice_phase_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'SAX LVED'
        self.phase = self.get_phase()

    def get_phase(self):
        lvendo_vol_curve = self.get_volume_curve('lv_endo')
        lvpamu_vol_curve = self.get_volume_curve('lv_pamu')
        vol_curve = np.array(lvendo_vol_curve) - np.array(lvpamu_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)

    
##################
# LAX Categories #
##################
class LAX_Category:
    def __init__(self, case):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'none'
        self.phase = None

    def relevant_image(self, dcm):
        return True
        
    def get_sop2depthandtime(self, sop2filepath, debug=False):
        if debug: st = time()
        imgs = {k:pydicom.dcmread(sop2filepath[k]) for k in sop2filepath.keys()}
        imgs = {k:dcm for k,dcm in imgs.items() if self.relevant_images(dcm)}
        sop2depthandtime = {}
        for dcm_sop, dcm in imgs.items():
            phase = int(dcm.InstanceNumber)-1
            sop2depthandtime[dcm_sop] = (0,phase)
        if debug: print('calculating sop2sorting takes: ', time()-st)
        return sop2depthandtime

    def set_image_height_width_depth(self, debug=False):
        if debug: st = time()
        sop = self.depthandtime2sop[(0, 0)]
        dcm = self.case.load_dcm(sop)
        self.height, self.width    = dcm.pixel_array.shape
        self.pixel_h, self.pixel_w = list(map(float, dcm.PixelSpacing))
        try: self.slice_thickness = dcm.SliceThickness
        except Exception as e: print('Exception in LAX_Slice_Phase_Category, ', e)
        if debug: print('Setting stuff took: ', time()-st)

    def set_nr_slices_phases(self):
        dat = list(self.depthandtime2sop.keys())
        self.nr_phases = max(dat, key=itemgetter(1))[1]+1
        self.nr_slices = max(dat, key=itemgetter(0))[0]+1
        
    def get_dcm(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_dcm(sop)

    def get_anno(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_anno(sop)

    def get_img(self, slice_nr, phase_nr, value_normalize=True, window_normalize=True):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)

    def get_area(self, cont_name, phase):
        if np.isnan(phase): return 0.0
        anno = self.get_anno(0, phase)
        pixel_area = self.pixel_h * self.pixel_w
        area = anno.get_contour(cont_name).area*pixel_area if anno is not None else 0.0
        return area

    def get_area_curve(self, cont_name):
        return [self.get_area(cont_name, p) for p in range(self.nr_phases)]


class LAX_4CV_LVES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV LVES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('lv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class LAX_4CV_LVED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV LVED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('lv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)
    
class LAX_4CV_LAES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV LAES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('la')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]
      
class LAX_4CV_LAED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV LAED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('la')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)

    
class LAX_4CV_RAES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV RAES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('ra')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]
      
class LAX_4CV_RAED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV RAED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('ra')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)


class LAX_2CV_LVES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 2CV LVES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 2CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('lv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class LAX_2CV_LVED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 2CV LVED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 2CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('lv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)

    
class LAX_2CV_LAES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 2CV LAES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 2CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('la')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class LAX_2CV_LAED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 2CV LAED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 2CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('la')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return None
        return np.argmax(vol_curve)




####################
# Clinical Results #
####################

class Clinical_Result:
    def __init(self, case):
        self.case = case
        self.name = ''
        self.unit = '[]'

    def get_cr(self, string=False):             pass
    def get_cr_diff(self, other, string=False): pass

class LVSAX_ESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_volume('lv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_volume('lv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr
    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_ESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_volume('rv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_EDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_volume('rv_endo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

# Phases
class LVSAX_ESPHASE(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVESP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]

    def get_cr(self, string=False):
        return str(self.cat.phase) if string else self.cat.phase

    def get_cr_diff(self, other, string=False):
        p1, p2, nrp = self.get_cr(), other.get_cr(), self.cat.nr_phases
        cr_diff = min(abs(p1-p2), (min(p1,p2) - max(p1,p2)) % nrp) # module ring difference
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EDPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVEDP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

class RVSAX_ESPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVESP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]

class RVSAX_EDPHASE(LVSAX_ESPHASE):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVEDP'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

class NR_SLICES(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'NrSlices'
        self.unit = '[#]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    def get_cr(self, string=False):
        return str(self.cat.nr_slices) if string else self.cat.nr_slices

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_MYO(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVM'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    def get_cr(self, string=False):
        cr = 1.05 * self.cat.get_volume('lv_myo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_MYO(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVM'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    def get_cr(self, string=False):
        cr = 1.05 * self.cat.get_volume('rv_myo', self.cat.phase)
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_SV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    def get_cr(self, string=False):
        esv = self.cat_es.get_volume('rv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('rv_endo', self.cat_ed.phase)
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class RVSAX_EF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'RVEF'
        self.unit = '[%]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_RV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_RV_ED_Category)][0]

    def get_cr(self, string=False):
        esv = self.cat_es.get_volume('rv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('rv_endo', self.cat_ed.phase) + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_SV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    def get_cr(self, string=False):
        esv = self.cat_es.get_volume('lv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('lv_endo', self.cat_ed.phase)
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LVSAX_EF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'LVEF'
        self.unit = '[%]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, SAX_LV_ES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, SAX_LV_ED_Category)][0]

    def get_cr(self, string=False):
        esv = self.cat_es.get_volume('lv_endo', self.cat_es.phase)
        edv = self.cat_ed.get_volume('lv_endo', self.cat_ed.phase) + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

###########
# LAX CRs #
###########
########################
# LV Values:           #
# 4CV / 2CV / Biplane: #
# - ESV, EDV           #
# - SV,  EF            #
########################

#######
# 4CV #
#######
class LAX_4CV_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LVEF'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000 + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

########
# 2 CV #
########
class LAX_2CV_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LVESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LVEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('lv_lax_endo', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LVSV'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        return "{:.2f}".format(edv - esv) if string else edv - esv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LVEF'
        self.unit = '[ml]'
        self.cat_es  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat_ed  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat_es.get_area('lv_lax_endo', self.cat_es.phase)
        anno = self.cat_es.get_anno(0, self.cat_es.phase)
        esv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000
        area = self.cat_ed.get_area('lv_lax_endo', self.cat_ed.phase)
        anno = self.cat_ed.get_anno(0, self.cat_ed.phase)
        edv  = 8/(3*np.pi) * (area**2)/anno.length_LV() / 1000 + 10**-9
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    

###########
# Biplane #
###########
class LAX_BIPLANE_LVESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE LVESV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cat1.get_area('lv_lax_endo', self.cat1.phase)
        area2 = self.cat2.get_area('lv_lax_endo', self.cat2.phase)
        anno1 = self.cat1.get_anno(0, self.cat1.phase)
        anno2 = self.cat2.get_anno(0, self.cat2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
class LAX_BIPLANE_LVEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE LVEDV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cat1.get_area('lv_lax_endo', self.cat1.phase)
        area2 = self.cat2.get_area('lv_lax_endo', self.cat2.phase)
        anno1 = self.cat1.get_anno(0, self.cat1.phase)
        anno2 = self.cat2.get_anno(0, self.cat2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANE_LVSV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE LVSV'
        self.unit = '[ml]'
        self.cates1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cates2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cated1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cated2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cates1.get_area('lv_lax_endo', self.cates1.phase)
        area2 = self.cates2.get_area('lv_lax_endo', self.cates2.phase)
        anno1 = self.cates1.get_anno(0, self.cates1.phase)
        anno2 = self.cates2.get_anno(0, self.cates2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        esv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        area1 = self.cated1.get_area('lv_lax_endo', self.cated1.phase)
        area2 = self.cated2.get_area('lv_lax_endo', self.cated2.phase)
        anno1 = self.cated1.get_anno(0, self.cated1.phase)
        anno2 = self.cated2.get_anno(0, self.cated2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        edv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        cr    = edv - esv
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANE_LVEF(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANE LVEF'
        self.unit = '[ml]'
        self.cates1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVES_Category)][0]
        self.cates2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVES_Category)][0]
        self.cated1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LVED_Category)][0]
        self.cated2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LVED_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cates1.get_area('lv_lax_endo', self.cates1.phase)
        area2 = self.cates2.get_area('lv_lax_endo', self.cates2.phase)
        anno1 = self.cates1.get_anno(0, self.cates1.phase)
        anno2 = self.cates2.get_anno(0, self.cates2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        esv   = 8/(3*np.pi) * (area1*area2)/L / 1000
        area1 = self.cated1.get_area('lv_lax_endo', self.cated1.phase)
        area2 = self.cated2.get_area('lv_lax_endo', self.cated2.phase)
        anno1 = self.cated1.get_anno(0, self.cated1.phase)
        anno2 = self.cated2.get_anno(0, self.cated2.phase)
        L     = min(anno1.length_LV(), anno2.length_LV())
        edv   = 8/(3*np.pi) * (area1*area2)/L / 1000 + 10**-9
        cr    = (edv - esv) / edv
        return "{:.2f}".format(100.0*(edv-esv)/edv) if string else 100.0*(edv-esv)/edv

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

################
# Right Atrium #
# - 4CV area   #
# - 4CV volume #
################

class LAX_4CV_RAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV RAESAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAES_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('ra', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV RAEDAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAED_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('ra', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV RAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAES_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('ra', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_RAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV RAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_RAED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('ra', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
    
############
# LA 4CV   #
# - Area   #
# - Volume #
############
class LAX_4CV_LAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LAESAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LAEDAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_4CV_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '4CV LAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    
############
# LA 2CV   #
# - Area   #
# - Volume #
############
class LAX_2CV_LAESAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LAESAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAEDAREA(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LAEDAREA'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]

    def get_cr(self, string=False):
        cr = self.cat.get_area('la', self.cat.phase) / 100
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LAESV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_2CV_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = '2CV LAEDV'
        self.unit = '[ml]'
        self.cat  = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]

    def get_cr(self, string=False):
        area = self.cat.get_area('la', self.cat.phase)
        anno = self.cat.get_anno(0, self.cat.phase)
        cr   = 8/(3*np.pi) * (area**2)/anno.length_LA() / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff
    

    
###############
# LA Biplanar #
# - Volume    #
###############
class LAX_BIPLANAR_LAESV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANAE LAESV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAES_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAES_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cat1.get_area('la', self.cat1.phase)
        L1    = self.cat1.get_anno(0, self.cat1.phase).length_LA()
        area2 = self.cat2.get_area('la', self.cat2.phase)
        L2    = self.cat2.get_anno(0, self.cat2.phase).length_LA()
        L     = min(L1, L2)
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff

class LAX_BIPLANAR_LAEDV(Clinical_Result):
    def __init__(self, case):
        self.case = case
        self.set_CR_information()

    def set_CR_information(self):
        self.name = 'BIPLANAR LAEDV'
        self.unit = '[ml]'
        self.cat1 = [c for c in self.case.categories if isinstance(c, LAX_2CV_LAED_Category)][0]
        self.cat2 = [c for c in self.case.categories if isinstance(c, LAX_4CV_LAED_Category)][0]

    def get_cr(self, string=False):
        area1 = self.cat1.get_area('la', self.cat1.phase)
        L1    = self.cat1.get_anno(0, self.cat1.phase).length_LA()
        area2 = self.cat2.get_area('la', self.cat2.phase)
        L2    = self.cat2.get_anno(0, self.cat2.phase).length_LA()
        L     = min(L1, L2)
        cr    = 8/(3*np.pi) * (area1*area2)/L / 1000
        return "{:.2f}".format(cr) if string else cr

    def get_cr_diff(self, other, string=False):
        cr_diff = self.get_cr()-other.get_cr()
        return "{:.2f}".format(cr_diff) if string else cr_diff




########
# Case #
########

class Case:
    def __init__(self, imgs_path, annos_path, case_name, reader_name, debug=False):
        if debug: st = time()
        self.imgs_path    = imgs_path
        self.annos_path   = annos_path
        self.case_name    = case_name
        self.reader_name  = reader_name
        self.type         = 'None'
        self.available_types = set()
        self.all_imgs_sop2filepath  = read_dcm_images_into_sop2filepaths(imgs_path, debug)
        self.studyinstanceuid       = self._get_studyinstanceuid()
        self.annos_sop2filepath     = read_annos_into_sop2filepaths(annos_path, debug)
        if debug: print('Initializing Case took: ', time()-st)

    def _get_studyinstanceuid(self):
        for n in self.all_imgs_sop2filepath.keys():
            for sop in self.all_imgs_sop2filepath[n].keys():
                return pydicom.dcmread(self.all_imgs_sop2filepath[n][sop], stop_before_pixels=False).StudyInstanceUID

    def attach_annotation_type(self, annotation_type):
        self.annotation_type = annotation_type

    def attach_categories(self, categories):
        self.categories = [] # iteratively adding categories is a speed-up
        for c in categories: self.categories.append(c(self))

    def attach_clinical_results(self, crs):
        self.crs = [cr(self) for cr in crs]

    # lazy loaders & getters
    def load_dcm(self, sop):
        return pydicom.dcmread(self.imgs_sop2filepath[sop], stop_before_pixels=False)

    def load_anno(self, sop):
        if sop not in self.annos_sop2filepath.keys(): return self.annotation_type(sop, None)
        return self.annotation_type(sop, self.annos_sop2filepath[sop])

    def get_img(self, sop, value_normalize=True, window_normalize=True):
        dcm = self.load_dcm(sop)
        img = dcm.pixel_array
        if value_normalize:
            if [0x0028, 0x1052] in dcm and [0x0028, 0x1053] in dcm:
                img = img * float(dcm[0x0028, 0x1053].value) + float(dcm[0x0028, 0x1052].value)
        if window_normalize:
            minn, maxx = 0, 255
            if [0x0028, 0x1050] in dcm and [0x0028, 0x1051] in dcm:
                c = float(dcm[0x0028, 0x1050].value) # window center
                w = float(dcm[0x0028, 0x1051].value) # window width
                search_if, search_elif   = img<=(c-0.5)-((w-1)/2), img>(c-0.5)+((w-1)/2)
                img = ((img-(c-0.5)) / (w-1)+0.5) * (maxx-minn) + minn
                img[search_if]   = minn
                img[search_elif] = maxx
        return img

    def store(self, storage_dir):
        if not os.path.isdir(storage_dir): print('Storage failed. Must specify a directory.'); return
        storage_path = os.path.join(storage_dir, self.reader_name+'_'+self.case_name+'_LL_case.pickle')
        f = open(storage_path, 'wb'); pickle.dump(self, f); f.close()
        return storage_path



###################
# Case Comparison #
###################

class Case_Comparison:
    def __init__(self, case1, case2):
        self.case1, self.case2 = case1, case2
        # assertions here? same case, same images,
        if self.case1.case_name!=self.case2.case_name:
            raise Exception('A Case Comparison must reference the same case: '+self.case1.case_name, self.case2.case_name)

    def get_categories_by_type(self, cat_type):
        cat1 = [cat for cat in self.case1.categories if isinstance(cat, cat_type)][0]
        cat2 = [cat for cat in self.case2.categories if isinstance(cat, cat_type)][0]
        return cat1, cat2

    def get_categories_by_example(self, cat_example):
        return self.get_categories_by_type(type(cat_example))

    def attach_analyzer(self, analyzer):
        self.analyzer = analyzer()

    def attach_metrics(self, metrics):
        self.metrics = [m(self) for m in metrics]



########
# View #
########

class View:
    def __init__(self):
        pass

class SAX_CINE_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        self.contour2categorytype = {None      : self.all,    'lv_endo' : self.lvcats,  'lv_epi'  : self.myocats,
                                     'lv_pamu' : self.lvcats, 'lv_myo'  : self.myocats, 'rv_endo' : self.rvcats,
                                     'rv_epi'  : self.rvcats, 'rv_pamu' : self.rvcats,  'rv_myo'  : self.rvcats}
        self.contour_names = ['lv_endo', 'lv_epi', 'lv_pamu', 'lv_myo',
                              'rv_endo', 'rv_epi', 'rv_pamu', 'rv_myo']
        
        # register tabs here:
        from LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab                        import CC_Metrics_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_Tab               import CCs_ClinicalResults_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_Qualitative_Correlationplot_Tab   import CCs_Qualitative_Correlationplot_Tab
        self.case_tabs  = {'Metrics and Figure': CC_Metrics_Tab}
        self.stats_tabs = {'Clinical Results'  : CCs_ClinicalResults_Tab, 
                           'Qualitative Metrics Correlation Plot' : CCs_Qualitative_Correlationplot_Tab}
        
    def load_categories(self):
        self.lvcats, self.rvcats  = [SAX_LV_ES_Category, SAX_LV_ED_Category], [SAX_RV_ES_Category, SAX_RV_ED_Category]
        self.myocats              = [SAX_LV_ED_Category]
        self.all = [SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CINE']
        # attach annotation type
        case.attach_annotation_type(SAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        case.other_categories['SAX CINE'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX CINE'
        case.available_types.add('SAX CINE')
        if debug: print('Customization in SAX CINE view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CINE']
        # attach annotation type
        case.attach_annotation_type(SAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        #print('Has Categories: ', hasattr(case, 'categories'), case.other_categories)
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
            case.other_categories['SAX CINE'] = case.categories
        else:
            if 'SAX CINE' in case.other_categories.keys(): case.categories = case.other_categories['SAX CINE']
            else: case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        #print('Has Categories: ', hasattr(case, 'categories'), case.categories[0].name, case.categories[0])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([LVSAX_ESV, LVSAX_EDV, RVSAX_ESV, RVSAX_EDV,
                                      LVSAX_SV, LVSAX_EF, RVSAX_SV, RVSAX_EF,
                                      LVSAX_MYO, RVSAX_MYO,
                                      LVSAX_ESPHASE, RVSAX_ESPHASE, LVSAX_EDPHASE, RVSAX_EDPHASE,
                                      NR_SLICES])
        # set new type
        case.type = 'SAX CINE'
        if debug: print('Customization in SAX CINE view took: ', time()-st)
        return case


class SAX_CS_View(SAX_CINE_View):
    def __init__(self):
        super().__init__()

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CS']
        # attach annotation type
        case.attach_annotation_type(SAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        case.other_categories['SAX CS'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'SAX CS'
        case.available_types.add('SAX CS')
        if debug: print('Customization in SAX CS view took: ', time()-st)
        return case
        
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = case.all_imgs_sop2filepath['SAX CS']
        # attach annotation type
        case.attach_annotation_type(SAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if 'SAX CS' in case.other_categories.keys(): case.categories = case.other_categories['SAX CS']
        else: case.attach_categories([SAX_LV_ES_Category, SAX_LV_ED_Category, SAX_RV_ES_Category, SAX_RV_ED_Category])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([LVSAX_ESV, LVSAX_EDV, RVSAX_ESV, RVSAX_EDV,
                                      LVSAX_SV, LVSAX_EF, RVSAX_SV, RVSAX_EF,
                                      LVSAX_MYO, RVSAX_MYO,
                                      LVSAX_ESPHASE, RVSAX_ESPHASE, LVSAX_EDPHASE, RVSAX_EDPHASE,
                                      NR_SLICES])
        # set new type
        case.type = 'SAX CS'
        if debug: print('Customization in SAX CS view took: ', time()-st)
        return case

    
class LAX_CINE_View(View):
    def __init__(self):
        self.colormap            = 'gray'
        self.available_colormaps = ['gray']
        self.load_categories()
        self.contour_names        = ['lv_lax_endo', 'lv_lax_epi', 'lv_lax_myo', 'rv_lax_endo', 'la', 'ra']
        self.contour2categorytype = {c:self.all for c in self.contour_names}
        
        # register tabs here:
        from LazyLuna.Guis.Addable_Tabs.CC_Metrics_Tab                        import CC_Metrics_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_ClinicalResults_Tab               import CCs_ClinicalResults_Tab
        from LazyLuna.Guis.Addable_Tabs.CCs_Qualitative_Correlationplot_Tab   import CCs_Qualitative_Correlationplot_Tab
        self.case_tabs  = {'Metrics and Figure': CC_Metrics_Tab}
        self.stats_tabs = {'Clinical Results'  : CCs_ClinicalResults_Tab}
        
    def load_categories(self):
        self.all = [LAX_4CV_LVES_Category]

    def get_categories(self, case, contour_name=None):
        types = [c for c in self.contour2categorytype[contour_name]]
        cats  = [c for c in case.categories if type(c) in types]
        return cats

    def initialize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX 2CV'], **case.all_imgs_sop2filepath['LAX 3CV'], **case.all_imgs_sop2filepath['LAX 4CV']}
        # attach annotation type
        case.attach_annotation_type(LAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        if not hasattr(case, 'other_categories'): case.other_categories = dict()
        case.attach_categories([LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                                LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                                LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
        case.other_categories['LAX CINE'] = case.categories
        case.categories = []
        if debug: print('Case categories are: ', case.categories)
        # set new type
        case.type = 'LAX CINE'
        case.available_types.add('LAX CINE')
        if debug: print('Customization in LAX CINE view took: ', time()-st)
        return case
    
    def customize_case(self, case, debug=False):
        if debug: st=time()
        # switch images
        case.imgs_sop2filepath = {**case.all_imgs_sop2filepath['LAX 2CV'], **case.all_imgs_sop2filepath['LAX 3CV'], **case.all_imgs_sop2filepath['LAX 4CV']}
        # attach annotation type
        case.attach_annotation_type(LAX_CINE_Annotation)
        # if categories have not been attached, attach the first and init other_categories
        # otherwise it has categories and a type, so store the old categories for later use
        #print('Has Categories: ', hasattr(case, 'categories'), case.other_categories)
        if not hasattr(case, 'categories'):
            case.other_categories = dict()
            case.attach_categories([LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                                    LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                    LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                    LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                                    LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
            case.other_categories['LAX CINE'] = case.categories
        else:
            if 'LAX CINE' in case.other_categories.keys(): case.categories = case.other_categories['LAX CINE']
            else: case.attach_categories([LAX_4CV_LVES_Category, LAX_4CV_LVED_Category,
                                          LAX_4CV_LAES_Category, LAX_4CV_LAED_Category,
                                          LAX_4CV_RAES_Category, LAX_4CV_RAED_Category,
                                          LAX_2CV_LVES_Category, LAX_2CV_LVED_Category,
                                          LAX_2CV_LAES_Category, LAX_2CV_LAED_Category])
        #print('Has Categories: ', hasattr(case, 'categories'), case.categories[0].name, case.categories[0])
        if debug: print('Case categories are: ', case.categories)
        # attach CRs
        case.attach_clinical_results([LAX_4CV_LVESV,      LAX_4CV_LVEDV,
                                      LAX_4CV_LVSV,       LAX_4CV_LVEF,
                                      LAX_2CV_LVESV,      LAX_2CV_LVEDV,
                                      LAX_2CV_LVSV,       LAX_2CV_LVEF,
                                      LAX_BIPLANE_LVESV,  LAX_BIPLANE_LVEDV,
                                      LAX_BIPLANE_LVSV,   LAX_BIPLANE_LVEF,
                                      LAX_4CV_RAESAREA,   LAX_4CV_RAEDAREA,
                                      LAX_4CV_RAESV,      LAX_4CV_RAEDV,
                                      LAX_4CV_LAESAREA,   LAX_4CV_LAEDAREA,
                                      LAX_4CV_LAESV,      LAX_4CV_LAEDV,
                                      LAX_2CV_LAESAREA,   LAX_2CV_LAEDAREA,
                                      LAX_2CV_LAESV,      LAX_2CV_LAEDV,
                                      LAX_BIPLANAR_LAESV, LAX_BIPLANAR_LAEDV])
        # set new type
        case.type = 'LAX CINE'
        if debug: print('Customization in LAX CINE view took: ', time()-st)
        return case




##########
# Metric #
##########

class Metric:
    def __init__(self):
        self.set_information()

    def set_information(self):
        self.name = ''
        self.unit = '[?]'

    def set_case_comparison(self, cc):
        self.cc = cc

    def get_all_sops(self):
        imgs_sop2filepath = self.cc.case2.imgs_sop2filepath
        annos_sop2filepath1, annos_sop2filepath2 = self.cc.case1.annos_sop2filepath, self.cc.case2.annos_sop2filepath
        annos_sops  = set(annos_sop2filepath1.keys()).union(set(annos_sop2filepath2.keys()))
        return annos_sops & set(imgs_sop2filepath.keys())

    def get_val(self, geo1, geo2, string=False):
        pass


class DiceMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'DSC'
        self.unit = '[%]'

    def get_val(self, geo1, geo2, dcm=None, string=False):
        try:
            m = CATCH_utils.dice(geo1, geo2)
            return "{:.2f}".format(m) if string else m
        except Exception as e:
            print(e)
            return '0.00' if string else 0.0

    def calculate_all_vals(self, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            for c in anno1.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                sopandcontname2metricval[(sop, c)] = CATCH_utils.dice(anno1.get_contour(c), anno2.get_contour(c))
        if debug: print('Calculating all DSC values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval

class HausdorffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'HD'
        self.unit = '[mm]'

    def get_val(self, geo1, geo2, dcm=None, string=False):
        m = CATCH_utils.hausdorff(geo1, geo2)
        return "{:.2f}".format(m) if string else m

    def calculate_all_vals(self, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            ph, pw = anno1.get_pixel_size()
            for c in anno1.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                hd = ph * CATCH_utils.hausdorff(anno1.get_contour(c), anno2.get_contour(c))
                sopandcontname2metricval[(sop, c)] = hd
        if debug: print('Calculating all HD values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval

class mlDiffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'millilitre'
        self.unit = '[ml]'

    def get_val(self, geo1, geo2, dcm=None, string=False):
        pw, ph = dcm.PixelSpacing; vd = dcm.SliceThickness
        m      = (pw*ph*vd/1000.0) * (geo1.area - geo2.area)
        return "{:.2f}".format(m) if string else m

    def calculate_all_vals(self, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            vd           = self.cc.case1.load_dcm(sop).SliceThickness
            ph, pw       = anno1.get_pixel_size()
            for c in anno1.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                ml_diff = (pw*ph*vd/1000.0) * (anno1.get_contour(c).area - anno2.get_contour(c).area)
                sopandcontname2metricval[(sop, c)] = ml_diff
        if debug: print('Calculating all mlDiff values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval



class SAX_CINE_analyzer:
    def __init__(self, case_comparison):
        self.cc   = case_comparison
        self.view = SAX_CINE_View()

    def get_cat_depth_time2sop(self, fixed_phase_first_reader=False):
        cat_depth_time2sop = dict()
        categories = [self.cc.get_categories_by_example(c) for c in self.cc.case1.categories]
        for c1,c2 in categories:
            if np.isnan(c1.phase) or np.isnan(c2.phase): continue
            p1, p2 = (c1.phase, c2.phase) if not fixed_phase_first_reader else (c1.phase, c1.phase)
            for d in range(c1.nr_slices):
                sop1, sop2 = c1.depthandtime2sop[d,p1], c2.depthandtime2sop[d,p2]
                cat_depth_time2sop[(type(c1), d, p1, p2)] = (sop1, sop2)
        return cat_depth_time2sop

    def get_metric_values_depth_time(self, metric, cont_name, fixed_phase_first_reader=False, debug=False):
        if debug: st = time()
        metrics_dict = dict()
        cat_depth_time2sop = self.get_cat_depth_time2sop(fixed_phase_first_reader)
        for cat_type, d, p1, p2 in cat_depth_time2sop.keys():
            sop1, sop2 = cat_depth_time2sop[(cat_type, d, p1, p2)]
            cont1 = self.cc.case1.load_anno(sop1).get_contour(cont_name)
            cont2 = self.cc.case2.load_anno(sop2).get_contour(cont_name)
            dcm   = self.cc.case1.load_dcm(sop1)
            metrics_dict[(cat_type, d, p1, p2)] = metric.get_val(cont1, cont2, dcm)
        if debug: print('Calculating metrics by depth time took: ', time()-st)
        return metrics_dict

    def _is_apic_midv_basal_outside(self, d, p, cont_name, first_reader=True):
        case = self.cc.case1 if first_reader else self.cc.case2
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

    def get_case_contour_comparison_pandas_dataframe(self, fixed_phase_first_reader=False, debug=False):
        # case, reader1, reader2, sop1, sop2, category, d, nr_slices, depth_perc, p1, p2, cont_name, dsc, hd, mldiff, apic/midv/bas/outside1, apic/midv/bas/outside2, has_cont1, has_cont2
        if debug: st = time()
        rows                  = []
        view                  = self.view
        case1, case2          = self.cc.case1, self.cc.case2
        case_name             = case1.case_name
        reader1, reader2      = case1.reader_name, case2.reader_name
        dsc_m, hd_m, mldiff_m = DiceMetric(), HausdorffMetric(), mlDiffMetric()
        for cont_name in self.view.contour_names:
            categories1, categories2 = view.get_categories(case1, cont_name), view.get_categories(case2, cont_name)
            for cat1, cat2 in zip(categories1, categories2):
                if np.isnan(cat1.phase) or np.isnan(cat2.phase): continue
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                nr_sl  = cat1.nr_slices
                for d in range(cat1.nr_slices):
                    d_perc       = 1.0 * d / nr_sl
                    sop1, sop2   = cat1.depthandtime2sop[d,p1], cat2.depthandtime2sop[d,p2]
                    anno1, anno2 = self.cc.case1.load_anno(sop1), self.cc.case2.load_anno(sop2)
                    cont1, cont2 = anno1.get_contour(cont_name), anno2.get_contour(cont_name)
                    dcm    = self.cc.case1.load_dcm(sop1)
                    dsc    = dsc_m   .get_val(cont1, cont2, dcm)
                    hd     = hd_m    .get_val(cont1, cont2, dcm)
                    mldiff = mldiff_m.get_val(cont1, cont2, dcm)
                    has_cont1, has_cont2     = anno1.has_contour(cont_name), anno2.has_contour(cont_name)
                    apic_midv_basal_outside1 = self._is_apic_midv_basal_outside(d, p1, cont_name, first_reader=True)
                    apic_midv_basal_outside2 = self._is_apic_midv_basal_outside(d, p2, cont_name, first_reader=False)
                    row = [case_name, reader1, reader2, sop1, sop2, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, dsc, hd, mldiff, np.abs(mldiff), apic_midv_basal_outside1, apic_midv_basal_outside2, has_cont1, has_cont2]
                    rows.append(row)
        columns=['case', 'reader1', 'reader2', 'sop1', 'sop2', 'category', 'slice', 'max_slices', 'depth_perc', 'phase1', 'phase2', 'contour name', 'DSC', 'HD', 'ml diff', 'abs ml diff', 'position1', 'position2', 'has_contour1', 'has_contour2']
        df = pandas.DataFrame(rows, columns=columns)
        if debug: print('pandas table took: ', time()-st)
        return df
