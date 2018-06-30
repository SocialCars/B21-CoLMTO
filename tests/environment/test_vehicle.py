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
import unittest
import numpy
import colmto.environment.vehicle
from colmto.common.helper import Behaviour
from colmto.common.helper import VehicleType
from colmto.common.helper import VehicleDisposition


class TestVehicle(unittest.TestCase):
    '''
    Test cases for Vehicle
    '''

    def test_basevehicle(self):
        '''
        Test BaseVehicle class
        '''

        # test default values
        l_basevehicle = colmto.environment.vehicle.BaseVehicle()

        self.assertEqual(l_basevehicle._speed, 0.0)         # pylint: disable=protected-access
        self.assertEqual(l_basevehicle.position, (0.0, 0))

        # test custom values
        l_basevehicle = colmto.environment.vehicle.BaseVehicle()
        l_basevehicle.position = numpy.array([23.0, 0])
        l_basevehicle._speed = 12.1                         # pylint: disable=protected-access

        self.assertEqual(l_basevehicle._speed, 12.1)        # pylint: disable=protected-access
        self.assertEqual(l_basevehicle.position, (23.0, 0))
        self.assertEqual(l_basevehicle.properties.get('position'), (23.0, 0))
        self.assertEqual(l_basevehicle.properties.get('speed'), 12.1)


    def test_sumovehicle(self):
        '''
        Test SUMOVehicle class.
        '''

        # test default values
        l_sumovehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4}
        )
        self.assertEqual(l_sumovehicle.speed_max, 0.0)
        self.assertEqual(l_sumovehicle._speed, 0.0)         # pylint: disable=protected-access
        self.assertEqual(l_sumovehicle.position, (0.0, 0))
        self.assertEqual(l_sumovehicle.vehicle_type, VehicleType.UNDEFINED)
        self.assertEqual(l_sumovehicle.colour, (255, 255, 0, 255))
        self.assertEqual(l_sumovehicle._time_step, 0.0)     # pylint: disable=protected-access
        l_sumovehicle._time_step = 42.1                     # pylint: disable=protected-access
        self.assertEqual(l_sumovehicle._time_step, 42.1)    # pylint: disable=protected-access
        self.assertIsInstance(l_sumovehicle.properties.get('cooperation_disposition'), VehicleDisposition)
        self.assertIs(l_sumovehicle.properties.get('cooperation_disposition'), VehicleDisposition.COOPERATIVE)
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
        l_sumovehicle.normal_colour = (128, 64, 255, 255)
        l_sumovehicle.start_time = 13
        self.assertTupleEqual(l_sumovehicle.start_position, (0.0, 0.0))
        l_sumovehicle.start_position = (1.2, 3.4)
        self.assertEqual(l_sumovehicle.start_position.x, 1.2)
        self.assertEqual(l_sumovehicle.start_position.y, 3.4)
        self.assertEqual(l_sumovehicle.start_position.gridified(2).x, 0)
        self.assertEqual(l_sumovehicle.start_position.gridified(2).y, 1)
        self.assertTupleEqual(l_sumovehicle.start_position, (1.2, 3.4))

        self.assertEqual(l_sumovehicle.speed_max, 27.777)
        self.assertEqual(l_sumovehicle.position, (42.0, 0))
        self.assertEqual(l_sumovehicle.vehicle_type, VehicleType.PASSENGER)
        self.assertEqual(l_sumovehicle.normal_colour, (128, 64, 255, 255))
        self.assertEqual(l_sumovehicle.start_time, 13)
        self.assertEqual(l_sumovehicle._grid_position, (0, 0))  # pylint: disable=protected-access

        l_sumovehicle._grid_position = (1, 2)                   # pylint: disable=protected-access

        self.assertEqual(l_sumovehicle._grid_position, (1, 2))  # pylint: disable=protected-access
        self.assertEqual(l_sumovehicle.properties.get('grid_position'), (1, 2))
        self.assertEqual(l_sumovehicle._travel_time, 0.0)       # pylint: disable=protected-access

    def test_disposition(self):
        '''Test disposition, i.e. cooperativity of vehicle'''
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
        l_sumovehicle._properties['cooperation_disposition'] = VehicleDisposition.UNCOOPERATIVE # pylint: disable=protected-access
        self.assertIsInstance(l_sumovehicle.properties.get('cooperation_disposition'), VehicleDisposition)
        self.assertIs(l_sumovehicle.properties.get('cooperation_disposition'), VehicleDisposition.UNCOOPERATIVE)
        self.assertEqual(l_sumovehicle.vehicle_class, Behaviour.ALLOW.vclass)
        l_sumovehicle.deny_otl_access()
        self.assertEqual(l_sumovehicle.vehicle_class, Behaviour.ALLOW.vclass)
        self.assertEqual(l_sumovehicle.colour, (127, 127, 127, 255))



    def test_update(self):
        '''Test update'''
        l_sumovehicle = colmto.environment.vehicle.SUMOVehicle(
            environment={'gridlength': 200, 'gridcellwidth': 4},
            speed_max=15,
            vtype_sumo_cfg={'dsat_threshold': 0.2}
        )

        self.assertEqual(l_sumovehicle.dsat_threshold, 0.2)
        self.assertEqual(l_sumovehicle.speed_max, 15)
        self.assertEqual(l_sumovehicle.dissatisfaction, 0.0)
        l_sumovehicle.position = (0, 0)
        l_sumovehicle.start_time = 0

        l_sumovehicle.update(
            position=colmto.environment.vehicle.Position(15000, 0),
            lane_index=1,
            speed=15,
            time_step=1000
        )

        self.assertAlmostEqual(l_sumovehicle.dissatisfaction, 0.0, places=4)

        self.assertEqual(
            l_sumovehicle.position,
            (15000, 0)
        )
        self.assertEqual(
            l_sumovehicle._speed,           # pylint: disable=protected-access
            15
        )
        self.assertEqual(
            l_sumovehicle._grid_position,   # pylint: disable=protected-access
            (round(15000/4)-1, -1)
        )
        self.assertEqual(
            l_sumovehicle._time_step,       # pylint: disable=protected-access
            1000
        )

        l_sumovehicle.update(
            position=colmto.environment.vehicle.Position(12500, 0),
            lane_index=0,
            speed=12,
            time_step=1000
        )

        self.assertAlmostEqual(l_sumovehicle.dissatisfaction, .5)


if __name__ == '__main__':
    unittest.main()
