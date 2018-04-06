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


import os
import sys
import h5py
import numpy
import colmto.common.io


def aggregate_run_stats_to_hdf5(hdf5_stats, detector_positions):
    '''
    Aggregates statistics of runs by applying the median.
    :param hdf5_stats: run stats as a hdf5 object
    :param detector_positions:
    :return: updated run_stats dictionary with aggregated stats (key: 'aggregated')
    '''

    l_aggregated = {
        'global': {
            i_view: {
                i_vtype: {
                    i_stat: {
                        'value': numpy.array(
                            [
                                i_hdf5_stat[os.path.join(
                                    i_run, 'global', i_view, i_vtype, i_stat
                                )] for i_hdf5_stat in hdf5_stats for i_run in i_hdf5_stat
                            ]
                        ),
                        'attr': {
                            'description': 'global stats of {} of {} {} for each run'.format(
                                i_view, i_vtype, i_stat
                            ),
                            'rows': 'runs',
                            'columns': '{} of {} {}'.format(i_view, i_vtype, i_stat)
                        }
                    } for i_stat in [
                        'dissatisfaction_start',
                        'dissatisfaction_end',
                        'dissatisfaction_delta',
                        'time_loss_start',
                        'time_loss_end',
                        'time_loss_delta',
                        'relative_time_loss_start',
                        'relative_time_loss_end',
                        'relative_time_loss_delta'
                    ]
                } for i_vtype in ['alltypes', 'passenger', 'truck', 'tractor']
            } for i_view in ['global_stats', 'driver']
        },
        'intervals': {
            '{}-{}'.format(*i_interval): {
                i_view: {
                    i_vtype: {
                        i_stat: {
                            'value': numpy.array(
                                [
                                    i_hdf5_stat[os.path.join(
                                        i_run,
                                        'intervals',
                                        '{}-{}'.format(*i_interval),
                                        i_view,
                                        i_vtype,
                                        i_stat
                                    )] for i_hdf5_stat in hdf5_stats for i_run in i_hdf5_stat
                                ]
                            ),
                            'attr': {
                                'description': 'interval [{}, {}] {}'.format(
                                    i_interval[0],
                                    i_interval[1],
                                    'stats of {} of {} {} for each run'.format(
                                        i_view, i_vtype, i_stat
                                    ),
                                ),
                                'rows': 'runs',
                                'columns': '{} of {} {}'.format(i_view, i_vtype, i_stat)
                            }
                        } for i_stat in [
                            'dissatisfaction_start',
                            'dissatisfaction_end',
                            'dissatisfaction_delta',
                            'time_loss_start',
                            'time_loss_end',
                            'time_loss_delta',
                            'relative_time_loss_start',
                            'relative_time_loss_end',
                            'relative_time_loss_delta'
                        ]
                    } for i_vtype in ['alltypes', 'passenger', 'truck', 'tractor']
                } for i_view in ['global_stats', 'driver']
            } for i_interval in zip(detector_positions[:-1], detector_positions[1:])
        }
    }
    print('|   |   |   |-- efficiency (global)')
    l_aggregated['global']['efficiency'] = {}
    for i_vtype in ['alltypes', 'passenger', 'truck', 'tractor']:
        if l_aggregated['global']['efficiency'].get(i_vtype) is None:
            l_aggregated['global']['efficiency'][i_vtype] = {}
        for i_stat in [
            'dissatisfaction_start',
            'dissatisfaction_end',
            'dissatisfaction_delta',
            'time_loss_start',
            'time_loss_end',
            'time_loss_delta',
            'relative_time_loss_start',
            'relative_time_loss_end',
            'relative_time_loss_delta'
        ]:
            l_aggregated['global']['efficiency'][i_vtype][i_stat] = {
                'value': [
                    numpy.sum(
                        i_hdf5_stat[
                            os.path.join(
                                i_run, 'global', 'driver', i_vtype, i_stat
                            )
                        ]
                    ) for i_hdf5_stat in hdf5_stats for i_run in i_hdf5_stat
                ],
                'attr': {
                    'description': 'efficiency as sum of {}'.format(i_stat)
                }
            }

    print('|   |   |   |-- efficiency {}'.format(detector_positions))
    for i_interval in zip(detector_positions[:-1], detector_positions[1:]):
        l_aggregated['intervals']['{}-{}'.format(*i_interval)]['efficiency'] = {}
        for i_vtype in ['alltypes', 'passenger', 'truck', 'tractor']:
            if l_aggregated[
                    'intervals'
            ]['{}-{}'.format(*i_interval)]['efficiency'].get(i_vtype) is None:
                l_aggregated[
                    'intervals'
                ]['{}-{}'.format(*i_interval)]['efficiency'][i_vtype] = {}
            for i_stat in [
                'dissatisfaction_start',
                'dissatisfaction_end',
                'dissatisfaction_delta',
                'time_loss_start',
                'time_loss_end',
                'time_loss_delta',
                'relative_time_loss_start',
                'relative_time_loss_end',
                'relative_time_loss_delta'
            ]:
                l_aggregated[
                        'intervals']['{}-{}'.format(*i_interval)]['efficiency'][i_vtype][i_stat] = {
                    'value': [
                        numpy.sum(
                            i_hdf5_stat[os.path.join(
                                i_run,
                                'intervals',
                                '{}-{}'.format(*i_interval),
                                'driver',
                                i_vtype,
                                i_stat
                            )]
                        ) for i_hdf5_stat in hdf5_stats for i_run in i_hdf5_stat
                    ],
                    'attr': {
                        'description': 'efficiency as sum of {}'.format(i_stat)
                    }
                }

    return l_aggregated


