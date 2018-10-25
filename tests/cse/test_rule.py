# -*- coding: utf-8 -*-
# @package tests.cse
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
colmto: Test module for environment.rule.
'''
import random
import typing   # pylint: disable=unused-import
import unittest

import colmto.cse.cse
import colmto.cse.rule
import colmto.environment.vehicle
import colmto.common.helper


class TestRule(unittest.TestCase):
    '''
    Test cases for Rule
    '''

    def test_base_rule(self):
        '''
        Test BaseRule class
        '''
        colmto.cse.rule.BaseRule()
        colmto.cse.rule.SUMOMinimalSpeedRule.from_configuration(
            {
                'type': 'SUMOMinimalSpeedRule',
                'args': {
                    'minimal_speed': 40/3.6
                }
            }
        )

        for i_error, i_arg in zip((TypeError, KeyError, ValueError), (None, {}, {'args': 'foo', 'type': None})):
            with self.subTest(pattern=(i_error, i_arg)):
                with self.assertRaises(i_error):
                    colmto.cse.rule.SUMOMinimalSpeedRule.from_configuration(i_arg)

    def test_sumo_rule(self):
        '''
        Test SumoRule class
        '''
        with self.assertRaises(TypeError):
            colmto.cse.rule.SUMORule()  # pylint: disable=abstract-class-instantiated

        self.assertEqual(colmto.cse.rule.SUMORule.disallowed_class_name(), 'custom1')
        self.assertEqual(colmto.cse.rule.SUMORule.allowed_class_name(), 'custom2')


    def test_sumo_null_rule(self):
        '''
        Test SumoNullRule class
        '''
        l_sumo_rule = colmto.cse.rule.SUMONullRule()
        self.assertIsInstance(l_sumo_rule, colmto.cse.rule.SUMONullRule)

        l_vehicles = [
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4}
            ) for _ in range(23)
        ]

        for i_vehicle in l_vehicles:
            if random.random() < 0.5:
                i_vehicle.allow_otl_access()
            else:
                i_vehicle.deny_otl_access()

        colmto.cse.cse.SumoCSE().add_rule(l_sumo_rule).apply(l_vehicles)

        for i, i_result in enumerate(l_vehicles):
            with self.subTest(pattern=(i, i_result.vehicle_class)):
                self.assertEqual(l_vehicles[i].vehicle_class, i_result.vehicle_class)
                self.assertFalse(l_sumo_rule.applies_to(l_vehicles[i]))


    def test_sumo_vtype_rule(self):
        '''Test SUMOVTypeRule class'''
        self.assertIsInstance(colmto.cse.rule.SUMOVTypeRule('passenger'), colmto.cse.rule.SUMOVTypeRule)

        self.assertEqual(
            str(colmto.cse.rule.SUMOVTypeRule('passenger')),
            '<class \'colmto.cse.rule.SUMOVTypeRule\'>: vehicle_type = VehicleType.PASSENGER'
        )

        self.assertTrue(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger'
            ).applies_to(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger'
                )
            )
        )

        self.assertFalse(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='truck'
            ).applies_to(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger'
                )
            )
        )
        l_vehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            vehicle_type='passenger'
        )
        colmto.cse.cse.SumoCSE().add_rule(colmto.cse.rule.SUMOVTypeRule(vehicle_type='passenger')).apply((l_vehicle,))
        self.assertEqual(
            l_vehicle.vehicle_class,
            colmto.common.helper.Behaviour.DENY.value
        )

        l_vehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            vehicle_type='passenger'
        )
        colmto.cse.cse.SumoCSE().add_rule(colmto.cse.rule.SUMOVTypeRule(vehicle_type='truck')).apply((l_vehicle,))
        self.assertEqual(
            l_vehicle.vehicle_class,
            colmto.common.helper.Behaviour.ALLOW.value
        )


    def test_sumo_extendable_vtype_rule(self):
        '''Test ExtendableSUMOVTypeRule'''

        l_evtrule = colmto.cse.rule.ExtendableSUMOVTypeRule(
            vehicle_type='passenger'
        ).add_subrule(
            colmto.cse.rule.SUMOPositionRule(
                bounding_box=((0., -1.), (100., 1.))
            )
        )

        self.assertEqual(
            str(l_evtrule),
            "<class 'colmto.cse.rule.ExtendableSUMOVTypeRule'>: vehicle_type = VehicleType.PASSENGER, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
        )

        l_vehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            vehicle_type='passenger'
        )

        l_vehicle._properties['position'] = colmto.common.helper.Position(0, -2)       # pylint: disable=protected-access
        self.assertFalse(
            l_evtrule.applies_to(
                l_vehicle
            )
        )

        l_vehicle._properties['position'] = colmto.common.helper.Position(0, -1)       # pylint: disable=protected-access
        self.assertTrue(
            l_evtrule.applies_to(
                l_vehicle
            )
        )

        l_vehicle._properties['position'] = colmto.common.helper.Position(100, 1)      # pylint: disable=protected-access
        self.assertTrue(
            l_evtrule.applies_to(
                l_vehicle
            )
        )

        l_vehicle._properties['position'] = colmto.common.helper.Position(101, 1)      # pylint: disable=protected-access
        self.assertFalse(
            l_evtrule.applies_to(
                l_vehicle
            )
        )

        with self.assertRaises(ValueError):
            l_evtrule.add_subrule(l_evtrule)

        with self.assertRaises(TypeError):
            l_evtrule.add_subrule(colmto.cse.rule.ExtendableSUMOVTypeRule(vehicle_type='passenger'))

        with self.assertRaises(TypeError):
            colmto.cse.rule.ExtendableSUMOVTypeRule(vehicle_type='passenger', subrule_operator=42)

    def test_sumo_extendable_rule(self):
        '''Test SUMOExtendableRule class'''
        with self.assertRaises(TypeError):
            colmto.cse.rule.ExtendableSUMORule(
                subrules=['foo'],
            )
            colmto.cse.rule.ExtendableSUMORule(
                subrules=123,
            )

        with self.assertRaises(KeyError):
            colmto.cse.rule.ExtendableSUMORule(
                subrule_operator='foo'
            )

        self.assertEqual(
            colmto.cse.rule.ExtendableSUMORule(
                subrule_operator='any'
            ).subrule_operator,
            colmto.common.helper.RuleOperator.ANY
        )

        self.assertIsInstance(
            colmto.cse.rule.ExtendableSUMORule(
                subrule_operator='any'
            ).subrules,
            frozenset
        )

        self.assertEqual(
            colmto.cse.rule.ExtendableSUMORule(
                subrules=[colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)],
                subrule_operator='any'
            ).subrule_operator,
            colmto.common.helper.RuleOperator.ANY
        )

        self.assertEqual(
            str(colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)),
            '<class \'colmto.cse.rule.SUMOMinimalSpeedRule\'>: minimal_speed = 60.0'
        )

        l_subrule = colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=120.)
        self.assertSetEqual(
            colmto.cse.rule.ExtendableSUMORule(
                subrules=(l_subrule, l_subrule),
                subrule_operator='any'
            ).subrules,
            {l_subrule}
        )

        l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(
            subrules=[colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)],
            subrule_operator=colmto.common.helper.RuleOperator.ANY
        )

        self.assertEqual(l_sumo_rule.subrule_operator, colmto.common.helper.RuleOperator.ANY)
        l_sumo_rule.subrule_operator = colmto.common.helper.RuleOperator.ALL
        self.assertEqual(l_sumo_rule.subrule_operator, colmto.common.helper.RuleOperator.ALL)

        with self.assertRaises(ValueError):
            l_sumo_rule.subrule_operator = 'foo'
            l_sumo_rule.add_subrule(l_sumo_rule)

        l_sumo_rule.add_subrule(colmto.cse.rule.SUMOPositionRule())

        with self.assertRaises(TypeError):
            l_sumo_rule.add_subrule('foo')
            l_sumo_rule.add_subrule(colmto.cse.rule.ExtendableRule())

        l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(subrules=[])
        l_sumo_sub_rule = colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=40.)
        l_sumo_rule.add_subrule(l_sumo_sub_rule)

        self.assertTrue(
            l_sumo_rule.applies_to_subrules(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=30.
                )
            )
        )

        self.assertTrue(
            l_sumo_sub_rule.applies_to(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=30.
                )
            )
        )

        l_sumo_rule = colmto.cse.rule.ExtendableSUMORule(
            subrules=[],
            subrule_operator=colmto.common.helper.RuleOperator.ALL
        )
        l_sumo_rule.add_subrule(l_sumo_sub_rule)

        self.assertTrue(
            l_sumo_rule.applies_to_subrules(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=30.
                )
            )
        )

        self.assertFalse(
            l_sumo_rule.applies_to_subrules(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=60.
                )
            )
        )

        self.assertTrue(
            l_sumo_sub_rule.applies_to(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=30.
                )
            )
        )

        self.assertFalse(
            l_sumo_sub_rule.applies_to(
                colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    speed_max=60.
                )
            )
        )

    def test_sumo_universal_rule(self):
        '''
        Test SUMOUniversalRule class
        '''
        l_vehicle = colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
        self.assertTrue(colmto.cse.rule.SUMOUniversalRule().applies_to(l_vehicle))
        colmto.cse.cse.SumoCSE().add_rule(colmto.cse.rule.SUMOUniversalRule()).apply((l_vehicle,))
        self.assertEqual(l_vehicle.vehicle_class, 'custom1')

    def test_sumo_speed_rule(self):
        '''
        Test SUMOMinimalSpeedRule class
        '''
        l_sumo_rule = colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)
        self.assertIsInstance(l_sumo_rule, colmto.cse.rule.SUMOMinimalSpeedRule)

        l_vehicles = [
            colmto.environment.vehicle.SUMOVehicle(
                environment={'gridlength': 200, 'gridcellwidth': 4},
                speed_max=random.randrange(0, 120)
            ) for _ in range(1000)
        ]

        colmto.cse.cse.SumoCSE().add_rule(l_sumo_rule).apply(l_vehicles)

        for i, i_results in enumerate(l_vehicles):
            with self.subTest(pattern=(i, i_results)):
                if l_vehicles[i].speed_max < 60.0:
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.disallowed_class_name()
                    )
                else:
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.allowed_class_name()
                    )

    def test_extendable_speed_rule(self):
        '''
        Test ExtendableSUMOMinimalSpeedRule class
        '''

        l_esmsr = colmto.cse.rule.ExtendableSUMOMinimalSpeedRule(
            minimal_speed=60.,
        ).add_subrule(
            colmto.cse.rule.SUMOPositionRule(
                bounding_box=((0., -1.), (100., 1.))
            )
        )

        self.assertEqual(
            str(l_esmsr),
            "<class 'colmto.cse.rule.ExtendableSUMOMinimalSpeedRule'>: minimal_speed = 60.0, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
        )

        l_vehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            vehicle_type='passenger'
        )

        for i_pos in (colmto.common.helper.Position(0, -1), colmto.common.helper.Position(100, 1)):
            with self.subTest(pattern=i_pos):
                l_vehicle._properties['position'] = i_pos         # pylint: disable=protected-access
                self.assertTrue(
                    l_esmsr.applies_to(l_vehicle)
                )

        for i_pos in (colmto.common.helper.Position(0, -2), colmto.common.helper.Position(101, 1)):
            with self.subTest(pattern=i_pos):
                l_vehicle._properties['position'] = i_pos         # pylint: disable=protected-access
                self.assertFalse(
                    l_esmsr.applies_to(l_vehicle)
                )

    def test_sumo_position_rule(self):
        '''
        Test SUMOPositionRule class
        '''
        l_sumo_rule = colmto.cse.rule.SUMOPositionRule(bounding_box=((0., -1.), (100., 1.)))
        self.assertIsInstance(l_sumo_rule, colmto.cse.rule.SUMOPositionRule)
        self.assertEqual(str(l_sumo_rule), '<class \'colmto.cse.rule.SUMOPositionRule\'>: bounding_box = BoundingBox(p1=Position(x=0.0, y=-1.0), p2=Position(x=100.0, y=1.0))')

        l_vehicles = [
            colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
            for _ in range(1000)
        ]

        for i_vehicle in l_vehicles:
            i_vehicle._properties['position'] = colmto.common.helper.Position(random.randrange(0, 200), 0.) # pylint: disable=protected-access

        colmto.cse.cse.SumoCSE().add_rule(l_sumo_rule).apply(l_vehicles)

        for i, i_results in enumerate(l_vehicles):
            with self.subTest(pattern=(i, i_results.position)):
                if 0. <= l_vehicles[i].position.x <= 100.0:
                    self.assertTrue(
                        l_sumo_rule.applies_to(l_vehicles[i])
                    )
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.disallowed_class_name()
                    )
                else:
                    self.assertFalse(
                        l_sumo_rule.applies_to(l_vehicles[i])
                    )
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.allowed_class_name()
                    )

        self.assertEqual(
            colmto.cse.rule.SUMOPositionRule(
                bounding_box=((0., -1.), (100., 1.)),
            ).bounding_box,
            colmto.common.helper.BoundingBox((0., -1.), (100., 1.))
        )

    def test_extendable_position_rule(self):
        '''
        Test ExtendableSUMOPositionRule class
        '''

        l_espr = colmto.cse.rule.ExtendableSUMOPositionRule(
            bounding_box=((0., -1.), (100., 1.)),
        )
        # without a sub-rule, an extended rule should always evaluate False
        for i_pos in (
                colmto.common.helper.Position(0, -1),
                colmto.common.helper.Position(100, 1),
                colmto.common.helper.Position(50, -1.5)):
            with self.subTest(pattern=i_pos):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                )
                l_vehicle._properties['position'] = i_pos         # pylint: disable=protected-access
                self.assertFalse(l_espr.applies_to(l_vehicle))

        l_espr.add_subrule(
            colmto.cse.rule.SUMOMinimalSpeedRule(
                minimal_speed=60.
            )
        )
        self.assertEqual(
            str(l_espr),
            "<class 'colmto.cse.rule.ExtendableSUMOPositionRule'>: bounding_box = BoundingBox(p1=Position(x=0.0, y=-1.0), p2=Position(x=100.0, y=1.0)), subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOMinimalSpeedRule'>"
        )

        for i_pos, i_speed in zip(
                (colmto.common.helper.Position(0, -1), colmto.common.helper.Position(100, 1)),
                (59, 20)):
            with self.subTest(pattern=(i_pos, i_speed)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                    speed_max=i_speed
                )
                l_vehicle._properties['position'] = i_pos         # pylint: disable=protected-access
                self.assertTrue(l_espr.applies_to(l_vehicle))

        for i_pos, i_speed in zip(
                (colmto.common.helper.Position(0, -2),
                 colmto.common.helper.Position(101, 1),
                 colmto.common.helper.Position(0, -1),
                 colmto.common.helper.Position(100, 1)),
                (60, 120, 60, 120)):
            with self.subTest(pattern=(i_pos, i_speed)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                    speed_max=i_speed
                )
                l_vehicle._properties['position'] = i_pos         # pylint: disable=protected-access
                self.assertFalse(l_espr.applies_to(l_vehicle))

    def test_sumo_dissatisfaction_rule(self):
        '''
        Test SUMOVehicleDissatisfactionRule
        '''
        for i_thr in (colmto.common.helper.DissatisfactionRange(0.1, 0.5), colmto.common.helper.DissatisfactionRange(0.25, 0.75)):
            with self.subTest(pattern=i_thr):
                self.assertEqual(
                    colmto.cse.rule.SUMOVehicleDissatisfactionRule(dissatisfaction_range=i_thr).threshold_range,
                    i_thr
                )

        self.assertEqual(
            str(colmto.cse.rule.SUMOVehicleDissatisfactionRule()),
            '<class \'colmto.cse.rule.SUMOVehicleDissatisfactionRule\'>: dissatisfaction_range = DissatisfactionRange(min=0.0, max=0.5), outside = False'
        )
        self.assertEqual(
            str(colmto.cse.rule.SUMOVehicleDissatisfactionRule(dissatisfaction_range=(1.0, 2.0), outside=True)),
            '<class \'colmto.cse.rule.SUMOVehicleDissatisfactionRule\'>: dissatisfaction_range = DissatisfactionRange(min=1.0, max=2.0), outside = True'
        )

        l_dsat_rule = colmto.cse.rule.SUMOVehicleDissatisfactionRule(dissatisfaction_range=(0, 50))

        for i_dsat in range(100):
            with self.subTest(pattern=(l_dsat_rule.threshold_range, i_dsat)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                )
                l_vehicle._properties['dissatisfaction'] = i_dsat           # pylint: disable=protected-access
                if i_dsat <= 50:
                    self.assertTrue(l_dsat_rule.applies_to(l_vehicle))
                else:
                    self.assertFalse(l_dsat_rule.applies_to(l_vehicle))


    def test_extendable_sumodissatisfactionrule(self):
        '''
        Test ExtendableSUMOVehicleDissatisfactionRule
        '''
        l_esdr = colmto.cse.rule.ExtendableSUMOVehicleDissatisfactionRule(dissatisfaction_range=(0, 50))

        for i_dsat in range(100):
            with self.subTest(pattern=i_dsat):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                )
                l_vehicle._properties['dissatisfaction'] = i_dsat   # pylint: disable=protected-access
                self.assertFalse(l_esdr.applies_to(l_vehicle))

        l_esdr.add_subrule(
            colmto.cse.rule.SUMOMinimalSpeedRule(
                minimal_speed=60.
            )
        )
        self.assertEqual(
            str(l_esdr),
            "<class 'colmto.cse.rule.ExtendableSUMOVehicleDissatisfactionRule'>: threshold = DissatisfactionRange(min=0, max=50), outside = False, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOMinimalSpeedRule'>"
        )

        for i_dsat, i_speed in zip((0, 50), (59, 20)):
            with self.subTest(pattern=(i_dsat, i_speed)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                    speed_max=i_speed
                )
                l_vehicle._properties['dissatisfaction'] = i_dsat   # pylint: disable=protected-access
                self.assertTrue(l_esdr.applies_to(l_vehicle))

        for i_dsat, i_speed in zip((0, 50), (66, 60)):
            with self.subTest(pattern=(i_dsat, i_speed)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                    speed_max=i_speed
                )
                l_vehicle._properties['dissatisfaction'] = i_dsat   # pylint: disable=protected-access
                self.assertFalse(l_esdr.applies_to(l_vehicle))

    def test_sumooccupancyrule(self):
        '''
        test SUMOOccupancyRule
        '''
        for i_dr in (colmto.common.helper.OccupancyRange(0.1, 0.5), colmto.common.helper.OccupancyRange(0.25, 0.75)):
            with self.subTest(pattern=i_dr):
                self.assertEqual(
                    colmto.cse.rule.SUMOOccupancyRule(occupancy_range=i_dr)._occupancy_range, # pylint: disable=protected-access
                    i_dr
                )
        self.assertEqual(
            str(colmto.cse.rule.SUMOOccupancyRule()),
            '<class \'colmto.cse.rule.SUMOOccupancyRule\'>: occupancy_range = OccupancyRange(min=0.0, max=1.0), outside = False'
        )
        self.assertEqual(
            str(colmto.cse.rule.SUMOOccupancyRule(occupancy_range=(0.01, 0.02), outside=True)),
            '<class \'colmto.cse.rule.SUMOOccupancyRule\'>: occupancy_range = OccupancyRange(min=0.01, max=0.02), outside = True'
        )
        l_occupancy_rule = colmto.cse.rule.SUMOOccupancyRule(occupancy_range=(0, 0.8))
        for i_occupancy in range(10):
            with self.subTest(pattern=(l_occupancy_rule._occupancy_range, i_occupancy/10)):
                l_vehicle = colmto.environment.vehicle.SUMOVehicle(
                    environment={'gridlength': 200, 'gridcellwidth': 4},
                    vehicle_type='passenger',
                )
                if i_occupancy/10 <= 0.8:
                    self.assertTrue(l_occupancy_rule.applies_to(l_vehicle, occupancy={'21edge_0': i_occupancy/10}))
                else:
                    self.assertFalse(l_occupancy_rule.applies_to(l_vehicle, occupancy={'21edge_0': i_occupancy/10}))

        self.assertFalse(l_occupancy_rule.applies_to(l_vehicle))
        with self.assertRaises(AssertionError):
            colmto.cse.rule.SUMOOccupancyRule(occupancy_range=(0, 1.1))
            colmto.cse.rule.SUMOOccupancyRule(occupancy_range=(-1, 0.8))

if __name__ == '__main__':
    unittest.main()
