# -*- coding: utf-8 -*-
# @package tests
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2018, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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


import argparse
from contextlib import ExitStack
import os
import sys
import h5py
import numpy
from colmto.common.helper import StatisticSeries


def main(args):
    '''
    Main function
    :param args: cmdline arguments
    '''

    print('opening input/output HDF5s')
    with ExitStack() as f_stack:
        print(' input:', '\n\t'.join(args.input_files), sep=' ')
        print('output:', args.output_file)
        l_inputs = [f_stack.enter_context(h5py.File(i_fname, 'r')) for i_fname in args.input_files]
        l_output = f_stack.enter_context(h5py.File(args.output_file, 'a', libver='latest'))

        print(f'merging HDF5 files into {args.output_file} ...')
        for i_input in l_inputs:
            for i_scenario in i_input.keys():
                print(f'|-- {i_scenario}')

                l_aadts = [i_aadt for i_aadt in i_input[i_scenario].keys()]
                if not l_aadts:
                    print('No aadt dirs found!')
                    return

                for i_aadt in l_aadts:
                    print(f'|   |-- {i_aadt}')
                    l_orderings = list(i_input[f'{i_scenario}/{i_aadt}'].keys())
                    if not l_orderings:
                        print('No ordering dirs found!')
                        return

                    for i_ordering in l_orderings:
                        l_runs = list(i_input[f'{i_scenario}/{i_aadt}/{i_ordering}'].keys())

                        print(f'|   |   |-- {i_ordering} ({len(l_runs)} runs)')
                        l_vtypes = list(i_input[f'{i_scenario}/{i_aadt}/{i_ordering}/0/{StatisticSeries.GRID.value}'].keys())
                        for i_vtype in l_vtypes:
                            print(f'|   |   |   |-- {i_vtype}')
                            l_metrics = list(i_input[f'{i_scenario}/{i_aadt}/{i_ordering}/0/{StatisticSeries.GRID.value}/{i_vtype}'].keys())

                            for i_metric in l_metrics:
                                print(f'|   |   |   |   |-- {i_metric}')
                                l_output.create_dataset(
                                    f'{i_scenario}/{i_aadt}/{i_ordering}/{i_vtype}/{i_metric}',
                                    data=numpy.array([i_input[f'{i_scenario}/{i_aadt}/{i_ordering}/{i_run}/{StatisticSeries.GRID.value}/{i_vtype}/{i_metric}'] for i_run in l_runs]),
                                    compression='gzip',
                                    compression_opts=9,
                                    fletcher32=True,
                                    shuffle=True,
                                    chunks=True,
                                    track_times=True
                                    )

if __name__ == '__main__':
    l_parser = argparse.ArgumentParser(
        prog='merge_runs_in_hdf5.py',
        description='Merge runs from multiple CoLMTO result HDF5s with different AADTs into one HDF5 file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    l_parser.add_argument(
        '-i', '--input',
        dest='input_files',
        type=str,
        nargs='*',
        required=True
    )
    l_parser.add_argument(
        '-o', '--output',
        dest='output_file',
        type=str,
        required=True
    )
    l_parser.add_argument(
        '--root',
        dest='root',
        type=str,
        default='NI-B210',
        help='Root dir element.'
    )

    main(l_parser.parse_args())
