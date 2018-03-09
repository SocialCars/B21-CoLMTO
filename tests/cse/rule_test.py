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

import colmto.cse.rule
import colmto.environment.vehicle

import numpy

from nose.tools import assert_equal
from nose.tools import assert_false
from nose.tools import assert_is_instance
from nose.tools import assert_raises
from nose.tools import assert_true
from nose.tools import assert_tuple_equal


def test_behaviour():
    '''
    Test Behaviour enum
    '''
    assert_equal(colmto.cse.rule.Behaviour.ALLOW.vclass, colmto.cse.rule.Behaviour.ALLOW.value)
    assert_equal(colmto.cse.rule.Behaviour.DENY.vclass, colmto.cse.rule.Behaviour.DENY.value)
    assert_equal(colmto.cse.rule.Behaviour.ALLOW.value, 'custom2')
    assert_equal(colmto.cse.rule.Behaviour.DENY.value, 'custom1')


def test_ruleoperator():
    '''
    Test RuleOperator enum
    '''
    assert_equal(colmto.cse.rule.RuleOperator.ANY.value, any)
    assert_equal(colmto.cse.rule.RuleOperator.ALL.value, all)
    assert_equal(colmto.cse.rule.RuleOperator.ANY.evaluate([True, True]), True)
    assert_equal(colmto.cse.rule.RuleOperator.ANY.evaluate([False, True]), True)
    assert_equal(colmto.cse.rule.RuleOperator.ANY.evaluate([True, False]), True)
    assert_equal(colmto.cse.rule.RuleOperator.ANY.evaluate([False, False]), False)
    assert_equal(colmto.cse.rule.RuleOperator.ALL.evaluate([True, True]), True)
    assert_equal(colmto.cse.rule.RuleOperator.ALL.evaluate([False, True]), False)
    assert_equal(colmto.cse.rule.RuleOperator.ALL.evaluate([True, False]), False)
    assert_equal(colmto.cse.rule.RuleOperator.ALL.evaluate([False, False]), False)


def test_base_rule():
    '''
    Test BaseRule class
    '''
    l_base_rule = colmto.cse.rule.BaseRule(
        colmto.cse.rule.Behaviour.DENY
    )
    assert_is_instance(l_base_rule, colmto.cse.rule.BaseRule)


def test_behaviourfromstringorelse():
    '''Test colmto.cse.rule.BaseRule.behaviour_from_string.'''
    assert_equal(
        colmto.cse.rule.BaseRule(
            colmto.cse.rule.Behaviour.DENY
        ).behaviour_from_string('Allow', colmto.cse.rule.Behaviour.DENY),
        colmto.cse.rule.Behaviour.ALLOW
    )
    assert_equal(
        colmto.cse.rule.BaseRule(
            colmto.cse.rule.Behaviour.DENY
        ).behaviour_from_string('Deny', colmto.cse.rule.Behaviour.ALLOW),
        colmto.cse.rule.Behaviour.DENY
    )
    assert_equal(
        colmto.cse.rule.BaseRule(
            colmto.cse.rule.Behaviour.DENY
        ).behaviour_from_string('Meh', colmto.cse.rule.Behaviour.ALLOW),
        colmto.cse.rule.Behaviour.ALLOW
    )


def test_ruleoperatorfromstring():
    '''Test colmto.cse.rule.BaseRule.ruleoperator_from_string.'''
    assert_equal(
        colmto.cse.rule.SUMOVehicleRule(
            behaviour=colmto.cse.rule.Behaviour.DENY,
            rule_operator=colmto.cse.rule.RuleOperator.ANY
        ).ruleoperator_from_string('All', colmto.cse.rule.RuleOperator.ANY),
        colmto.cse.rule.RuleOperator.ALL
    )
    assert_equal(
        colmto.cse.rule.SUMOVehicleRule(
            behaviour=colmto.cse.rule.Behaviour.DENY,
            rule_operator=colmto.cse.rule.RuleOperator.ANY
        ).ruleoperator_from_string('Any', colmto.cse.rule.RuleOperator.ALL),
        colmto.cse.rule.RuleOperator.ANY
    )
    assert_equal(
        colmto.cse.rule.SUMOVehicleRule(
            behaviour=colmto.cse.rule.Behaviour.DENY,
            rule_operator=colmto.cse.rule.RuleOperator.ANY
        ).ruleoperator_from_string('Meh', colmto.cse.rule.RuleOperator.ALL),
        colmto.cse.rule.RuleOperator.ALL
    )


