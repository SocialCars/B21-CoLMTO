# -*- coding: utf-8 -*-
# @package optom.cse
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Optimisation of Overtaking Manoeuvres project.   #
# # Copyright (c) 2016, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
import numpy

import optom.common.helper

DEFAULT = optom.common.helper.Enum(["deny", "allow"])


class BasePolicy(object):
    """Base Policy"""

    def __init__(self, default_behaviour=DEFAULT.deny):
        """
        C'tor
        :param default_behaviour: Default, i.e. baseline policy.
                                  Enum of optom.cse.policy.DEFAULT.deny/allow
        """
        self._default_behaviour = default_behaviour


class SUMOPolicy(BasePolicy):
    """
    Policy class to encapsulate SUMO's 'custom2'/'custom1' vehicle classes
    for allowing/disallowing access to overtaking lane (OTL)
    """

    def __init__(self, p_default_behaviour=DEFAULT.deny):
        """C'tor"""
        super(SUMOPolicy, self).__init__(p_default_behaviour)

    _m_policy = {
        DEFAULT.allow: "custom2",
        DEFAULT.deny: "custom1"
    }

    @property
    def to_allowed_class(self):
        """Get the SUMO class for allowed vehicles"""
        return self._m_policy.get(DEFAULT.allow)

    @property
    def to_disallowed_class(self):
        """Get the SUMO class for disallowed vehicles"""
        return self._m_policy.get(DEFAULT.deny)


class SUMONullPolicy(SUMOPolicy):
    """
    Null policy, i.e. no restrictions: Every vehicle can use overtaking lane (OTL) depending on
    default policy
    """

    def __init__(self, p_default_behaviour=DEFAULT.deny):
        """C'tor"""
        super(SUMONullPolicy, self).__init__(p_default_behaviour)

    def apply(self, p_vehicles):
        """
        apply policy to vehicles
        :param p_vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._m_policy[self._default_behaviour]
            ) for i_vehicle in p_vehicles
        ]


class SUMOMinSpeedPolicy(SUMOPolicy):
    """Speed based policy"""

    def __init__(self, p_min_speed=0, p_default_behaviour=DEFAULT.deny):
        """C'tor"""
        super(SUMOMinSpeedPolicy, self).__init__(p_default_behaviour)
        self._m_min_speed = p_min_speed

    def apply(self, p_vehicles):
        """
        apply policy to vehicles
        :param p_vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._m_policy[DEFAULT.deny]
            ) if i_vehicle.speed_max < self._m_min_speed else i_vehicle.change_vehicle_class(
                self._m_policy[DEFAULT.allow]
            ) for i_vehicle in p_vehicles
        ]


class SUMOPositionPolicy(SUMOPolicy):
    """Position based policy: Applies to the given position until end of scenario road"""

    def __init__(self, min_position=numpy.array((0.0,)), default_behaviour=DEFAULT.deny):
        """C'tor"""
        super(SUMOPositionPolicy, self).__init__(default_behaviour)
        self._m_min_position = min_position

    def apply(self, p_vehicles):
        """
        apply policy to vehicles
        :param p_vehicles: iterable object containing BaseVehicles, or inherited objects
        :return: List of vehicles with applied, i.e. set attributes, whether they can use otl or not
        """

        return [
            i_vehicle.change_vehicle_class(
                self._m_policy[DEFAULT.allow]
            ) if numpy.greater_equal(i_vehicle.position, self._m_min_position).all()
            else i_vehicle.change_vehicle_class(
                self._m_policy[DEFAULT.deny]
            ) for i_vehicle in p_vehicles
        ]
