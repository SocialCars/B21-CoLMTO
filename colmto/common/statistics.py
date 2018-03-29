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
from colmto.common.property import Metric
from colmto.common.property import StatisticSeries
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


    def merge_vehicle_series(self, run: int, vehicles: typing.Dict[str, SUMOVehicle]) -> typing.Dict[str, dict]:
        l_run_stats = {
            StatisticSeries.GRID.value: {
                'all': {
                    i_metric : pandas.concat(
                        (
                            StatisticSeries.GRID.of(vehicles[i_vehicle])
                            for i_vehicle in sorted(vehicles.keys())
                        ),
                        axis=1,
                        keys=sorted(vehicles.keys())
                    ).T[i_metric] if len(vehicles) > 0 else None
                    for i_metric in StatisticSeries.GRID.metrics()
                },
                **{
                    i_vtype.value : {
                        i_metric : pandas.concat(
                            (
                                StatisticSeries.GRID.of(vehicles[i_vehicle])
                                for i_vehicle in sorted(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))
                            ),
                            axis=1,
                            keys=sorted(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))
                        ).T[i_metric] if len(list(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))) > 0 else None
                        for i_metric in StatisticSeries.GRID.metrics()
                    }
                    for i_vtype in VehicleType
                }
            }
        }

        # write to hdf5
        # todo: move to_hdf call to io module
        self._log.debug(f'results for {StatisticSeries.GRID.value}')
        for i_vtype in l_run_stats.get(StatisticSeries.GRID.value).keys():
            self._log.debug(f'\ttype {i_vtype}')
            for i_metric in l_run_stats.get(StatisticSeries.GRID.value).get(i_vtype).keys():
                if l_run_stats.get(StatisticSeries.GRID.value).get(i_vtype).get(i_metric) is not None:
                    self._log.debug(f'\t\tmetric {i_metric} with {len(l_run_stats.get(StatisticSeries.GRID.value).get(i_vtype).get(i_metric))} vehicles')
                    l_run_stats.get(StatisticSeries.GRID.value).get(i_vtype).get(i_metric).to_hdf('runs.hdf5', f'/{StatisticSeries.GRID.value}/{run}/{i_vtype}/{i_metric}')

        # l_all_vehicle_series_grid.T['dissatisfaction'].boxplot()
        # plt.savefig('ALL-boxplot29.png', dpi=600)

        return l_run_stats
