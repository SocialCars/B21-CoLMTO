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
from colmto.common.helper import VehicleType
from colmto.common.helper import Metric
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

        self._log.debug('Merging vehicle series of run %d', run)

        return {
            i_series.value: {
                'all': {
                    i_metric.value: {
                        'value': pandas.concat(
                            (
                                i_series.of(vehicles[i_vehicle], interpolate=True)
                                for i_vehicle in sorted(vehicles.keys())
                            ),
                            axis=1,
                            keys=sorted(vehicles.keys())
                        ).T[i_metric.value],
                        'attr': {'type': 'pandas.DataFrame'}
                    }
                    for i_metric in i_series.metrics()
                    if len(vehicles) > 0
                },
                **{
                    i_vtype.value : {
                        i_metric.value : {
                            'value' : pandas.concat(
                                (
                                    i_series.of(vehicles[i_vehicle], interpolate=True)
                                    for i_vehicle in sorted(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))
                                ),
                                axis=1,
                                keys=sorted(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))
                            ).T[i_metric.value],
                            'attr': {'type': 'pandas.DataFrame'}
                        }
                        for i_metric in i_series.metrics()
                        if len(list(filter(lambda v: vehicles[v].vehicle_type == i_vtype, vehicles.keys()))) > 0
                    }
                    for i_vtype in VehicleType
                }
            }
            for i_series in StatisticSeries
        }
