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
colmto: Test module for environment.cse.
'''
import random
from types import SimpleNamespace

from nose.tools import assert_equal
from nose.tools import assert_is_instance
from nose.tools import assert_raises
from nose.tools import assert_in

import colmto.cse.cse
import colmto.cse.rule
import colmto.environment.vehicle


def test_base_cse():
    '''
    Test BaseCSE class
    '''
    assert_is_instance(colmto.cse.cse.BaseCSE(), colmto.cse.cse.BaseCSE)
    assert_is_instance(
        colmto.cse.cse.BaseCSE(
            SimpleNamespace(
                loglevel='debug', quiet=False, logfile='foo.log'
            )
        ),
        colmto.cse.cse.BaseCSE
    )


def test_sumo_cse():
    '''
    Test SumoCSE class
    '''
    assert_is_instance(
        colmto.cse.cse.SumoCSE(
            SimpleNamespace(
                loglevel='debug', quiet=False, logfile='foo.log'
            )
        ),
        colmto.cse.cse.SumoCSE
    )

    l_rule_speed = colmto.cse.rule.SUMOMinimalSpeedRule(80.)

    l_rule_outside_position = colmto.cse.rule.SUMOPositionRule(
        bounding_box=((0., 0), (64.0, 1)),
        outside=True
    )

    l_sumo_cse = colmto.cse.cse.SumoCSE().add_rule(l_rule_outside_position).add_rule(l_rule_speed)

    assert_is_instance(l_sumo_cse, colmto.cse.cse.SumoCSE)
    assert_is_instance(l_sumo_cse.rules, frozenset)
    assert_in(l_rule_speed, l_sumo_cse.rules)
    assert_in(l_rule_outside_position, l_sumo_cse.rules)

    with assert_raises(TypeError):
        l_sumo_cse.add_rule('foo')

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            speed_max=random.randrange(0, 250)
        ) for _ in range(10)
    ]

    for i_vehicle in l_vehicles:
        i_vehicle.position = (random.randrange(0, 120), random.randint(0, 1))

    l_sumo_cse.apply(l_vehicles)

    for i_vehicle in l_vehicles:
        if 0 <= i_vehicle.position.x <= 64.0 and 0 <= i_vehicle.position.y <= 1 and \
                i_vehicle.speed_max >= 80.0:
            assert_equal(
                i_vehicle.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )
        else:
            assert_equal(
                i_vehicle.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )

    assert_equal(
        len(colmto.cse.cse.SumoCSE().add_rules_from_cfg({}).rules),
        0
    )

    l_sumo_cse = colmto.cse.cse.SumoCSE().add_rules_from_cfg(
        [
            {
                'type': 'ExtendableSUMOPositionRule',
                'args': {
                    'bounding_box': ((1350., -2.), (2500., 2.))
                },
                'subrule_operator': 'ANY',
                'subrules': [
                    {
                        'type': 'SUMOMinimalSpeedRule',
                        'args': {
                            'minimal_speed': 85/3.6
                        },
                    }
                ]
            }
        ]
    )

    assert_is_instance(tuple(l_sumo_cse.rules)[0], colmto.cse.rule.ExtendableSUMOPositionRule)

    # assert_is_instance(tuple(tuple(l_sumo_cse.rules)[0].subrules)[0], colmto.cse.rule.SUMOMinimalSpeedRule)

    l_rule_speed = colmto.cse.rule.SUMOMinimalSpeedRule.from_configuration(
        {
            'type': 'SUMOMinimalSpeedRule',
            'args': {
                'minimal_speed': 30/3.6
            }
        }
    )

    l_sumo_cse.add_rule(
        l_rule_speed
    )

    assert_in(l_rule_speed, l_sumo_cse.rules)


