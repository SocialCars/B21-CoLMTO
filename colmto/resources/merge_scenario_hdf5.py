# -*- coding: utf-8 -*-
# @package tests
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2017, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
# # This program is free software: you can redistribute it and/or modify      #
# # it under the terms of the GNU Lesser General Public License as            #
# # published by the Free Software Foundation, either version 3 of the        #
# # License, or (at your option) any later version.                           #
# #                                                                           #
# # This program is distributed in the hope that it will be useful,           #
# # but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# # GNU Lesser General Public License for more details.                       #
# #                                                                           #
# # You should have received a copy of the GNU Lesser General Public License  #
# # along with this program. If not, see http://www.gnu.org/licenses/         #
# #############################################################################
# @endcond
'''Configuration super class.'''



import sys
import h5py


def main(argv):
    '''
    main
    :param argv: cmdline args
    '''
    if len(sys.argv) != 3:
        print('Usage: merge_scenario_hdf5.py hdf5-input-file hdf5-output-file')
        return

    with h5py.File(argv[1], 'r') as f_src, h5py.File(argv[2], 'a', libver='latest') as f_dest:
        for i_key in f_src:
            f_src.copy(source=i_key, dest=f_dest)

if __name__ == '__main__':
    main(sys.argv)
