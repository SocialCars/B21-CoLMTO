# -*- coding: utf-8 -*-
# @package colmto.cse
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2017, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
        self._rules = []

    @property
    def rules(self) -> tuple:
        '''
        Policies of CSE

        :return: rules tuple

        '''

        return tuple(self._rules)

    def apply(self, vehicles: typing.Dict[str, colmto.environment.vehicle.SUMOVehicle]):
        '''
        Apply rules to vehicles

        :param vehicles: Iterable of vehicles or dictionary Id -> Vehicle
        :return: future self

        '''

        for i_vehicle in iter(vehicles.values()) if isinstance(vehicles, dict) else vehicles:
            self.apply_one(i_vehicle)

        return self

    def apply_one(self, vehicle: colmto.environment.vehicle.SUMOVehicle):
        '''
        Apply rules to one vehicles

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
    '''First-come-first-served CSE (basically do nothing and allow all vehicles access to OTL.'''

    _valid_rules = {
        'SUMOUniversalRule': colmto.cse.rule.SUMOUniversalRule,
        'SUMONullRule': colmto.cse.rule.SUMONullRule,
        'SUMOSpeedRule': colmto.cse.rule.SUMOSpeedRule,
        'SUMOPositionRule': colmto.cse.rule.SUMOPositionRule,
        'SUMOVTypeRule': colmto.cse.rule.SUMOVTypeRule
    }

    def add_rule(self, rule: colmto.cse.rule.SUMOVehicleRule, rule_cfg=None):
        '''
        Add rule to SumoCSE.

        :param rule: rule object
        :param rule_cfg: rule configuration
        :return: future self

        '''

        if not isinstance(rule, colmto.cse.rule.SUMOVehicleRule):
            raise TypeError

        if rule_cfg is not None \
                and rule_cfg.get('vehicle_rules', {}).get('rule', False):
            # look for sub-rules
            rule.rule = colmto.cse.rule.RuleOperator.ruleoperator_from_string(
                rule_cfg.get('vehicle_rules', {}).get('rule'),
                colmto.cse.rule.RuleOperator.ALL
            )
            for i_subrule in rule_cfg.get('vehicle_rules', {}).get('rules', []):
                rule.add_subrule(
                    self._valid_rules.get(i_subrule.get('type'))(
                        behaviour=colmto.cse.rule.Behaviour.behaviour_from_string(
                            i_subrule.get('behaviour'),
                            colmto.cse.rule.Behaviour.DENY
                        ),
                        **i_subrule.get('args')
                    )
                )

        self._rules.append(
            rule
        )

        return self

    def add_rules_from_cfg(self, rules_config: typing.Union[typing.List[dict], None]):
        '''
        Add rules to SumoCSE based on run config's 'rules' section.

        :param rules_config: run config's 'rules' section
        :return: future self

        '''

        if rules_config is None:
            return self

        for i_rule in rules_config:
            self.add_rule(
                self._valid_rules.get(i_rule.get('type'))(
                    behaviour=colmto.cse.rule.Behaviour.behaviour_from_string(
                        i_rule.get('behaviour'),
                        colmto.cse.rule.Behaviour.DENY
                    ),
                    **i_rule.get('args')
                ),
                i_rule
            )

        return self
