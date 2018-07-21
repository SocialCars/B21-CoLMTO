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

from collections import namedtuple
from dataclasses import dataclass
import typing
import enum
import matplotlib.pyplot as plt
import numpy
import pandas

@dataclass(frozen=True)
class Colour:
    '''
    Data class to represent RGBa values.

    '''

    red: float
    green: float
    blue: float
    alpha: float
    __slots__ = ('red', 'green', 'blue', 'alpha')

    def __iter__(self) -> typing.Iterable[float]:
        '''
        Make Colour iterable for unpacking
        :return: iterable over colour channels
        '''
        return iter((self.red, self.green, self.blue, self.alpha))

    def __mul__(self, value):
        '''
        Scalars can be attribute-wise multiplied to a Colour.

        :param value: scalar
        :return: new Colour with attributes multiplied with scalar

        '''

        return Colour(
            red=self.red     * value,
            green=self.green * value,
            blue=self.blue   * value,
            alpha=self.alpha * value
        )

    @staticmethod
    def map(name: str, max_value: int, value: int):
        '''
        Map value to a colour based on given colourmap and max_value for scaling

        :param name: colourmap name (needs to be supported by matplotlib, e.g. plasma)
        :param max_value: maximum value, needed for scaling
        :param value: value on scale
        :return: Colour

        '''
        return Colour(*plt.get_cmap(name=name, lut=int(max_value))(int(value)))

    def as_tuple(self) -> typing.Tuple[float, float, float, float]:
        '''
        Return indexable tuple for passing it via TraCI to SUMO.

        :return: tuple of colour channels

        '''

        return (self.red, self.green, self.blue, self.alpha)


@dataclass
class Position:
    '''
    Data class to represent the vehicle position.

    '''

    x: float
    y: float
    __slots__ = ('x', 'y')

    def __iter__(self):
        '''
        Make Position iterable for unpacking
        :return: iterable over (x, y)
        '''
        return iter((self.x, self.y))

    def gridified(self, width: float) -> 'GridPosition':
        '''
        Round position to grid depending on `width` of grid cells and return new Position object.

        :param width: grid cell width
        :return: new Position object with gridified positional attributes

        '''

        return GridPosition(x=int(round(self.x/width)-1), y=int(round(self.y/width)-1))


@dataclass
class GridPosition(Position):
    '''
    Data class to represent the vehicle position on a grid.

    '''

    x: int
    y: int


@dataclass
class BoundingBox:
    '''
    Data class to represent a bounding box, consisting of Position p1 and Position p2.

    '''

    p1: Position
    p2: Position
    __slots__ = ('p1', 'p2')

    def __iter__(self) -> typing.Iterable[Position]:
        '''
        Make BoundingBox iterable for unpacking
        :return: iterable over Positions
        '''
        return iter((self.p1, self.p2))

    def __post_init__(self):
        '''
        Ensure p1 and p2 are Position data classes.

        '''

        self.p1=Position(*self.p1)
        self.p2=Position(*self.p2)

    def contains(self, position: Position) -> bool:
        '''
        Checks whether position is inside bounding box.

        :param position: Position data class
        :type position: Position
        :return: True if position is inside BoundingBox, False otherwise.

        '''

        assert isinstance(position, Position)
        return self.p1.x <= position.x <= self.p2.x and self.p1.y <= position.y <= self.p2.y


@dataclass(frozen=True)
class Range:
    '''
    Data class to represent a range.
    '''

    min: float
    max: float
    __slots__ = ('min', 'max')

    def __iter__(self) -> typing.Iterable[float]:
        '''
        Make Range iterable for unpacking
        :return: iterable over range (min, max)
        '''
        return iter((self.min, self.max))

    def contains(self, value: float) -> bool:
        '''
        Checks whether value lies between min and max (including).

        :param value: value to check
        :type value: float
        :return: True if position is inside BoundingBox, False otherwise.
        '''
        return self.min <= value <= self.max


