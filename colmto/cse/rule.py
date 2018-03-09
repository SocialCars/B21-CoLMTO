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
'''Rule related classes'''

from abc import ABCMeta
from abc import abstractclassmethod

from typing import Any
from typing import Generator
from typing import Iterable

import enum

from colmto.common.property import Position
from colmto.common.property import BoundingBox

@enum.unique
class Behaviour(enum.Enum):
    '''Behaviour enum for enumerating allow/deny states and corresponding vehicle classes.'''
    ALLOW = 'custom2'
    DENY = 'custom1'

    @property
    def vclass(self) -> str:
        '''returns vehicle class string'''
        return self.value

    @staticmethod
    def behaviour_from_string(behaviour: str, or_else: 'Behaviour') -> 'Behaviour':
        '''
        Transforms string argument of behaviour, i.e. 'allow', 'deny' case insensitive to
        Behaviour enum value. Otherwise return passed or_else argument.

        :param behaviour: string 'allow', 'deny'
        :param or_else: otherwise returned argument
        :type or_else: Behaviour
        :return: Behaviour.ALLOW, Behaviour.DENY, or_else

        '''

        try:
            return Behaviour[behaviour.upper()]
        except KeyError:
            return or_else


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

    @staticmethod
    def ruleoperator_from_string(rule_operator: str, or_else: 'RuleOperator') -> 'RuleOperator':
        '''
        Transforms string argument of rule operator, i.e. 'any', 'all' case insensitive to
        RuleOperator enum value. Otherwise return passed or_else argument.

        :param rule_operator: str ('any'|'all')
        :param or_else: otherwise returned argument
        :type or_else: RuleOperator
        :return: RuleOperator.ANY, RuleOperator.ALL, or_else

        '''

        try:
            return RuleOperator[rule_operator.upper()]
        except KeyError:
            return or_else

class BaseRule(metaclass=ABCMeta):
    '''Base Rule'''

    # register known rules here for figuring out whether a configured rule-type is actually valid.
    _valid_rules = {}

    def __init_subclass__(cls, *, rule_name=None, **kwargs):
        if rule_name:
            cls._valid_rules[rule_name] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def rule_cls(cls, rule_name: str) -> 'BaseRule':
        '''
        Return a class object for instantiating a valid rule.

        :param rule_name: valid rule name
        :return: cls
        '''

        return cls._valid_rules[rule_name]

    @classmethod
    def from_configuration(cls, rule_config: dict) -> 'BaseRule':
        '''
        Create a rule from a dictionary configuration

        Example:

        >>> from colmto.cse import rule
        >>> position_rule_config = {
        >>>     'type': 'ExtendableSUMOPositionRule',
        >>>     'args': {
        >>>         'position_bbox': [[0,0], [100,100]]
        >>>     }
        >>> }
        >>> vtype_rule_config = {
        >>>     'type': 'SUMOVTypeRule',
        >>>     'args': {
        >>>         'vehicle_type': 'truck'
        >>>     }
        >>> }
        >>> position_rule = rule.ExtendableSUMOPositionRule.from_configuration(position_rule_config) # type: rule.ExtendableSUMOPositionRule
        >>> vtype_rule = rule.SUMOVTypeRule.from_configuration(vtype_rule_config) # type: rule.SUMOVTypeRule
        >>> print(position_rule._valid_rules.keys())
        dict_keys(['SUMOUniversalRule', 'SUMONullRule', 'SUMOVehicleRule', 'SUMOVTypeRule', 'ExtendableSUMOVTypeRule', 'SUMOMinimalSpeedRule', 'ExtendableSUMOMinimalSpeedRule', 'SUMOPositionRule', 'ExtendableSUMOPositionRule'])
        >>> print(position_rule.add_subrule(vtype_rule))
        <class 'colmto.cse.rule.ExtendableSUMOPositionRule'>: position_bbox = BoundingBox(p1=Position(x=0, y=0), p2=Position(x=100, y=100)), subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOVTypeRule'>

        :param rule_config: rule configuration
        :return: rule
        '''

        if not isinstance(rule_config, dict):
            raise TypeError("rule_cfg is not a dictionary.")

        if rule_config.get('args') is None:
            raise KeyError("rule_cfg must contain a key \'args\'")

        if rule_config.get('type') != cls.__name__:
            raise ValueError('Configured type must match class. Class method called from '
                             f'\"{cls.__name__}\" but config has type set to \"{rule_config.get("type")}\".')

        return cls(**rule_config.get('args'))

    def __init__(self, **kwargs):
        '''
        C'tor
        :param kwargs: configuration args
        '''


