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
'''Rule related classes'''

from collections import namedtuple

from typing import Any
from typing import Generator
from typing import Iterable

import enum
import numpy

from colmto.environment import SUMOVehicle


class Position(namedtuple('Position', ('x', 'y'))):
    __slots__ = ()


class BoundingBox(namedtuple('BoundingBox', ('p1', 'p2'))):
    __slots__ = ()

    def __new__(cls, p1, p2):
        # noinspection PyArgumentList
        return super(cls, BoundingBox).__new__(cls, p1=Position(*p1), p2=Position(*p2))

    def contains(self, position: Position) -> bool:
        '''checks whether position is inside bounding box'''
        return self.p1.x <= position.x <= self.p2.x and self.p1.y <= position.y <= self.p2.y


class SpeedRange(namedtuple('SpeedRange', ('min', 'max'))):
    __slots__ = ()

    def contains(self, speed):
        '''checks whether speed lies between min and max (including)'''
        return self.min <= speed <= self.max


@enum.unique
class Behaviour(enum.Enum):
    '''Behaviour enum for enumerating allow/deny states and corresponding vehicle classes.'''
    ALLOW = 'custom2'
    DENY = 'custom1'

    @property
    def vclass(self) -> str:
        '''returns vehicle class string'''
        return self.value


@enum.unique
class RuleOperator(enum.Enum):
    '''
    Operator to be applied to logical rule expressions.

    Denotes whether an iterable with boolean expressions is True,
    iff all elements are True (all()) or iff at least one element has to be True (any())
    '''
    ALL = all
    ANY = any

    def evaluate(self, args: Iterable):
        '''evaluate iterable args'''
        return self.value(args)  # pylint: disable=too-many-function-args


class BaseRule(object):
    '''Base Rule'''

    def __init__(self, behaviour=Behaviour.DENY):
        '''
        C'tor
        @param behaviour Default, i.e. baseline rule.
                       Enum of colmto.cse.rule.Behaviour.DENY/ALLOW
        '''
        self._behaviour = behaviour

    @staticmethod
    def behaviour_from_string(behaviour: str, or_else: Behaviour) -> Behaviour:
        '''
        Transforms string argument of behaviour, i.e. 'allow', 'deny' case insensitive to
        Behaviour enum value. Otherwise return passed or_else argument.
        @param behaviour string 'allow', 'deny'
        @param or_else otherwise returned argument
        @type or_else Behaviour
        @retval Behaviour.ALLOW, Behaviour.DENY, or_else
        '''
        try:
            return Behaviour[behaviour.upper()]
        except KeyError:
            return or_else

    @staticmethod
    def ruleoperator_from_string(
            rule_operator: str, or_else: RuleOperator) -> RuleOperator:
        '''
        Transforms string argument of rule operator, i.e. 'any', 'all' case insensitive to
        RuleOperator enum value. Otherwise return passed or_else argument.
        @param rule_operator str ('any'|'all')
        @param or_else otherwise returned argument
        @type or_else RuleOperator
        @retval RuleOperator.ANY, RuleOperator.ALL, or_else
        '''
        try:
            return RuleOperator[rule_operator.upper()]
        except KeyError:
            return or_else

    @property
    def behaviour(self) -> Behaviour:
        '''
        Returns behaviour
        @retval behaviour
        '''
        return self._behaviour

    # pylint: disable=unused-argument,no-self-use
    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        '''
        return False


class SUMORule(BaseRule):
    '''
    Rule class to encapsulate SUMO's 'custom2'/'custom1' vehicle classes
    for allowing/disallowing access to overtaking lane (OTL)
    '''

    @staticmethod
    def to_allowed_class() -> str:
        '''Get the SUMO class for allowed vehicles'''
        return Behaviour.ALLOW.vclass

    @staticmethod
    def to_disallowed_class() -> str:
        '''Get the SUMO class for disallowed vehicles'''
        return Behaviour.DENY.vclass


class SUMOExtendableRule(object):
    '''Add ability to rules to be extended, i.e. to add sub-rules to them'''

    def __init__(self, rules: Iterable[SUMORule], rule_operator=RuleOperator.ANY):
        '''
        C'tor.

        @param rules List of rules
        @param rule_operator Rule operator of RuleOperator enum for applying sub-rules ANY|ALL
        '''

        # check rule types
        for i_rule in rules:
            if not isinstance(i_rule, SUMORule):
                raise TypeError(
                    '%s is not of colmto.cse.rule.SUMORule', i_rule
                )

        self._vehicle_rules = list(rules)

        if rule_operator not in RuleOperator:
            raise ValueError

        self._rule_operator = rule_operator

        super().__init__()

    @property
    def vehicle_rules(self) -> tuple:
        '''
        Return vehicle related sub-rules.

        Returns:
            vehicle_rules
        '''
        return tuple(self._vehicle_rules)

    @property
    def vehicle_rules_as_str(self) -> str:
        '''
        Return string representation of vehicle related sub-rules.

        Returns:
            vehicle_rules as string
        '''
        return ', '.join(str(type(i_rule)) for i_rule in self._vehicle_rules)

    @property
    def rule_operator(self) -> RuleOperator:
        '''
        Returns rule operator.

        Returns:
            rule operator
        '''
        return self._rule_operator

    @rule_operator.setter
    def rule_operator(self, rule_operator: RuleOperator):
        '''
        Sets rule operator for applying sub-rules (ANY|ALL).

        @param rule_operator Rule for applying sub-rules (ANY|ALL)
        '''
        if rule_operator not in RuleOperator:
            raise ValueError
        self._rule_operator = rule_operator

    def add_rule(self, vehicle_rule: SUMORule):
        '''
        Adds a rule, specifically for SUMO attributes.

        Rule must derive from colmto.cse.rule.SUMORule.

        @param vehicle_rule A rule

        @retval self
        '''

        if not isinstance(vehicle_rule, SUMOExtendableRule):
            raise TypeError('%s is not of colmto.cse.rule.SUMOExtendableRule', vehicle_rule)

        self._vehicle_rules.append(vehicle_rule)

        return self

    def subrules_apply_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Check whether sub-rules apply to this vehicle.

        @param vehicle vehicle object
        @retval boolean
        '''

        # pylint: disable=no-member
        return self.rule_operator.evaluate(
            (i_subrule.applies_to(vehicle) for i_subrule in self._vehicle_rules)
        )


