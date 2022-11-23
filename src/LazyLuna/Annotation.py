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
        self.filepath = filepath
        self.sop = sop
        self.h,  self.w  = self.get_image_size()
        self.ph, self.pw = self.get_pixel_size()

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
        
        Args:
            cont_name (str): contour to be verified
            
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
        
        Args:
            cont_name (str): contour name
            
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
        
        Args:
            point_name (str): point name
            
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
        
        Args:
            point_name (str): point name
            
        Returns:
            shapely.geometry: point if available, else empty shapely.geometry.Point
        """
        if self.has_point(point_name): return self.anno[point_name]['cont']
        else:                          return Point()

    def get_cont_as_mask(self, cont_name):
        """Transforms contour to binarized mask
        
        Args:
            cont_name (str): contour name
            
        Returns:
            ndarray (2D array of np.uint8): binarized mask
        """
        if not self.has_contour(cont_name): return np.zeros((self.h, self.w))
        mp = self.get_contour(cont_name)
        if not mp.geom_type=='MultiPolygon': mp = MultiPolygon([mp])
        return utils.to_mask(mp, self.h, self.w)
    
    def get_image_size(self):
        """Returns the image height and width of the referenced dicom image
        
        Returns:
            (int, int): image size
        """
        try: h, w = self.anno[next(iter(self.anno))]['imageSize'] # next iter provides fast access to first dict key
        except: h, w = -1,-1
        return (h, w)
    
    def get_pixel_size(self):
        """Returns the pixel height and width
        
        Returns:
            (float, float): pixel size
        """
        try: ph, pw = self.anno[next(iter(self.anno))]['pixelSize']
        except: ph, pw = -1,-1
        return (ph, pw)

    ######################
    # LAX CINE functions #
    ######################
    def length_LV(self):
        """Left ventricular length determined by the lv extent points
        
        Returns:
            float: length of left ventricle
        """
        if not self.has_point('lv_extent'): return np.nan
        extent = self.get_point('lv_extent')
        pw, ph = self.ph, self.pw
        lv_ext1, lv_ext2, apex = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([lv_ext1, lv_ext2]).centroid
        dist = mitral.distance(apex)
        return dist
    
    def length_LA(self):
        """Left atrial length determined by the la extent points
        
        Returns:
            float: length of left atrium
        """
        if not self.has_point('la_extent'): return np.nan
        extent = self.get_point('la_extent')
        pw, ph = self.ph, self.pw
        la_ext1, la_ext2, ceil = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([la_ext1, la_ext2]).centroid
        dist = mitral.distance(ceil)
        return dist
    
    def length_RA(self):
        """Right atrial length determined by the ra extent points
        
        Returns:
            float: length of right atrium
        """
        if not self.has_point('ra_extent'): return np.nan
        extent = self.get_point('ra_extent')
        pw, ph = self.ph, self.pw
        ra_ext1, ra_ext2, ceil = scale(extent, xfact=pw, yfact=ph)
        mitral = MultiPoint([ra_ext1, ra_ext2]).centroid
        dist = mitral.distance(ceil)
        return dist
    
    def get_pixel_values(self, cont_name, img):
        """Returns pixel values inside the contour
        
        Args:
            cont_name (str): contour name
            img (numpy.ndarray of floats): image from which pixels are extracted
            
        Returns:
            numpy.ndarray of floats: pixel values inside contour
        """
        h, w = img.shape
        mask = self.get_cont_as_mask(cont_name)
        return img[np.where(mask!=0)]
        
    #####################
    # Mapping functions #
    #####################
    def get_angle_mask_to_middle_point(self):
        """Returns angle mask according to lv endocardial centroid
        
        Returns:
            ndarray (2D array of floats): angle mask to lv_endo centroid
        """
        h, w = self.h, self.w
        if not self.has_contour('lv_endo'): return np.ones((h,w))*np.nan
        p = self.get_contour('lv_endo').centroid
        x,y = p.x, p.y
        mask = np.zeros((self.h,self.w,3))
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

    def get_angle_mask_to_middle_point_by_reference_point(self, refpoint=None):
        """Returns angle mask according to lv endocardial centroid, rotated by the sax reference point
        
        Args:
            refpoint (float): (optional) only if sax_ref is provided by another reader
        
        Returns:
            ndarray (2D array of floats): angle mask to lv_endo centroid, rotated by sax_ref
        """
        angle_mask = self.get_angle_mask_to_middle_point()
        angle      = self.get_reference_angle(refpoint)
        angle_mask = angle_mask - angle
        angle_mask = angle_mask % 360
        return angle_mask

    def get_reference_angle(self, refpoint=None):
        """Returns reference angle
        
        Args:
            refpoint (float): (optional) only if sax_ref is provided by another reader
            
        Returns:
            float: angle of sax_ref
        """
        if not self.has_contour('lv_endo'): return np.nan
        if not self.has_point('sax_ref'): return np.nan
        mp = self.get_contour('lv_endo').centroid
        rp = self.get_point('sax_ref') if refpoint is None else refpoint
        v1 = np.array([rp.x-mp.x, rp.y-mp.y])
        v2 = np.array([1,0])
        v1_u = v1 / np.linalg.norm(v1)
        v2_u = v2 / np.linalg.norm(v2)
        angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))*180/np.pi
        return angle

    def get_myo_mask_by_angles(self, img, nr_bins=6, refpoint=None):
        """Returns dict of angle tuples to list of values inside lv_myo contour and angle limits 
        
        Note:
            The dictionary keys denote the lower and upper limit of the bin. The dictionary values are arrays of myocardial pixel values within the contour boundaries and within the angle limits of the dictionary key.
            
        Args:
            img (ndarray 2D array of floats): image from which pixels are extracted
            nr_bins (int): number of bins into which the lv_myo is divided
            refpoint (float): (optional) only if sax_ref is provided by another reader
        
        Returns:
            dict of (float, float): array of floats
        """
        h, w       = img.shape
        myo_mask   = self.get_cont_as_mask('lv_myo')
        angle_mask = self.get_angle_mask_to_middle_point_by_reference_point(refpoint)
        bins       = [i*360/nr_bins for i in range(0, nr_bins+1)]
        bin_dict   = dict()
        for i in range(nr_bins):
            low, high = bins[i], bins[i+1]
            vals = img[(low<=angle_mask) & (angle_mask<high) & (myo_mask!=0)]
            bin_dict[(low, high)] = vals
        return bin_dict
