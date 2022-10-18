import os
import traceback
from time import time
import pickle
import pydicom
import numpy as np
import pandas

from LazyLuna import utils, loading_functions
from LazyLuna.Annotation import Annotation


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

    def attach_categories(self, categories):
        self.categories = [] # iteratively adding categories is a speed-up
        for c in categories: self.categories.append(c(self))

    def attach_clinical_results(self, crs):
        self.crs = [cr(self) for cr in crs]

    # lazy loaders & getters
    def load_dcm(self, sop):
        return pydicom.dcmread(self.imgs_sop2filepath[sop], stop_before_pixels=False)

    def load_anno(self, sop):
        if sop not in self.annos_sop2filepath.keys(): return Annotation(None)
        return Annotation(self.annos_sop2filepath[sop], sop)

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
        storage_path = os.path.join(storage_dir, self.reader_name+'_'+self.case_name+'_'+self.studyinstanceuid+'_LL_case.pickle')
        f = open(storage_path, 'wb'); pickle.dump(self, f); f.close()
        return storage_path


###################
# Case Comparison #
###################
class Case_Comparison:
    def __init__(self, case1, case2):
        self.case1, self.case2 = case1, case2
        # assertions here? same case, same images,
        if self.case1.studyinstanceuid!=self.case2.studyinstanceuid:
            raise Exception('A Case Comparison must reference the same case: '+self.case1.case_name, self.case2.case_name, ' , StudyInstanceUIDs: ', self.case1.studyinstanceuid, self.case2.studyinstanceuid)

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


class HausdorffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'HD'
        self.unit = '[mm]'

    def get_val(self, geo1, geo2, dcm=None, string=False):
        m = utils.hausdorff(geo1, geo2)
        return "{:.2f}".format(m) if string else m


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
        from LazyLuna.Views import SAX_T1_PRE_View
        self.view = SAX_T1_PRE_View()
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