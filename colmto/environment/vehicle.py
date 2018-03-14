# -*- coding: utf-8 -*-
# @package colmto.environment
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
'''Vehicle classes for storing vehicle data/attributes/states.'''

from types import MappingProxyType
from pandas import Series
from pandas import MultiIndex
import numpy

import colmto.cse.rule
import colmto.common.model
from colmto.common.property import Position
from colmto.common.property import Colour


class BaseVehicle(object):
    '''Base Vehicle.'''

    def __init__(self):
        '''C'tor'''

        self._properties = {
            'position': Position(x=0.0, y=0.0),
            'speed': 0.0,
        }

    @property
    def properties(self) -> MappingProxyType:
        '''
        :return: vehicle properties as MappingProxyType dictionary bundle
        '''
        return MappingProxyType(self._properties)

    @property
    def speed(self) -> float:
        '''
        :return: current speed at time step
        '''
        return self._properties.get('speed')

    @speed.setter
    def speed(self, speed: float):
        '''
        Set vehicle speed
        :param speed: current position
        '''
        self._properties['speed'] = float(speed)

    @property
    def position(self) -> Position:
        '''
        :return: current position
        '''
        return self._properties.get('position')

    @position.setter
    def position(self, position: Position):
        '''
        Set vehicle position
        :param position: current position
        '''
        self._properties['position'] = Position(*position)