def test_sumo_rule():
    '''
    Test SumoRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMORule(
        colmto.cse.rule.Behaviour.DENY
    )
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMORule)

    assert_equal(l_sumo_rule.to_disallowed_class(), 'custom1')
    assert_equal(l_sumo_rule.to_allowed_class(), 'custom2')


def test_sumo_null_rule():
    '''
    Test SumoNullRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMONullRule()
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMONullRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle() for _ in range(23)
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
        assert_equal(l_vehicles[i].vehicle_class, i_result.vehicle_class)
        assert_false(l_sumo_rule.applies_to(l_vehicles[i]))


def test_sumo_vtype_rule():
    '''Test SUMOVTypeRule class'''
    assert_is_instance(colmto.cse.rule.SUMOVTypeRule(), colmto.cse.rule.SUMOVTypeRule)

    assert_equal(
        str(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger',
                behaviour=colmto.cse.rule.Behaviour.DENY
            ).add_subrule(
                colmto.cse.rule.SUMOPositionRule(
                    position_bbox=((0., -1.), (100., 1.))
                )
            )
        ),
        '<class \'colmto.cse.rule.SUMOVTypeRule\'>: vehicle_type = passenger, behaviour = custom1, '
        'rule_operator: RuleOperator.ANY, subrules: <class \'colmto.cse.rule.SUMOPositionRule\'>'
    )

    assert_true(
        colmto.cse.rule.SUMOVTypeRule(
            vehicle_type='passenger',
            behaviour=colmto.cse.rule.Behaviour.DENY
        ).applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                vehicle_type='passenger'
            )
        )
    )

    assert_false(
        colmto.cse.rule.SUMOVTypeRule(
            vehicle_type='truck',
            behaviour=colmto.cse.rule.Behaviour.ALLOW
        ).applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                vehicle_type='passenger'
            )
        )
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger',
                behaviour=colmto.cse.rule.Behaviour.DENY
            ).apply(
                [colmto.environment.vehicle.SUMOVehicle(vehicle_type='passenger')]
            )
        ).vehicle_class,
        colmto.cse.rule.Behaviour.DENY.value
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='passenger',
                behaviour=colmto.cse.rule.Behaviour.ALLOW
            ).apply(
                [colmto.environment.vehicle.SUMOVehicle(vehicle_type='passenger')]
            )
        ).vehicle_class,
        colmto.cse.rule.Behaviour.ALLOW.value
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOVTypeRule(
                vehicle_type='truck',
                behaviour=colmto.cse.rule.Behaviour.DENY
            ).apply(
                [colmto.environment.vehicle.SUMOVehicle(vehicle_type='passenger')]
            )
        ).vehicle_class,
        colmto.cse.rule.Behaviour.ALLOW.value
    )


def test_sumo_extendable_rule():
    '''Test SUMOExtendableRule class'''
    with assert_raises(ValueError):
        colmto.cse.rule.SUMOExtendableRule(
            rules=[colmto.cse.rule.SUMONullRule()],
            rule_operator='any'
        )

    with assert_raises(ValueError):
        colmto.cse.rule.SUMOExtendableRule(
            rules=[colmto.cse.rule.SUMOMinimalSpeedRule()],
            rule_operator='foo'
        )

    l_sumo_rule = colmto.cse.rule.SUMOExtendableRule(
        subrules=[colmto.cse.rule.SUMOMinimalSpeedRule()],
        subrule_operator=colmto.cse.rule.RuleOperator.ANY
    )

    assert_equal(l_sumo_rule.subrule_operator, colmto.cse.rule.RuleOperator.ANY)
    l_sumo_rule.subrule_operator = colmto.cse.rule.RuleOperator.ALL
    assert_equal(l_sumo_rule.subrule_operator, colmto.cse.rule.RuleOperator.ALL)

    with assert_raises(ValueError):
        l_sumo_rule.rule_operator = 'foo'

    l_sumo_rule.add_subrule(colmto.cse.rule.SUMOPositionRule())

    with assert_raises(TypeError):
        l_sumo_rule.add_subrule(colmto.cse.rule.SUMONullRule())

    l_sumo_rule = colmto.cse.rule.SUMOExtendableRule(subrules=[])
    l_sumo_sub_rule = colmto.cse.rule.SUMOMinimalSpeedRule(speed_range=(0., 60.))
    l_sumo_rule.add_subrule(l_sumo_sub_rule)

    assert_true(
        l_sumo_rule.subrules_apply_to(
            colmto.environment.vehicle.SUMOVehicle(
                speed_max=50.,
            )
        )
    )

    assert_true(
        l_sumo_sub_rule.applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                speed_max=50.,
            )
        )
    )

    l_sumo_rule = colmto.cse.rule.SUMOExtendableRule(
        subrules=[],
        subrule_operator=colmto.cse.rule.RuleOperator.ALL
    )
    l_sumo_rule.add_subrule(l_sumo_sub_rule)

    assert_true(
        l_sumo_rule.subrules_apply_to(
            colmto.environment.vehicle.SUMOVehicle(
                speed_max=50.,
            )
        )
    )

    assert_true(
        l_sumo_sub_rule.applies_to(
            colmto.environment.vehicle.SUMOVehicle(
                speed_max=50.,
            )
        )
    )


