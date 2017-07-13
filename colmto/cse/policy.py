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
"""Policy related classes"""

import typing

import enum
import numpy

from colmto.environment import SUMOVehicle


@enum.unique
class Behaviour(enum.Enum):
    """Behaviour enum for enumerating allow/deny states and corresponding vehicle classes."""
    ALLOW = "custom2"
    DENY = "custom1"


class BasePolicy(object):
    """Base Policy"""

    def __init__(self, behaviour=Behaviour.DENY):
        """
        C'tor
        @param behaviour Default, i.e. baseline policy.
                       Enum of colmto.cse.policy.Behaviour.DENY/ALLOW
        """
        self._behaviour = behaviour

    @staticmethod
    def behaviour_from_string_or_else(behaviour, or_else: Behaviour):
        """
        Transforms string argument of behaviour, i.e. "allow", "deny" case insensitive to
        BEHAVIOUR enum value. Otherwise return passed or_else argument.
        @param behaviour string "allow", "deny"
        @param or_else otherwise returned argument
        @type or_else Behaviour
        @retval Behaviour.ALLOW, Behaviour.DENY, or_else
        """
        if behaviour.lower() == "allow":
            return Behaviour.ALLOW
        if behaviour.lower() == "deny":
            return Behaviour.DENY
        return or_else

    @property
    def behaviour(self) -> Behaviour:
        """
        Returns behaviour
        @retval behaviour
        """
        return self._behaviour


class SUMOPolicy(BasePolicy):
    """
    Policy class to encapsulate SUMO's 'custom2'/'custom1' vehicle classes
    for allowing/disallowing access to overtaking lane (OTL)
    """

    @staticmethod
    def to_allowed_class():
        """Get the SUMO class for allowed vehicles"""
        return Behaviour.ALLOW.value

    @staticmethod
    def to_disallowed_class():
        """Get the SUMO class for disallowed vehicles"""
        return Behaviour.DENY.value


class SUMOExtendablePolicy(object):
    """Add ability to policies to be extended, i.e. to add sub-policies to them"""

    def __init__(self, vehicle_policies, rule="any"):
        """
        C'tor.

        @param vehicle_policies List of policies
        @param rule Rule for applying sub-policies ("any", "all")
        """

        # check policy types
        for i_vehicle_policy in vehicle_policies:
            if not isinstance(i_vehicle_policy, SUMOVehiclePolicy):
                raise TypeError(
                    "%s is not of colmto.cse.policy.SUMOVehiclePolicy", i_vehicle_policy
                )

        self._vehicle_policies = vehicle_policies

        if rule not in ("any", "all"):
            raise ValueError

        self._rule = rule

        super(SUMOExtendablePolicy, self).__init__()

    @property
    def vehicle_policies(self):
        """
        Return vehicle related sub-policies.

        Returns:
            vehicle_policies
        """
        return self._vehicle_policies

    @property
    def rule(self):
        """
        Returns rule.

        Returns:
            rule
        """
        return self._rule

    @rule.setter
    def rule(self, rule):
        """
        Sets rule for applying sub-policies ("any", "all").

        @param rule Rule for applying sub-policies ("any", "all")
        """
        if rule not in ("any", "all"):
            raise ValueError
        self._rule = rule

    def add_vehicle_policy(self, vehicle_policy):
        """
        Adds a vehicle policy, specifically for vehicle attributes.

        Policy must derive from colmto.cse.policy.SUMOVehiclePolicy.

        @param vehicle_policy Iterable of policies derived from colmto.cse.policy.SUMOVehiclePolicy

        @retval self
        """

        if not isinstance(vehicle_policy, SUMOVehiclePolicy):
            raise TypeError("%s is not of colmto.cse.policy.SUMOVehiclePolicy", vehicle_policy)

        self._vehicle_policies.append(vehicle_policy)

        return self

    def subpolicies_apply_to(self, vehicle):
        """
        Check whether sub-policies apply to this vehicle.

        @param vehicle vehicle object
        @retval boolean
        """

        if self._rule == "any":
            return any(
                [i_subpolicy.applies_to(vehicle) for i_subpolicy in self._vehicle_policies]
            )
        elif self._rule == "all":
            return all(
                [i_subpolicy.applies_to(vehicle) for i_subpolicy in self._vehicle_policies]
            )

        return False


