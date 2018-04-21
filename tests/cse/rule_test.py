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
import typing
import unittest

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

    def test_sumo_rule(self):
        '''
        Test SumoRule class
        '''
        with self.assertRaises(TypeError):
            colmto.cse.rule.SUMORule()  # pylint: disable=abstract-class-instantiated

        self.assertEqual(colmto.cse.rule.SUMORule.to_disallowed_class(), 'custom1')
        self.assertEqual(colmto.cse.rule.SUMORule.to_allowed_class(), 'custom2')


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
            i_vehicle.change_vehicle_class(
                random.choice(
                    [
                        colmto.cse.rule.SUMORule.to_disallowed_class(),
                        colmto.cse.rule.SUMORule.to_allowed_class()
                    ]
                )
            )

        l_results = l_sumo_rule.apply(l_vehicles)

        for i, i_result in enumerate(l_results):
            with self.subTest(pattern=(i, i_result.vehicle_class)):
                self.assertEqual(l_vehicles[i].vehicle_class, i_result.vehicle_class)
                self.assertFalse(l_sumo_rule.applies_to(l_vehicles[i]))


    def test_sumo_vtype_rule(self):
        '''Test SUMOVTypeRule class'''
        self.assertIsInstance(colmto.cse.rule.SUMOVTypeRule('passenger'), colmto.cse.rule.SUMOVTypeRule)

        self.assertEqual(
            str(
                colmto.cse.rule.ExtendableSUMOVTypeRule(
                    vehicle_type='passenger'
                ).add_subrule(
                    colmto.cse.rule.SUMOPositionRule(
                        bounding_box=((0., -1.), (100., 1.))
                    )
                )
            ),
            "<class 'colmto.cse.rule.ExtendableSUMOVTypeRule'>: vehicle_type = VehicleType.PASSENGER, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
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

        self.assertEqual(
            next(
                colmto.cse.rule.SUMOVTypeRule(
                    vehicle_type='passenger'
                ).apply(
                    (
                        colmto.environment.vehicle.SUMOVehicle(
                            environment={'gridlength': 200, 'gridcellwidth': 4},
                            vehicle_type='passenger'
                        ),
                    )
                )
            ).vehicle_class,
            colmto.common.helper.Behaviour.DENY.value
        )

        self.assertEqual(
            next(
                colmto.cse.rule.SUMOVTypeRule(
                    vehicle_type='passenger'
                ).apply(
                    (
                        colmto.environment.vehicle.SUMOVehicle(
                            environment={'gridlength': 200, 'gridcellwidth': 4},
                            vehicle_type='passenger'
                        ),
                    )
                )
            ).vehicle_class,
            colmto.common.helper.Behaviour.DENY.value
        )

        self.assertEqual(
            next(
                colmto.cse.rule.SUMOVTypeRule(
                    vehicle_type='truck'
                ).apply(
                    (
                        colmto.environment.vehicle.SUMOVehicle(
                            environment={'gridlength': 200, 'gridcellwidth': 4},
                            vehicle_type='passenger'
                        ),
                    )
                )
            ).vehicle_class,
            colmto.common.helper.Behaviour.ALLOW.value
        )


    def test_sumo_extendable_rule(self):
        '''Test SUMOExtendableRule class'''
        with self.assertRaises(TypeError):
            colmto.cse.rule.ExtendableSUMORule(
                subrules=['foo'],
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

        self.assertEqual(
            colmto.cse.rule.ExtendableSUMORule(
                subrules=[colmto.cse.rule.SUMOMinimalSpeedRule(minimal_speed=60.)],
                subrule_operator='any'
            ).subrule_operator,
            colmto.common.helper.RuleOperator.ANY
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
        '''Test SUMOUniversalRule class'''

        self.assertTrue(
            colmto.cse.rule.SUMOUniversalRule().applies_to(
                colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
            )
        )

        self.assertEqual(
            next(
                colmto.cse.rule.SUMOUniversalRule().apply(
                    (colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4}),)
                )
            ).vehicle_class,
            'custom1'
        )


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
            ) for _ in range(4711)
            ]

        l_results = l_sumo_rule.apply(l_vehicles)

        for i, i_results in enumerate(l_results):
            if l_vehicles[i].speed_max < 60.0:
                self.assertEqual(
                    i_results.vehicle_class,
                    colmto.cse.rule.SUMORule.to_disallowed_class()
                )
            else:
                self.assertEqual(
                    i_results.vehicle_class,
                    colmto.cse.rule.SUMORule.to_allowed_class()
                )

        self.assertEqual(
            str(
                colmto.cse.rule.ExtendableSUMOMinimalSpeedRule(
                    minimal_speed=60.,
                ).add_subrule(
                    colmto.cse.rule.SUMOPositionRule(
                        bounding_box=((0., -1.), (100., 1.))
                    )
                )
            ),
            "<class 'colmto.cse.rule.ExtendableSUMOMinimalSpeedRule'>: minimal_speed = 60.0, subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOPositionRule'>"
        )


    def test_sumo_position_rule(self):
        '''
        Test SUMOPositionRule class
        '''
        l_sumo_rule = colmto.cse.rule.SUMOPositionRule(bounding_box=((0., -1.), (100., 1.)))
        self.assertIsInstance(l_sumo_rule, colmto.cse.rule.SUMOPositionRule)

        l_vehicles = [
            colmto.environment.vehicle.SUMOVehicle(environment={'gridlength': 200, 'gridcellwidth': 4})
            for _ in range(4711)
        ]

        for i_vehicle in l_vehicles:
            i_vehicle.position = (random.randrange(0, 200), 0.)

        l_results = l_sumo_rule.apply(l_vehicles)  # type: typing.List[colmto.environment.vehicle.SUMOVehicle]

        for i, i_results in enumerate(l_results):
            with self.subTest(pattern=(i, i_results.position)):
                if 0. <= l_vehicles[i].position[0] <= 100.0:
                    self.assertTrue(
                        l_sumo_rule.applies_to(l_vehicles[i])
                    )
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.to_disallowed_class()
                    )
                else:
                    self.assertFalse(
                        l_sumo_rule.applies_to(l_vehicles[i])
                    )
                    self.assertEqual(
                        i_results.vehicle_class,
                        colmto.cse.rule.SUMORule.to_allowed_class()
                    )

        self.assertTupleEqual(
            colmto.cse.rule.SUMOPositionRule(
                bounding_box=((0., -1.), (100., 1.)),
            ).bounding_box,
            ((0., -1.), (100., 1.))
        )

        self.assertEqual(
            str(
                colmto.cse.rule.ExtendableSUMOPositionRule(
                    bounding_box=((0., -1.), (100., 1.)),
                ).add_subrule(
                    colmto.cse.rule.SUMOMinimalSpeedRule(
                        minimal_speed=60.
                    )
                )
            ),
            "<class 'colmto.cse.rule.ExtendableSUMOPositionRule'>: bounding_box = BoundingBox(p1=Position(x=0.0, y=-1.0), p2=Position(x=100.0, y=1.0)), subrule_operator: RuleOperator.ANY, subrules: <class 'colmto.cse.rule.SUMOMinimalSpeedRule'>"
        )
