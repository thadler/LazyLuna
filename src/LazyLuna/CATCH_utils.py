from time import time

import numpy as np
from skimage.transform import resize
from scipy.ndimage import morphology
from shapely.geometry import Polygon, MultiPolygon, LineString, GeometryCollection, Point, MultiPoint, shape
from skimage.measure import find_contours
from rasterio import features

import cv2
from PIL import Image, ImageDraw
from descartes import PolygonPatch
import matplotlib.pyplot as plt



def get_polygons_from_geometry(geo):
    if isinstance(geo, list):       geo = MultiPolygon(geo)
    if geo.is_empty or geo.area==0: geo = MultiPolygon([])
    if isinstance(geo, Polygon):    geo = MultiPolygon([geo])
    return list(geo)

def bounding_box(geo):
    return geo.bounds


##################
# Mask functions #
##################

def to_mask(polygons, height, width):
    """
    Convert to mask (Origin (0.0, 0.0))
    rasterio.features.rasterize(shapes, out_shape=None, fill=0, out=None, transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    all_touched=False, merge_alg=MergeAlg.replace, default_value=1, dtype=None)
    For Origin (-0.5, -0.5) apply Affine Transformation (1.0, 0.0, -0.5, 0.0, 1.0, -0.5)
    https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html#rasterio.features.rasterize
    """
    if not isinstance(polygons, list):
        if isinstance(polygons, Polygon) or isinstance(polygons, MultiPolygon):polygons = [polygons]
        else: raise Exception('CATCH.to_mask accepts a List of Polygons or Multipolygons')
    if len(polygons) > 0:
        try: mask = features.rasterize(polygons, out_shape=(height, width), dtype=np.uint8)
        except Exception as e:
            mask = np.zeros((height, width), np.uint8)
            print(str(e) + ', returning empty mask.')
    else: mask = np.zeros((height, width), np.uint8)
    return mask



def to_polygon(mask):
    """
    Convert to Polygons (Origin (0.0, 0.0))
    rasterio.features.shapes(source, mask=None, connectivity=4, transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0))
    For Origin (-0.5, -0.5) apply Polygon Transformation -0.5 for all xy
    https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html#rasterio.features.shapes
    """
    polygons = []
    for geom, val in features.shapes(mask):
        if val:
            polygon = shape(geom)
            print(polygon.geom_type)
            if polygon.geom_type == 'Polygon' and polygon.is_valid: polygons.append(polygon)
            else: print('Ignoring GeoJSON with cooresponding shape: ' + 
                      str(polygon.geom_type) + ' | Valid: ' + str(polygon.is_valid))
    
    return MultiPolygon(polygons) if len(polygons)>0 else Polygon()#polygons[0]





####################
# Metric functions #
####################
def mask_dice(geo1, geo2, debug=False):
    if debug: st = time()
    mask1, mask2 = geo2mask(geo1, 200, 200, res=8), geo2mask(geo2, 200, 200, res=8)
    area1, area2 = np.sum(mask1), np.sum(mask2)
    overlap = np.sum(mask1 & mask2)
    dice = 2*overlap / (area1 + area2)
    if debug: print("Mask dice took: ", time()-st)
    return dice
    
# works for Polygons, Multipolygons, GeometryCollections (containing LineStrings)
def dice(geo1, geo2, debug=False):
    if debug: st = time()
    area1, area2 = geo1.area, geo2.area
    if area1==0==area2:                return 100.0
    overlap = geo1.intersection(geo2)
    dice = 100.0 * 2*overlap.area / (area1 + area2)
    if debug: print("Dice took: ", time()-st)
    return dice

def hausdorff(geo1, geo2):
    # setting them to nan only causes issues
    #if geo1.is_empty and not geo2.is_empty: return np.nan
    #if not geo1.is_empty and geo2.is_empty: return np.nan
    return geo1.hausdorff_distance(geo2)

