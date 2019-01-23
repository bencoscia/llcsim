#!/usr/bin/env python

import argparse
import numpy as np
import matplotlib.pyplot as plt
import mdtraj as md
from scipy.spatial import distance, ConvexHull
from scipy.linalg import lstsq
from llcsim.llclib import topology
import tqdm
import sqlite3 as sql
import os


def initialize():

    parser = argparse.ArgumentParser(description='Model a continuous time random walk')

    # MD trajectory control
    parser.add_argument('-t', '--trajectory', default='PR_nojump.xtc', help='Name of gromacs trajectory file. Molecules'
                                                                            'must remain whole throughout simulation')
    parser.add_argument('-g', '--gro', default='em.gro', help='Name of .gro coordinate file.')
    parser.add_argument('-r', '--residue', default='ETH', help='Name of residue whose radius we want to calculate')
    parser.add_argument('--update', action="store_true", help="update database with geometric values")

    return parser


class Geometry(object):

    def __init__(self, gro, traj, residue):
        """ Initialize object to hold description of molecular geometry

        :param gro: name of gro file describing topology of trajectory
        :param traj: gromacs trajectory files (.trr or .xtc)
        :param residue: name of residue to study (as named in .gro file)

        :type gro: str
        :type traj: str
        :type residue: str
        """

        self.residue = topology.Residue(residue)  # make object out of residue

        t = md.load(traj, top=gro)

        self.time = t.time
        self.nframes = t.n_frames  # total frames in simulation

        keep = [a.index for a in t.topology.atoms if a.residue.name == residue]  # keep indices of residue of interest

        if len(keep) == 0:
            print("Warning: No atoms selected. Did you pass the correct residue name with the -r flag?")

        self.xyz = t.xyz[:, keep, :]  # xyz coordinates

        self.nres = len(keep) // self.residue.natoms  # number of residues in system

        self.res_ndx = np.zeros([self.nres, self.residue.natoms], dtype=int)  # organize residue indices by residue
        for r in range(self.nres):
            self.res_ndx[r, :] = np.arange(r*self.residue.natoms, (r + 1)*self.residue.natoms)

        self.radius = None
        self.volume = None
        self.planarity = None
        self.ellipse_parameters = None
        self.ellipse_uncertainty = None
        self.location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))  # This script location

    def calculate_radius(self):
        """ Calculate longest atom-atom distance at each frame of trajectory
        """

        self.radius = np.zeros([self.nres, self.nframes])

        print("Calculating Maximum Pairwise radius...")
        for t in tqdm.tqdm(range(self.nframes)):  # calculate radius at each frame
            for r in range(self.nres):  # calculate radius of each residue separately
                self.radius[r, t] = distance.pdist(self.xyz[t, self.res_ndx[r, :], :]).max()

    def calculate_volume(self):
        """ Calculate volume occupied by points making up residues using a Convex Hull
        """

        self.volume = np.zeros([self.nres, self.nframes])

        print("Calculating Volume...")
        for t in tqdm.tqdm(range(self.nframes)):  # calculate radius at each frame
            for r in range(self.nres):  # calculate radius of each residue separately
                hull = ConvexHull(self.xyz[t, self.res_ndx[r, :], :])
                self.volume[r, t] = hull.volume

    def calculate_planarity(self, heavy_atoms=True):
        """ Calculate 'planarity' parameter by fitting a plane to each solute and measure the normalized sum of square
        deviations from the plane

        Calculate least squares fit parameters for z = a * x + b * y + c
        Make it a matrix problem: z = A*C where A = [x, y, 1] and C = [a, b, c]
        The exact solution is (A^T A)^-1 A^Tb (where ^T is matrix transpose and ^-1 is matrix inversion)

        :param heavy_atoms: Fit plane to heavy atoms (not H) only

        :type heavy_atoms: bool
        """

        self.planarity = np.zeros([self.nres, self.nframes])

        if heavy_atoms:

            fit_atoms = [i for i, x in enumerate(list(self.residue.names.values())) if 'H' not in x]

        else:
            fit_atoms = np.arange(len(self.residue.names))

        for t in tqdm.tqdm(range(self.nframes)):
            for r in range(self.nres):

                coords = self.xyz[t, self.res_ndx[r, fit_atoms], :]  # coordinates to which we want to fit plane
                A = np.c_[coords[:, 0], coords[:, 1], np.ones(coords.shape[0])]
                C, R, _, _ = lstsq(A, coords[:, 2])  # least squares exact calculation

                # residual, as calculated by scipy above (R) is z - AC: sum((coords[:, 2] - np.dot(A, C))**2)
                # So in words the actual z-value minus the functional evaluations at x and y all squared
                # We can convert to standard deviation by dividing by N (total atoms in fit_atoms) and then taking sqrt

                # The following calculates the residual as a function of distance from the plane
                # Can probably vectorize this pretty easily
                n = [C[0], C[1], -1]
                res = 0
                for i in fit_atoms:
                    p = self.xyz[t, self.res_ndx[r, i], :]
                    res += (np.abs(C[0]*p[0] + C[1]*p[1] - p[2] + C[2]) / np.linalg.norm(n))**2

                self.planarity[r, t] = np.sqrt(res / len(fit_atoms))

                projection = np.zeros([len(fit_atoms), 3])

                #self.planarity[r, t] = np.sqrt(R / len(fit_atoms))

                # To check that above works (mean for use with heavy_atoms = True)
                # from mpl_toolkits.mplot3d import Axes3D
                # X, Y = np.meshgrid(np.linspace(coords[:, 0].min(), coords[:, 0].max()), np.linspace(coords[:, 1].min(),
                #                                                                                     coords[:, 1].max()))
                # Z = C[0]*X + C[1]*Y + C[2]
                # fig = plt.figure()
                # ax = fig.gca(projection='3d')
                # ax.plot_surface(X, Y, Z)
                # H_coord_ndx = [i for i in np.arange(len(self.residue.names)) if i not in fit_atoms]
                # H_coords = self.xyz[t, self.res_ndx[r, H_coord_ndx], :]
                # ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], c='r', s=100)
                # ax.scatter(H_coords[:, 0], H_coords[:, 1], H_coords[:, 2], c='b', s=50)
                # plt.xlabel('X')
                # plt.ylabel('Y')
                # ax.set_zlabel('Z')
                # ax.axis('equal')
                # ax.axis('tight')
                # plt.show()
                # exit()

        print(np.mean(self.planarity))
        # plt.plot(self.time / 1000, self.planarity[0, :])
        # plt.show()
        exit()

    def fit_ellipsoid(self):

        self.ellipse_parameters = np.zeros([self.nframes, self.nres, 3])

        for t in tqdm.tqdm(range(self.nframes)):
            for r in range(self.nres):
                coords = self.xyz[t, self.res_ndx[r, :], :]  # coordinates to which we want to fit plane

                # Perform principal component analysis to figure out direction where greatest variance occurs
                # y = (coords - np.mean(coords, axis=0)) * (1 / np.std(coords, axis=0)) # scale so mean is 0 and variance is 1
                cov = np.cov(coords.T)  # covariance matrix
                eig_vals, eig_vecs = np.linalg.eig(cov)  # eigenvectors are all perpendicular to each other

                # Eigenvalues give the actual variance in the direction of the eigenvectors, since data isnt normalized
                self.ellipse_parameters[t, r, :] = eig_vals[np.argsort(eig_vals)][::-1]**0.5

        self.ellipse_parameters = self.ellipse_parameters.reshape(self.nframes * self.nres, 3)
        self.ellipse_uncertainty = self.ellipse_parameters.std(axis=0)
        self.ellipse_parameters = self.ellipse_parameters.mean(axis=0)

    def plot_residue(self, n):
        """ Plot trajectory of geometric properties for a given residue

        :param n: residue number in context of all same type residues

        :type n: int
        """

        fig, ax1 = plt.subplots()

        ax1.plot(self.time / 1000, self.radius[n, :], linewidth=2, color='blue')
        mean = np.mean(self.radius)
        ax1.set_ylim(mean - (2 * (mean - min(self.radius[n, :]))), mean + (4 * (max(self.radius[n, :]) - mean)))
        ax1.tick_params('y', colors='blue', labelsize=14)
        ax1.set_ylabel('Radius ($nm$)', color='blue', fontsize=14)

        ax2 = ax1.twinx()
        ax2.plot(self.time / 1000, self.volume[n, :], linewidth=2, color='red')
        mean = np.mean(self.volume[n, :])
        ax2.set_ylim(mean - (4 * (mean - min(self.volume[n, :]))), mean + (2 * (max(self.volume[n, :]) - mean)))
        ax2.set_ylabel('Volume ($nm^3$)', color='red', fontsize=14)
        ax2.tick_params('y', colors='red', labelsize=14)

        ax1.set_xlabel('Time (ns)', fontsize=14)
        ax1.tick_params('x', labelsize=14)

        plt.tight_layout()
        plt.show()

    def update_database(self, file="../timeseries/msd.db", tablename="msd", type='ellipse'):
        """ Update SQL database with information from this run

        :param file: relative path (relative to directory where this script is stored) to database to be updated
        :param tablename: name of table being modified in database
        :param type: The type of info to be updated/added to the table. 'parameters' indicates an update to alpha,
        sigma, hurst, sim_length and mw. 'msds' indicates an update to python_MSD, python_MSD_CI_upper and
        python_MSD_CI_Lower

        :type file: str
        :type tablename: str
        :type type: str
        :type data: list
        """

        connection = sql.connect("%s/%s" % (self.location, file))
        crsr = connection.cursor()

        # Count number of entries in table with same residue name
        check_existence = "SELECT COUNT(1) FROM %s WHERE name = '%s'" % (tablename, self.residue.name)

        output = crsr.execute(check_existence).fetchall()

        if type == 'ellipse':

            a, b, c = self.ellipse_parameters
            a_std, b_std, c_std = self.ellipse_uncertainty

            if output[0][0] > 1:  # There might be more than one entry for a given residue

                update_entry = "UPDATE %s SET ellipse_a = %.3f, ellipse_b = %.3f, ellipse_c = %.3f, ellipse_a_std = " \
                               "%.3f, ellipse_b_std = %.3f, ellipse_c_std = %.3f where name = '%s'" % \
                               (tablename, a, b, c, a_std, b_std, c_std, self.residue.name)

                crsr.execute(update_entry)

            else:

                fill_new_entry = "INSERT INTO %s (name, ellipse_a, ellipse_b, ellipse_c, ellipse_a_std, ellipse_b_std, " \
                                 "ellipse_c_std) VALUES ('%s', %.3f, %.3f, %.3f, %.3f, %.3f, %.3f)" % \
                                 (tablename, self.residue.name, a, b, c, a_std, b_std, c_std)

                crsr.execute(fill_new_entry)

        connection.commit()
        connection.close()


if __name__ == "__main__":

    args = initialize().parse_args()

    mol = Geometry(args.gro, args.trajectory, args.residue)

    mol.fit_ellipsoid()

    if args.update:
        mol.update_database(type='ellipse')

    exit()

    mol.calculate_planarity(heavy_atoms=False)

    mol.calculate_radius()
    mol.calculate_volume()

    print("Average Radius: %.2f" % mol.radius.mean())
    print("Average Volume: %.4f" % mol.volume.mean())

    sphere_volume = (4./3.)*np.pi*mol.radius.mean()**3

    print("Asphericity: %.4f" % (mol.volume.mean() / sphere_volume))

    mol.plot_residue(n=0)

