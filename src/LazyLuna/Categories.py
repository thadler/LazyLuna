############
# Category #
############

from operator import itemgetter
import numpy as np
import pydicom
from time import time
import traceback

from LazyLuna.Mini_LL import Annotation


class SAX_slice_phase_Category:
    def __init__(self, case):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'none'
        self.phase = np.nan

    def get_sop2depthandtime(self, sop2filepath, debug=False):
        if debug: st = time()
        if hasattr(self.case, 'categories'):
            for c in self.case.categories:
                if hasattr(c, 'sop2depthandtime'):
                    if debug: print('calculating sop2sorting takes: ', time()-st)
                    return c.sop2depthandtime
        # returns dict sop --> (depth, time)
        imgs = {k:pydicom.dcmread(sop2filepath[k]) for k in sop2filepath.keys()}
        
        # NEW
        sortable = [[k,v.SliceLocation,v.InstanceNumber] for k,v in imgs.items()]
        #sortable = [[k,float(v.SliceLocation),float(v.AcquisitionNumber)] for k,v in imgs.items()]
        slice_nrs = {x:i for i,x in enumerate(sorted(list(set([x[1] for x in sortable]))))}
        sortable = [s+[slice_nrs[s[1]]] for s in sortable]
        sortable_by_slice = {d:[] for d in slice_nrs.values()}
        for s in sortable: sortable_by_slice[s[-1]].append(s)
        for d in range(len(sortable_by_slice.keys())):
            sortable_by_slice[d] = sorted(sortable_by_slice[d], key=lambda s:s[2])
            for p in range(len(sortable_by_slice[d])):
                sortable_by_slice[d][p].append(p)
        sop2depthandtime = dict()
        for d in range(len(sortable_by_slice.keys())):
            for s in sortable_by_slice[d]:
                sop2depthandtime[s[0]] = (s[-2],s[-1])
        
        # potentially flip slice direction: base top x0<x1, y0>y1, z0>z1, apex top x0>x1, y0<y1, z0<z1
        depthandtime2sop = {v:k for k,v in sop2depthandtime.items()}
        img1, img2 = imgs[depthandtime2sop[(0,0)]], imgs[depthandtime2sop[(1,0)]]
        img1x,img1y,img1z = list(map(float,img1.ImagePositionPatient))
        img2x,img2y,img2z = list(map(float,img2.ImagePositionPatient))
        if img1x<img2x and img1y>img2y and img1z>img2z: pass
        else: #img1x>img2x or img1y<img2y or img1z<img2z:
            max_depth = max(sortable_by_slice.keys())
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
        try: sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        except Exception as e:
            print(e)
            sop = None
        return self.case.load_anno(sop)

    def get_img(self, slice_nr, phase_nr, value_normalize=True, window_normalize=True):
        try:
            sop = self.depthandtime2sop[(slice_nr, phase_nr)]
            img = self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)
        except Exception as e:
            print(e)
            img = np.zeros((self.height, self.width))
        return img

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
        if True not in has_conts: return np.nan
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
        if True not in has_conts: return np.nan
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
        self.phase = np.nan

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
        try:
            sop = self.depthandtime2sop[(slice_nr, phase_nr)]
            return self.case.load_anno(sop)
        except Exception as e:
            print(traceback.format_exc())
            return Annotation(None)

    def get_img(self, slice_nr, phase_nr, value_normalize=True, window_normalize=True):
        try:
            sop = self.depthandtime2sop[(slice_nr, phase_nr)]
            return self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)
        except Exception as e:
            print(traceback.format_exc())
            return np.zeros((self.height, self.width))

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
        if True not in has_conts: return np.nan
        return np.argmax(vol_curve)
    
class LAX_4CV_RVES_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV RVES'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('rv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
        valid_idx = np.where(vol_curve > 0)[0]
        return valid_idx[vol_curve[valid_idx].argmin()]

class LAX_4CV_RVED_Category(LAX_Category):
    def __init__(self, case):
        super().__init__(case)
        self.name  = 'LAX 4CV RVED'
        self.phase = self.get_phase()
    
    def relevant_images(self, dcm): return 'LAX 4CV' in dcm[0x0b, 0x10].value
    
    def get_phase(self):
        lvendo_vol_curve = self.get_area_curve('rv_lax_endo')
        vol_curve = np.array(lvendo_vol_curve)
        has_conts = [a!=0 for a in vol_curve]
        if True not in has_conts: return np.nan
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
        if True not in has_conts: return np.nan
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
        if True not in has_conts: return np.nan
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
        if True not in has_conts: return np.nan
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
        if True not in has_conts: return np.nan
        return np.argmax(vol_curve)