class SUMORule(BaseRule, metaclass=ABCMeta):
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

    # pylint: disable=unused-argument,no-self-use
    @abstractclassmethod
    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''
        pass

    def apply(self, vehicles: Iterable['SUMOVehicle']) -> Generator['SUMOVehicle', Any, None]:
        '''
        Apply rule to vehicles.

        :param vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not

        '''

        return (
            i_vehicle.change_vehicle_class(self.to_disallowed_class())
            if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        )


class ExtendableRule(BaseRule, metaclass=ABCMeta):
    '''
    Add ability to rules to be extended, i.e. to add sub-rules to them.

    '''

    def __init__(self, subrules=tuple(), subrule_operator=RuleOperator.ANY):
        '''
        C'tor.

        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL

        '''

        # verify rule types
        for i_subrule in subrules:
            if not isinstance(i_subrule, BaseRule):
                raise TypeError(f'{i_subrule} is not of colmto.cse.rule.BaseRule.')
            if isinstance(i_subrule, ExtendableRule):
                raise TypeError(f'{i_subrule} can\'t be an ExtendableRule.')

        if subrule_operator not in RuleOperator:
            raise ValueError

        self._subrules = set(subrules)
        self._subrule_operator = subrule_operator

        super().__init__()

    @property
    def subrules(self) -> tuple:
        '''
        :return: vehicle related subrules
        '''
        return tuple(self._subrules)

    @property
    def subrules_as_str(self) -> str:
        '''
        :return: string representation of vehicle related sub-rules
        '''
        return ', '.join(str(type(i_rule)) for i_rule in sorted(self._subrules))

    @property
    def subrule_operator(self) -> RuleOperator:
        '''
        :return: sub-rule operator
        '''
        return self._subrule_operator

    @subrule_operator.setter
    def subrule_operator(self, rule_operator: RuleOperator):
        '''
        Sets rule operator for applying sub-rules (ANY|ALL).

        :param rule_operator: Rule for applying sub-rules (ANY|ALL)

        '''

        if rule_operator not in RuleOperator:
            raise ValueError
        self._subrule_operator = rule_operator

    def add_subrule(self, subrule: BaseRule) -> 'BaseRule':
        '''
        Adds a sub-rule.

        Rule must derive from colmto.cse.rule.BaseRule.

        :param subrule: A rule

        :return: future self
        '''

        if subrule is self:
            raise ValueError('Cyclic rules: Can\'t add itself as a sub-rule.')

        if not isinstance(subrule, BaseRule):
            raise TypeError(f'{type(subrule)} is not of colmto.cse.rule.BaseRule.')

        if isinstance(subrule, ExtendableRule):
            raise TypeError(f'{type(subrule)} can\'t be an ExtendableRule.')

        self._subrules.add(subrule)

        return self