class SUMOVehicle(BaseVehicle):
    '''SUMO vehicle class.

    **Note on statistics:**
    To properly store results from SUMO (discrete time vs. "continuous" space),
    there exists a `pandas.Series <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_ related to the current time step (self._time_based_series)
    and a `Series` for grid cells in x-direction (self._grid_based_series).
    As vehicles are expected to "jump" over cells while traveling faster than `cell width / time step`,
    we create an entry for each cell (initialised as `NaN`) and linear interpolate the missing values afterwards.

    '''

    # pylint: disable=too-many-arguments
    def __init__(self,
                 vehicle_type=None,
                 vtype_sumo_cfg=None,
                 speed_deviation=0.0,
                 sigma=0.0,
                 speed_max=0.0):
        '''
        C'tor.

        :param vehicle_type:
        :param vtype_sumo_cfg:
        :param speed_deviation:
        :param sigma:
        :param speed_max:

        '''

        super().__init__()

        if isinstance(vtype_sumo_cfg, dict):
            self._properties.update(vtype_sumo_cfg)

        self._properties.update(
            {
                'colour': Colour(red=255, green=255, blue=0, alpha=255),
                'start_time': 0.0,
                'speedDev': speed_deviation,
                'sigma': sigma,
                'maxSpeed': speed_max,
                'vType': vehicle_type,
                'vClass': colmto.cse.rule.SUMORule.to_allowed_class(),
                'grid_position': Position(x=0, y=0),
                'time_step': 0.0
            }
        )

        self._time_based_series = Series(
            # optionally if numpy.nan is required: [numpy.nan for i in range(30)],  # indices x number of cells of x-axis
            index=MultiIndex.from_product(
                iterables=[['position_x', 'position_y', 'dissatisfaction'], range(10)], # range(number of cells of x-axis)
                names=['type', 'timestep']
            )
        )

        self._grid_based_series = Series(
            index=MultiIndex.from_product(
                iterables=[['time_step', 'position_y', 'dissatisfaction'], [0]],
                names=['type', 'grid_position_x'])
        )

    @property
    def grid_position(self) -> Position:
        '''
        :return: current grid position
        '''
        return Position(*self._properties.get('grid_position'))

    @grid_position.setter
    def grid_position(self, position: Position):
        '''
        Updates current position
        :param position: current grid position
        '''
        self._properties['grid_position'] = Position(*position)

    @property
    def vehicle_type(self) -> str:
        '''
        :return: vehicle type
        '''
        return str(self._properties.get('vType'))

    @property
    def start_time(self) -> float:
        '''
        :return: start time
        '''
        return float(self._properties.get('start_time'))

    @start_time.setter
    def start_time(self, start_time: float):
        '''
        :param start_time: start time
        '''
        self._properties['start_time'] = float(start_time)

    @property
    def colour(self) -> Colour:
        '''
        :return: colour
        '''
        return Colour(*self._properties.get('colour'))

    @colour.setter
    def colour(self, colour: Colour):
        '''
        Update colour
        :param colour: Color (rgba tuple, e.g. (255, 255, 0, 255))
        '''
        self._properties['colour'] = Colour(*colour)

    @property
    def vehicle_class(self) -> str:
        '''
        :return: SUMO vehicle class
        '''
        return str(self._properties.get('vClass'))

    @property
    def speed_max(self) -> float:
        '''
        :return: self._properties.get('maxSpeed')
        '''
        return float(self._properties.get('maxSpeed'))

    @property
    def travel_time(self) -> float:
        '''
        :return: current travel time
        '''
        return float(self._travel_stats.get('travel_time'))

    @property
    def travel_stats(self) -> MappingProxyType:
        '''
        :return: MappingProxyType travel stats dictionary
        '''
        return MappingProxyType(self._travel_stats)

    @property
    def dsat_threshold(self) -> float:
        '''
        :return: dissatisfaction threshold, i.e. `self.properties.get('dsat_threshold')`
        '''
        return float(self._properties.get('dsat_threshold'))

    @dsat_threshold.setter
    def dsat_threshold(self, threshold: float):
        ''' sets dissatisfaction threshold '''
        self._properties['dsat_threshold'] = float(threshold)

    def record_travel_stats(self, time_step: float) -> BaseVehicle:
        r'''Record travel statistics to vehicle.
        Instruct vehicle to write travel stats, i.e. travel time, time loss, position,
        and dissatisfaction for a given time step into `self._travel_stats`

        :param time_step: current time step
        :return: future self

        '''

        # update current travel time
        self._travel_stats['travel_time'] = float(time_step) - self.start_time

        # current step number
        self._travel_stats.get('step').get('number').append(float(time_step))

        # position
        self._travel_stats.get('step').get('pos_x').append(self.position[0])
        self._travel_stats.get('step').get('pos_y').append(self.position[1])

        # grid based stats
        # check whether vehicle stayed in this grid cell
        if len(self._travel_stats.get('grid').get('pos_x')) + \
                len(self._travel_stats.get('grid').get('pos_y')) > 0 \
                and isinstance(self._travel_stats.get('grid').get('pos_x')[-1], list) \
                and isinstance(self._travel_stats.get('grid').get('pos_y')[-1], list) \
                and self._travel_stats.get('grid').get('pos_x')[-1][0] == self.grid_position[0] \
                and self._travel_stats.get('grid').get('pos_y')[-1][0] == self.grid_position[1]:
            self._travel_stats.get('grid').get('pos_x')[-1].append(self.grid_position[0])
            self._travel_stats.get('grid').get('pos_y')[-1].append(self.grid_position[1])
            self._travel_stats.get('grid').get('speed')[-1].append(self.speed)
            self._travel_stats.get('grid').get('time_loss')[-1].append(
                time_step - self.start_time - self.position[0] / self.speed_max
            )
            self._travel_stats.get('grid').get('relative_time_loss')[-1].append(
                (time_step - self.start_time - self.position[0] / self.speed_max) /
                (self.position[0] / self.speed_max)
            )

            self._travel_stats.get('grid').get('dissatisfaction')[-1].append(
                colmto.common.model.dissatisfaction(
                    time_step - self.start_time - self.position[0] / self.speed_max,
                    self.position[0] / self.speed_max,
                    self._properties.get('dsat_threshold')
                )
            )

        else:
            self._travel_stats.get('grid').get('pos_x').append([self.grid_position[0]])
            self._travel_stats.get('grid').get('pos_y').append([self.grid_position[1]])
            self._travel_stats.get('grid').get('speed').append([self.speed])
            self._travel_stats.get('grid').get('time_loss').append(
                [time_step - self.start_time - self.position[0] / self.speed_max]
            )
            self._travel_stats.get('grid').get('relative_time_loss').append(
                [
                    (time_step - self.start_time - self.position[0] / self.speed_max) /
                    (self.position[0] / self.speed_max)
                ]
            )
            self._travel_stats.get('grid').get('dissatisfaction').append(
                [
                    colmto.common.model.dissatisfaction(
                        time_step - self.start_time - self.position[0] / self.speed_max,
                        self.position[0] / self.speed_max,
                        self._properties.get('dsat_threshold')
                    )
                ]
            )

        # step based stats
        self._travel_stats.get('step').get('time_loss').append(
            time_step - self.start_time - self.position[0] / self.speed_max
        )
        self._travel_stats.get('step').get('relative_time_loss').append(
            (time_step - self.start_time - self.position[0] / self.speed_max) /
            (self.position[0] / self.speed_max)
        )

        self._travel_stats.get('step').get('speed').append(self.speed)

        self._travel_stats.get('step').get('dissatisfaction').append(
            colmto.common.model.dissatisfaction(
                time_step - self.start_time - self.position[0] / self.speed_max,
                self.position[0] / self.speed_max,
                self._properties.get('dsat_threshold')
            )
        )

        # force dissatisfaction of first entry to 0.0 to avoid start-time quirks introduced by SUMO
        if self._travel_stats.get('grid').get('dissatisfaction')[0] != [0.]:
            self._travel_stats.get('grid').get('dissatisfaction')[0] = [0.]
        if self._travel_stats.get('step').get('dissatisfaction')[0] != 0.:
            self._travel_stats.get('step').get('dissatisfaction')[0] = 0.

        # force time_loss of first entry to 0.0 to avoid start-time quirks
        if self._travel_stats.get('grid').get('time_loss')[0] != [0.]:
            self._travel_stats.get('grid').get('time_loss')[0] = [0.]
        if self._travel_stats.get('step').get('time_loss')[0] != 0.:
            self._travel_stats.get('step').get('time_loss')[0] = 0.

        # force relative_time_loss of first entry to 0.0 to avoid start-time quirks
        if self._travel_stats.get('grid').get('relative_time_loss')[0] != [0.]:
            self._travel_stats.get('grid').get('relative_time_loss')[0] = [0.]
        if self._travel_stats.get('step').get('relative_time_loss')[0] != 0.:
            self._travel_stats.get('step').get('relative_time_loss')[0] = 0.

        return self

    def change_vehicle_class(self, class_name: str) -> BaseVehicle:
        '''
        Change vehicle class

        :param class_name: vehicle class
        :return: future self

        '''

        self._properties['vClass'] = str(class_name)
        return self

    def update(self, position: Position, lane_index: int, speed: float, time_step: float) -> BaseVehicle:
        '''
        Update current properties of vehicle providing data acquired from TraCI call.

        For the grid cell the vehicle is in, take the global position in x-direction divided by grid
        cell size and int-rounded. For the y-coordinate take the lane index.

        :NOTE: We assume a fixed grid cell size of 4 meters. This has to be set via cfg in future.
        :todo: make grid-size configurable

        :param position: tuple TraCI provided position
        :param lane_index: int TraCI provided lane index
        :param speed: float TraCI provided speed
        :param time_step: float TraCI provided time step
        :return: future Vehicle reference

        '''

        self._properties['position'] = Position(*position)
        self._properties['grid_position'] = Position(*position).gridified(width=4.)
        self._properties['speed'] = float(speed)
        self._properties['time_step'] = float(time_step)



        return self
