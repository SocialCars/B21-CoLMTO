# -*- coding: utf-8 -*-
# @package tests.common
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
'''
colmto: Test module for common.helper.
'''

from nose.tools import assert_equal
from nose.tools import assert_tuple_equal
from nose.tools import assert_false
from nose.tools import assert_almost_equal
from nose.tools import assert_true
from nose.tools import assert_greater
from nose.tools import assert_raises

import random
import typing

import colmto.common.helper as helper
from colmto.environment.vehicle import SUMOVehicle

def test_colour():
    '''
    Test Colour
    '''
    l_colour_tuple = (23, 42, 12, 255)
    l_colour = helper.Colour(*l_colour_tuple)

    assert_tuple_equal(l_colour, l_colour_tuple)
    assert_equal(l_colour.red, l_colour_tuple[0])
    assert_equal(l_colour.green, l_colour_tuple[1])
    assert_equal(l_colour.blue, l_colour_tuple[2])
    assert_equal(l_colour.alpha, l_colour_tuple[3])
    l_3colour = l_colour * 3
    assert_true(isinstance(l_3colour, helper.Colour))
    assert_tuple_equal((69, 126, 36, 765), l_3colour)
    assert_tuple_equal(
        helper.Colour.map('plasma', 255, 127),
        helper.Colour(red=0.798216, green=0.280197, blue=0.469538, alpha=1.0)
    )


def speedrange_test():
    '''
    Test SpeedRange
    '''
    l_speedrange = helper.SpeedRange(12,120)
    for i_speed in range(12, 121):
        assert_true(l_speedrange.contains(i_speed))
    for i_speed in range(-10, 12):
        assert_false(l_speedrange.contains(i_speed))
    for i_speed in range(121, 150):
        assert_false(l_speedrange.contains(i_speed))

def distribution_test():
    '''
    Test Distribution
    '''
    assert_greater(
        helper.Distribution.POISSON.next_timestep(10.5, 1),
        1
    )
    assert_almost_equal(
        helper.Distribution.LINEAR.next_timestep(10.5, 1),
        1 + 1/10.5
    )

def initialsorting_test():
    '''
    Test InitialSorting
    '''
    l_vehicles = [SUMOVehicle(speed_max=random.randrange(0, 120), environment={}) for _ in range(30)]  # type: typing.List[SUMOVehicle]

    helper.InitialSorting.BEST.order(l_vehicles)
    for i in range(len(l_vehicles)-1):
        assert_true(l_vehicles[i].speed_max >= l_vehicles[i+1].speed_max)

    helper.InitialSorting.WORST.order(l_vehicles)
    for i in range(len(l_vehicles)-1):
        assert_true(l_vehicles[i].speed_max <= l_vehicles[i+1].speed_max)

    helper.InitialSorting.RANDOM.order(l_vehicles)


def test_ruleoperatorfromstring():
    '''Test colmto.cse.rule.BaseRule.ruleoperator_from_string.'''

    assert_equal(
        helper.RuleOperator.ruleoperator_from_string('All'),
        helper.RuleOperator.ALL
    )
    assert_equal(
        helper.RuleOperator.ruleoperator_from_string('Any'),
        helper.RuleOperator.ANY
    )
    with assert_raises(KeyError):
        helper.RuleOperator.ruleoperator_from_string('Meh')


def test_behaviour():
    '''
    Test Behaviour enum
    '''
    assert_equal(helper.Behaviour.ALLOW.vclass, helper.Behaviour.ALLOW.value)
    assert_equal(helper.Behaviour.DENY.vclass, helper.Behaviour.DENY.value)
    assert_equal(helper.Behaviour.ALLOW.value, 'custom2')
    assert_equal(helper.Behaviour.DENY.value, 'custom1')
    with assert_raises(KeyError):
        helper.Behaviour.behaviour_from_string('Meh')


def test_ruleoperator():
    '''
    Test RuleOperator enum
    '''
    assert_equal(helper.RuleOperator.ANY.value, any)
    assert_equal(helper.RuleOperator.ALL.value, all)
    assert_equal(helper.RuleOperator.ANY.evaluate([True, True]), True)
    assert_equal(helper.RuleOperator.ANY.evaluate([False, True]), True)
    assert_equal(helper.RuleOperator.ANY.evaluate([True, False]), True)
    assert_equal(helper.RuleOperator.ANY.evaluate([False, False]), False)
    assert_equal(helper.RuleOperator.ALL.evaluate([True, True]), True)
    assert_equal(helper.RuleOperator.ALL.evaluate([False, True]), False)
    assert_equal(helper.RuleOperator.ALL.evaluate([True, False]), False)
    assert_equal(helper.RuleOperator.ALL.evaluate([False, False]), False)
