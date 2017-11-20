# -*- coding: utf-8 -*-
# @package tests.cse
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
'''
colmto: Test module for environment.cse.
'''
import random

from nose.tools import assert_equal
from nose.tools import assert_is_instance
from nose.tools import assert_raises
from nose.tools import assert_in

import colmto.cse.cse
import colmto.cse.rule
import colmto.environment.vehicle


class Namespace(object):
    '''Namespace similar to argparse'''
    # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        '''C'tor.'''
        self.__dict__.update(kwargs)


def test_base_cse():
    '''
    Test BaseCSE class
    '''
    assert_is_instance(colmto.cse.cse.BaseCSE(), colmto.cse.cse.BaseCSE)
    assert_is_instance(
        colmto.cse.cse.BaseCSE(
            Namespace(
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
            Namespace(
                loglevel='debug', quiet=False, logfile='foo.log'
            )
        ),
        colmto.cse.cse.SumoCSE
    )

    l_rule_speed = colmto.cse.rule.SUMOSpeedRule(speed_range=(0., 80.))
    l_rule_position = colmto.cse.rule.SUMOPositionRule(
        position_bbox=((0., 0), (64.0, 1))
    )
    l_subrule_speed = colmto.cse.rule.SUMOSpeedRule(speed_range=(0., 60.))
    l_rule_position.add_rule(l_subrule_speed)

    l_sumo_cse = colmto.cse.cse.SumoCSE().add_rule(l_rule_speed).add_subrule(l_rule_position)

    assert_is_instance(l_sumo_cse, colmto.cse.cse.SumoCSE)
    assert_is_instance(l_sumo_cse.rules, tuple)
    assert_in(l_rule_position, l_sumo_cse.rules)
    assert_in(l_rule_position, l_sumo_cse.rules)

    with assert_raises(TypeError):
        l_sumo_cse.add_rule('foo')

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(
            speed_max=random.randrange(0, 250)
        ) for _ in range(2342)
        ]
    for i_vehicle in l_vehicles:
        i_vehicle.position = (random.randrange(0, 120), random.randint(0, 1))

    l_sumo_cse.apply(l_vehicles)

    for i, i_result in enumerate(l_vehicles):
        if (0 <= l_vehicles[i].position.x <= 64.0 and 0 <= l_vehicles[i].position.y <= 1
                and 0. <= l_vehicles[i].speed_max <= 60.0) \
                or 0. <= l_vehicles[i].speed_max <= 80.0:
            assert_equal(
                i_result.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )
        else:
            assert_equal(
                i_result.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )

    assert_equal(
        colmto.cse.cse.SumoCSE().add_rules_from_cfg(None).rules,
        tuple()
    )

    l_sumo_cse = colmto.cse.cse.SumoCSE().add_rules_from_cfg(
        [
            {
                'type': 'SUMOSpeedRule',
                'behaviour': 'deny',
                'args': {
                    'speed_range': (0., 30/3.6)
                }
            },
            {
                'type': 'SUMOPositionRule',
                'behaviour': 'deny',
                'args': {
                    'position_bbox': ((1350., -2.), (2500., 2.))
                },
                'vehicle_rules': {
                    'rule': 'any',
                    'rules': [
                        {
                            'type': 'SUMOSpeedRule',
                            'behaviour': 'deny',
                            'args': {
                                'speed_range': (0., 85/3.6)
                            },
                        }
                    ]
                }
            }
        ]
    )

    assert_is_instance(l_sumo_cse.rules[0], colmto.cse.rule.SUMOSpeedRule)
    assert_is_instance(l_sumo_cse.rules[1], colmto.cse.rule.SUMOPositionRule)
    assert_is_instance(
        l_sumo_cse.rules[1].subrules[0],
        colmto.cse.rule.SUMOSpeedRule
    )
