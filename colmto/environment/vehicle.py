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

from collections import namedtuple
from types import MappingProxyType
import pandas

import colmto.cse.rule
import colmto.common.model
from colmto.common.property import Position, VehicleType
from colmto.common.property import GridPosition
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
                 environment: dict,
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
        :param grid_length:

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

        self._environment = environment

        self._time_based_series = pandas.Series(
            index=pandas.MultiIndex.from_product(
                iterables=[
                    [
                        'position_x',  # todo: use Metrics enum
                        'position_y',
                        'grid_position_x',
                        'grid_position_y',
                        'dissatisfaction',
                        'travel_time',
                        'time_loss',
                        'relative_time_loss'
                    ], [0]
                ],
                names=['metric', 'timestep']
            )
        )

        self._grid_based_series = pandas.Series(
            index=pandas.MultiIndex.from_product(
                iterables=[
                    [
                        'time_step',  # todo: use Metrics enum
                        'position_y',
                        'grid_position_y',
                        'dissatisfaction',
                        'travel_time',
                        'time_loss',
                        'relative_time_loss'
                    ], range(int(environment.get('gridlength')))  # range(number of cells of x-axis)
                ],
                names=['metric', 'grid_position_x']
            )
        )

    @property
    def _position(self) -> Position:
        '''
        :return: current position
        '''
        return Position(*self._properties.get('position'))

    @_position.setter
    def _position(self, position: Position):
        '''
        Updates current position
        :param position: current position
        '''
        self._properties['position'] = Position(*position)

    @property
    def _grid_position(self) -> GridPosition:
        '''
        :return: current grid position
        '''
        return GridPosition(*self._properties.get('grid_position'))

    @_grid_position.setter
    def _grid_position(self, position: GridPosition):
        '''
        Updates current position
        :param position: current grid position
        '''
        self._properties['grid_position'] = GridPosition(*position)

    @property
    def vehicle_type(self) -> VehicleType:
        '''
        :return: vehicle type
        '''
        return VehicleType[str(self._properties.get('vType')).upper()]

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
    def _travel_time(self) -> float:
        '''
        :return: current travel time
        '''
        return float(self._properties['travel_time'])

    @_travel_time.setter
    def _travel_time(self, travel_time: float):
        '''
        Updates current travel time
        :param travel_time: current travel time
        '''
        self._properties['travel_time'] = float(travel_time)

    @property
    def _time_step(self) -> float:
        '''
        Current time step
        :return: time step
        '''
        return float(self._properties['time_step'])

    @_time_step.setter
    def _time_step(self, time_step: float):
        '''
        Updates current time step
        :param time_step: time step
        '''
        self._properties['time_step'] = float(time_step)

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
    def _speed(self) -> float:
        '''
        :return: self._properties.get('speed')
        '''
        return float(self._properties.get('speed'))

    @_speed.setter
    def _speed(self, speed: float):
        '''
        Updates current speed.

        @retval travel time
        '''
        self._properties['speed'] = float(speed)

    @property
    def speed_max(self) -> float:
        '''
        :return: self._properties.get('maxSpeed')
        '''
        return float(self._properties.get('maxSpeed'))

    @property
    def dsat_threshold(self) -> float:
        '''
        :return: dissatisfaction threshold, i.e. `self.properties.get('dsat_threshold')`
        '''
        return float(self._properties.get('dsat_threshold'))

    def statistic_series_grid(self, interpolate=False) -> pandas.Series:
        '''
        Recorded travel statistics as `pandas.Series`.

        :note: To properly store results from SUMO (discrete time vs. "continuous" space), there exists a `pandas.Series <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_ related to the current time step (self._time_based_series) and a `Series` for grid cells in x-direction (self._grid_based_series).
        As vehicles are expected to "jump" over cells while traveling faster than `cell width / time step`, we create an entry for each cell (initialised as `NaN`) and linear interpolate the missing values afterwards.

        :param interpolate: return a data copy with NaN values linear interpolated
        :return: grid-based `pandas.Series`
        '''

        return pandas.concat(
            (
                self._grid_based_series[i_metric].interpolate()
                for i_metric in ('time_step',
                               'position_y',
                               'grid_position_y',
                               'dissatisfaction',
                               'travel_time',
                               'time_loss',
                               'relative_time_loss')
            ),
            keys=('time_step',
                  'position_y',
                  'grid_position_y',
                  'dissatisfaction',
                  'travel_time',
                  'time_loss',
                  'relative_time_loss')
        ) if interpolate else self._grid_based_series

    def statistic_series_time(self, interpolate=False) -> pandas.Series:
        '''
        Recorded travel statistics as `pandas.Series`.

        :note: To properly store results from SUMO (discrete time vs. "continuous" space), there exists a `pandas.Series <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_ related to the current time step (self._time_based_series) and a `Series` for grid cells in x-direction (self._grid_based_series).
        As vehicles are expected to "jump" over cells while traveling faster than `cell width / time step`, we create an entry for each cell (initialised as `NaN`) and linear interpolate the missing values afterwards.

        :param interpolate: return a data copy with NaN values linear interpolated
        :return: timestep-based `pandas.Series`
        '''

        return pandas.concat(
            (
                self._time_based_series[i_type].interpolate()
                for i_type in ('position_x',
                               'position_y',
                               'grid_position_x',
                               'grid_position_y',
                               'dissatisfaction',
                               'travel_time',
                               'time_loss',
                               'relative_time_loss')
             ),
            keys=('position_x',
                  'position_y',
                  'grid_position_x',
                  'grid_position_y',
                  'dissatisfaction',
                  'travel_time',
                  'time_loss',
                  'relative_time_loss')
        ) if interpolate else self._time_based_series

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
        NOTE: We assume a fixed grid cell size of 4 meters. This has to be set via cfg in future.

        :NOTE: We assume a fixed grid cell size of 4 meters. This has to be set via cfg in future.

        :param position: tuple TraCI provided position
        :param lane_index: int TraCI provided lane index
        :param speed: float TraCI provided speed
        :param time_step: float TraCI provided time step
        :return: future Vehicle reference

        '''

        # update current vehicle properties
        self._position = Position(*position)
        self._grid_position = Position(*position).gridified(width=self._environment.get('gridcellwidth'))
        self._speed = float(speed)
        self._time_step = float(time_step)
        self._travel_time = float(time_step) - self.start_time

        # update data series based on grid cell
        l_dissatisfaction = colmto.common.model.dissatisfaction(
            time_step - self.start_time - self._position.x / self.speed_max,
            self._position.x / self.speed_max,
            self.dsat_threshold
        )
        self._grid_based_series['time_step', self._grid_position.x] = float(time_step)
        self._grid_based_series['position_y', self._grid_position.x] = self._position.y
        self._grid_based_series['grid_position_y', self._grid_position.x] = self._grid_position.y
        self._grid_based_series['dissatisfaction', self._grid_position.x] = l_dissatisfaction
        self._grid_based_series['travel_time', self._grid_position.x] = self._travel_time
        self._grid_based_series['time_loss', self._grid_position.x] = time_step - self.start_time - self._position.x / self.speed_max
        self._grid_based_series['relative_time_loss', self._grid_position.x] = (time_step - self.start_time - self._position.x / self.speed_max) / (self._position.x / self.speed_max)
        self._grid_based_series['time_step', self._grid_position.x] = float(time_step)

        # update data series based on time step
        self._time_based_series['position_x', int(time_step)] = self._position.x
        self._time_based_series['position_y', int(time_step)] = self._position.y
        self._time_based_series['grid_position_x', int(time_step)] = self._grid_position.x
        self._time_based_series['grid_position_y', int(time_step)] = self._grid_position.y
        self._time_based_series['dissatisfaction', int(time_step)] = l_dissatisfaction
        self._time_based_series['travel_time', int(time_step)] = self._travel_time
        self._time_based_series['time_loss', int(time_step)] = time_step - self.start_time - self._position.x / self.speed_max
        self._time_based_series['relative_time_loss', int(time_step)] = (time_step - self.start_time - self._position.x / self.speed_max) / (self._position.x / self.speed_max)

        return self
