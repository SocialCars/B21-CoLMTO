# -*- coding: utf-8 -*-
# @package colmto.cse
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

'''CSE classes'''

import typing
if typing.TYPE_CHECKING:
    import traci

from collections import deque
import numpy
import colmto.common.log
from colmto.common.helper import VehicleType
from colmto.cse.rule import BaseRule
from colmto.cse.rule import SUMORule
from colmto.environment.vehicle import SUMOVehicle


class BaseCSE(object):
    '''Base class for the central optimisation entity (CSE).'''

    def __init__(self, args=None):
        '''
        Initialisation

        :param args: argparse configuration

        '''

        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        self._log = colmto.common.log.logger(__name__)
        self._vehicles = set()
        self._rules = set()

    @property
    def rules(self) -> frozenset:
        '''
        Policies of CSE

        :return: frozen set of rules

        '''

        return frozenset(self._rules)


class SumoCSE(BaseCSE):
    '''
    First-come-first-served CSE (basically do nothing and allow all vehicles access to OTL.
    '''

    def __init__(self, args=None):
        '''
        Init
        '''
        super().__init__(args)
        self._traci = None
        self._occupancy = {
            i_lane: deque((float('NaN') for _ in range(60)), maxlen=60)
            for i_lane in ('21edge_0', '21edge_1')
        }
        self._satisfaction = {
            i_vtype: deque((float('NaN') for _ in range(60)), maxlen=60)
            for i_vtype in VehicleType
        }

    def traci(self, _traci: 'traci') -> 'SumoCSE':
        '''
        Set TraCI reference

        :return: self

        '''

        self._traci = _traci
        return self

    def observe_traffic(self, lane_subscription_results: typing.Dict[str, typing.Dict[int, float]]) -> None:
        '''
        Observe traffic, i.e. collect data about traffic via TraCI (if provided) to base future rule decisions on

        :todo: add driver dissatisfaction stats

        :param lane_subscription_results: traci lane subscription results
        :type lane_subscription_results: dict
        '''

        if not self._traci:
            raise ValueError('Can\'t observe traffic without TraCI reference')

        for i_key, i_value in lane_subscription_results.items():
            self._occupancy.get(i_key).appendleft(i_value.get(self._traci.constants.LAST_STEP_OCCUPANCY))

    def _median_occupancy(self, lane: str=None) -> typing.Union[float, typing.Dict[str, float]]:
        '''
        Calculate median (ignoring NaN values) of occupancy for given lane (optional). If lane is None, return dict for all lanes.
        :param lane: laneID (optional)
        :type lane: str
        :return: median of occupancy

        '''

        return float(numpy.nanmedian(self._occupancy.get(lane))) if lane else {
            i_lane: numpy.nanmedian(self._occupancy.get(i_lane))
            for i_lane in self._occupancy
        }


    def add_rules_from_cfg(self, rules_cfg: typing.Iterable[dict]) -> 'SumoCSE':
        '''
        Create `Rules` from dict-based config and add them to SumoCSE.

        :param rules_cfg: dict-based config (see example)
        :return: `SumoCSE` as future reference

        Example:

        >>> rules_cfg = [
        >>>     {
        >>>         'type': 'SUMOPositionRule',
        >>>         'args': {
        >>>             'bounding_box': ((0., -2.), (9520., 2.))
        >>>         },
        >>>     },
        >>> ]
        >>> SumoCSE(args).add_rules_from_cfg(rules_cfg)

        '''

        self.add_rules(
            BaseRule.rule_cls(i_rule.get('type')).from_configuration(i_rule)
            for i_rule in rules_cfg
        )

        return self

    def add_rule(self, rule: SUMORule) -> 'SumoCSE':
        '''
        Add rule to SumoCSE.

        :type rule: SUMORule
        :param rule: rule object
        :return: `SumoCSE` as future reference

        '''

        if isinstance(rule, SUMORule):
            self._rules.add(rule)
        else:
            raise TypeError

        return self

    def add_rules(self, rules: typing.Iterable[SUMORule]) -> 'SumoCSE':
        '''
        Add iterable of rules to SumoCSE.

        :type rules: typing.Iterable[SUMORule]
        :param rules: iterable of `SUMORule` objects
        :return: `SumoCSE` as future reference

        '''

        for i_rule in rules:
            self.add_rule(i_rule)

        return self

    def apply(self, vehicles: typing.Union[typing.Iterable[SUMOVehicle], typing.Dict[str, SUMOVehicle]]) -> 'SumoCSE':
        '''
        Apply rules to vehicles

        :type vehicles: typing.Union[SUMOVehicle, typing.Dict[str, SUMOVehicle]]
        :param vehicles: Iterable of vehicles or dictionary Id -> Vehicle
        :return: `SumoCSE` as future reference

        '''

        for i_vehicle in vehicles.values() if isinstance(vehicles, dict) else vehicles:
            self.apply_one(i_vehicle)
        return self

    def apply_one(self, vehicle: SUMOVehicle) -> 'SumoCSE':
        '''
        Apply rules to one vehicle

        :type vehicle: SUMOVehicle
        :param vehicle: Vehicle
        :return: `SumoCSE` as future reference

        '''

        for i_rule in self._rules:
            if i_rule.applies_to(vehicle, occupancy=self._median_occupancy()):
                vehicle.deny_otl_access(self._traci).vehicle_class = SUMORule.disallowed_class_name()
                self._traci.vehicle.setVehicleClass(vehicle.sumo_id, vehicle.vehicle_class) if self._traci else None
                return self
        # default case: no applicable rule found -> allow
        vehicle.allow_otl_access(self._traci).vehicle_class = SUMORule.allowed_class_name()
        self._traci.vehicle.setVehicleClass(vehicle.sumo_id, vehicle.vehicle_class) if self._traci else None
        return self