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

import colmto.common.log
import colmto.cse.rule
import colmto.environment.vehicle
from colmto.cse.rule import BaseRule


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

    def apply(self, vehicles: typing.Union[colmto.environment.vehicle.SUMOVehicle, typing.Dict[str, colmto.environment.vehicle.SUMOVehicle]], traci: 'traci'=None) -> 'BaseCSE':
        '''
        Apply rules to vehicles

        :param vehicles: Iterable of vehicles or dictionary Id -> Vehicle
        :param traci: Optional TraCI reference for controlling vehicle.
        :return: `BaseCSE` as future reference

        '''

        for i_vehicle in vehicles.values() if isinstance(vehicles, dict) else vehicles:
            self.apply_one(i_vehicle, traci)

        return self

    def apply_one(self, vehicle: colmto.environment.vehicle.SUMOVehicle, traci: 'traci'=None) -> 'BaseCSE':
        '''
        Apply rules to one vehicle

        :param vehicle: Vehicle
        :param traci: Optional TraCI reference for controlling vehicle.
        :return: `BaseCSE` as future reference

        '''

        for i_rule in self._rules:
            if i_rule.applies_to(vehicle):
                vehicle.deny_otl_access(traci)
                return self

        # default case: no applicable rule found
        vehicle.allow_otl_access(traci)

        return self


class SumoCSE(BaseCSE):
    '''
    First-come-first-served CSE (basically do nothing and allow all vehicles access to OTL.
    '''

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
        >>> colmto.cse.cse.SumoCSE(args).add_rules_from_cfg(rules_cfg)

        '''

        self.add_rules(
            BaseRule.rule_cls(i_rule.get('type')).from_configuration(i_rule)
            for i_rule in rules_cfg
        )

        return self

    def add_rule(self, rule: colmto.cse.rule.BaseRule) -> 'SumoCSE':
        '''
        Add rule to SumoCSE.

        :param rule: `SUMOVehicleRule` object
        :return: `SumoCSE` as future reference

        '''

        if isinstance(rule, colmto.cse.rule.BaseRule):
            self._rules.add(rule)
        else:
            raise TypeError

        return self

    def add_rules(self, rules: typing.Iterable[colmto.cse.rule.BaseRule]) -> 'SumoCSE':
        '''
        Add iterable of rules to SumoCSE.

        :param rules: iterable of `SUMOVehicleRule` objects
        :return: `SumoCSE` as future reference

        '''

        for i_rule in rules:
            self.add_rule(i_rule)

        return self
