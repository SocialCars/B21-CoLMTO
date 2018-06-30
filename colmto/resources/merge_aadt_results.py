# -*- coding: utf-8 -*-
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


import argparse
from contextlib import ExitStack
import h5py


def main(args):
    '''
    main
    :param args: cmdline args
    '''

    with ExitStack() as f_stack:
        print('input :', args.input_files)
        print('output:', args.output_file)
        l_input_files = [f_stack.enter_context(h5py.File(i_fname, 'r')) for i_fname in args.input_files]
        f_output_file = f_stack.enter_context(h5py.File(args.output_file, 'a', libver='latest'))
        for i_fin in l_input_files:
            for i_aadt in i_fin[args.root].keys():
                if not args.dryrun:
                    print(f'copy {args.root}/{i_aadt} to {f_output_file}')
                    i_fin.copy(source=f'{args.root}/{i_aadt}', dest=f_output_file)
                else:
                    print(f'would copy {args.root}/{i_aadt} to {f_output_file}')

if __name__ == '__main__':
    l_parser = argparse.ArgumentParser(
        prog='merge_aadt_results.py',
        description='Merge CoLMTO results from different AADTs.'
    )
    l_parser.add_argument(
        '-i',
        dest='input_files',
        type=str,
        nargs='*',
        default=None
    )
    l_parser.add_argument(
        '-o',
        dest='output_file',
        type=str,
        default=None
    )
    l_parser.add_argument(
        '-root',
        dest='root',
        type=str,
        default='NI-B210',
        help='Root dir element. DEFAULT: \'NI-B210\''
    )
    l_parser.add_argument(
        '-d',
        dest='dryrun',
        action='store_true',
        default=False
    )

    main(l_parser.parse_args())
