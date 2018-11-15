#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt


n = 2  # number of points in each direction (n**2 total points). Must be even to maintain periodicity
nbins = 101  # must be odd to center the pattern at 0
x = np.zeros([n**2, 2])
lxy = 4.5  # distance between hexagon points
lz = 4.5  # distance between points vertically
theta = 60 * (np.pi / 180)
for i in range(n):
	x[i*n:(i + 1)*n, 0] = np.linspace(0, lxy*(n-1), n) + (i % 2)*lxy*np.cos(theta)
	x[i*n:(i + 1)*n, 1] = i*lz

# Show some periodic copies of the unit cell

fig, ax = plt.subplots()
ax.set_aspect(1)

ax.scatter(x[:, 0], x[:, 1], label='Original Unit Cell')
ax.scatter(x[:, 0] + lxy*n, x[:, 1] + lz*n)
ax.scatter(x[:, 0], x[:, 1] + lz*n)
ax.scatter(x[:, 0] + lxy*n, x[:, 1])
ax.set_xlabel('$x$-positions ($\AA$)')
ax.set_ylabel('$z$-positions ($\AA$)')
ax.legend()

hist_range = [[0, n*lxy], [0, lz*n]]  # bounds of unit cell

H, xedges, yedges = np.histogram2d(x[:, 0], x[:, 1], bins=nbins, range=hist_range)
X = [(xedges[i - 1] + xedges[i])/2 for i in range(1, len(xedges))]
Y = [(xedges[i - 1] + xedges[i])/2 for i in range(1, len(xedges))]

# structure factor calculation
xbin = xedges[1] - xedges[0]
ybin = yedges[1] - yedges[0]
ft = np.fft.fftn(H)
sf = (ft * ft.conjugate()).real
freq_x = np.fft.fftfreq(len(X), d=xbin)
freq_y = np.fft.fftfreq(len(Y), d=ybin)
ndx_x = np.argsort(freq_x)
ndx_y = np.argsort(freq_y)
freq_x = freq_x[ndx_x]
freq_y = freq_y[ndx_y]

sf = sf[ndx_x, :]
sf = sf[:, ndx_y]

freq_x *= 2*np.pi
freq_y *= 2*np.pi

fig, ax = plt.subplots()

ax.contourf(freq_x, freq_y, sf, 100, cmap='Greys') # gives diamonds

# imshow has best interpolation options. imshow also inverts the data, so the transpose is plotted
#ax.imshow(sf.T, interpolation='Gaussian', extent=[freq_x[0], freq_x[-1], freq_y[0], freq_y[-1]], cmap='Greys')

# plt just one hexagon by restricting axis limits
plt.xlim(-1.8, 1.8)
plt.ylim(-1.8, 1.8)
plt.xlabel('$q_x$', fontsize=20)
plt.ylabel('$q_z$', fontsize=20)
plt.gcf().get_axes()[0].set_aspect('equal')
plt.gcf().get_axes()[0].tick_params(labelsize=18)
plt.tight_layout()
#plt.savefig('hexagonal_ft.pdf')
plt.show()
