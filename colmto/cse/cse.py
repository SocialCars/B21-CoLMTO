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
# pylint: disable=too-few-public-methods
# pylint: disable=no-self-use
'''CSE classes'''
import typing

import colmto.common.log
import colmto.cse.rule
import colmto.environment.vehicle


class BaseCSE(object):
    '''Base class for the central optimisation entity (CSE).'''

    def __init__(self, args=None):
        '''
        C'tor

        :param args: argparse configuration

        '''

        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        self._log = colmto.common.log.logger(__name__)
        self._vehicles = set()
        self._rules = set()

    @property
    def rules(self) -> tuple:
        '''
        Policies of CSE

        :return: rules tuple

        '''

        return tuple(self._rules)

    def apply(self, vehicles: typing.Dict[str, colmto.environment.vehicle.SUMOVehicle]) -> 'BaseCSE':
        '''
        Apply rules to vehicles

        :param vehicles: Iterable of vehicles or dictionary Id -> Vehicle
        :return: future self

        '''

        for i_vehicle in iter(vehicles.values()) if isinstance(vehicles, dict) else vehicles:
            self.apply_one(i_vehicle)

        return self

    def apply_one(self, vehicle: colmto.environment.vehicle.SUMOVehicle) -> 'BaseCSE':
        '''
        Apply rules to one vehicle

        :param vehicle: Vehicle
        :return: future self

        '''

        for i_rule in self._rules:
            if i_rule.applies_to(vehicle) \
                    and i_rule.behaviour == colmto.cse.rule.Behaviour.DENY:
                vehicle.change_vehicle_class(
                    colmto.cse.rule.SUMORule.to_disallowed_class()
                )
                return self

        # default case: no applicable rule found
        vehicle.change_vehicle_class(
            colmto.cse.rule.SUMORule.to_allowed_class()
        )

        return self


class SumoCSE(BaseCSE):
    '''
    First-come-first-served CSE (basically do nothing and allow all vehicles access to OTL.
    '''

    def add_rule(self, rule: colmto.cse.rule.SUMOVehicleRule) -> 'SumoCSE':
        '''
        Add rule to SumoCSE.

        :param rule: rule object
        :return: future self

        '''

        if isinstance(rule, colmto.cse.rule.SUMOVehicleRule):
            self._rules.add(rule)
        else:
            raise TypeError

        return self

    def add_rules(self, rules: typing.Iterable[colmto.cse.rule.SUMOVehicleRule]) -> 'SumoCSE':
        '''
        Add iterable of rules to SumoCSE.

        :param rules: iterable of rule objects
        :return: future self

        '''

        for i_rule in rules:
            self.add_rule(i_rule)

        return self
