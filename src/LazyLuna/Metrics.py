import traceback
from functools import wraps
import numpy as np

from LazyLuna import utils

##########################################################################################
##########################################################################################
## Metrics refer to all quantitative results for individual images or image comparisons ##
##########################################################################################
##########################################################################################

# decorator function for exception handling
def Metrics_exception_handler(f):
    @wraps(f)
    def inner_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f.__name__ + ' failed to calculate the metric value. Returning np.nan. Error traceback:')
            print(traceback.format_exc())
            return np.nan
    return inner_function


class Metric:
    """Metric is an abstract class for metric value calculations

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        self.set_information()

    def set_information(self):
        """Sets name and unit"""
        self.name = ''
        self.unit = '[?]'
    @Metrics_exception_handler
    def get_val(self, geo1, geo2, string=False):
        """Returns metric value

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            
        Returns:
            float | str: Metric value
        """
        pass


class DiceMetric(Metric):
    """DiceMetric for metric value calculation in percent (in [0, 100])

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'DSC'
        self.unit = '[%]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        """Gets Dice percentage in [0,100]

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            string (bool):           return string of float with 2 decimal places
            
        Returns:
            float | str: Dice 
        """
        m = utils.dice(geo1, geo2)
        return "{:.2f}".format(m) if string else m


class AreaDiffMetric(Metric):
    """Area Difference calculation

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'AreaDiff'
        self.unit = '[cm²]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        """Returns area difference of geometries in cm²

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            dcm (shapely.geometry):  dicom dataset with pixel spacing and slice thickness
            string (bool):           return string of float with 2 decimal places
            
        Returns:
            float | str: area difference in cm²
        """
        pw, ph = dcm.PixelSpacing
        m = (geo1.area - geo2.area) * (pw*ph) / 100.0
        return "{:.2f}".format(m) if string else m


class HausdorffMetric(Metric):
    """Hausdorff Distance calculation

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'HD'
        self.unit = '[mm]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        """Returns Hausdorff distance of geometries in mm

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            dcm (shapely.geometry):  dicom dataset with pixel spacing
            string (bool):           return string of float with 2 decimal places
            
        Returns:
            float | str: HD in mm
        """
        pw, ph = dcm.PixelSpacing
        m = ph * utils.hausdorff(geo1, geo2)
        return "{:.2f}".format(m) if string else m


class mlDiffMetric(Metric):
    """Millilitre difference calculation

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'millilitre'
        self.unit = '[ml]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        """Returns millilitre difference of geometries in ml

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            dcm (shapely.geometry):  dicom dataset with pixel spacing
            string (bool):           return string of float with 2 decimal places
            
        Returns:
            float | str: millilitre difference in ml
        """
        pw, ph = dcm.PixelSpacing; vd = dcm.SliceThickness
        m      = (pw*ph*vd/1000.0) * (geo1.area - geo2.area)
        return "{:.2f}".format(m) if string else m
    
    
class absMlDiffMetric(Metric):
    """Absolute millilitre difference calculation

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'absolute millilitre'
        self.unit = '[ml]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, dcm=None, string=False):
        """Returns absolute millilitre difference of geometries in ml

        Args:
            geo1 (shapely.geometry): first object for comparison
            geo2 (shapely.geometry): second object for comparison
            dcm (shapely.geometry):  dicom dataset with pixel spacing
            string (bool):           return string of float with 2 decimal places
            
        Returns:
            float | str: absolute millilitre difference in ml
        """
        pw, ph = dcm.PixelSpacing; vd = dcm.SliceThickness
        m      = np.abs((pw*ph*vd/1000.0) * (geo1.area - geo2.area))
        return "{:.2f}".format(m) if string else m


############################
# Mapping Specific Metrics #
############################

class T1AvgDiffMetric(Metric):
    """Average T1 difference values of pixels

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'T1AVG'
        self.unit = '[ms]'

    @Metrics_exception_handler
    def get_val(self, geo1, geo2, img1, img2, string=False):
        """Returns average T1 difference of pixels in geometry

        Args:
            geo1 (shapely.geometry):    first object for comparison
            geo2 (shapely.geometry):    second object for comparison
            img1 (2D ndarray of float): normalized T1 image
            img2 (2D ndarray of float): normalized T1 image
            string (bool):              return string of float with 2 decimal places
            
        Returns:
            float | str: Average T1 difference of pixels in geometry
        """
        # imgs = get_img (d,0,True,False)
        h,     w     = img1.shape
        mask1, mask2 = utils.to_mask(geo1,h,w).astype(bool), utils.to_mask(geo2,h,w).astype(bool)
        myo1_vals, myo2_vals = img1[mask1], img2[mask2]
        global_t1_1 = np.mean(myo1_vals)
        global_t1_2 = np.mean(myo2_vals)
        m           = global_t1_1 - global_t1_2
        return "{:.2f}".format(m) if string else m
        

class T1AvgReaderMetric(Metric):
    """Average T1 pixel value for geometry

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'T1AVG'
        self.unit = '[ms]'

    @Metrics_exception_handler
    def get_val(self, geo, img, string=False):
        """Returns average T1 value of pixels in geometry

        Args:
            geo (shapely.geometry):    contour
            img (2D ndarray of float): normalized T1 image
            string (bool):             return string of float with 2 decimal places
            
        Returns:
            float | str: Average T1 value of pixels in geometry
        """
        # imgs = get_img (d,0,True,False)
        h, w = img.shape
        mask = utils.to_mask(geo, h,w).astype(bool)
        myo_vals  = img[mask]
        global_t1 = np.mean(myo_vals)
        m         = global_t1
        return "{:.2f}".format(m) if string else m
        
        
class AngleDiffMetric(Metric):
    """Angle difference calculation

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()

    def set_information(self):
        self.name = 'AngleDiff'
        self.unit = '[°]'

    @Metrics_exception_handler
    def get_val(self, anno1, anno2, string=False):
        """Returns angle difference of sax_ref to lv_endo between anno1 and anno2

        Args:
            anno1 (Annotation): first annotation
            anno2 (Annotation): second annotation
            string (bool):      return string of float with 2 decimal places
            
        Returns:
            float | str: Angle differences of sax_ref to lv_endo between anno1 and anno2
        """
        ext1    = anno1.get_point('sax_ref')
        lv_mid1 = anno1.get_contour('lv_endo').centroid
        ext2    = anno2.get_point('sax_ref')
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
    """Average difference of T2 values of pixels in geometry

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()
    def set_information(self):
        self.name = 'T2AVG'
        self.unit = '[ms]'
    
class T2AvgReaderMetric(T1AvgReaderMetric):
    """Average T2 pixel value for geometry

    Attributes:
        name (str): metric name for display
        unit (str): unit name for display
    """
    def __init__(self):
        super().__init__()
    def set_information(self):
        self.name = 'T2AVG'
        self.unit = '[ms]'
