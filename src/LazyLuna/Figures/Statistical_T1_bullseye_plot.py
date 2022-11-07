import os
import traceback

import matplotlib.pyplot as plt
from matplotlib import colors, cm
from matplotlib import path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from shapely.geometry import Polygon, Point
import numpy as np
import pandas

from LazyLuna.Figures.Visualization import *
        

class Statistical_T1_bullseye_plot(Visualization):
    def set_values(self, view, cases, canvas):
        self.cases  = cases
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def plot_polygon(self, ax, poly, **kwargs):
        p = path.Path.make_compound_path(path.Path(np.asarray(poly.exterior.coords)[:, :2]), *[path.Path(np.asarray(ring.coords)[:, :2]) for ring in poly.interiors])
        collection = PatchCollection([PathPatch(p, **kwargs)], **kwargs)
        ax.add_collection(collection, autolim=True)
        return collection

    def write_val(self, ax, mean, std, x, y):
        mean, std = '{:.1f}'.format(float(mean)), '({:.1f})'.format(float(std))
        ax.annotate(mean + '\n' + str(std), xy = (x,y), xytext = (x,y), textcoords = 'data',
                    bbox = dict(boxstyle='round', fc='w', edgecolor='w'), size = 10, 
                    horizontalalignment = 'center', verticalalignment = 'center')
        
    def segment(self, center, st_angle, end_angle, radius_st, radius_end, steps=500):
        def polar_p(op, a,  dist): # origin point, angle, distance
            return [op.x + dist*-np.sin(np.radians(a)), op.y + dist*-np.cos(np.radians(a))]
        step_angle_width = (end_angle - st_angle) / steps
        segment_vertices = [polar_p(center, st_angle, radius_st), polar_p(center, st_angle, radius_end)]
        for step in range(1, steps): 
            segment_vertices.append((polar_p(center, st_angle + step*step_angle_width, radius_end)))
        segment_vertices.extend([polar_p(center, end_angle, radius_end), polar_p(center, end_angle, radius_st)])
        for step in range(1, steps): 
            segment_vertices.append((polar_p(center, end_angle-step*step_angle_width, radius_st)))
        segment_vertices.append((polar_p(center, st_angle, radius_st)))
        return Polygon(segment_vertices)
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        """Calculates a bullseye plot for cases in T1 mapping view
        
        Note:
            requires setting values first:
            - self.set_values(View, cases, canvas)
        
        Args:
            None (works with the cases in set values)
        """
        self.clear()
        collecting_means = []
        collecting_stds  = []
        for case in self.cases:
            cat         = case.categories[0]
            means, stds = cat.calc_mapping_aha_model()
            means = np.concatenate((means[0],means[1],means[2]))
            stds  = np.concatenate((stds[0], stds[1], stds[2]))
            collecting_means.append(means)
            collecting_stds .append(stds)
        means = np.mean(np.asarray(collecting_means), axis=0)
        stds  = np.mean(np.asarray(collecting_stds),  axis=0)
        
        cmap=plt.cm.bwr
        norm = colors.Normalize(vmin=np.min(means), vmax=np.max(means))
        
        ax = self.subplots(1,1); ax.imshow(np.ones((240,280)), vmin=0, vmax=1, cmap='gray'); ax.axis('off')

        # plot segments with colors
        center = Point(120,120)
        basal_segments = [self.segment(center, -30+60*i, -30+60*(i+1), 80, 110) for i in range(6)]
        midv_segments  = [self.segment(center, -30+60*i, -30+60*(i+1), 50, 80)  for i in range(6)]
        apex_segments  = [self.segment(center, -45+90*i, -45+90*(i+1), 20, 50)  for i in range(4)]
        segments = basal_segments + midv_segments + apex_segments
        for i_p, p in enumerate(segments): self.plot_polygon(ax, p, color=cmap(norm(means[i_p])), ec='k', lw=2.5)
        cbaxes = self.add_axes([0.79, 0.24, 0.03, 0.5])
        cb = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=ax, cax=cbaxes)

        # write values onto segment patches # (basal, midv, apex)
        xs = [120,38,38,120,202,202, 120,63,63,120,178,178, 120,85,120,155]
        ys = [25,71,169,215,169,71,  55,90,150,185,150,90,  85,120,155,120]
        for mean,std, x,y in zip(means, stds, xs,ys): self.write_val(ax, mean, std, x, y)
        
        ax.set_title('Average AHA Model [ms]: '+self.cases[0].reader_name)
        self.canvas.draw()
    