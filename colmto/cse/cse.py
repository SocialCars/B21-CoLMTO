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
"""CSE classes"""
import typing

import colmto.common.log
import colmto.cse.rule
import colmto.environment.vehicle


class BaseCSE(object):
    """Base class for the central optimisation entity (CSE)."""

    def __init__(self, args=None):
        """
        C'tor
        @param args: argparse configuration
        """
        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        self._log = colmto.common.log.logger(__name__)
        self._vehicles = set()
        self._policies = []

    @property
    def policies(self) -> tuple:
        """
        Policies of CSE
        @retval policies tuple
        """
        return tuple(self._policies)

    def apply(self, vehicles: typing.Dict[str, colmto.environment.vehicle.SUMOVehicle]):
        """
        Apply policies to vehicles
        @param vehicles: Iterable of vehicles or dictionary Id -> Vehicle
        @retval self
        """
        for i_vehicle in iter(vehicles.values()) if isinstance(vehicles, dict) else vehicles:
            self.apply_one(i_vehicle)

        return self

    def apply_one(self, vehicle: colmto.environment.vehicle.SUMOVehicle):
        """
        Apply policies to one vehicles
        @param vehicle: Vehicle
        @retval self
        """
        for i_rule in self._policies:
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
    """First-come-first-served CSE (basically do nothing and allow all vehicles access to OTL."""

    _valid_policies = {
        "SUMOUniversalRule": colmto.cse.rule.SUMOUniversalRule,
        "SUMONullRule": colmto.cse.rule.SUMONullRule,
        "SUMOSpeedRule": colmto.cse.rule.SUMOSpeedRule,
        "SUMOPositionRule": colmto.cse.rule.SUMOPositionRule,
        "SUMOVTypeRule": colmto.cse.rule.SUMOVTypeRule
    }

    def add_rule(self, rule: colmto.cse.rule.SUMOVehicleRule, rule_cfg=None):
        """
        Add rule to SumoCSE.
        @param rule: rule object
        @param rule_cfg: rule configuration
        @retval self
        """

        if not isinstance(rule, colmto.cse.rule.SUMOVehicleRule):
            raise TypeError

        if rule_cfg is not None \
                and rule_cfg.get("vehicle_policies", {}).get("rule", False):
            # look for sub-policies
            rule.rule = colmto.cse.rule.BaseRule.ruleoperator_from_string(
                rule_cfg.get("vehicle_policies", {}).get("rule"),
                colmto.cse.rule.RuleOperator.ALL
            )
            for i_subrule in rule_cfg.get("vehicle_policies", {}).get("policies", []):
                rule.add_rule(
                    self._valid_policies.get(i_subrule.get("type"))(
                        behaviour=colmto.cse.rule.BaseRule.behaviour_from_string(
                            i_subrule.get("behaviour"),
                            colmto.cse.rule.Behaviour.DENY
                        ),
                        **i_subrule.get("args")
                    )
                )

        self._policies.append(
            rule
        )

        return self

    def add_policies_from_cfg(self, policies_config: typing.Dict[dict, typing.Any]):
        """
        Add policies to SumoCSE based on run config's "policies" section.
        @param policies_config: run config's "policies" section
        @retval self
        """

        if policies_config is None:
            return self

        for i_rule in policies_config:
            self.add_rule(
                self._valid_policies.get(i_rule.get("type"))(
                    behaviour=colmto.cse.rule.BaseRule.behaviour_from_string(
                        i_rule.get("behaviour"),
                        colmto.cse.rule.Behaviour.DENY
                    ),
                    **i_rule.get("args")
                ),
                i_rule
            )

        return self
