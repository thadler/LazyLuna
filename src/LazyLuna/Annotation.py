import pickle
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, MultiPoint
from LazyLuna import utils
from shapely.affinity import scale


class Annotation:
    """Annotation is an interface class to LazyLuna annotation files.

    Annotation offers:
        - plot functions for points, contours and face surfaces (anno.plot_...)
        - has and get functions for points and contours
        - other auxiliary functions

    Args:
        filepath (str): The filepath to the annotation
        sop (str): SOPInstanceUID of the Dicom image to which the annotation pertains

    Attributes:
        anno (dict of str: {'cont': shapely.geometry, 
                            'contType': str, 
                            'subpixelResolution': int, 
                            'imageSize': (int,int), 
                            'pixelSize', (float,float)}): Annotation dictionary maps contour names (like 'lv_endo') to contours.
        sop (str): SOPInstanceUID of the Dicom image to which the annotation pertains
        h, w (int, int): height and width of dicom image
        ph, pw (float, float): pixel height and width
    """
    
    def __init__(self, filepath, sop=None):
        try:    self.anno = pickle.load(open(filepath, 'rb'))
        except: self.anno = dict()
        self.sop = sop
        self.h, self.w = self.image_size()
        self.ph, self.pw = self.pixel_size()

    def plot_contours(self, ax, cont_name='all', c='w', debug=False):
        """Plots contours on matplotlib axis
            
        Args:
            ax (matplotlib.pyplot.axis): Axis onto which the contours are plotted
            cont_name (str): name of the contour_type to plot. If 'all' or None all available contours are plotted
            c (str): contour color
        """
        if cont_name not in ['all', None]: 
            if self.has_contour(cont_name): utils.plot_outlines(ax, self.get_contour(cont_name), edge_c=c)
        else:
            for cname in self.available_contour_names(): utils.plot_outlines(ax, self.get_contour(cname), edge_c=c)

    def plot_points(self, ax, point_name='all', c='w', marker='x', s=None):
        """Plots points on matplotlib axis
            
        Args:
            ax (matplotlib.pyplot.axis): Axis onto which the contours are plotted
            point_name (str): name of the point_type to plot. If 'all' or None all available points are plotted
            c (str): point color
            marker (str): point symbol
        """
        if point_name not in ['all', None]:
            if self.has_point(point_name): utils.plot_points(ax, self.get_point(point_name), c=c, marker=marker, s=s)
        else:
            for p in self.available_point_names(): utils.plot_points(ax, self.get_point(p), c, marker, s)

    def plot_face(self, ax, cont_name, c='r', alpha=0.4):
        """Plots contour surface on matplotlib axis
            
        Args:
            ax (matplotlib.pyplot.axis): Axis onto which the surface is plotted
            cont_name (str): name of the contour_type to plot
            c (str): surface color
        """
        if not self.has_contour(cont_name): return
        utils.plot_geo_face(ax, self.get_contour(cont_name), c=c, ec=c, alpha=alpha)

    def plot_cont_comparison(self, ax, other_anno, cont_name, colors=['g','r','b'], alpha=0.4):
        """Plots contour comparison on matplotlib axis
            
        Args:
            ax (matplotlib.pyplot.axis): Axis onto which the comparison is plotted
            other_anno (LazyLuna.Annotation.Anntotation): The annotation to which this annotation is compared
            cont_name (str): name of the contour_type to plot
            colors (list of str): colors[0] = agreement color, colors[1] = first anno color, colors[2] = second anno color
        """
        cont1, cont2 = self.get_contour(cont_name), other_anno.get_contour(cont_name)
        utils.plot_geo_face_comparison(ax, cont1, cont2, colors=colors, alpha=alpha)

    def available_contour_names(self):
        """Accessible contour names
        
        Returns:
            list of str: available contour names
        """
        return [c for c in self.anno.keys() if self.has_contour(c)]

    def has_contour(self, cont_name):
        """has function
        
        Returns:
            bool: True if contour available, else False
        """
        if not cont_name in self.anno.keys():              return False
        if not 'cont' in self.anno[cont_name]:             return False
        a = self.anno[cont_name]['cont']
        if a.is_empty:                                     return False
        if a.geom_type not in ['Polygon', 'MultiPolygon']: return False
        return True

    def get_contour(self, cont_name):
        """getter function
        
        Returns:
            shapely.geometry: contour polygon if contour available, else empty shapely.geometry.Polygon
        """
        if self.has_contour(cont_name): return self.anno[cont_name]['cont']
        else: return Polygon()

    def available_point_names(self):
        """Accessible point names
        
        Returns:
            list of str: available point names
        """
        return [p for p in self.anno.keys() if self.has_point(p)]

    def has_point(self, point_name):
        """has function
        
        Returns:
            bool: True if point available, else False
        """
        if not point_name in self.anno.keys():         return False
        if not 'cont' in self.anno[point_name]:        return False
        a = self.anno[point_name]['cont']
        if a.is_empty:                                 return False
        if a.geom_type not in ['Point', 'MultiPoint']: return False
        return True

    def get_point(self, point_name):
        """getter function
        
        Returns:
            shapely.geometry: point if available, else empty shapely.geometry.Point
        """
        if self.has_point(point_name): return self.anno[point_name]['cont']
        else:                          return Point()

    def get_cont_as_mask(self, cont_name, h=None, w=None):
        """Transforms contour to binarized mask
        
        Returns:
            ndarray (2D array containing data with np.uint8 type)
        """
        if not self.has_contour(cont_name): return np.zeros(self.h, self.w)
        mp = self.get_contour(cont_name)
        if not mp.geom_type=='MultiPolygon': mp = MultiPolygon([mp])
        return utils.to_mask(mp, self.h, self.w)
    
    def image_size(self):
        try: h, w = self.anno[next(iter(self.anno))]['imageSize'] # next iter provides fast access to first dict key
        except: h, w = -1,-1
        return (w, h) # converter has them this way around
    
    def pixel_size(self):
        try: ph, pw = self.anno[next(iter(self.anno))]['pixelSize'] # next iter provides fast access to first dict key
        except: ph, pw = -1,-1
        return (ph, pw)

    ######################
    # LAX CINE functions #
    ######################
    def length_LV(self):
        if not self.has_point('lv_lax_extent'): return np.nan
        extent = self.get_point('lv_lax_extent')
        pw, ph = self.ph, self.pw
        lv_ext1, lv_ext2, apex = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
    
    def length_LA(self):
        if not self.has_point('laxLaExtentPoints'): return np.nan
        extent = self.get_point('laxLaExtentPoints')
        pw, ph = self.ph, self.pw
        la_ext1, la_ext2, ceil = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([la_ext1, la_ext2]).centroid
        dist = mitral.distance(ceil)
        return dist
    
    def length_RA(self):
        if not self.has_point('laxRaExtentPoints'): return np.nan
        extent = self.get_point('laxRaExtentPoints')
        pw, ph = self.ph, self.pw
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
