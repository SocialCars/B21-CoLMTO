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
import matplotlib.pyplot as plt
import enum
import numpy


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