@dataclass(frozen=True)
class SpeedRange(Range):
    '''
    Data class to represent allowed speed range.
    '''

    def __post_init__(self):
        '''
        Check whether min <= max
        '''
        if self.min > self.max:
            raise ValueError(f'SpeedRange minumium is larger than maximum.')


@dataclass(frozen=True)
class OccupancyRange(Range):
    '''
    Data class to represent allowed occupancy range.
    '''

    def __post_init__(self):
        '''
        Check whether min <= max
        '''
        if self.min > self.max:
            raise ValueError(f'OccupancyRange minumium is larger than maximum.')


@dataclass(frozen=True)
class DissatisfactionRange(Range):
    '''
    Data class to represent allowed speed range.
    '''

    def __post_init__(self):
        '''
        Check whether min <= max
        '''
        if self.min > self.max:
            raise ValueError(f'DissatisfactionRange minumium is larger than maximum.')


@enum.unique
class Distribution(enum.Enum):
    '''
    Enumerates distribution types for vehicle starting times

    '''

    LINEAR = enum.auto()
    POISSON = enum.auto()
    _prng = numpy.random.RandomState()  # pylint: disable=no-member

    def next_timestep(self, lamb: float, prev_start_time: float) -> float:
        r'''
        Calculate next time step in Exponential or linear distribution.
        Exponential distribution with
        \f$F(x) := 1 - e^{-\lambda x}\f$
        by using numpy.random.exponential(lambda).
        Linear distribution just adds 1/lamb to the previous start time.
        For every other value of distribution this function just returns the input value of
        prev_start_time.

        :param lamb: lambda
        :type lamb: float
        :param prev_start_time: start time
        :type prev_start_time: float
        :param distribution: distribution, i.e. Distribution.POISSON or Distribution.LINEAR
        :type distribution: Distribution
        :return: next start time

        '''

        if self is Distribution.POISSON:
            return prev_start_time + self._prng.value.exponential(scale=1/lamb)

        assert self is Distribution.LINEAR
        return prev_start_time + 1 / lamb # i.e. Distribution.LINEAR


@enum.unique
class InitialSorting(enum.Enum):
    '''
    Initial sorting modes of vehicles

    '''

    BEST = enum.auto()
    RANDOM = enum.auto()
    WORST = enum.auto()
    _prng = numpy.random.RandomState()  # pylint: disable=no-member

    def order(self, vehicles: typing.List['SUMOVehicle']):
        '''
        *in-place* brings list of vehicles into required order (BEST, RANDOM, WORST)

        :param vehicles: list of vehicles
        :return: None

        '''

        if self is InitialSorting.BEST:
            vehicles.sort(key=lambda i_v: i_v.speed_max, reverse=True)
        elif self is InitialSorting.RANDOM:
            self._prng.value.shuffle(vehicles)
        elif self is InitialSorting._prng:
            raise KeyError('Can\'t order vehicles on prng')
        else:
            assert self is InitialSorting.WORST
            vehicles.sort(key=lambda i_v: i_v.speed_max)


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
    LANE_INDEX = 'lane_index'

    def __str__(self):
        return self.value


@enum.unique
class StatisticSeries(enum.Enum):
    '''
    Types of statistic series

    '''

    GRID = 'grid_based_series'

    @staticmethod
    def from_vehicle(vehicle: 'SUMOVehicle', interpolate=False) -> pandas.Series:
        '''
        return statistic series from given vehicle

        :param vehicle: Vehicle
        :param interpolate: interpolate values (True|False)
        :return: pandas.Series

        '''

        return vehicle.statistic_series_grid(interpolate)

    @staticmethod
    def metrics():
        '''
        Returns a tuple of metrics for grid-based series

        :param seriestype: defines for which type of series the metrics shall be returned
        :return: tuple of metrics

        '''

        return (Metric.TIME_STEP,
                Metric.POSITION_Y,
                Metric.GRID_POSITION_Y,
                Metric.DISSATISFACTION,
                Metric.TRAVEL_TIME,
                Metric.TIME_LOSS,
                Metric.RELATIVE_TIME_LOSS,
                Metric.LANE_INDEX)


