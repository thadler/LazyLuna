import traceback
import numpy as np

from LazyLuna import utils

##########################################################################################
##########################################################################################
## Metrics refer to all quantitative results for individual images or image comparisons ##
##########################################################################################
##########################################################################################

# decorator function for exception handling
def Metrics_exception_handler(f):
    def inner_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f.__name__ + ' failed to calculate the metric value. Returning np.nan. Error traceback:')
            print(traceback.format_exc())
            return np.nan
    return inner_function


class Metric:
    def __init__(self):
        self.set_information()

    def set_information(self):
        self.name = ''
        self.unit = '[?]'
    @Metrics_exception_handler
    def get_val(self, geo1, geo2, string=False):
        pass


class DiceMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'DSC'
        self.unit = '[%]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        m = utils.dice(geo1, geo2)
        return "{:.2f}".format(m) if string else m


class AreaDiffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'AreaDiff'
        self.unit = '[cm²]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        pw, ph = dcm.PixelSpacing; vd = dcm.SliceThickness
        m = (geo1.area - geo2.area) * (pw*ph) / 100.0
        return "{:.2f}".format(m) if string else m


class HausdorffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'HD'
        self.unit = '[mm]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        pw, ph = dcm.PixelSpacing
        m = ph * utils.hausdorff(geo1, geo2)
        return "{:.2f}".format(m) if string else m


class mlDiffMetric(Metric):
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'millilitre'
        self.unit = '[ml]'

    @Metrics_exception_handler
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

    @Metrics_exception_handler
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

    @Metrics_exception_handler
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

    @Metrics_exception_handler
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