def test_sumo_universal_rule():
    '''Test SUMOUniversalRule class'''

    assert_true(
        colmto.cse.rule.SUMOUniversalRule().applies_to(
            colmto.environment.vehicle.SUMOVehicle()
        )
    )

    assert_equal(
        next(
            colmto.cse.rule.SUMOUniversalRule().apply(
                (colmto.environment.vehicle.SUMOVehicle(),)
            )
        ).vehicle_class,
        'custom1'
    )


def test_sumo_speed_rule():
    '''
    Test SUMOMinimalSpeedRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMOMinimalSpeedRule(speed_range=numpy.array((0., 60.)))
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMOMinimalSpeedRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle(
            speed_max=random.randrange(0, 120)
        ) for _ in range(4711)
        ]

    l_results = l_sumo_rule.apply(l_vehicles)

    for i, i_results in enumerate(l_results):
        if 0.0 <= l_vehicles[i].speed_max <= 60.0:
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )
        else:
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )

    assert_equal(
        str(
            colmto.cse.rule.SUMOMinimalSpeedRule(
                speed_range=(0., 60.),
                behaviour=colmto.cse.rule.Behaviour.DENY
            ).add_subrule(
                colmto.cse.rule.SUMOPositionRule(
                    position_bbox=((0., -1.), (100., 1.))
                )
            )
        ),
        '<class \'colmto.cse.rule.SUMOMinimalSpeedRule\'>: speed_range = [  0.  60.], behaviour = DENY, ru'
        'le_operator: RuleOperator.ANY, subrules: <class \'colmto.cse.rule.SUMOPositionRule\'>'
    )


def test_sumo_position_rule():
    '''
    Test SUMOPositionRule class
    '''
    l_sumo_rule = colmto.cse.rule.SUMOPositionRule(position_bbox=((0., -1.), (100., 1.)))
    assert_is_instance(l_sumo_rule, colmto.cse.rule.SUMOPositionRule)

    l_vehicles = [
        colmto.environment.vehicle.SUMOVehicle() for _ in range(4711)
    ]
    for i_vehicle in l_vehicles:
        i_vehicle.position = (random.randrange(0, 200), 0.)

    l_results = l_sumo_rule.apply(l_vehicles)

    for i, i_results in enumerate(l_results):
        if 0. <= l_vehicles[i].position[0] <= 100.0:
            assert_true(
                l_sumo_rule.applies_to(l_vehicles[i])
            )
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_disallowed_class()
            )
        else:
            assert_false(
                l_sumo_rule.applies_to(l_vehicles[i])
            )
            assert_equal(
                i_results.vehicle_class,
                colmto.cse.rule.SUMORule.to_allowed_class()
            )

    assert_tuple_equal(
        colmto.cse.rule.SUMOPositionRule(
            position_bbox=((0., -1.), (100., 1.)),
            behaviour=colmto.cse.rule.Behaviour.DENY
        ).position_bbox,
        ((0., -1.), (100., 1.))
    )

    assert_equal(
        str(
            colmto.cse.rule.SUMOPositionRule(
                position_bbox=((0., -1.), (100., 1.)),
                behaviour=colmto.cse.rule.Behaviour.DENY
            ).add_subrule(
                colmto.cse.rule.SUMOMinimalSpeedRule(
                    speed_range=(0., 60.)
                )
            )
        ),
        '<class \'colmto.cse.rule.SUMOPositionRule\'>: position_bbox = ((0.0, -1.0), (100.0, 1.0)),'
        ' behaviour = custom1, rule_operator: RuleOperator.ANY, subrules: <class \'colmto.cse.rule.'
        'SUMOMinimalSpeedRule\'>'
    )
