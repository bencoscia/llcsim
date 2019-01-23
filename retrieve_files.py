#!/usr/bin/env python

import subprocess

scripts = '/home/bcoscia/PycharmProjects/LLC_Membranes/'
setup = scripts + 'setup'
analysis = scripts + 'analysis'
llclib = scripts + 'llclib'
top = scripts + 'top/'
topologies = top + 'topologies'  # has topologies + coordinate files
ff = top + 'Forcefields'  # has forcefields
xlink = scripts + 'Crosslink'
notebooks = scripts + 'notebooks'

# only scripts and files used for setting up and running simulations
setup_scripts = ['add_dummies.py',
               'balance_charge.py',
               'build.py',
               'input.py',
               'equil.py',
               'equil.sh',
               'genmdp.py',
               'gentop.py',
               'insertmol2charges.py',
               'lc_class.py',
               'param.sh',
               'place_solutes_pores.py',
               'place_solutes.py',
               'reorder_gro.py',
               'restrain.py',
               'residue_topology.py',
               'setup_umbrella_configs.py',
               'shift_box.py',
               'solvate_equilibrated.sh',
               'solvate_equilibrated.py',
               'solvate_tails.py',
               'solvation_equilibration.py',
               'xlink.py'
              ]

# only scripts and files for post-simulation analysis
analysis_scripts = ['Atom_props.py',
                    'compare_disorder.py',
                    'coordination_number.py',
                    'correlation.py',
                    'hbond_pairing.py',
                    'hbonds.py',
                    'Ionic_Conductivity.py',
                    'make_dict.py',
                    'molecular_geometry.py',
                    'msd.py',
                    'orientational_order.py',
                    'pmf.py',
                    'Poly_fit.py',
                    'poresize.py',
                    'regional_density.py',
                    'p2p.py',
                    'rdf.py',
                    'solute_order.py',
                    'solute_partitioning.py',
                    'structure_factor.py',
                    'tail_packing.py',
                    'tilt.py',
                    'top.py',
                    'torsions.py',
                    'water_content.py',
                    '2DSAXS.py',
                    '2D-SAXS.png',
                    'WAXS.py',
                    'WAXS.npy',
                    'structure_factor.py',
                    'disorder.py',
                   ]

# scripts from llclib (~/PycharmProjects/GitHub/llclib)
llclib_scripts = ['file_rw.py',
                  'fast_rotate.py',
                  'physical.py',
                  'transform.py',
                  'fitting_functions.py',
                  'sampling.py',
                  'stats.py',
                  'timeseries.py',
                  'topology.py'
                  ]

notebook_scripts = ['discrete_powerlaw.ipynb',
             'introduction.ipynb',
             'Mean Squared Displacement.ipynb',
             'practice.ipynb',
             'Structure_Factor.ipynb'
            ]

for i in setup_scripts:
	subprocess.call(['cp', '%s/%s' %(setup,i), './setup'])
	subprocess.call(['sed', '-i', '-e', "s/LLC_Membranes/llcsim/g", './setup/%s' %i])

for i in analysis_scripts:
	subprocess.call(['cp', '%s/%s' %(analysis,i), './analysis'])
	subprocess.call(['sed', '-i', '-e', "s/LLC_Membranes/llcsim/g", './analysis/%s' %i])

for i in llclib_scripts:
	subprocess.call(['cp', '%s/%s' %(llclib,i), './llclib'])
	subprocess.call(['sed', '-i', '-e', "s/LLC_Membranes/llcsim/g", './llclib/%s' %i])

for i in notebook_scripts:
	subprocess.call(['cp', '%s/%s' %(notebooks,i), './notebooks'])
	subprocess.call(['sed', '-i', '-e', "s/LLC_Membranes/llcsim/g", './notebooks/%s' %i])

subprocess.call(['cp', '-r', '%s' %topologies, './top/'])
subprocess.call(['cp', '-r', '%s' %ff, './top/'])
