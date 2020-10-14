# from mpl_toolkits.mplot3d import Axes3D
# import matplotlib.pyplot as plt
# from matplotlib import cm
# import numpy as np
# from sys import argv
# x = [1,2,3,4]
# y = [1,2,3,4]
# z = [3,2,3,4]
#
# fig = plt.figure()
# ax = Axes3D(fig)
# surf = ax.plot_trisurf(x, y, z, cmap=cm.jet, linewidth=0.1)
# fig.colorbar(surf, shrink=0.5, aspect=5)
# plt.show()


# Import libraries
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt

# Creating dataset
z = np.linspace(0, 50000, 100)
x = np.sin(z)
y = np.cos(z)

# Creating figyre
fig = plt.figure(figsize=(14, 9))
ax = plt.axes(projection='3d')

# Creating plot
ax.plot_trisurf(x, y, z,
                linewidth=0.2,
                antialiased=True);

# show plot
plt.show()