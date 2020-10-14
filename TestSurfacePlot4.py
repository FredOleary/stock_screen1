"""
=============================================
Generate polygons to fill under 3D line graph
=============================================

Demonstrate how to create polygons which fill the space under a line
graph. In this example polygons are semi-transparent, creating a sort
of 'jagged stained glass' effect.
"""

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
from matplotlib.collections import LineCollection
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np
from datetime import timedelta
import datetime
import matplotlib.dates as mdates

fig = plt.figure()
ax = fig.gca(projection='3d')


def cc(arg):
    return mcolors.to_rgba(arg, alpha=0.6)

date_now = datetime.datetime.now()
date_array = [date_now]
for i in range(100):
    date_now += timedelta(days=1)
    date_array.append(date_now)

date_array = mdates.date2num(date_array)

xs = np.asarray(date_array)
#xs = np.arange(0, 10, 0.4)
verts = []
zs = [0.0, 1.0, 2.0, 3.0, 4.0]
for z in zs:
    ys = np.random.rand(len(xs))
    ys[0], ys[-1] = 0, 0
    verts.append(list(zip(xs, ys)))

poly = PolyCollection(verts, facecolors=[cc('r'), cc('g'), cc('b'),
                                         cc('y'), cc('b')])
poly.set_alpha(0.7)
ax.add_collection3d(poly, zs=zs, zdir='y')

date_format = mdates.DateFormatter('%D')
ax.xaxis.set_major_formatter(date_format)

ax.set_xlabel('Date/Time')
ax.set_xlim3d(xs[0], xs[len(xs)-1])
ax.set_ylabel('Z')
ax.set_ylim3d(0, 4)
ax.set_zlabel('Y')
ax.set_zlim3d(0, 1)

plt.show()
