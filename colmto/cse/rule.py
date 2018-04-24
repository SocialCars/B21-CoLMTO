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
'''Rule related classes'''

import typing

from abc import ABCMeta
from abc import abstractmethod

from colmto.common.helper import Position
from colmto.common.helper import VehicleType
from colmto.common.helper import BoundingBox
from colmto.common.helper import Behaviour
from colmto.common.helper import RuleOperator
from colmto.common.helper import DissatisfactionRange


class BaseRule(metaclass=ABCMeta):
    '''Base Rule'''

    # register known rules here for figuring out whether a configured rule-type is actually valid.
    _valid_rules = {}

    def __init_subclass__(cls, *, rule_name=None, **kwargs):
        if rule_name:
            cls._valid_rules[rule_name] = cls
        super().__init_subclass__(**kwargs)

    def __init__(self, **kwargs):
        '''
        Initialisation
        :param kwargs: configuration args
        '''
        pass

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
        >>> extendable_position_rule_config = {
        >>>     'type': 'ExtendableSUMOPositionRule',
        >>>     'args': {
        >>>         'bounding_box': ((1350., -2.), (2500., 2.)),
        >>>         'subrule_operator': 'all',
        >>>         'subrules': [
        >>>             {
        >>>                 'type': 'SUMOMinimalSpeedRule',
        >>>                 'args': {
        >>>                     'minimal_speed': 80/3.6
        >>>                 },
        >>>             }
        >>>         ]
        >>>     }
        >>> }
        >>> vtype_rule_config = {
        >>>     'type': 'SUMOVTypeRule',
        >>>     'args': {
        >>>         'vehicle_type': 'truck'
        >>>     }
        >>> }
        >>> extendable_position_rule = rule.ExtendableSUMOPositionRule.from_configuration(extendable_position_rule_config)
        >>> vtype_rule = rule.SUMOVTypeRule.from_configuration(vtype_rule_config)
        >>> print(extendable_position_rule._valid_rules.keys())
        dict_keys(['SUMOUniversalRule', 'SUMONullRule', 'SUMOVehicleRule', 'SUMOVTypeRule',
                   'ExtendableSUMOVTypeRule', 'SUMOMinimalSpeedRule', 'ExtendableSUMOMinimalSpeedRule',
                   'SUMOPositionRule', 'ExtendableSUMOPositionRule', 'SUMODissatisfactionRule',
                   'ExtendableSUMODissatisfactionRule'])
        >>> print(extendable_position_rule.add_subrule(vtype_rule))
        <class 'colmto.cse.rule.ExtendableSUMOPositionRule'>: posbounding_boxBoundingBox(p1=Position(x=0, y=0), p2=Position(x=100, y=100)),
        subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOVTypeRule'>

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

    @abstractmethod
    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        '''
        pass

    def apply(self, vehicles: typing.Iterable['SUMOVehicle']) -> typing.Generator['SUMOVehicle', typing.Any, None]:
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
        Initialisation.

        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL
        :type subrule_operator: typing.Union[RuleOperator, str]

        '''

        self._subrules = set()

        if not isinstance(subrule_operator, (str, RuleOperator)):
            raise TypeError

        # verify rule types
        for i_subrule in subrules:
            if not isinstance(i_subrule, (BaseRule, dict)):
                raise TypeError(f'{i_subrule} is not of colmto.cse.rule.BaseRule or dict.')

            self.add_subrule(
                i_subrule
                if isinstance(i_subrule, BaseRule)
                else BaseRule.rule_cls(i_subrule.get('type')).from_configuration(i_subrule)
            )

        self._subrule_operator = subrule_operator \
            if isinstance(subrule_operator, RuleOperator) \
            else RuleOperator.ruleoperator_from_string(subrule_operator)

        super().__init__()

    @property
    def subrules(self) -> frozenset:
        '''
        :return: vehicle related subrules
        '''
        return frozenset(self._subrules)

    @property
    def subrules_as_str(self) -> str:
        '''
        :return: string representation of vehicle related sub-rules
        '''
        return ', '.join(str(type(i_rule)) for i_rule in self._subrules)

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
        ) if self._subrules else False  # always return False if subrules is empty


