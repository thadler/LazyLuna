from time import time

import numpy as np
from scipy.ndimage import morphology
from shapely.geometry import Polygon, MultiPolygon, LineString, GeometryCollection, Point, MultiPoint, shape
from skimage.measure import find_contours
from rasterio import features

from PIL import Image, ImageDraw
from descartes import PolygonPatch
import matplotlib.pyplot as plt


##################
# Mask functions #
##################

def to_mask(polygons, height, width):
    """Convert to mask (Origin (0.0, 0.0))
    
    Note:
        rasterio.features.rasterize(shapes, out_shape=None, fill=0, out=None, transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        all_touched=False, merge_alg=MergeAlg.replace, default_value=1, dtype=None)
        For Origin (-0.5, -0.5) apply Affine Transformation (1.0, 0.0, -0.5, 0.0, 1.0, -0.5)
        https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html#rasterio.features.rasterize
        
    Args:
        polygons (shapely.geometry. Polygon | Multipolygon): geometry to be burned into mask
        height (int): output mask height
        width (int):  output mask width
        
    Returns:
        ndarray (2D array of np.uint8): binarized mask of polygon
    """
    if not isinstance(polygons, list):
        if isinstance(polygons, Polygon) or isinstance(polygons, MultiPolygon): polygons = [polygons]
        else: raise Exception('to_mask accepts a List of Polygons or Multipolygons')
    if len(polygons) > 0:
        try: mask = features.rasterize(polygons, out_shape=(height, width), dtype=np.uint8)
        except Exception as e:
            mask = np.zeros((height, width), np.uint8)
            print(str(e) + ', returning empty mask.')
    else: mask = np.zeros((height, width), np.uint8)
    return mask



def to_polygon(mask):
    """Convert mask to Polygons (Origin (0.0, 0.0))
    
    Note:
        rasterio.features.shapes(source, mask=None, connectivity=4, transform=Affine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0))
        For Origin (-0.5, -0.5) apply Polygon Transformation -0.5 for all xy
        https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html#rasterio.features.shapes
        
    Args:
        mask (ndarray (2D array of np.uint8): binary mask
        
    Returns:
        MultiPolygon | Polygon: Geometries extracted from mask, empty Polygon if empty mask
    """
    polygons = []
    for geom, val in features.shapes(mask):
        if val:
            polygon = shape(geom)
            if polygon.geom_type == 'Polygon' and polygon.is_valid: polygons.append(polygon)
            else: print('Ignoring GeoJSON with cooresponding shape: ' + 
                      str(polygon.geom_type) + ' | Valid: ' + str(polygon.is_valid))
    return MultiPolygon(polygons) if len(polygons)>0 else Polygon()#polygons[0]



####################
# Metric functions #
####################

# works for Polygons, Multipolygons, GeometryCollections (containing LineStrings)
def dice(geo1, geo2):
    if geo1.is_empty and geo2.is_empty: return 100.0
    overlap = geo1.intersection(geo2)
    return 100.0 * (2*overlap.area) / (geo1.area + geo2.area)

def hausdorff(geo1, geo2):
    if geo1.is_empty and geo2.is_empty: return 0.0
    return geo1.hausdorff_distance(geo2)


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
    ax.add_patch(PolygonPatch(geo.buffer(0), color=c, ec=ec, alpha=alpha))
        
def plot_points(ax, points, c='w', marker='x', s=None):
    if points.geom_type=='Point': # case: points is really just point
        ax.scatter(points.x, points.y, c=c, marker=marker, s=s)
        return
    xs, ys = [point.x for point in points.geoms], [point.y for point in points.geoms]
    ax.scatter(xs, ys, c=c, marker=marker, s=s)
    
    
##############################
## Spatial Dicom Operations ##
##############################
def transform_ics_to_rcs(dcm, arr_points=None):
    '''
    ics = image coordinate system (tupel of x-, y-values in units of pixel in dicom pixel data x = column, y = row)
    rcs = reference coordinate system (standard to store points in dicom tags)
    Function to transform ics -> rcs in dependence of arr_points
    :param dcm: object - pydicom object
    :param arr_points: array - nx2 array with x and y values (units of pixels) of the points in the dicom image plane for conversion points to
    :return: list of lists - 1 x n x 3
    '''
    # conversion as described in https://dicom.innolitics.com/ciods/rt-dose/roi-contour/30060039/30060040/30060050
    # modified for inversion purpose: P = Mx + S / x = M^-1(P-S)
    matrix = np.zeros((3, 3))
    # read in relevant dicom tags
    image_position   = np.asarray(dcm[0x0020, 0x0032].value, np.double)
    direction_cosine = np.asarray(dcm[0x0020, 0x0037].value, np.double)
    pixel_spacing    = np.asarray(dcm[0x0028, 0x0030].value, np.double)
    # create the matrix
    matrix[:3,0] = direction_cosine[:3]
    matrix[:3,1] = direction_cosine[3:6]
    orthogonal   = np.cross(direction_cosine[0:3], direction_cosine[3:])
    matrix[:3,2] = orthogonal / np.linalg.norm(orthogonal)
    # ics -> rcs
    vector = np.zeros((arr_points.shape[0], 3))
    vector[:, 1] = arr_points[:, 0] * pixel_spacing[0]
    vector[:, 0] = arr_points[:, 1] * pixel_spacing[1]
    product = np.transpose(np.dot(matrix, np.transpose(vector))) # x y z 1
    product = np.add(product[:, 0:3], image_position.reshape((1, 3)))
    return product