def main(argv):
    '''
    Main function
    :param argv: cmdline arguments
    '''
    l_writer = colmto.common.io.Writer()

    if len(argv) < 3:
        print('Usage: aggregate_runs_in_hdf5.py [hdf5-input-file ...] [hdf5-output-file]')
        return

    print('reading input HDF5s ({})'.format(argv[:-1]))
    f_hdf5_input = {
        i_filename: h5py.File(i_filename, 'r') for i_filename in argv[1:-1]
    }

    if len(list(f_hdf5_input.values())[0].keys()) == 0:
        print('No scenario dirs found!')
        return

    print('aggregating data...')

    for i_scenario in list(f_hdf5_input.values())[0].keys():
        print('|-- {}'.format(i_scenario))

        l_aadts = list(f_hdf5_input.values())[0][i_scenario].keys()
        if len(l_aadts) == 0:
            print('No aadt dirs found!')
            return

        for i_aadt in l_aadts:
            print('|   |-- {}'.format(i_aadt))

            l_orderings = list(f_hdf5_input.values())[0][os.path.join(i_scenario, i_aadt)].keys()
            if len(l_orderings) == 0:
                print('No ordering dirs found!')
                return

            for i_ordering in l_orderings:
                l_runs = list(f_hdf5_input.values())[0][
                    os.path.join(i_scenario, i_aadt, i_ordering)
                ].keys()
                l_intervals = list(f_hdf5_input.values())[0][os.path.join(
                    i_scenario,
                    i_aadt,
                    i_ordering,
                    l_runs[0],
                    'intervals'
                )].keys()
                l_detector_positions = sorted(
                    set(
                        [
                            e for tupl in [
                                (int(i.split('-')[0]), int(i.split('-')[1])) for i in l_intervals
                            ] for e in tupl
                        ]
                    )
                )
                print('|   |   |-- {} {}'.format(i_ordering, l_detector_positions))

                l_writer.write_hdf5(
                    aggregate_run_stats_to_hdf5(
                        [
                            i_hdf5_input[os.path.join(i_scenario, i_aadt, i_ordering)]
                            for i_hdf5_input in f_hdf5_input.values()
                        ],
                        l_detector_positions
                    ),
                    hdf5_file=argv[-1],
                    hdf5_base_path=os.path.join(i_scenario, str(i_aadt), i_ordering),
                    compression='gzip',
                    compression_opts=9,
                    fletcher32=True
                )

    for i_hdf5_input in list(f_hdf5_input.values()):
        i_hdf5_input.close()

if __name__ == '__main__':
    main(sys.argv)