######################
# Mapping Categories #
######################

class SAX_T1_Category(SAX_slice_phase_Category):
    def __init__(self, case, debug=False):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath, debug=debug)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'SAX T1'
        self.phase = 0
        
    def get_phase(self):
        return self.phase

    def get_sop2depthandtime(self, sop2filepath, debug=False):
        if debug: st = time()
        # returns dict sop --> (depth, time)
        imgs = {k:pydicom.dcmread(sop2filepath[k]) for k in sop2filepath.keys()}
        sortable_slice_location = [float(v.SliceLocation) for sopinstanceuid, v in imgs.items()]
        sl_len = len(set([elem for elem in sortable_slice_location]))
        sorted_slice_location = np.array(sorted(sortable_slice_location))
        sop2depthandtime = dict()
        for sopinstanceuid in imgs.keys():
            s_loc = imgs[sopinstanceuid].SliceLocation
            for i in range(len(sorted_slice_location)):
                if not s_loc==sorted_slice_location[i]: continue
                sop2depthandtime[sopinstanceuid] = (i,0)
        # potentially flip slice direction: base top x0<x1, y0>y1, z0>z1, apex top x0>x1, y0<y1, z0<z1
        depthandtime2sop = {v:k for k,v in sop2depthandtime.items()}
        img1, img2 = imgs[depthandtime2sop[(0,0)]], imgs[depthandtime2sop[(1,0)]]
        img1x,img1y,img1z = list(map(float,img1.ImagePositionPatient))
        img2x,img2y,img2z = list(map(float,img2.ImagePositionPatient))
        if img1x<img2x and img1y>img2y and img1z>img2z: pass
        else: #img1x>img2x and img1y<img2y and img1z<img2z:
            max_depth = sl_len-1
            for sop in sop2depthandtime.keys():
                sop2depthandtime[sop] = (max_depth-sop2depthandtime[sop][0], 0)
        if debug: print('calculating sop2sorting takes: ', time()-st)
        return sop2depthandtime

    def set_image_height_width_depth(self, debug=False):
        if debug: st = time()
        nr_slices = self.nr_slices
        dcm1 = self.case.load_dcm(self.depthandtime2sop[(0, 0)])
        dcm2 = self.case.load_dcm(self.depthandtime2sop[(1, 0)])
        self.height, self.width = dcm1.pixel_array.shape
        self.pixel_h, self.pixel_w = list(map(float, dcm1.PixelSpacing))
        spacingbs = []
        for d in range(nr_slices-1):
            dcm1 = self.case.load_dcm(self.depthandtime2sop[(d,   0)])
            dcm2 = self.case.load_dcm(self.depthandtime2sop[(d+1, 0)])
            spacingbs += [round(np.abs(dcm1.SliceLocation - dcm2.SliceLocation), 2)]
            try: self.slice_thickness = dcm1.SliceThickness
            except Exception as e: print('Exception in SAX_T1_Category, ', e)
        self.spacing_between_slices = min(spacingbs)
        self.missing_slices = []
        for d in range(nr_slices-1):
            dcm1 = self.case.load_dcm(self.depthandtime2sop[(d,   0)])
            dcm2 = self.case.load_dcm(self.depthandtime2sop[(d+1, 0)])
            curr_spacing = round(np.abs(dcm1.SliceLocation - dcm2.SliceLocation), 2)
            if round(curr_spacing / self.spacing_between_slices) != 1:
                for m in range(int(round(curr_spacing / self.spacing_between_slices))-1):
                    self.missing_slices += [(d + m)]
                
    def set_nr_slices_phases(self):
        dat = list(self.depthandtime2sop.keys())
        self.nr_phases = 1
        self.nr_slices = max(dat, key=itemgetter(0))[0]+1
        
    def get_dcm(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_dcm(sop)

    def get_anno(self, slice_nr, phase_nr=0):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_anno(sop)

    def get_img(self, slice_nr, phase_nr=0, value_normalize=True, window_normalize=False):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)

    def get_imgs(self, value_normalize=True, window_normalize=False):
        return [self.get_img(d, 0, value_normalize, window_normalize) for d in range(self.nr_slices)]

    def get_annos(self):
        return [self.get_anno(d,0) for d in range(self.nr_slices)]

    def get_base_apex(self, cont_name, debug=False):
        annos     = self.get_annos()
        has_conts = [a.has_contour(cont_name) for a in annos]
        if True not in has_conts: return 0
        base_idx = has_conts.index(True)
        apex_idx = self.nr_slices - has_conts[::-1].index(True) - 1
        if debug: print('Base idx / Apex idx: ', base_idx, apex_idx)
        return base_idx, apex_idx
    
    def get_volume(self, cont_name, debug=False):
        annos = self.get_annos()
        pixel_area = self.pixel_h * self.pixel_w
        areas = [a.get_contour(cont_name).area*pixel_area if a is not None else 0.0 for a in annos]
        if debug: print('Areas: ', [round(a, 2) for a in areas])
        has_conts = [a!=0 for a in areas]
        if True not in has_conts: return 0
        base_idx = has_conts.index(True)
        apex_idx = self.nr_slices - has_conts[::-1].index(True) - 1
        if debug: print('Base idx / Apex idx: ', base_idx, apex_idx)
        vol = 0
        for d in range(self.nr_slices):
            pixel_depth = (self.slice_thickness+self.spacing_between_slices)/2.0 if d in [base_idx, apex_idx] else self.spacing_between_slices
            vol += areas[d] * pixel_depth
        # for missing slices
        for d in self.missing_slices:
            pixel_depth = self.spacing_between_slices
            vol += (areas[d] + areas[d+1])/2 * pixel_depth
        return vol / 1000.0
    
    def lax_points(self):
        self.lax_sop_fps = []
        for sop, fp in self.case.annos_sop2filepath.items():
            anno = Annotation(fp, sop)
            if anno.has_point('lv_lax_extent'):
                self.lax_sop_fps.append((sop, fp, anno, self.get_lax_image(sop)))
    
    def get_lax_image(self, sop):
        for k in self.case.all_imgs_sop2filepath:
            if sop in self.case.all_imgs_sop2filepath[k].keys():
                return pydicom.dcmread(self.case.all_imgs_sop2filepath[k][sop], stop_before_pixels=False)
            
    def get_slice_distances_to_extent_points(self):
        if hasattr(self, 'mindists_slices_lax_extpoint'):
            return self.mindists_slices_lax_extpoint
        if not hasattr(self, 'lax_sop_fps'): self.lax_points()
        if not hasattr(self, 'lax_sop_fps'):
            print('No extent points in lax images')
            return None
        lax_dcm      = self.lax_sop_fps[0][3]
        lax_h, lax_w = lax_dcm.pixel_array.shape
        lax_anno     = self.lax_sop_fps[0][2]
        p1, p2, p3 = [[lax_anno.get_point('lv_lax_extent')[i].y, lax_anno.get_point('lv_lax_extent')[i].x] for i in range(3)]
        extpoints_rcs = utils.transform_ics_to_rcs(lax_dcm, np.array([p1, p2, p3]))
        ext_st  = (extpoints_rcs[0] + extpoints_rcs[1])/2.0
        ext_end = extpoints_rcs[2]
        base_center = ext_st + 1/6 * (ext_end - ext_st)
        midv_center = ext_st + 3/6 * (ext_end - ext_st)
        apex_center = ext_st + 5/6 * (ext_end - ext_st)
        minimal_distances = []
        for d in range(self.nr_slices):
            dcm    = self.get_dcm(d,0)
            img    = self.get_img(d,0,True,True)
            h, w   = img.shape
            mesh   = np.meshgrid(np.arange(w), np.arange(h))
            idxs   = np.stack((mesh[0].flatten(), mesh[1].flatten())).T
            points = utils.transform_ics_to_rcs(dcm, idxs)
            dists_base = np.linalg.norm(np.subtract(points, base_center), axis=1)
            dists_midv = np.linalg.norm(np.subtract(points, midv_center), axis=1)
            dists_apex = np.linalg.norm(np.subtract(points, apex_center), axis=1)
            minimal_distances.append([np.min(dists_base), np.min(dists_midv), 
                                      np.min(dists_apex)])
        self.mindists_slices_lax_extpoint = np.asarray(minimal_distances)
        return self.mindists_slices_lax_extpoint
    
    def calc_mapping_aha_model(self):
        # returns means and stds
        if self.nr_slices == 1:
            print('AHA assuming single midv slice.')
            img, anno = self.get_img(0,0,True,False), self.get_anno(0,0)
            m = anno.get_myo_mask_by_angles(img, nr_bins=6)
            m_m = np.asarray([np.mean(v) for v in b.values()])
            m_s = np.asarray([np.std(v) for v in b.values()])
            return ([np.full(6,np.nan), np.roll(m_m,1), np.full(4,np.nan)],
                    [np.full(6,np.nan), np.roll(m_s,1), np.full(4,np.nan)])
        
        if self.nr_slices == 3:
            # assume 3 of 5 so: 0:base, 1:midv, 2:apex
            print('AHA as three individual slices.')
            img, anno = self.get_img(0,0,True,False), self.get_anno(0,0)
            b = anno.get_myo_mask_by_angles(img, nr_bins=6)
            b_m = np.asarray([np.mean(v) for v in b.values()])
            b_s = np.asarray([np.std(v) for v in b.values()])
            img, anno = self.get_img(1,0,True,False), self.get_anno(1,0)
            m = anno.get_myo_mask_by_angles(img, nr_bins=6)
            m_m = np.asarray([np.mean(v) for v in m.values()])
            m_s = np.asarray([np.std(v) for v in m.values()])
            img, anno = self.get_img(2,0,True,False), self.get_anno(2,0)
            a = anno.get_myo_mask_by_angles(img, nr_bins=4)
            a_m = np.asarray([np.mean(v) for v in a.values()])
            a_s = np.asarray([np.std(v) for v in a.values()])
            return ([np.roll(b_m,1),np.roll(m_m,1),np.roll(a_m,1)],
                    [np.roll(b_s,1),np.roll(m_s,1),np.roll(a_s,1)])
        
        # else nr slices > 3 OR nr slices == 2
        min_dists = self.get_slice_distances_to_extent_points()
        if min_dists is None: 
            print('No extent & apical points in long axis views. No AHA possible.')
            return [np.full(6,np.nan), np.full(6,np.nan), np.full(4,np.nan)]
        idxs      = np.argmin(min_dists, axis=1)
        weights   = [1/x if x!=0 else np.nan for x in np.bincount(idxs)]
        means = [np.zeros(6) if 0 in idxs else np.full(6,np.nan),
                 np.zeros(6) if 1 in idxs else np.full(6,np.nan),
                 np.zeros(4) if 2 in idxs else np.full(4,np.nan)]
        stds  = [np.zeros(6) if 0 in idxs else np.full(6,np.nan),
                 np.zeros(6) if 1 in idxs else np.full(6,np.nan),
                 np.zeros(4) if 2 in idxs else np.full(4,np.nan)]
        # get all vals for individual slices
        vals_by_slice = dict()
        for d, idx in enumerate(idxs):
            nr_bins = 4 if idx==2 else 6
            img, anno = self.get_img(d,0,True,False), self.get_anno(d,0)
            vals = anno.get_myo_mask_by_angles(img, nr_bins=nr_bins)
            vals_by_slice[d] = vals
        # concatenate by indexes
        vals_by_idx = dict()
        for d, idx in enumerate(idxs):
            if idx not in vals_by_idx.keys():
                vals_by_idx[idx] = vals_by_slice[d]
            else:
                for k in vals_by_slice[d].keys():
                    vals_by_idx[idx][k] = np.append(vals_by_idx[idx][k], vals_by_slice[d][k])
        # vals by index to arrays
        for idx in set(idxs):
            means[idx] = np.asarray([np.mean(v) for v in vals_by_idx[idx].values()])
            stds [idx] = np.asarray([np.std(v)  for v in vals_by_idx[idx].values()])
        print('AHA via extent & apical points in long axis view.')
        return ([np.roll(r,1) for r in means],[np.roll(r,1) for r in stds])
    
    
