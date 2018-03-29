# -*- coding: utf-8 -*-
# @package colmto.common
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
'''Statistics module'''

import bisect
import numpy
import typing
import pandas
import matplotlib.pyplot as plt
import colmto.common.io
import colmto.common.log
import colmto.common.model
from colmto.common.property import VehicleType
from colmto.environment.vehicle import SUMOVehicle




class Statistics(object):
    '''Statistics class for computing/aggregating SUMO results'''

    def __init__(self, args=None):
        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
            self._writer = colmto.common.io.Writer(args)
        else:
            self._log = colmto.common.log.logger(__name__)
            self._writer = colmto.common.io.Writer(None)


    @staticmethod
    def merge_vehicle_series(run: int, vehicles: typing.Dict[str, SUMOVehicle]) -> typing.Dict[str, dict]:
        l_all_vehicle_series_grid = pandas.concat(
            (
                vehicles[i_vehicle].statistic_series_grid(interpolate=True)
                for i_vehicle in sorted(vehicles.keys())
            ),
            axis=1,
            keys=sorted(vehicles.keys())
        )
        l_run_stats = {
            'ALL': {
                i_metric : l_all_vehicle_series_grid.T[i_metric]
                for i_metric in ('time_step',  # todo: use Metrics enum
                                 'position_y',
                                 'grid_position_y',
                                 'dissatisfaction',
                                 'travel_time',
                                 'time_loss',
                                 'relative_time_loss')
            },
            **{
                i_vtype.name : {}
                for i_vtype in VehicleType
            }
        }
        # for i_vehicle in sorted(vehicles.keys()):
        #     for i_metric in ('time_step',  # todo: use Metrics enum
        #                      'position_y',
        #                      'grid_position_y',
        #                      'dissatisfaction',
        #                      'travel_time',
        #                      'time_loss',
        #                      'relative_time_loss'):
        #         l_run_stats[vehicles[i_vehicle].vehicle_type.name][i_metric] = pandas.concat(
        #             [
        #                 l_run_stats[vehicles[i_vehicle].vehicle_type.name][i_metric],
        #                 vehicles[i_vehicle].statistic_series_grid(interpolate=True).T[i_metric]
        #             ],
        #             axis=1,
        #         ) if l_run_stats.get(vehicles[i_vehicle].vehicle_type.name).get(i_metric) is not None else \
        #             vehicles[i_vehicle].statistic_series_grid(interpolate=True).T[i_metric]

        print(l_all_vehicle_series_grid.T[-3:]['dissatisfaction'].T)

        # split grid series by vehicle and series type
        # l_vehicle_series_grid_types = {
        #     i_series_type : l_all_vehicle_series_grid.T[i_series_type]
        #     for i_series_type in ('time_step',
        #                    'position_y',
        #                    'grid_position_y',
        #                    'dissatisfaction',
        #                    'travel_time',
        #                    'time_loss',
        #                    'relative_time_loss')
        # }
        # print(l_run_stats.keys())
        # print(l_run_stats.get(VehicleType.PASSENGER.name).get('dissatisfaction'))

        # test write to hdf5
        # for i_vtype in l_run_stats.keys():
        #     for i_metric in l_run_stats.get(i_vtype).keys():
        #         l_run_stats.get(i_vtype).get(i_metric).to_hdf('runs.hdf5', f'/{run}/{i_vtype}/{i_metric}')

        l_all_vehicle_series_grid.T['dissatisfaction'].boxplot()
        plt.savefig('ALL-boxplot2.png', dpi=600)

        return l_run_stats
