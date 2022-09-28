import os
import traceback
from pathlib import Path
from time import time
import pickle
from uuid import uuid4
import pydicom
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, GeometryCollection, Point, MultiPoint
from LazyLuna import utils, loading_functions
from shapely.affinity import translate, scale
import pandas

##############
# Annotation #
##############

class Annotation:
    def __init__(self, filepath, sop=None):
        try:    self.anno = pickle.load(open(filepath, 'rb'))
        except: self.anno = dict()
        self.sop = sop

    def plot_all_contour_outlines(self, ax, c='w', debug=False):
        for cname in self.available_contour_names():
            utils.plot_outlines(ax, self.get_contour(cname), edge_c=c)
            
    def plot_contour_outlines(self, ax, cont_name, edge_c=(1,1,1,1.0), debug=False):
        if self.has_contour(cont_name):
            utils.plot_outlines(ax, self.get_contour(cont_name), edge_c)

    def plot_all_points(self, ax, c='w', marker='x', s=None):
        for p in self.available_point_names():
            self.plot_point(ax, p, c, marker, s)

    def plot_contour_face(self, ax, cont_name, c='r', alpha=0.4):
        if not self.has_contour(cont_name): return
        utils.plot_geo_face(ax, self.get_contour(cont_name), c=c, ec=c, alpha=alpha)

    def plot_point(self, ax, point_name, c='w', marker='x', s=None):
        if not self.has_point(point_name): return
        utils.plot_points(ax, self.get_point(point_name), c=c, marker=marker, s=s)

    def plot_cont_comparison(self, ax, other_anno, cont_name, colors=['g','r','b'], alpha=0.4):
        cont1, cont2 = self.get_contour(cont_name), other_anno.get_contour(cont_name)
        utils.plot_geo_face_comparison(ax, cont1, cont2, colors=colors, alpha=alpha)

    def available_contour_names(self):
        return [c for c in self.anno.keys() if self.has_contour(c)]

    def has_contour(self, cont_name):
        if not cont_name in self.anno.keys():              return False
        if not 'cont' in self.anno[cont_name]:             return False
        a = self.anno[cont_name]['cont']
        if a.is_empty:                                     return False
        if a.geom_type not in ['Polygon', 'MultiPolygon']: return False
        return True

    def get_contour(self, cont_name):
        if self.has_contour(cont_name): return self.anno[cont_name]['cont']
        else: return Polygon()

    def available_point_names(self):
        return [p for p in self.anno.keys() if self.has_point(p)]

    def has_point(self, point_name):
        if not point_name in self.anno.keys():         return False
        if not 'cont' in self.anno[point_name]:        return False
        a = self.anno[point_name]['cont']
        if a.is_empty:                                 return False
        if a.geom_type not in ['Point', 'MultiPoint']: return False
        return True

    def get_point(self, point_name):
        if self.has_point(point_name): return self.anno[point_name]['cont']
        else:                          return Point()

    def get_cont_as_mask(self, cont_name, h, w):
        if not self.has_contour(cont_name): return np.zeros((h,w))
        mp = self.get_contour(cont_name)
        if not mp.geom_type=='MultiPolygon': mp = MultiPolygon([mp])
        return utils.to_mask(mp, h, w)

    def get_pixel_size(self):
        ph, pw = self.anno['info']['pixelSize'] if 'info' in self.anno.keys() and 'pixelSize' in self.anno['info'].keys() else (-1,-1)
        return (ph, pw)
    
    def get_image_size(self):
        h, w = self.anno['info']['imageSize'] if 'info' in self.anno.keys() and 'imageSize' in self.anno['info'].keys() else (-1,-1)
        return (h,w)

    ######################
    # LAX CINE functions #
    ######################
    def length_LV(self):
        if not self.has_point('lv_lax_extent'): return np.nan
        extent = self.get_point('lv_lax_extent')
        pw, ph = self.get_pixel_size()
        lv_ext1, lv_ext2, apex = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
    
    def length_LA(self):
        if not self.has_point('laxLaExtentPoints'): return np.nan
        extent = self.get_point('laxLaExtentPoints')
        pw, ph = self.get_pixel_size()
        la_ext1, la_ext2, ceil = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([la_ext1, la_ext2]).centroid
        dist = mitral.distance(ceil)
        return dist
    
    def length_RA(self):
        if not self.has_point('laxRaExtentPoints'): return np.nan
        extent = self.get_point('laxRaExtentPoints')
        pw, ph = self.get_pixel_size()
        ra_ext1, ra_ext2, ceil = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([ra_ext1, ra_ext2]).centroid
        dist = mitral.distance(ceil)
        return dist
    
    def get_pixel_values(self, cont_name, img):
        h, w = img.shape
        mask = self.get_cont_as_mask(cont_name, h, w)
        return img[np.where(mask!=0)]
        
    #####################
    # Mapping functions #
    #####################
    def get_angle_mask_to_middle_point(self, h, w):
        if not self.has_contour('lv_endo'): return np.ones((h,w))*np.nan
        p = self.get_contour('lv_endo').centroid
        x,y = p.x, p.y
        mask = np.zeros((h,w,3))
        for i in range(h): mask[i,:,0] = i
        for j in range(w): mask[:,j,1] = j
        mask[:,:,0] -= y
        mask[:,:,1] -= x
        mask[:,:,2]  = np.sqrt(mask[:,:,0]**2+mask[:,:,1]**2) + 10**-9
        angle_img = np.zeros((h,w))
        angle_img[:int(y),int(x):] = np.arccos(mask[:int(y),int(x):,1] / mask[:int(y),int(x):,2]) * 180/np.pi
        angle_img[:int(y),:int(x)] = np.arcsin(np.abs(mask[:int(y),:int(x),1]) / mask[:int(y),:int(x),2]) * 180/np.pi +90
        angle_img[int(y):,:int(x)] = np.arccos(np.abs(mask[int(y):,:int(x),1]) / mask[int(y):,:int(x),2]) * 180/np.pi + 180
        angle_img[int(y):,int(x):] = np.arcsin(mask[int(y):,int(x):,1] / mask[int(y):,int(x):,2]) * 180/np.pi + 270
        return angle_img

    def get_angle_mask_to_middle_point_by_reference_point(self, h, w, refpoint=None):
        angle_mask = self.get_angle_mask_to_middle_point(h, w)
        angle      = self.get_reference_angle(refpoint)
        angle_mask = angle_mask - angle
        angle_mask = angle_mask % 360
        return angle_mask

    def get_reference_angle(self, refpoint=None):
        if not self.has_contour('lv_endo'):         return np.nan
        if not self.has_point('sacardialRefPoint'): return np.nan
        mp = self.get_contour('lv_endo').centroid
        rp = self.get_point('sacardialRefPoint') if refpoint is None else refpoint
        v1 = np.array([rp.x-mp.x, rp.y-mp.y])
        v2 = np.array([1,0])
        v1_u = v1 / np.linalg.norm(v1)
        v2_u = v2 / np.linalg.norm(v2)
        angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))*180/np.pi
        return angle

    def get_myo_mask_by_angles(self, img, nr_bins=6, refpoint=None):
        h, w       = img.shape
        myo_mask   = self.get_cont_as_mask('lv_myo', h, w)
        angle_mask = self.get_angle_mask_to_middle_point_by_reference_point(h, w, refpoint)
        bins       = [i*360/nr_bins for i in range(0, nr_bins+1)]
        bin_dict   = dict()
        for i in range(nr_bins):
            low, high = bins[i], bins[i+1]
            vals = img[(low<=angle_mask) & (angle_mask<high) & (myo_mask!=0)]
            bin_dict[(low, high)] = vals
        return bin_dict