@enum.unique
class Behaviour(enum.Enum):
    '''
    Behaviour enum for enumerating allow/deny states and corresponding vehicle classes.

    '''

    ALLOW = 'custom2'
    DENY = 'custom1'

    @property
    def vclass(self) -> str:
        '''
        returns vehicle class string

        :return: vehicle class
        '''
        return self.value

    @staticmethod
    def behaviour_from_string(behaviour: str) -> 'Behaviour':
        '''
        Transforms string argument of behaviour, i.e. 'allow', 'deny' case insensitive to
        Behaviour enum value. Otherwise raises KeyError.

        :param behaviour: string 'allow', 'deny' (case insensitive)
        :return: Behaviour.ALLOW, Behaviour.DENY,
        :raises: KeyError

        '''

        try:
            return Behaviour[behaviour.upper()]
        except KeyError:
            raise KeyError(f'provided behaviour string \"{behaviour}\" is not valid! Available strings are {Behaviour.ALLOW.name}, {Behaviour.DENY.name}')


@enum.unique
class RuleOperator(enum.Enum):
    '''
    Operator to be applied to logical rule expressions.

    Denotes whether an iterable with boolean expressions is True,
    iff all elements are True (all()) or iff at least one element has to be True (any())

    '''

    ALL = all
    ANY = any

    def evaluate(self, args: typing.Iterable) -> bool:
        '''
        evaluate iterable args

        :param args: iterable
        :return: True|False depending on RuleOperator
        '''

        return self.value(args)  # pylint: disable=too-many-function-args

    @staticmethod
    def ruleoperator_from_string(rule_operator: str) -> 'RuleOperator':
        '''
        Transforms string argument of rule operator, i.e. 'any', 'all' case insensitive to
        RuleOperator enum value. Otherwise raises KeyError.

        :param rule_operator: str ('any'|'all')
        :return: RuleOperator.ANY, RuleOperator.ALL
        :raises: KeyError
        '''

        try:
            return RuleOperator[rule_operator.upper()]
        except KeyError:
            raise KeyError(f'provided rule operator string \"{rule_operator}\" is not valid! Available strings are \"{RuleOperator.ALL.name}\", \"{RuleOperator.ANY.name}')


@enum.unique
class VehicleDisposition(enum.Enum):
    '''
    Vehicle agent's disposition
    Describes whether a vehicle agent is cooperative or uncoorperative
    '''

    COOPERATIVE = 'cooperative'
    UNCOOPERATIVE = 'uncooperative'
    _prng = numpy.random.RandomState()  # pylint: disable=no-member

    @staticmethod
    def choose(cooperation_probability: float = 0.5) -> 'VehicleDisposition':
        '''
        Pick a random disposition by given probability (default 50/50)

        :param cooperation_probability: probability p=[0,1] (default: 0.5)
        :return: VehicleDisposition.COOPERATIVE | VehicleDisposition.UNCOOPERATIVE

        '''

        return VehicleDisposition._prng.value.choice(
            (VehicleDisposition.COOPERATIVE, VehicleDisposition.UNCOOPERATIVE),
            p=(cooperation_probability, 1-cooperation_probability)
        )


class StatisticValue(namedtuple('StatisticValue', ('minimum', 'median', 'mean', 'maximum'))):
    '''
    Named tuple to represent a statistical value containing a minimum, median, mean and maximum.
    Using named tuple instead of data class as we can pass it directly into numpy ufuncs.
    '''

    __slots__ = ()

    @staticmethod
    def nanof(values: typing.Union[None, typing.Iterable[float]]=None):
        '''
        Create nan-safe new StatisticValue from iterable by using `numpy.nan*`.

        :param values: iterable of floats
        :return: StatisticValue
        '''

        return StatisticValue(
            minimum=numpy.nanmin(values),
            median=numpy.nanmedian(values),
            mean=numpy.nanmean(values),
            maximum=numpy.nanmax(values)
        ) if values and not numpy.all(numpy.isnan(values)) else StatisticValue(numpy.nan, numpy.nan, numpy.nan, numpy.nan)