class SUMOUniversalRule(SUMORule):
    '''
    Universal rule, i.e. always applies to any vehicle
    '''

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        '''
        return True

    def apply(self, vehicles: Iterable[SUMOVehicle]) -> Generator[SUMOVehicle, Any, None]:
        '''
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        '''

        return (
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) if self.applies_to(i_vehicle) else i_vehicle for i_vehicle in vehicles
        )


class SUMONullRule(SUMORule):
    '''
    Null rule, i.e. no restrictions: Applies to no vehicle
    '''

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this rule applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        '''
        return False

    # pylint: disable=no-self-use
    def apply(self, vehicles: Iterable[SUMOVehicle]) -> Generator[SUMOVehicle, Any, None]:
        '''
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        '''
        return (
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) if self.applies_to(i_vehicle) else i_vehicle for i_vehicle in vehicles
        )


class SUMOVehicleRule(SUMORule, SUMOExtendableRule):
    '''Base class for vehicle attribute specific rules.'''

    def __init__(self, behaviour=Behaviour.DENY, rule_operator=RuleOperator.ANY):
        '''C'tor.'''
        self._vehicle_rules = []
        self._rule_operator = rule_operator
        super().__init__(behaviour)


class SUMOVTypeRule(SUMOVehicleRule):
    '''Vehicle type based rule: Applies to vehicles with a given SUMO vehicle type'''

    def __init__(self, vehicle_type=None, behaviour=Behaviour.DENY):
        '''C'tor.'''
        super().__init__(behaviour)
        self._vehicle_type = vehicle_type

    def __str__(self):
        return f'{self.__class__}: ' \
               f'vehicle_type = {self._vehicle_type}, ' \
               f'behaviour = {self._behaviour.vclass}, ' \
               f'rule_operator: {self._rule_operator}, ' \
               f'subrules: {self.vehicle_rules_as_str}'

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle.
        @param vehicle Vehicle
        @retval boolean
        '''
        if (self._vehicle_type == vehicle.vehicle_type) and \
                (self.subrules_apply_to(vehicle) if self._vehicle_rules else True):
            return True
        return False

    def apply(self, vehicles: Iterable[SUMOVehicle]) -> Generator[SUMOVehicle, Any, None]:
        '''
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        '''

        return (
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        )


class SUMOSpeedRule(SUMOVehicleRule):
    '''Speed based rule: Applies to vehicles within a given speed range'''

    def __init__(self, speed_range=SpeedRange(0, 120), behaviour=Behaviour.DENY):
        '''C'tor.'''
        super().__init__(behaviour)
        self._speed_range = SpeedRange(*speed_range)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'speed_range = {self._speed_range}, ' \
               f'behaviour = {self._behaviour.name}, ' \
               f'rule_operator: {self._rule_operator}, ' \
               f'subrules: {self.vehicle_rules_as_str}'

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        '''
        return self._speed_range.contains(vehicle.speed_max) and \
                self.subrules_apply_to(vehicle) if self._vehicle_rules else True

    def apply(self, vehicles: Iterable[SUMOVehicle]) -> Generator[SUMOVehicle, Any, None]:
        '''
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        '''

        return (
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        )


class SUMOPositionRule(SUMOVehicleRule):
    '''
    Position based rule: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)]
    '''

    def __init__(self, position_bbox=BoundingBox(Position(0.0, 0), Position(100.0, 1)),
                 behaviour=Behaviour.DENY):
        '''C'tor.'''
        super().__init__(behaviour)
        self._position_bbox = BoundingBox(*position_bbox)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'position_bbox = {self._position_bbox}, ' \
               f'behaviour = {self._behaviour.vclass}, ' \
               f'rule_operator: {self._rule_operator}, ' \
               f'subrules: {self.vehicle_rules_as_str}'

    @property
    def position_bbox(self) -> BoundingBox:
        '''
        Returns position bounding box.
        @retval position bounding box
        '''
        return BoundingBox(*self._position_bbox)

    def applies_to(self, vehicle: SUMOVehicle) -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        '''
        return self._position_bbox.contains(vehicle.position) \
               and self.subrules_apply_to(vehicle) if self._vehicle_rules else True

    def apply(self, vehicles: Iterable[SUMOVehicle]) -> Generator[SUMOVehicle, Any, None]:
        '''
        apply rule to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        '''

        return (
            i_vehicle.change_vehicle_class(
                self._behaviour.vclass
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        )
