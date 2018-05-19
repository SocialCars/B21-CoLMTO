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

import typing
import pandas
import numpy

import colmto.common.io
import colmto.common.log
import colmto.common.model

from colmto.common.helper import VehicleType, Metric
from colmto.common.helper import StatisticSeries
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
        '''
        merge vehicle data series into a dictionary structure suitable for writing to hdf5

        :param run: current run number
        :param vehicles: named dictionary of vehicles
        :return: dictionary of metrics for current run
        '''

        self._log.debug('Merging vehicle series of run %d', run)

        return {
            StatisticSeries.GRID.value: {
                'all': {
                    i_metric.value: {
                        'value': pandas.concat(
                            (
                                StatisticSeries.from_vehicle(vehicles[i_vehicle], interpolate=True)
                                for i_vehicle in sorted(vehicles.keys())
                            ),
                            axis=1,
                            keys=sorted(vehicles.keys())
                        ).T[i_metric.value],
                        'attr': {
                            'description': f'{StatisticSeries.GRID.value}-based data for all vehicle types',
                            'metric': i_metric.value,
                        }
                    }
                    for i_metric in StatisticSeries.metrics()
                    if len(vehicles) > 0
                },
                **{
                    i_vtype.value : {
                        i_metric.value : {
                            'value' : pandas.concat(
                                (
                                    StatisticSeries.from_vehicle(vehicles[i_vehicle], interpolate=True)
                                    for i_vehicle in sorted(filter(lambda v, vtype=i_vtype: vehicles[v].vehicle_type == vtype, vehicles.keys()))
                                ),
                                axis=1,
                                keys=sorted(filter(lambda v, vtype=i_vtype: vehicles[v].vehicle_type == vtype, vehicles.keys()))
                            ).T[i_metric.value],
                            'attr': {
                                'description': f'{StatisticSeries.GRID.value}-based data of {i_vtype}s',
                                'metric': i_metric.value,
                                'vtype': i_vtype.value,
                            }
                        }
                        for i_metric in StatisticSeries.metrics()
                        if len(list(filter(lambda v, vtype=i_vtype: vehicles[v].vehicle_type == vtype, vehicles.keys()))) > 0
                    }
                    for i_vtype in VehicleType
                }
            }
        }

    def global_stats(self, merged_series: typing.Dict[str, dict]):
        '''
        Inplace ddd global statistics, i.e. unfairness and inefficiency for each series element.

        :param merged_series: data aquired by calling `merge_vehicle_series`
        :return: inplace updated `merged series data`
        '''

        self._log.debug('Adding global stats to merged series')

        for i_series in merged_series:
            # for the individual vehicle types
            for i_vtype in merged_series.get(i_series):
                if merged_series.get(i_series).get(i_vtype):
                    l_stat = merged_series.get(i_series).get(i_vtype).get(Metric.RELATIVE_TIME_LOSS.value).get('value').dropna() # type: pandas.DataFrame
                    merged_series.get(i_series).get(i_vtype)['unfairness'] = {
                        'value': numpy.array([colmto.common.model.unfairness(l_stat[i_column]) for i_column in l_stat]),
                        'attr': {'description': f'unfairness for each cell of {i_vtype} vehicles with {Metric.RELATIVE_TIME_LOSS.value} != NaN'}
                    }
                    merged_series.get(i_series).get(i_vtype)['inefficiency'] = {
                        'value': numpy.array([colmto.common.model.inefficiency(l_stat[i_column]) for i_column in l_stat]),
                        'attr': {'description':f'inefficiency for each cell of {i_vtype} vehicles with {Metric.RELATIVE_TIME_LOSS.value} != NaN'}
                    }

        return merged_series
