# -*- coding: utf-8 -*-
# @package colmto.common.property
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
'''Classes and functions to realise property structures, e.g. Position, Colour, ...'''
import typing
from collections import namedtuple
import matplotlib.pyplot as plt
import enum
import numpy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from colmto.environment.vehicle import SUMOVehicle


class Colour(namedtuple('Colour', ('red', 'green', 'blue', 'alpha'))):
    '''
    Named tuple to represent RGBa values.

    '''

    __slots__ = ()

    def __mul__(self, value):
        '''
        Scalars can be attribute-wise multiplied to a Colour.

        :param value: scalar
        :return: new Colour with attrubutes multiplied with scalar

        '''

        return Colour(
            red=self.red     * value,
            green=self.green * value,
            blue=self.blue   * value,
            alpha=self.alpha * value
        )

    @staticmethod
    def map(name: str, max_value: float, value: float):
        return Colour(*plt.get_cmap(name=name, lut=max_value)(value))


class Position(namedtuple('Position', ('x', 'y'))):
    '''
    Named tuple to represent the vehicle position.

    '''

    __slots__ = ()

    def gridified(self, width: float) -> 'GridPosition':
        '''
        Round position to grid depending on `width` of grid cells and return new Position object.

        :param width: grid cell width
        :return: new Position object with gridified positional attributes

        '''

        return GridPosition(x=int(round(self.x/width)-1), y=int(round(self.y/width)-1))


class GridPosition(Position):
    '''
    Named tuple to represent the vehicle position on a grid.

    '''

    __slots__ = ()


class BoundingBox(namedtuple('BoundingBox', ('p1', 'p2'))):
    '''
    Named tuple to represent a bounding box, consisting of Position p1 and Position p2.

    '''

    __slots__ = ()

    def __new__(cls, p1, p2):
        '''Override to ensure Position named tuples.'''
        # noinspection PyArgumentList
        return super(cls, BoundingBox).__new__(cls, p1=Position(*p1), p2=Position(*p2))

    def contains(self, position: Position) -> bool:
        '''checks whether position is inside bounding box'''
        return self.p1.x <= position.x <= self.p2.x and self.p1.y <= position.y <= self.p2.y


class SpeedRange(namedtuple('SpeedRange', ('min', 'max'))):
    '''
    Named tuple to represent allowed speed range.

    '''

    __slots__ = ()

    def contains(self, speed: float):
        '''checks whether speed lies between min and max (including)'''
        return self.min <= speed <= self.max

@enum.unique
class Distribution(enum.Enum):
    '''Enumerates distribution types for vehicle starting times'''
    LINEAR = enum.auto()
    POISSON = enum.auto()
    _prng = numpy.random.RandomState()

    def next_timestep(self, lamb, prev_start_time):
        r'''
        Calculate next time step in Exponential or linear distribution.
        Exponential distribution with
        \f$F(x) := 1 - e^{-\lambda x}\f$
        by using numpy.random.exponential(lambda).
        Linear distribution just adds 1/lamb to the previous start time.
        For every other value of distribution this function just returns the input value of
        prev_start_time.

        :param lamb: lambda
        :param prev_start_time: start time
        :param distribution: distribution, i.e. Distribution.POISSON or Distribution.LINEAR
        :return: next start time
        '''
        if self is Distribution.POISSON:
            return prev_start_time + self._prng.value.exponential(scale=lamb)
        elif self is Distribution.LINEAR:
            return prev_start_time + 1 / lamb
        return prev_start_time


@enum.unique
class InitialSorting(enum.Enum):
    '''Initial sorting modes of vehicles'''
    BEST = enum.auto()
    RANDOM = enum.auto()
    WORST = enum.auto()
    _prng = numpy.random.RandomState()

    def order(self, vehicles: list):
        '''*in-place* brings list of vehicles into required order (BEST, RANDOM, WORST)'''
        if self is InitialSorting.BEST:
            vehicles.sort(key=lambda i_v: i_v.speed_max, reverse=True)
        elif self is InitialSorting.WORST:
            vehicles.sort(key=lambda i_v: i_v.speed_max)
        elif self is InitialSorting.RANDOM:
            self.prng.shuffle(vehicles)

    @property
    def prng(self):
        '''returns numpy PRNG state'''
        return self._prng.value


@enum.unique
class VehicleType(enum.Enum):
    '''
    Available vehicle types
    '''
    DELIVERY = 'delivery'
    HEAVYTRANSPORT = 'heavytransport'
    PASSENGER = 'passenger'
    TRACTOR = 'tractor'
    TRUCK = 'truck'
    VAN = 'van'
    UNDEFINED = 'undefined'


@enum.unique
class Metric(enum.Enum):
    '''
    Statistical metrices
    '''
    DISSATISFACTION = 'dissatisfaction'
    GRID_POSITION_X = 'grid_position_x'
    GRID_POSITION_Y = 'grid_position_y'
    POSITION_X = 'position_x'
    POSITION_Y = 'position_y'
    RELATIVE_TIME_LOSS = 'relative_time_loss'
    TIME_LOSS = 'time_loss'
    TIME_STEP = 'time_step'
    TRAVEL_TIME = 'travel_time'

    def __str__(self):
        return self.value


@enum.unique
class StatisticSeries(enum.Enum):
    GRID = 'grid_based_series'
    TIME = 'time_based_series'

    def of(self, vehicle: 'SUMOVehicle', interpolate=False):
        if self is self.GRID:
            return vehicle.statistic_series_grid(interpolate)
        return vehicle.statistic_series_time(interpolate)

    def metrics(self):
        '''
        Returns a tuple of metrics of grid- or time-based series, depending on passed `seriestype`
        :raises TypeError if `seriestype` is neither `StatisticSeries.GRID` or `StatisticSeries.TIME`
        :param seriestype: defines for which type of series the metrics shall be returned
        :return: tuple of metrics
        '''
        if self is StatisticSeries.GRID:
            return (Metric.TIME_STEP,
                    Metric.POSITION_Y,
                    Metric.GRID_POSITION_Y,
                    Metric.DISSATISFACTION,
                    Metric.TRAVEL_TIME,
                    Metric.TIME_LOSS,
                    Metric.RELATIVE_TIME_LOSS)

        if self is StatisticSeries.TIME:
            return (Metric.POSITION_X,
                    Metric.POSITION_Y,
                    Metric.GRID_POSITION_X,
                    Metric.GRID_POSITION_Y,
                    Metric.DISSATISFACTION,
                    Metric.TRAVEL_TIME,
                    Metric.TIME_LOSS,
                    Metric.RELATIVE_TIME_LOSS)

        # raise TypeError
        raise TypeError(f'{seriestype} is neither {StatisticSeries.GRID} or {StatisticSeries.TIME}.')



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

    def evaluate(self, args: typing.Iterable):
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