class SUMOUniversalRule(SUMORule, rule_name='SUMOUniversalRule'):
    '''
    Universal rule, i.e. always applies to any vehicle
    '''

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return True


class SUMONullRule(SUMORule, rule_name='SUMONullRule'):
    '''
    Null rule, i.e. no restrictions: Applies to no vehicle
    '''

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this rule applies to given vehicle

        :param vehicle: Vehicle
        :return: boolean (always False)

        '''

        return False


class SUMOVehicleRule(SUMORule, metaclass=ABCMeta, rule_name='SUMOVehicleRule'):
    '''Base class for vehicle attribute specific rules.'''

    @abstractmethod
    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        applies to
        :param vehicle: vehicles
        :return: bool (always False)
        '''
        return False


class SUMOVTypeRule(SUMOVehicleRule, rule_name='SUMOVTypeRule'):
    '''Vehicle type based rule: Applies to vehicles with a given SUMO vehicle type'''

    def __init__(self, vehicle_type: typing.Union[VehicleType, str]):
        '''
        Initialisation.

        :param vehicle_type: vehicle type

        '''

        super().__init__()
        self._vehicle_type = vehicle_type \
            if isinstance(vehicle_type, VehicleType) else VehicleType[vehicle_type.upper()]

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

    def __init__(self, vehicle_type: typing.Union[VehicleType, str],
                 subrules=tuple(), subrule_operator=RuleOperator.ANY):
        '''
        Initialisation

        :param vehicle_type: vehicle type
        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL

        '''

        SUMOVTypeRule.__init__(self, vehicle_type=vehicle_type)
        ExtendableSUMORule.__init__(self, subrules=subrules, subrule_operator=subrule_operator)

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

        return super().applies_to(vehicle) and self.applies_to_subrules(vehicle)


class SUMOMinimalSpeedRule(SUMOVehicleRule, rule_name='SUMOMinimalSpeedRule'):
    '''MinimalSpeed rule: Applies to vehicles unable to reach a minimal velocity.'''

    def __init__(self, minimal_speed: float):
        '''
        Initialisation
        :param minimal_speed: minimal speed a vehicle has to undercut for this rule to apply

        '''

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

    def __init__(self, minimal_speed: float,
                 subrules=tuple(), subrule_operator=RuleOperator.ANY):
        '''
        Initialisation

        :param minimal_speed: minimal speed a vehicle has to undercut for this rule to apply
        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL

        '''

        SUMOMinimalSpeedRule.__init__(self, minimal_speed=minimal_speed)
        ExtendableSUMORule.__init__(self, subrules=subrules, subrule_operator=subrule_operator)

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

        return super().applies_to(vehicle) and self.applies_to_subrules(vehicle)


class SUMOPositionRule(SUMOVehicleRule, rule_name='SUMOPositionRule'):
    '''
    Position based rule: Applies to vehicles which are located inside/outside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)].
    '''

    def __init__(self, bounding_box=BoundingBox(Position(0.0, 0), Position(100.0, 1)), outside=False):
        '''
        Initialisation.
        :param bounding_box: BoundingBox, can be represented as a tuple, i.e. ((x1,y1),(x2,y2))
        :param outside: True|False, apply to vehicles outside (or resp. inside) of the bounding box (default: False -> inside)

        '''

        super().__init__()
        self._bounding_box = BoundingBox(*bounding_box)
        self._outside = bool(outside)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'bounding_box = {self._bounding_box}'

    @property
    def bounding_box(self) -> BoundingBox:
        '''
        :return: rule bounding box

        '''

        return BoundingBox(*self._bounding_box)

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return self._outside ^ self._bounding_box.contains(vehicle.position)