class ExtendableSUMORule(ExtendableRule, metaclass=ABCMeta):
    '''
    Extends Extendable rule to check whether sub-rules apply to a given SUMOVehicle
    '''

    def applies_to_subrules(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Check whether sub-rules apply to this vehicle.

        :param vehicle: SUMOVehicle object
        :return: boolean

        '''

        return self._subrule_operator.evaluate(
            (i_rule.applies_to(vehicle) for i_rule in self._subrules)
        )


class SUMOUniversalRule(SUMORule, rule_name='SUMOUniversalRule'):
    '''
    Universal rule, i.e. always applies to any vehicle
    '''

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return True

    def apply(self, vehicles: Iterable['SUMOVehicle']) -> Generator['SUMOVehicle', Any, None]:
        '''
        Apply rule to vehicles.

        :param vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not

        '''

        return (
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) if self.applies_to(i_vehicle) else i_vehicle for i_vehicle in vehicles
        )


class SUMONullRule(SUMORule, rule_name='SUMONullRule'):
    '''
    Null rule, i.e. no restrictions: Applies to no vehicle
    '''

    # pylint: disable=unused-argument
    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return False

    # pylint: disable=no-self-use
    def apply(self, vehicles: Iterable['SUMOVehicle']) -> Generator['SUMOVehicle', Any, None]:
        '''
        Apply rule to vehicles.

        :param vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not

        '''

        return (
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) if self.applies_to(i_vehicle) else i_vehicle for i_vehicle in vehicles
        )


class SUMOVehicleRule(SUMORule, metaclass=ABCMeta, rule_name='SUMOVehicleRule'):
    '''Base class for vehicle attribute specific rules.'''
    pass

class SUMOVTypeRule(SUMOVehicleRule, rule_name='SUMOVTypeRule'):
    '''Vehicle type based rule: Applies to vehicles with a given SUMO vehicle type'''

    def __init__(self, vehicle_type=None):
        '''C'tor.'''
        super().__init__()
        self._vehicle_type = vehicle_type  # type: str

    def __str__(self):
        return f'{self.__class__}: ' \
               f'vehicle_type = {self._vehicle_type}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''

        return self._vehicle_type == vehicle.vehicle_type


class ExtendableSUMOVTypeRule(SUMOVTypeRule, ExtendableSUMORule, rule_name='ExtendableSUMOVTypeRule'):
    '''
    Extendable vehicle-type based rule: Applies to vehicles with a given SUMO vehicle type.
    Can be extendend by sub-rules.
    '''

    def __str__(self):
        return f'{self.__class__}: ' \
               f'vehicle_type = {self._vehicle_type}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''

        return super().applies_to(vehicle) and (self.subrules_apply_to(vehicle) if self._subrules else True)


class SUMOMinimalSpeedRule(SUMOVehicleRule, rule_name='SUMOMinimalSpeedRule'):
    '''MinimalSpeed rule: Applies to vehicles unable to reach a minimal velocity.'''

    def __init__(self, minimal_speed: float):
        '''C'tor.'''
        super().__init__()
        self._minimal_speed = minimal_speed

    def __str__(self):
        return f'{self.__class__}: ' \
               f'minimal_speed = {self._minimal_speed}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''

        return vehicle.speed_max < self._minimal_speed


class ExtendableSUMOMinimalSpeedRule(SUMOMinimalSpeedRule, ExtendableSUMORule, rule_name='ExtendableSUMOMinimalSpeedRule'):
    '''
    Extendable speed-based rule: Applies to vehicles unable to reach a minimal velocity.
    Can be extendend by sub-rules.
    '''

    def __str__(self):
        return f'{self.__class__}: ' \
               f'minimal_speed = {self._minimal_speed}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''
        return super().applies_to(vehicle) and (self.applies_to_subrules(vehicle) if self._subrules else True)


class SUMOPositionRule(SUMOVehicleRule, rule_name='SUMOPositionRule'):
    '''
    Position based rule: Applies to vehicles which are located inside/outside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)].
    '''

    def __init__(self, position_bbox=BoundingBox(Position(0.0, 0), Position(100.0, 1)), outside=False):
        '''
        C'tor.
        :param position_bbox: BoundingBox, can be represented as a tuple, i.e. ((x1,y1),(x2,y2))
        :param outside: True|False, apply to vehicles outside (or resp. inside) of the bounding box (default: False -> inside)
        '''
        super().__init__()
        self._position_bbox = BoundingBox(*position_bbox)
        self._outside = outside

    def __str__(self):
        return f'{self.__class__}: ' \
               f'position_bbox = {self._position_bbox}'

    @property
    def position_bbox(self) -> BoundingBox:
        '''
        :return: position bounding box
        '''
        return BoundingBox(*self._position_bbox)

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''
        return self._outside ^ self._position_bbox.contains(vehicle.position)


class ExtendableSUMOPositionRule(SUMOPositionRule, ExtendableSUMORule, rule_name='ExtendableSUMOPositionRule'):
    '''
    Extendable position-based rule: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)].
    Can be extendend by sub-rules.
    '''

    def __str__(self):
        return f'{self.__class__}: ' \
               f'position_bbox = {self._position_bbox}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''
        return super().applies_to(vehicle) and (self.applies_to_subrules(vehicle) if self._subrules else True)


class SUMODissatisfactionRule(SUMOVehicleRule, rule_name='SUMODissatisfactionRule'):
    '''
    Dissatisfaction based rule:
    Applies to vehicles which have reached a given dissatisfaction threshold (default: >=0.5).
    '''

    def __init__(self, threshold=0.5):
        '''C'tor.'''
        super().__init__()
        self._threshold = threshold

    def __str__(self):
        return f'{self.__class__}: ' \
               f'threshold = {self._threshold}'

    @property
    def threshold(self) -> float:
        '''
        :return: dissatisfaction threshold
        '''
        return self._threshold

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return vehicle.dsat_threshold >= self._threshold


class ExtendableSUMODissatisfactionRule(SUMODissatisfactionRule, ExtendableSUMORule, rule_name='ExtendableSUMODissatisfactionRule'):
    '''
    Extendable dissatisfaction-based rule:
    Applies to vehicles which have reached a given dissatisfaction threshold (default: >=0.5).
    '''

    def __str__(self):
        return f'{self.__class__}: ' \
               f'threshold = {self._threshold}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return super().applies_to(vehicle) and (self.applies_to_subrules(vehicle) if self._subrules else True)
