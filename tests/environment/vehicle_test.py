# -*- coding: utf-8 -*-
# @package tests.environment
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
colmto: Test module for environment.vehicle.
'''
import numpy
from nose.tools import assert_equal
from nose.tools import assert_almost_equal
from nose.tools import assert_list_equal


import colmto.environment.vehicle
from colmto.common.helper import Position, VehicleType


def test_basevehicle():
    '''
    Test BaseVehicle class
    '''

    # test default values
    l_basevehicle = colmto.environment.vehicle.BaseVehicle()

    assert_equal(l_basevehicle.speed, 0.0)
    assert_equal(l_basevehicle.position, (0.0, 0))

    # test custom values
    l_basevehicle = colmto.environment.vehicle.BaseVehicle()
    l_basevehicle.position = numpy.array([23.0, 0])
    l_basevehicle.speed = 12.1

    assert_equal(l_basevehicle.speed, 12.1)
    assert_equal(l_basevehicle.position, (23.0, 0))
    assert_equal(l_basevehicle.properties.get('position'), (23.0, 0))
    assert_equal(l_basevehicle.properties.get('speed'), 12.1)


def test_sumovehicle():
    '''
    Test SUMOVehicle class.
    '''

    # test default values
    l_sumovehicle = colmto.environment.vehicle.SUMOVehicle(
        environment={'gridlength': 200, 'gridcellwidth': 4}
    )

    assert_equal(l_sumovehicle.speed_max, 0.0)
    assert_equal(l_sumovehicle.speed, 0.0)
    assert_equal(l_sumovehicle.position, (0.0, 0))
    assert_equal(l_sumovehicle.vehicle_type, VehicleType.UNDEFINED)
    assert_equal(l_sumovehicle.colour, (255, 255, 0, 255))

    # test custom values
    l_sumovehicle = colmto.environment.vehicle.SUMOVehicle(
        speed_max=27.777,
        speed_deviation=1.2,
        environment={'gridlength': 200, 'gridcellwidth': 4},
        vehicle_type='passenger',
        vtype_sumo_cfg={
            'length': 3.00,
            'minGap': 2.50
        }
    )
    l_sumovehicle.position = numpy.array([42.0, 0])
    l_sumovehicle.colour = (128, 64, 255, 255)
    l_sumovehicle.speed_current = 12.1
    l_sumovehicle.start_time = 13

    assert_equal(l_sumovehicle.speed_max, 27.777)
    assert_equal(l_sumovehicle.speed_current, 12.1)
    assert_equal(l_sumovehicle.position, (42.0, 0))
    assert_equal(l_sumovehicle.vehicle_type, VehicleType.PASSENGER)
    assert_equal(l_sumovehicle.colour, (128, 64, 255, 255))
    assert_equal(l_sumovehicle.start_time, 13)
    assert_equal(l_sumovehicle._grid_position, (0, 0))

    l_sumovehicle._grid_position = (1, 2)

    assert_equal(l_sumovehicle._grid_position, (1, 2))
    assert_equal(l_sumovehicle.properties.get('grid_position'), (1, 2))
    assert_equal(l_sumovehicle._travel_time, 0.0)


def test_update():
    '''Test update'''
    l_sumovehicle = colmto.environment.vehicle.SUMOVehicle(
        environment={'gridlength': 200, 'gridcellwidth': 4},
        speed_max=10,
        vtype_sumo_cfg={'dsat_threshold': 0.2}
    )
    l_sumovehicle.update(
        position=colmto.environment.vehicle.Position(20, 2),
        lane_index=1,
        speed=12.1,
        time_step=2
    )
    assert_equal(
        l_sumovehicle.position,
        (20, 2)
    )
    assert_equal(
        l_sumovehicle.speed,
        12.1
    )
    assert_equal(
        l_sumovehicle._grid_position,
        (round(20/4)-1, -1)
    )