class SAX_T2_Category(SAX_T1_Category):
    def __init__(self, case, debug=False):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath, debug=debug)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'SAX T2'
        self.phase = 0

class SAX_LGE_Category(SAX_slice_phase_Category):
    def __init__(self, case, debug=False):
        self.case = case
        self.sop2depthandtime = self.get_sop2depthandtime(case.imgs_sop2filepath, debug=debug)
        self.depthandtime2sop = {v:k for k,v in self.sop2depthandtime.items()}
        self.set_nr_slices_phases()
        self.set_image_height_width_depth()
        self.name = 'SAX LGE'
        self.phase = 0

    def get_sop2depthandtime(self, sop2filepath, debug=False):
        if debug: st = time()
        # returns dict sop --> (depth, time)
        imgs = {k:pydicom.dcmread(sop2filepath[k]) for k in sop2filepath.keys()}
        sortable_slice_location = [float(v.SliceLocation) for sopinstanceuid, v in imgs.items()]
        sl_len = len(set([elem for elem in sortable_slice_location]))
        sorted_slice_location = np.array(sorted(sortable_slice_location))
        sop2depthandtime = dict()
        for sopinstanceuid in imgs.keys():
            s_loc = imgs[sopinstanceuid].SliceLocation
            for i in range(len(sorted_slice_location)):
                if not s_loc==sorted_slice_location[i]: continue
                sop2depthandtime[sopinstanceuid] = (i,0)
        # potentially flip slice direction: base top x0<x1, y0>y1, z0>z1, apex top x0>x1, y0<y1, z0<z1
        depthandtime2sop = {v:k for k,v in sop2depthandtime.items()}
        img1, img2 = imgs[depthandtime2sop[(0,0)]], imgs[depthandtime2sop[(1,0)]]
        img1x,img1y,img1z = list(map(float,img1.ImagePositionPatient))
        img2x,img2y,img2z = list(map(float,img2.ImagePositionPatient))
        if img1x<img2x and img1y>img2y and img1z>img2z: pass
        else: #img1x>img2x and img1y<img2y and img1z<img2z:
            max_depth = sl_len-1
            for sop in sop2depthandtime.keys():
                sop2depthandtime[sop] = (max_depth-sop2depthandtime[sop][0], 0)
        if debug: print('calculating sop2sorting takes: ', time()-st)
        return sop2depthandtime
    
    def get_phase(self):
        return self.phase

    def set_image_height_width_depth(self, debug=False):
        if debug: st = time()
        nr_slices = self.nr_slices
        dcm1 = self.case.load_dcm(self.depthandtime2sop[(0, 0)])
        dcm2 = self.case.load_dcm(self.depthandtime2sop[(1, 0)])
        self.height, self.width = dcm1.pixel_array.shape
        self.pixel_h, self.pixel_w = list(map(float, dcm1.PixelSpacing))
        spacingbs = []
        for d in range(nr_slices-1):
            dcm1 = self.case.load_dcm(self.depthandtime2sop[(d,   0)])
            dcm2 = self.case.load_dcm(self.depthandtime2sop[(d+1, 0)])
            spacingbs += [round(np.abs(dcm1.SliceLocation - dcm2.SliceLocation), 2)]
            try: self.slice_thickness = dcm1.SliceThickness
            except Exception as e: print('Exception in SAX_LGE_Category, ', e)
        self.spacing_between_slices = min(spacingbs)
        print('Spacings: ', spacingbs)
        self.missing_slices = []
        for d in range(nr_slices-1):
            dcm1 = self.case.load_dcm(self.depthandtime2sop[(d,   0)])
            dcm2 = self.case.load_dcm(self.depthandtime2sop[(d+1, 0)])
            curr_spacing = round(np.abs(dcm1.SliceLocation - dcm2.SliceLocation), 2)
            if round(curr_spacing / self.spacing_between_slices) != 1:
                for m in range(int(round(curr_spacing / self.spacing_between_slices))-1):
                    self.missing_slices += [(d + m)]
                
    def set_nr_slices_phases(self):
        dat = list(self.depthandtime2sop.keys())
        self.nr_phases = 1
        self.nr_slices = max(dat, key=itemgetter(0))[0]+1
        
    def get_dcm(self, slice_nr, phase_nr):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_dcm(sop)

    def get_anno(self, slice_nr, phase_nr=0):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.load_anno(sop)

    def get_img(self, slice_nr, phase_nr=0, value_normalize=True, window_normalize=False):
        sop = self.depthandtime2sop[(slice_nr, phase_nr)]
        return self.case.get_img(sop, value_normalize=value_normalize, window_normalize=window_normalize)

    def get_imgs(self, value_normalize=True, window_normalize=False):
        return [self.get_img(d, 0, value_normalize, window_normalize) for d in range(self.nr_slices)]

    def get_annos(self):
        return [self.get_anno(d,0) for d in range(self.nr_slices)]

    def get_anno_with_scar_fwhm(self, slice_nr, exclude=True):
        img  = self.get_img (slice_nr, 0)
        anno = self.get_anno(slice_nr, 0)
        if anno.has_contour('saEnhancementReferenceMyoContour'):
            anno.add_fwhm_scar(img, exclude=exclude)
            return anno
        for i in range(self.nr_slices):
            low_d  = max(0, slice_nr - i)
            high_d = min(slice_nr + i, self.nr_slices-1)
            for d in [low_d, high_d]:
                other_anno = self.get_anno(d, 0)
                if other_anno.has_contour('saEnhancementReferenceMyoContour'):
                    other_img = self.get_img(d, 0)
                    other_anno.add_fwhm_scar(other_img, exclude=exclude)
                    anno.add_fwhm_scar_other_slice(img, other_anno, exclude=exclude)
                    return anno
    
    def preprocess_scars(self):
        for d in range(self.nr_slices):
            anno = self.get_anno(d,0)
            if anno.sop not in self.case.annos_sop2filepath: continue
            new_anno = anno.anno
            for exclude in [False, True]:
                anno = self.get_anno_with_scar_fwhm(d, exclude)
                new_anno = {**new_anno, **anno.anno}
            path = self.case.annos_sop2filepath[anno.sop]
            pickle.dump(new_anno, open(path, 'wb'), pickle.HIGHEST_PROTOCOL)
    
    def get_base_apex(self, cont_name, debug=False):
        annos     = self.get_annos()
        has_conts = [a.has_contour(cont_name) for a in annos]
        if True not in has_conts: return -1,-1
        base_idx = has_conts.index(True)
        apex_idx = self.nr_slices - has_conts[::-1].index(True) - 1
        if debug: print('Base idx / Apex idx: ', base_idx, apex_idx)
        return base_idx, apex_idx
    
    def get_volume(self, cont_name, debug=False):
        annos = self.get_annos()
        pixel_area = self.pixel_h * self.pixel_w
        areas = [a.get_contour(cont_name).area*pixel_area if a is not None else 0.0 for a in annos]
        if debug: print('Areas: ', [round(a, 2) for a in areas])
        has_conts = [a!=0 for a in areas]
        if True not in has_conts: return 0
        base_idx = has_conts.index(True)
        apex_idx = self.nr_slices - has_conts[::-1].index(True) - 1
        if debug: print('Base idx / Apex idx: ', base_idx, apex_idx)
        vol = 0
        for d in range(self.nr_slices):
            pixel_depth = (self.slice_thickness+self.spacing_between_slices)/2.0 if d in [base_idx, apex_idx] else self.spacing_between_slices
            vol += areas[d] * pixel_depth
        # for missing slices
        for d in self.missing_slices:
            pixel_depth = self.spacing_between_slices
            vol += (areas[d] + areas[d+1])/2 * pixel_depth
        return vol / 1000.0
    
    def lax_points(self):
        self.lax_sop_fps = []
        for sop, fp in self.case.annos_sop2filepath.items():
            anno = Annotation(fp, sop)
            if anno.has_point('lv_lax_extent'):
                self.lax_sop_fps.append((sop, fp, anno, self.get_lax_image(sop)))
                #fig, ax = plt.subplots(1,1,figsize=(7,7))
                #ax.imshow(self.lax_sop_fps[-1][-1].pixel_array)
                #anno.plot_all_points(ax)
                #plt.show()
    
    def get_lax_image(self, sop):
        for k in self.case.all_imgs_sop2filepath:
            if sop in self.case.all_imgs_sop2filepath[k].keys():
                return pydicom.dcmread(self.case.all_imgs_sop2filepath[k][sop], stop_before_pixels=False)
        