class SUMOUniversalPolicy(SUMOPolicy):
    """
    Universal policy, i.e. always applies to any vehicle
    """

    @staticmethod
    # pylint: disable=unused-argument
    def applies_to(vehicle):
        """
        Test whether this policy applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        return True

    def apply(self, vehicles):
        """
        apply policy to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self.to_disallowed_class()
            ) for i_vehicle in vehicles
        ]


class SUMONullPolicy(SUMOPolicy):
    """
    Null policy, i.e. no restrictions: Applies to no vehicle
    """

    @staticmethod
    # pylint: disable=unused-argument
    def applies_to(vehicle):
        """
        Test whether this policy applies to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        return False

    @staticmethod
    def apply(vehicles):
        """
        apply policy to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """
        return vehicles


class SUMOVehiclePolicy(SUMOPolicy, SUMOExtendablePolicy):
    """Base class for vehicle attribute specific policies."""

    def __init__(self, behaviour=Behaviour.DENY):
        """C'tor."""
        self._vehicle_policies = []
        self._rule = []
        super(SUMOVehiclePolicy, self).__init__(behaviour)


class SUMOVTypePolicy(SUMOVehiclePolicy):
    """Vehicle type based policy: Applies to vehicles with a given SUMO vehicle type"""

    def __init__(self, vehicle_type=None, behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOVTypePolicy, self).__init__(behaviour)
        self._vehicle_type = vehicle_type

    def __str__(self):
        return "{}: vehicle_type = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._vehicle_type, self._behaviour.value,
            self._rule, ",".join([str(i_policy) for i_policy in self._vehicle_policies])
        )

    def applies_to(self, vehicle):
        """
        Test whether this (and sub)policies apply to given vehicle.
        @param vehicle Vehicle
        @retval boolean
        """
        if (self._vehicle_type == vehicle.vehicle_type) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False

    def apply(self, vehicles):
        """
        apply policy to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.value
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]


class SUMOSpeedPolicy(SUMOVehiclePolicy):
    """Speed based policy: Applies to vehicles within a given speed range"""

    def __init__(self, speed_range=(0, 120), behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOSpeedPolicy, self).__init__(behaviour)
        self._speed_range = numpy.array(speed_range)

    def __str__(self):
        return "{}: speed_range = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._speed_range, self._behaviour.name,
            self._rule, ",".join([str(i_policy) for i_policy in self._vehicle_policies])
        )

    def applies_to(self, vehicle):
        """
        Test whether this (and sub)policies apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        if (self._speed_range[0] <= vehicle.speed_max <= self._speed_range[1]) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False

    def apply(self, vehicles):
        """
        apply policy to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.value
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]


class SUMOPositionPolicy(SUMOVehiclePolicy):
    """
    Position based policy: Applies to vehicles which are located inside a given bounding box, i.e.
    [(left_lane_0, right_lane_0) -> (left_lane_1, right_lane_1)]
    """

    def __init__(self, position_bbox=numpy.array(((0.0, 0), (100.0, 1))),
                 behaviour=Behaviour.DENY):
        """C'tor."""
        super(SUMOPositionPolicy, self).__init__(behaviour)
        self._position_bbox = position_bbox

    def __str__(self):
        return "{}: position_bbox = {}, behaviour = {}, subpolicies: {}: {}".format(
            self.__class__, self._position_bbox, self._behaviour.value,
            self._rule, ",".join([str(i_policy) for i_policy in self._vehicle_policies])
        )

    @property
    def position_bbox(self):
        """
        Returns position bounding box.
        @retval position bounding box
        """
        return self._position_bbox

    def applies_to(self, vehicle: SUMOVehicle):
        """
        Test whether this (and sub)policies apply to given vehicle
        @param vehicle Vehicle
        @retval boolean
        """
        # pylint: disable=no-member
        if numpy.all(numpy.logical_and(self._position_bbox[0] <= vehicle.position,
                                       vehicle.position <= self._position_bbox[1])) and \
                (self.subpolicies_apply_to(vehicle) if self._vehicle_policies else True):
            return True
        return False
        # pylint: enable=no-member

    def apply(self, vehicles: typing.Iterable[SUMOVehicle]) \
            -> typing.List[SUMOVehicle]:
        """
        apply policy to vehicles
        @param vehicles iterable object containing BaseVehicles, or inherited objects
        @retval List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._behaviour.value
            ) if self.applies_to(i_vehicle) else i_vehicle
            for i_vehicle in vehicles
        ]
