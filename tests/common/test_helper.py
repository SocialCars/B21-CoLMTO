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

import random
import unittest

import colmto.common.helper as helper
from colmto.environment.vehicle import SUMOVehicle

class HelperTests(unittest.TestCase):
    '''
    Testing the helper module
    '''

    def setUp(self):
        '''
        Set up vars with test data
        '''
        self.vehicles = [SUMOVehicle(speed_max=random.randrange(0, 120), environment={}) for _ in range(500)]
        self.colour_tuple = (23, 42, 12, 255)

    def tearDown(self):
        '''
        Clean up vars with test data
        '''
        del self.vehicles
        del self.colour_tuple

    def test_colour(self):
        '''
        Test Colour
        '''

        l_colour = helper.Colour(*self.colour_tuple)

        self.assertTupleEqual(l_colour, self.colour_tuple)
        self.assertEqual(l_colour.red, self.colour_tuple[0])
        self.assertEqual(l_colour.green, self.colour_tuple[1])
        self.assertEqual(l_colour.blue, self.colour_tuple[2])
        self.assertEqual(l_colour.alpha, self.colour_tuple[3])
        l_3colour = l_colour * 3
        self.assertTrue(isinstance(l_3colour, helper.Colour))
        self.assertTupleEqual((69, 126, 36, 765), l_3colour)
        self.assertTupleEqual(
            helper.Colour.map('plasma', 255, 127),
            helper.Colour(red=0.798216, green=0.280197, blue=0.469538, alpha=1.0)
        )

    def test_range(self):
        '''
        Test Range
        '''

        l_range = helper.Range(12, 120)

        for i_range in range(12, 121):
            with self.subTest(pattern=i_range):
                self.assertTrue(l_range.contains(i_range))
        for i_range in range(-10, 12):
            with self.subTest(pattern=i_range):
                self.assertFalse(l_range.contains(i_range))
        for i_range in range(121, 150):
            with self.subTest(pattern=i_range):
                self.assertFalse(l_range.contains(i_range))

    def test_speedrange(self):
        '''
        Test SpeedRange
        '''

        l_speedrange = helper.SpeedRange(12, 120)

        for i_speed in range(12, 121):
            with self.subTest(pattern=i_speed):
                self.assertTrue(l_speedrange.contains(i_speed))
        for i_speed in range(-10, 12):
            with self.subTest(pattern=i_speed):
                self.assertFalse(l_speedrange.contains(i_speed))
        for i_speed in range(121, 150):
            with self.subTest(pattern=i_speed):
                self.assertFalse(l_speedrange.contains(i_speed))
        with self.assertRaises(ValueError):
            helper.SpeedRange(12, -120)

    def test_dissatisfactionrange(self):
        '''
        Test DissatisfactionRange
        '''

        l_dsatrange = helper.DissatisfactionRange(12, 120)

        for i_drange in range(12, 121):
            with self.subTest(pattern=i_drange):
                self.assertTrue(l_dsatrange.contains(i_drange))
        for i_drange in range(-10, 12):
            with self.subTest(pattern=i_drange):
                self.assertFalse(l_dsatrange.contains(i_drange))
        for i_drange in range(121, 150):
            with self.subTest(pattern=i_drange):
                self.assertFalse(l_dsatrange.contains(i_drange))
        with self.assertRaises(ValueError):
            helper.DissatisfactionRange(12, -120)

    def test_distribution(self):
        '''
        Test Distribution
        '''
        self.assertGreater(
            helper.Distribution.POISSON.next_timestep(10.5, 1),
            1
        )
        self.assertAlmostEqual(
            helper.Distribution.LINEAR.next_timestep(10.5, 1),
            1 + 1/10.5
        )

    def test_initialsorting_best(self):
        '''
        Test InitialSorting BEST case
        '''

        helper.InitialSorting.WORST.order(self.vehicles)
        for i in range(len(self.vehicles)-1):
            with self.subTest(pattern=i):
                self.assertTrue(self.vehicles[i].speed_max <= self.vehicles[i+1].speed_max)

    def test_initialsorting_worst(self):
        '''
        Test InitialSorting BEST case
        '''

        helper.InitialSorting.BEST.order(self.vehicles)
        for i in range(len(self.vehicles)-1):
            with self.subTest(pattern=i):
                self.assertTrue(self.vehicles[i].speed_max >= self.vehicles[i+1].speed_max)

    def test_initialsorting_random(self):
        '''
        Test InitialSorting RANDOM case
        '''

        helper.InitialSorting.RANDOM.order(self.vehicles)

    def test_initialsorting_prng(self):
        '''
        Test InitialSorting prng error case
        '''

        with self.assertRaises(KeyError):
            helper.InitialSorting._prng.order(self.vehicles)    # pylint: disable=protected-access

    def test_ruleoperatorfromstring(self):
        '''Test colmto.cse.rule.BaseRule.ruleoperator_from_string.'''

        self.assertEqual(
            helper.RuleOperator.ruleoperator_from_string('All'),
            helper.RuleOperator.ALL
        )
        self.assertEqual(
            helper.RuleOperator.ruleoperator_from_string('Any'),
            helper.RuleOperator.ANY
        )
        with self.assertRaises(KeyError):
            helper.RuleOperator.ruleoperator_from_string('Meh')


    def test_behaviour(self):
        '''
        Test Behaviour enum
        '''
        self.assertEqual(helper.Behaviour.ALLOW.vclass, helper.Behaviour.ALLOW.value)
        self.assertEqual(helper.Behaviour.DENY.vclass, helper.Behaviour.DENY.value)
        self.assertEqual(helper.Behaviour.ALLOW.value, 'custom2')
        self.assertEqual(helper.Behaviour.DENY.value, 'custom1')
        with self.assertRaises(KeyError):
            helper.Behaviour.behaviour_from_string('Meh')


    def test_ruleoperator(self):
        '''
        Test RuleOperator enum
        '''
        self.assertEqual(helper.RuleOperator.ANY.value, any)
        self.assertEqual(helper.RuleOperator.ALL.value, all)
        self.assertEqual(helper.RuleOperator.ANY.evaluate([True, True]), True)
        self.assertEqual(helper.RuleOperator.ANY.evaluate([False, True]), True)
        self.assertEqual(helper.RuleOperator.ANY.evaluate([True, False]), True)
        self.assertEqual(helper.RuleOperator.ANY.evaluate([False, False]), False)
        self.assertEqual(helper.RuleOperator.ALL.evaluate([True, True]), True)
        self.assertEqual(helper.RuleOperator.ALL.evaluate([False, True]), False)
        self.assertEqual(helper.RuleOperator.ALL.evaluate([True, False]), False)
        self.assertEqual(helper.RuleOperator.ALL.evaluate([False, False]), False)

    def test_metric(self):
        '''
        Test Metric
        '''

        for i_metric, i_value in (
                (helper.Metric.DISSATISFACTION, 'dissatisfaction'),
                (helper.Metric.GRID_POSITION_X, 'grid_position_x'),
                (helper.Metric.GRID_POSITION_Y, 'grid_position_y'),
                (helper.Metric.POSITION_X, 'position_x'),
                (helper.Metric.POSITION_Y, 'position_y'),
                (helper.Metric.RELATIVE_TIME_LOSS, 'relative_time_loss'),
                (helper.Metric.TIME_LOSS, 'time_loss'),
                (helper.Metric.TIME_STEP, 'time_step'),
                (helper.Metric.TRAVEL_TIME, 'travel_time')):
            with self.subTest(pattern=(i_metric, i_value)):
                self.assertEqual(i_metric.value, i_value)
                self.assertEqual(str(i_metric), i_value)

    def test_disposition(self):
        '''
        Test VehicleDisposition
        '''

        self.assertEqual(helper.VehicleDisposition.COOPERATIVE.value, 'cooperative')
        self.assertEqual(helper.VehicleDisposition.UNCOOPERATIVE.value, 'uncooperative')
        for i_dispo in (helper.VehicleDisposition.choose(0) for _ in range(100)):
            with self.subTest(pattern=i_dispo):
                self.assertIs(i_dispo, helper.VehicleDisposition.UNCOOPERATIVE)
        for i_dispo in (helper.VehicleDisposition.choose(1) for _ in range(100)):
            with self.subTest(pattern=i_dispo):
                self.assertIs(i_dispo, helper.VehicleDisposition.COOPERATIVE)
        l_distribution = [helper.VehicleDisposition.choose() for _ in range(10000)]
        self.assertAlmostEqual(
            l_distribution.count(helper.VehicleDisposition.COOPERATIVE)/10000,
            l_distribution.count(helper.VehicleDisposition.UNCOOPERATIVE)/10000,
            1
        )
        l_distribution = [helper.VehicleDisposition.choose(0.1) for _ in range(10000)]
        self.assertAlmostEqual(
            l_distribution.count(helper.VehicleDisposition.COOPERATIVE)/0.1/10000,
            l_distribution.count(helper.VehicleDisposition.UNCOOPERATIVE)/0.9/10000,
            1
        )

if __name__ == '__main__':
    unittest.main()