class SAX_LGE_Annotation(Annotation):
    def __init__(self, filepath, sop):
        super().__init__(sop, filepath)

    def set_information(self):
        self.name = 'SAX LGE Annotation'
        self.contour_names = ['lv_endo', 'lv_epi', 'lv_myo',
                              'excludeEnhancementAreaContour',
                              'saEnhancementReferenceMyoContour',
                              'scar_fwhm', 'scar_fwhm_excluded_area', 
                             'scar', 'noreflow']
        self.point_names   = ['sacardialRefPoint']
        self.pixel_h, self.pixel_w = self.anno['info']['pixelSize'] if 'info' in self.anno.keys() and 'pixelSize' in self.anno['info'].keys() else (-1,-1)#1.98,1.98
        self.h,       self.w       = self.anno['info']['imageSize'] if 'info' in self.anno.keys() and 'imageSize' in self.anno['info'].keys() else (-1,-1)

    def add_fwhm_scar(self, img, exclude=True, normalize_myocardium=True):
        if not self.has_contour('saEnhancementReferenceMyoContour'): return
        h, w  = img.shape
        cont  = self.get_contour('saEnhancementReferenceMyoContour')
        mask  = utils.to_mask(cont, h, w)
        self.scar_max = img[np.where(mask!=0)].max()
        #threshold = myoMinimum + (myoMax-Min) / 2
        thresh = self.scar_max/2.0
        if normalize_myocardium:
            mask      = utils.to_mask(self.get_contour('lv_myo'), h, w)
            lvmyo_min = img[np.where(mask!=0)].min()
            thresh    = lvmyo_min + (self.scar_max - lvmyo_min)/2.0
            #print('Possible threshs: ', self.scar_max/2.0, thresh)
        cont = utils.to_polygon((img>thresh).astype(np.int16))
        cont = cont.intersection(self.get_contour('lv_myo'))
        if exclude: cont = cont.difference(self.get_contour('excludeEnhancementAreaContour'))
        cont = utils.geometry_collection_to_Polygon(cont)
        cont_name = 'scar_fwhm' + ('_excluded_area' if exclude else '')
        self.anno[cont_name] = {'cont':cont, 'contType':'FREE', 'subpixelResolution': scale}
        self.contour_names += [cont_name]
            
    def add_fwhm_scar_other_slice(self, img, other_anno, exclude=True, normalize_myocardium=True):
        h, w  = img.shape
        self.scar_max    = other_anno.scar_max
        #threshold = myoMinimum + (myoMax-Min) / 2
        thresh = self.scar_max/2.0
        if normalize_myocardium and self.has_contour('lv_myo'):
            mask      = utils.to_mask(self.get_contour('lv_myo'), h, w)
            lvmyo_min = img[np.where(mask!=0)].min()
            lvmyo_max = img[np.where(mask!=0)].max()
            thresh    = lvmyo_min + (self.scar_max - lvmyo_min)/2.0
            #print('Possible threshs other slice: ', self.scar_max/2.0, thresh)
        cont  = utils.to_polygon((img>thresh).astype(np.int16))
        cont  = cont.intersection(self.get_contour('lv_myo'))
        if exclude: cont = cont.difference(self.get_contour('excludeEnhancementAreaContour'))
        cont  = utils.geometry_collection_to_Polygon(cont)
        if cont.is_empty: return
        cont_name = 'scar_fwhm' + ('_excluded_area' if exclude else '')
        self.anno[cont_name] = {'cont':cont, 'contType':'FREE', 'subpixelResolution': scale}
        self.contour_names += [cont_name]
        

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
        self.all_imgs_sop2filepath  = loading_functions.read_dcm_images_into_sop2filepaths(imgs_path, debug)
        self.studyinstanceuid       = self._get_studyinstanceuid()
        self.annos_sop2filepath     = loading_functions.read_annos_into_sop2filepaths(annos_path, debug)
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
        return self.annotation_type(self.annos_sop2filepath[sop], sop)

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
            m = utils.dice(geo1, geo2)
            return "{:.2f}".format(m) if string else m
        except Exception: 
            print('Dice Metric failed:/n', traceback.format_exc())
            return '0.00' if string else 0.0

    def calculate_all_vals(self, view, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            for c in view.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                sopandcontname2metricval[(sop, c)] = utils.dice(anno1.get_contour(c), anno2.get_contour(c))
        if debug: print('Calculating all DSC values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval

class HausdorffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'HD'
        self.unit = '[mm]'

    def get_val(self, geo1, geo2, dcm=None, string=False):
        m = utils.hausdorff(geo1, geo2)
        return "{:.2f}".format(m) if string else m

    def calculate_all_vals(self, view, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            ph, pw = anno1.get_pixel_size()
            for c in view.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                hd = ph * utils.hausdorff(anno1.get_contour(c), anno2.get_contour(c))
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

    def calculate_all_vals(self, view, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            vd           = self.cc.case1.load_dcm(sop).SliceThickness
            ph, pw       = anno1.get_pixel_size()
            for c in view.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                ml_diff = (pw*ph*vd/1000.0) * (anno1.get_contour(c).area - anno2.get_contour(c).area)
                sopandcontname2metricval[(sop, c)] = ml_diff
        if debug: print('Calculating all mlDiff values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval

############################
# Mapping Specific Metrics #
############################

class T1AvgDiffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'T1AVG'
        self.unit = '[ms]'

    def get_val(self, geo1, geo2, img1, img2, string=False):
        # imgs = get_img (d,0,True,False)
        h,     w     = img1.shape
        mask1, mask2 = utils.to_mask(geo1,h,w).astype(bool), utils.to_mask(geo2,h,w).astype(bool)
        myo1_vals, myo2_vals = img1[mask1], img2[mask2]
        global_t1_1 = np.mean(myo1_vals)
        global_t1_2 = np.mean(myo2_vals)
        m           = global_t1_1 - global_t1_2
        return "{:.2f}".format(m) if string else m
        
    def calculate_all_vals(self, view, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            img1,  img2  = self.cc.case1.load_img(sop,True,False), self.cc.case2.load_img(sop,True,False)
            anno1, anno2 = self.cc.case1.load_anno(sop), self.cc.case2.load_anno(sop)
            for c in view.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                sopandcontname2metricval[(sop, c)] = self.get_val(anno1.get_contour(c), anno2.get_contour(c), img1, img2)
        if debug: print('Calculating all T1AvgDiff values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval

class T1AvgReaderMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'T1AVG'
        self.unit = '[ms]'

    def get_val(self, geo, img, string=False):
        # imgs = get_img (d,0,True,False)
        h, w = img.shape
        mask = utils.to_mask(geo, h,w).astype(bool)
        myo_vals  = img[mask]
        global_t1 = np.mean(myo_vals)
        m         = global_t1
        return "{:.2f}".format(m) if string else m
        
    def calculate_all_vals(self, view, debug=False):
        if debug: st = time(); nr_conts = 0
        sopandcontname2metricval = dict()
        for sop in self.get_all_sops():
            img  = self.cc.case1.load_img(sop,True,False)
            anno = self.cc.case1.load_anno(sop)
            for c in view.contour_names:
                if debug and (anno1.has_contour(c) or anno2.has_contour(c)): nr_conts += 1
                sopandcontname2metricval[(sop, c)] = self.get_val(anno.get_contour(c), img)
        if debug: print('Calculating all T1Avg values for ', nr_conts, ' contours took: ', time()-st, ' seconds.')
        return sopandcontname2metricval
        
class AngleDiffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'AngleDiff'
        self.unit = '[°]'

    def get_val(self, anno1, anno2, string=False):
        ext1    = anno1.get_point('sacardialRefPoint')
        lv_mid1 = anno1.get_contour('lv_endo').centroid
        ext2    = anno2.get_point('sacardialRefPoint')
        lv_mid2 = anno2.get_contour('lv_endo').centroid
        v1 = np.array(ext1 - lv_mid1)
        v2 = np.array(ext2 - lv_mid2)
        v1_u = v1 / np.linalg.norm(v1)
        v2_u = v2 / np.linalg.norm(v2)
        if len(v1_u)!=len(v2_u):    return 'nan' if string else np.nan
        if len(v1_u)==len(v2_u)==0: return "{:.2f}".format(0) if string else 0
        angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))*180/np.pi
        return "{:.2f}".format(angle) if string else angle
    

class T2AvgDiffMetric(T1AvgDiffMetric):
    def __init__(self):
        super().__init__()
    def set_information(self):
        self.name = 'T2AVG'
        self.unit = '[ms]'
    
class T2AvgReaderMetric(T1AvgReaderMetric):
    def __init__(self):
        super().__init__()
    def set_information(self):
        self.name = 'T2AVG'
        self.unit = '[ms]'


class SAX_CINE_analyzer:
    def __init__(self, case_comparison):
        self.cc   = case_comparison
        from LazyLuna.Views import SAX_CINE_View
        self.view = SAX_CINE_View()
        self.contour_comparison_pandas_dataframe = None

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
        if not self.contour_comparison_pandas_dataframe is None: return self.contour_comparison_pandas_dataframe
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


class LAX_CINE_analyzer:
    def __init__(self, cc):
        self.cc = cc
        from LazyLuna.Views import LAX_CINE_View
        self.view = LAX_CINE_View()
        self.contour_comparison_pandas_dataframe = None
    
    def get_case_contour_comparison_pandas_dataframe(self, fixed_phase_first_reader=False, debug=False):
        if not self.contour_comparison_pandas_dataframe is None: return self.contour_comparison_pandas_dataframe
        # case, reader1, reader2, sop1, sop2, category, d, nr_slices, depth_perc, p1, p2, cont_name, dsc, hd, mldiff, apic/midv/bas/outside1, apic/midv/bas/outside2, has_cont1, has_cont2
        #print('In get_case_contour_comparison_pandas_dataframe')
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
                #print(cat1, cat2, cat1.phase, cat2.phase)
                #if np.isnan(cat1.phase) or np.isnan(cat2.phase): continue
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                nr_sl  = cat1.nr_slices
                for d in range(cat1.nr_slices):
                    d_perc       = 1.0 * d / nr_sl
                    try:
                        sop1, sop2   = cat1.depthandtime2sop[d,p1], cat2.depthandtime2sop[d,p2]
                        anno1, anno2 = self.cc.case1.load_anno(sop1), self.cc.case2.load_anno(sop2)
                        cont1, cont2 = anno1.get_contour(cont_name), anno2.get_contour(cont_name)
                        dcm    = self.cc.case1.load_dcm(sop1)
                        dsc    = dsc_m   .get_val(cont1, cont2, dcm)
                        hd     = hd_m    .get_val(cont1, cont2, dcm)
                        mldiff = mldiff_m.get_val(cont1, cont2, dcm)
                        has_cont1, has_cont2     = anno1.has_contour(cont_name), anno2.has_contour(cont_name)
                        row = [case_name, reader1, reader2, sop1, sop2, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, dsc, hd, mldiff, np.abs(mldiff), has_cont1, has_cont2]
                        rows.append(row)
                    except Exception as e:
                        row = [case_name, reader1, reader2, np.nan, np.nan, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, np.nan, np.nan, np.nan, np.nan, 'False', 'False']
                        rows.append(row)
                    
        columns=['case', 'reader1', 'reader2', 'sop1', 'sop2', 'category', 'slice', 'max_slices', 'depth_perc', 'phase1', 'phase2', 'contour name', 'DSC', 'HD', 'ml diff', 'abs ml diff', 'has_contour1', 'has_contour2']
        df = pandas.DataFrame(rows, columns=columns)
        if debug: print('pandas table took: ', time()-st)
        self.contour_comparison_pandas_dataframe = df
        return df
    


class SAX_T1_analyzer:
    def __init__(self, cc):
        self.cc = cc
        from LazyLuna.Views import SAX_T1_View
        self.view = SAX_T1_View()
        self.contour_comparison_pandas_dataframe = None
    
    def get_case_contour_comparison_pandas_dataframe(self, fixed_phase_first_reader=False, debug=False):
        if not self.contour_comparison_pandas_dataframe is None: return self.contour_comparison_pandas_dataframe
        # case, reader1, reader2, sop1, sop2, category, d, nr_slices, depth_perc, p1, p2, cont_name, dsc, hd, mldiff, apic/midv/bas/outside1, apic/midv/bas/outside2, has_cont1, has_cont2
        print('In get_case_contour_comparison_pandas_dataframe')
        if debug: st = time()
        rows                  = []
        view                  = self.view
        case1, case2          = self.cc.case1, self.cc.case2
        case_name             = case1.case_name
        reader1, reader2      = case1.reader_name, case2.reader_name
        dsc_m, hd_m           = DiceMetric(), HausdorffMetric()
        t1avg_m               = T1AvgReaderMetric()
        t1avgdiff_m, angle_m  = T1AvgDiffMetric(), AngleDiffMetric()
        
        for cont_name in self.view.contour_names:
            categories1, categories2 = view.get_categories(case1, cont_name), view.get_categories(case2, cont_name)
            for cat1, cat2 in zip(categories1, categories2):
                print(cat1, cat2, cat1.phase, cat2.phase)
                if np.isnan(cat1.phase) or np.isnan(cat2.phase): continue
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                nr_sl  = cat1.nr_slices
                for d in range(cat1.nr_slices):
                    d_perc       = 1.0 * d / nr_sl
                    sop1, sop2   = cat1.depthandtime2sop[d,p1], cat2.depthandtime2sop[d,p2]
                    anno1, anno2 = self.cc.case1.load_anno(sop1), self.cc.case2.load_anno(sop2)
                    cont1, cont2 = anno1.get_contour(cont_name), anno2.get_contour(cont_name)
                    dcm1 = self.cc.case1.load_dcm(sop1)
                    dcm2 = self.cc.case1.load_dcm(sop2)
                    img1 = cat1.get_img(d,0, True, False)
                    img2 = cat2.get_img(d,0, True, False)
                    dsc      = dsc_m   .get_val(cont1, cont2, dcm1)
                    hd       = hd_m    .get_val(cont1, cont2, dcm1)
                    t11, t12 = t1avg_m.get_val(cont1, img1), t1avg_m.get_val(cont2, img2)
                    t1_diff  = t1avgdiff_m.get_val(cont1, cont2, img1, img2)
                    angle_d  = angle_m.get_val(anno1, anno2)
                    has_cont1, has_cont2     = anno1.has_contour(cont_name), anno2.has_contour(cont_name)
                    row = [case_name, reader1, reader2, sop1, sop2, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, dsc, hd, t11, t12, t1_diff, angle_d, has_cont1, has_cont2]
                    rows.append(row)
        columns=['case', 'reader1', 'reader2', 'sop1', 'sop2', 'category', 'slice', 'max_slices', 'depth_perc', 'phase1', 'phase2', 'contour name', 'DSC', 'HD', 'T1_R1', 'T1_R2', 'T1_Diff', 'Angle_Diff', 'has_contour1', 'has_contour2']
        df = pandas.DataFrame(rows, columns=columns)
        if debug: print('pandas table took: ', time()-st)
        self.contour_comparison_pandas_dataframe = df
        return df
    
    
class SAX_T2_analyzer:
    def __init__(self, cc):
        self.cc = cc
        from LazyLuna.Views import SAX_T2_View
        self.view = SAX_T2_View()
        self.contour_comparison_pandas_dataframe = None
    
    def get_case_contour_comparison_pandas_dataframe(self, fixed_phase_first_reader=False, debug=False):
        if not self.contour_comparison_pandas_dataframe is None: return self.contour_comparison_pandas_dataframe
        # case, reader1, reader2, sop1, sop2, category, d, nr_slices, depth_perc, p1, p2, cont_name, dsc, hd, mldiff, apic/midv/bas/outside1, apic/midv/bas/outside2, has_cont1, has_cont2
        print('In get_case_contour_comparison_pandas_dataframe')
        if debug: st = time()
        rows                  = []
        view                  = self.view
        case1, case2          = self.cc.case1, self.cc.case2
        case_name             = case1.case_name
        reader1, reader2      = case1.reader_name, case2.reader_name
        dsc_m, hd_m           = DiceMetric(), HausdorffMetric()
        t2avg_m               = T2AvgReaderMetric()
        t2avgdiff_m, angle_m  = T2AvgDiffMetric(), AngleDiffMetric()
        
        for cont_name in self.view.contour_names:
            categories1, categories2 = view.get_categories(case1, cont_name), view.get_categories(case2, cont_name)
            for cat1, cat2 in zip(categories1, categories2):
                print(cat1, cat2, cat1.phase, cat2.phase)
                if np.isnan(cat1.phase) or np.isnan(cat2.phase): continue
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                nr_sl  = cat1.nr_slices
                for d in range(cat1.nr_slices):
                    d_perc       = 1.0 * d / nr_sl
                    sop1, sop2   = cat1.depthandtime2sop[d,p1], cat2.depthandtime2sop[d,p2]
                    anno1, anno2 = self.cc.case1.load_anno(sop1), self.cc.case2.load_anno(sop2)
                    cont1, cont2 = anno1.get_contour(cont_name), anno2.get_contour(cont_name)
                    dcm1 = self.cc.case1.load_dcm(sop1)
                    dcm2 = self.cc.case1.load_dcm(sop2)
                    img1 = cat1.get_img(d,0, True, False)
                    img2 = cat2.get_img(d,0, True, False)
                    dsc      = dsc_m   .get_val(cont1, cont2, dcm1)
                    hd       = hd_m    .get_val(cont1, cont2, dcm1)
                    t21, t22 = t2avg_m.get_val(cont1, img1), t2avg_m.get_val(cont2, img2)
                    t2_diff  = t2avgdiff_m.get_val(cont1, cont2, img1, img2)
                    angle_d  = angle_m.get_val(anno1, anno2)
                    has_cont1, has_cont2     = anno1.has_contour(cont_name), anno2.has_contour(cont_name)
                    row = [case_name, reader1, reader2, sop1, sop2, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, dsc, hd, t21, t22, t2_diff, angle_d, has_cont1, has_cont2]
                    rows.append(row)
        columns=['case', 'reader1', 'reader2', 'sop1', 'sop2', 'category', 'slice', 'max_slices', 'depth_perc', 'phase1', 'phase2', 'contour name', 'DSC', 'HD', 'T2_R1', 'T2_R2', 'T2_Diff', 'Angle_Diff', 'has_contour1', 'has_contour2']
        df = pandas.DataFrame(rows, columns=columns)
        if debug: print('pandas table took: ', time()-st)
        self.contour_comparison_pandas_dataframe = df
        return df