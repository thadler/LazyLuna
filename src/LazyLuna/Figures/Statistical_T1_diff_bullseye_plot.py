import os
import traceback

from matplotlib import gridspec, colors, cm
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection
from mpl_interactions import ioff, panhandler, zoom_factory
import matplotlib.pyplot as plt
import seaborn as sns

import shapely
from shapely.geometry import Polygon
from descartes import PolygonPatch
from scipy.stats import probplot
import numpy as np
import pandas

from LazyLuna.Tables import *
from LazyLuna.Metrics import *
from LazyLuna import utils
from LazyLuna.Figures.Visualization import *


class Statistical_T1_diff_bullseye_plot(Visualization):
    def set_values(self, view, ccs, canvas):
        self.ccs    = ccs
        self.view   = view
        self.canvas = canvas
        self.add_annotation = True
        
    def visualize(self, segBold=[], minv=None, maxv=None):
        """Plots a bullseye differences plot for case comparisons in mapping view
        
        Note:
            requires setting values first:
            - self.set_values(view, case comparisons, canvas)
        
        Args:
            None (works with case comparisons in set_values)
        """
        self.clear()
        
        collecting_means = []
        collecting_stds  = []
        for cc in self.ccs:
            cat1 = cc.case1.categories[0]
            cat2 = cc.case2.categories[0]
            means1, stds1 = cat1.calc_mapping_aha_model()
            means2, stds2 = cat2.calc_mapping_aha_model()
            means = np.concatenate((means1[0]-means2[0],
                                    means1[1]-means2[1],
                                    means1[2]-means2[2]))
            stds  = np.concatenate((stds1[0]-stds2[0], 
                                    stds1[1]-stds2[1], 
                                    stds1[2]-stds2[2]))
            collecting_means.append(means)
            collecting_stds.append(stds)
        means = np.mean(np.asarray(collecting_means), axis=0)
        stds  = np.mean(np.asarray(collecting_stds),  axis=0)
        
        ax = self.subplots(1,1, subplot_kw=dict(projection='polar'))
        cmap = plt.cm.PRGn
        if minv is None: minv=np.min(means)-5
        if maxv is None: maxv=np.max(means)+5
        minv, maxv = min([minv, -maxv]), max([maxv, -minv])
        norm = colors.Normalize(vmin=minv, vmax=maxv)
        means = np.array(means).ravel()
        stds  = np.array(stds) .ravel()
        theta = np.linspace(0, 2*np.pi, 768)
        r = np.linspace(0.2, 1, 4)
        linewidth = 2
        for i in range(r.shape[0]): ax.plot(theta, np.repeat(r[i], theta.shape), '-k', lw=linewidth)
        for i in range(6):
            theta_i = i * 60 * np.pi/180
            ax.plot([theta_i, theta_i], [r[1], 1], '-k', lw=linewidth)
        for i in range(4):
            theta_i = i * 90 * np.pi/180 - 45*np.pi/180
            ax.plot([theta_i, theta_i], [r[0], r[1]], '-k', lw=linewidth)
        r0 = r[2:4]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i], stds[i], i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+1 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[2],r[3]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[2],r[3]], '-k', lw=linewidth+1)
        r0 = r[1:3]
        r0 = np.repeat(r0[:,np.newaxis], 128, axis=1).T
        for i in range(6):
            theta0 = theta[i*128:i*128+128] + 60*np.pi/180 #+ 60*np.pi/180
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax, means[i+6], stds[i+6],  i*60*np.pi/180 + 30*np.pi/180 + 60*np.pi/180, np.mean(r0[0]))
            z = np.ones((128,2)) * means[i+6]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+7 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[1],r[2]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[1],r[2]], '-k', lw=linewidth+1)
        r0 = r[0:2]
        r0 = np.repeat(r0[:,np.newaxis], 192, axis=1).T
        for i in range(4):
            theta0 = theta[i*192:i*192+192] + 45*np.pi/180  #+ 90*np.pi/180 
            theta0 = np.repeat(theta0[:,np.newaxis], 2, axis=1)
            self.write_val(ax,means[i+12], stds[i+12], i*90*np.pi/180 + 90*np.pi/180, np.mean(r0[0]))
            z = np.ones((192,2)) * means[i+12]
            ax.pcolormesh(theta0, r0, z, cmap=cmap, norm=norm)
            if i+13 in segBold:
                ax.plot(theta0, r0, '-k', lw=linewidth+2)
                ax.plot(theta0[0 ], [r[0],r[1]], '-k', lw=linewidth+1)
                ax.plot(theta0[-1], [r[0],r[1]], '-k', lw=linewidth+1)
        ax.set_ylim([0, 1])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        axp    = ax.imshow(np.random.randint(0, 100, (100, 100)))
        cbaxes = self.add_axes([0.78, 0.1, 0.03, 0.8])  # This is the position for the colorbar
        cb     = self.colorbar(cm.ScalarMappable(cmap=cmap, norm=norm), ax=axp, cax=cbaxes)
        ax.set_title('Averaged AHA Difference Model: '+self.ccs[0].case1.reader_name+' - '+self.ccs[0].case2.reader_name)
        
        self.canvas.draw()

    def write_val(self, ax, mean, std, angle, y):
        mean = "{:.1f}".format(float(mean))
        std  = "{:.1f}".format(float(std))
        ax.annotate(str(mean) + '\n(' + str(std) + ')',
                xy                  = (angle, y), # theta, radius
                xytext              = (angle, y), # fraction, fraction
                textcoords          = 'data',     #'figure fraction',
                bbox                = dict(boxstyle="round", fc="1.0", edgecolor="1.0"),
                horizontalalignment = 'center',
                size                = 10,
                verticalalignment   = 'center',
                )
        