class ExtendableSUMOPositionRule(SUMOPositionRule, ExtendableSUMORule, rule_name='ExtendableSUMOPositionRule'):
    '''
    Extendable position-based rule: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)], AND match at least one sub-rule.
    Should be extendend by sub-rules, as an empty sub-rule set defaults to False (i.e. applies-not).
    '''

    def __init__(self, bounding_box=BoundingBox(Position(0.0, 0), Position(100.0, 1)),
                 outside=False, subrules=tuple(), subrule_operator=RuleOperator.ANY):
        '''
        Initialisation

        :param bounding_box: BoundingBox, can be represented as a tuple, i.e. ((x1,y1),(x2,y2))
        :param outside: True|False, apply to vehicles outside (or resp. inside) of the bounding box (default: False -> inside)
        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL

        '''

        SUMOPositionRule.__init__(self, bounding_box=bounding_box, outside=outside)
        ExtendableSUMORule.__init__(self, subrules=subrules, subrule_operator=subrule_operator)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'bounding_box = {self._bounding_box}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle.

        :param vehicle: Vehicle
        :return: boolean

        '''

        return super().applies_to(vehicle) and self.applies_to_subrules(vehicle)


class SUMODissatisfactionRule(SUMOVehicleRule, rule_name='SUMODissatisfactionRule'):
    '''
    Dissatisfaction based rule:
    Applies to vehicles which are in- or outside a given dissatisfaction range (default: inside [0, 0.5]).
    '''

    def __init__(self, dissatisfaction_range=DissatisfactionRange(0.0, 0.5), outside=False):
        '''
        Initialisation
        :param dissatisfaction_range: vehicle have to be in- or outside for this rule to apply
        :param outside: controls whether this rules applies to vehicles inside (default) or outside of range

        '''

        super().__init__()
        self._dissatisfaction_range = DissatisfactionRange(*dissatisfaction_range)
        self._outside = bool(outside)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'dissatisfaction_range = {self._dissatisfaction_range}, ' \
               f'outside = {self._outside}'

    @property
    def threshold_range(self) -> float:
        '''
        :return: dissatisfaction threshold range

        '''

        return self._dissatisfaction_range

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return self._outside ^ self._dissatisfaction_range.contains(vehicle.dissatisfaction)


class ExtendableSUMODissatisfactionRule(SUMODissatisfactionRule, ExtendableSUMORule, rule_name='ExtendableSUMODissatisfactionRule'):
    '''
    Extendable dissatisfaction-based rule:
    Applies to vehicles which have reached a given dissatisfaction threshold (default: >=0.5).
    '''

    def __init__(self, dissatisfaction_range=DissatisfactionRange(0.0, 0.5), outside=False,
                 subrules=tuple(), subrule_operator=RuleOperator.ANY):
        '''
        Initialisation

        :param threshold: vehicle has to have reached for this rule to apply
        :param subrules: List of sub-rules
        :param subrule_operator: Rule operator of RuleOperator enum for applying sub-rules ANY|ALL

        '''

        SUMODissatisfactionRule.__init__(self, dissatisfaction_range=dissatisfaction_range, outside=outside)
        ExtendableSUMORule.__init__(self, subrules=subrules, subrule_operator=subrule_operator)

    def __str__(self):
        return f'{self.__class__}: ' \
               f'threshold = {self._dissatisfaction_range}, ' \
               f'outside = {self._outside}, ' \
               f'subrule_operator: {self._subrule_operator}, ' \
               f'subrules: {self.subrules_as_str}'

    def applies_to(self, vehicle: 'SUMOVehicle') -> bool:
        '''
        Test whether this (and sub)rules apply to given vehicle

        :param vehicle: Vehicle
        :return: boolean

        '''

        return super().applies_to(vehicle) and self.applies_to_subrules(vehicle)
