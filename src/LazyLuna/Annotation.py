import pickle
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, MultiPoint
from LazyLuna import utils
from shapely.affinity import scale


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