def mask_asd(geo1, geo2, voxel_sizes, connectivity=1, debug=False):
    if debug: st = time()
    area1, area2 = geo1.area, geo2.area
    if area1==0==area2: return 0
    if area1==0 or area2==0: return np.nan
    mask1, mask2 = geo2mask(geo1, 200, 200, res=8), geo2mask(geo2, 200, 200, res=8)
    input_1 = np.atleast_1d(mask1.astype(np.bool8))
    input_2 = np.atleast_1d(mask2.astype(np.bool8))
    conn = morphology.generate_binary_structure(input_1.ndim, connectivity)
    S_1 = input_1 ^ morphology.binary_erosion(input_1, conn)
    S_2 = input_2 ^ morphology.binary_erosion(input_2, conn)
    dta = morphology.distance_transform_edt(~S_1, voxel_sizes)
    dtb = morphology.distance_transform_edt(~S_2, voxel_sizes)
    surface_distance = np.concatenate([np.ravel(dta[S_2!=0]), np.ravel(dtb[S_1!=0])])
    asd = surface_distance.mean()
    if debug: print('Mask ASD took: ', time()-st)
    return asd

#######################
# geometry operations #
#######################
def get_overlapping_geometry(geo1, geo2):
    overlap = geo1.intersection(geo2)
    if overlap.is_empty: overlap = Polygon([])
    return overlap

def get_geometry_diff1(geo1, geo2):
    diff = geo1.difference(geo2)
    return diff
    
def get_geometry_diff2(geo1, geo2):
    return get_geometry_diff1(geo2, geo1)

# convenience function
def get_geometry_comparison(geo1, geo2):
    overlapping = get_overlapping_geometry(geo1, geo2)
    diff1 = get_geometry_diff1(geo1, geo2)
    diff2 = get_geometry_diff2(geo1, geo2)
    return overlapping, diff1, diff2



#####################
# plotting funtions #
#####################
def plot_mask(mask):
    fig, ax = plt.subplots(1,1,figsize=(7,7))
    ax.imshow(mask, interpolation='none')
    
def plot_masks(masks):
    fig, axes = plt.subplots(1,len(masks),figsize=(15,15))
    for i in range(len(masks)): axes[i].imshow(masks[i], interpolation='none')
    plt.show()
    
def plot_mask_comparison(mask1, mask2):
    h,w = mask1.shape
    mask_comparison = np.zeros((h,w,3))
    mask_comparison[:,:,0] = np.logical_and(mask1==1, mask2==0)
    mask_comparison[:,:,2] = np.logical_and(mask2==1, mask1==0)
    mask_comparison[:,:,1] = np.logical_and(mask1==1, mask2==1)
    fig, axes = plt.subplots(1,3,figsize=(15,15))
    axes[0].imshow(mask1,           interpolation='none')
    axes[1].imshow(mask2,           interpolation='none')
    axes[2].imshow(mask_comparison, interpolation='none')
    
def plot_outlines(ax, geo, edge_c=(1,1,1,1.0)):
    patch = PolygonPatch(geo, facecolor=(0,0,0,0.0), edgecolor=edge_c)
    ax.add_patch(patch)
        
def plot_geo_face_comparison(ax, geo1, geo2, colors=['g','r','b'],alpha=0.4):
    agreed, diff1, diff2 = get_geometry_comparison(geo1, geo2)
    if agreed.geom_type=='GeometryCollection' and not agreed.is_empty:
        agreed = MultiPolygon([g for g in agreed.geoms if g.area!=0])
    if diff1.geom_type=='GeometryCollection' and not diff1.is_empty:
        diff1 = MultiPolygon([g for g in diff1.geoms if g.area!=0])
    if diff2.geom_type=='GeometryCollection' and not diff2.is_empty:
        diff2 = MultiPolygon([g for g in diff2.geoms if g.area!=0])
    for i, thing in enumerate([agreed, diff1, diff2]):
        if not thing.is_empty:
            ax.add_patch(PolygonPatch(thing.buffer(0), color=colors[i], alpha=alpha))
    
def plot_geo_face(ax, geo, c='r', ec=None, alpha=0.4):
    # buffer is a hack, make sure contours are in clockwise or counter cw direction
    #ax.add_patch(PolygonPatch(geo.buffer(0), color=c, alpha=alpha))
    ax.add_patch(PolygonPatch(geo, color=c, ec=c, alpha=alpha))
        
def plot_points(ax, points, c='w', marker='x'):
    if points.geom_type=='Point': # case: points is really just point
        ax.scatter(points.x, points.y, c='w', marker='x')
        return
    xs, ys = [point.x for point in points], [point.y for point in points]
    ax.scatter(xs, ys, c='w', marker='x')