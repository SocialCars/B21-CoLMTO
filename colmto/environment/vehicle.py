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
import typing
if typing.TYPE_CHECKING:
    import traci

from collections import OrderedDict
import numpy
import pandas

import colmto.cse.rule
import colmto.common.model
import colmto.common.log
from colmto.common.helper import Position
from colmto.common.helper import VehicleType
from colmto.common.helper import VehicleDisposition
from colmto.common.helper import StatisticSeries
from colmto.common.helper import GridPosition
from colmto.common.helper import Colour
from colmto.common.helper import Metric


class BaseVehicle(object):
    '''Base Vehicle.'''

    def __init__(self):
        '''Initialisation'''
        self._log = colmto.common.log.logger(f'{__name__} ({hex(id(self))})', loglevel='debug')
        self._properties = {
            'position': Position(x=0.0, y=0.0),
            'speed': 0.0
        }

    @property
    def properties(self) -> MappingProxyType:
        '''
        :return: vehicle properties as MappingProxyType dictionary bundle
        '''
        return MappingProxyType(self._properties)

    @property
    def _speed(self) -> float:
        '''
        :return: current speed at time step
        '''
        return self._properties.get('speed')

    @_speed.setter
    def _speed(self, speed: float):
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

    :note: **Note on statistics:**
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
        Initialisation.

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
                'normal_colour': Colour(red=255, green=255, blue=0, alpha=255),
                'start_time': 0.0,
                'speedDev': speed_deviation,
                'sigma': sigma,
                'maxSpeed': speed_max,
                'vType': vehicle_type,
                'vClass': colmto.cse.rule.SUMORule.allowed_class_name(),
                'grid_position': Position(x=0, y=0),
                'time_step': 0.0,
                'travel_time': 0.0,
                'dissatisfaction': 0.0,
                'disposition': VehicleDisposition.COOPERATIVE # VehicleDisposition.choose((0.5, 0.5))
            }
        )

        self._environment = environment

        # prepare grid-based series using OrderedDicts to maintain the order of keys
        self._grid_based_series_dict = {
            i_metric.value : OrderedDict()
            for i_metric in StatisticSeries.GRID.metrics()
        }

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
    def _lane(self) -> int:
        '''
        :return: current lane index
        '''
        return int(self._properties.get('lane_index'))

    @_lane.setter
    def _lane(self, lane_index: int):
        '''
        Updates current lane index

        :param lane_index: current lane index
        '''
        self._properties['lane_index'] = int(lane_index)

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
    def sumo_id(self) -> str:
        '''
        Get assigned SUMO vehicle id
        :return: vehicle id
        '''
        return self._properties.get('sumo_id')

    @sumo_id.setter
    def sumo_id(self, sumo_id: str):
        '''
        Set SUMO vehicle id

        :param sumo_id: vehicle id
        '''
        self._properties['sumo_id'] = str(sumo_id)

    @property
    def vehicle_type(self) -> VehicleType:
        '''
        :return: vehicle type
        '''
        return VehicleType[str(self._properties.get('vType')).upper()] \
            if self._properties.get('vType') else VehicleType.UNDEFINED

    @property
    def disposition(self) -> VehicleDisposition:
        '''
        Vehicle dispostion, i.e. cooperative or uncooperative

        :return: VehicleDisposition
        '''
        return self._properties['disposition']

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
        Get current colour

        :return: colour
        '''
        return Colour(*self._properties.get('colour'))

    @property
    def normal_colour(self) -> Colour:
        '''
        :return: colour
        '''
        return Colour(*self._properties.get('normal_colour'))

    @normal_colour.setter
    def normal_colour(self, colour: Colour):
        '''
        Set normal colour a vehicle should have if not in 'denied access state'

        :param colour: Color (rgba tuple, e.g. (255, 255, 0, 255))
        '''
        self._properties['normal_colour'] = Colour(*colour)

    @property
    def vehicle_class(self) -> str:
        '''
        :return: SUMO vehicle class
        '''
        return str(self._properties.get('vClass'))

    @vehicle_class.setter
    def vehicle_class(self, vehicle_class: str):
        '''
        Set UMO vehicle class
        '''
        self._properties['vClass'] = str(vehicle_class)

    @property
    def speed_max(self) -> float:
        '''
        :return: self._properties.get('maxSpeed')
        '''
        return float(self._properties.get('maxSpeed'))

    @property
    def dissatisfaction(self) -> float:
        '''
        Current dissatisfaction (updated via update() function)

        :return: Dissatisfaction, float of range [0, 1]

        '''
        return float(self._properties.get('dissatisfaction'))

    @property
    def dsat_threshold(self) -> float:
        '''
        :return: dissatisfaction threshold, i.e. `self.properties.get('dsat_threshold')`
        '''
        return float(self._properties.get('dsat_threshold'))


    def statistic_series_grid(self, interpolate=False) -> pandas.Series:
        '''
        Recorded travel statistics as `pandas.Series`.

        :note: To properly store results from SUMO (discrete time vs. "continuous" space), there exists a
          `pandas.Series <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_
          related to the current time step (self._time_based_series) and a `Series` for grid cells in
          x-direction (self._grid_based_series). As vehicles are expected to "jump" over cells while
          traveling faster than `cell width / time step`, we create an entry for each cell
          (initialised as `NaN`) and linear interpolate the missing values afterwards.

        :param interpolate: return a data copy with NaN values linear interpolated
        :return: grid-based `pandas.Series`

        '''

        l_grid_based_series = pandas.Series(
            index=pandas.MultiIndex.from_product(
                iterables=(
                    (i_metric.value for i_metric in StatisticSeries.GRID.metrics()),
                    range(int(self._environment.get('gridlength')))  # range(number of cells of x-axis)
                ),
                names=('metric', Metric.GRID_POSITION_X.value)
            )
        )

        for i_metric in StatisticSeries.GRID.metrics():
            l_grid_based_series.update(
                pandas.Series(data=self._grid_based_series_dict.get(i_metric.value))
            )

        return pandas.concat(
            (
                l_grid_based_series[i_metric.value].interpolate()
                for i_metric in StatisticSeries.GRID.metrics()
            ),
            keys=(i_metric.value for i_metric in StatisticSeries.GRID.metrics())
        ) if interpolate else l_grid_based_series

    def allow_otl_access(self, traci: 'traci'=None):
        '''
        Signal the vehicle that overtaking lane (OTL) access has been allowed.
        It is now the vehicle's responsibility to act cooperatively, e.g.
        1. set own class to allow, 2. change colour back to default.

        :note: This is the place where cooperative behaviour can be implemented. I.e. 'free will' (TM) starts here.

        :param traci: traci control reference
        :return: self
        '''

        self._properties['colour'] = self.normal_colour
        if traci:
            traci.vehicle.setColor(self.sumo_id, self.colour)
        return self

    def deny_otl_access(self, traci: 'traci'=None) -> BaseVehicle:
        '''
        Signal the vehicle that overtaking lane (OTL) access has been denied.
        It is now the vehicle's responsibility to act cooperatively, i.e.
        1. set own class to deny, 2. change colour to red and 3. do a lane change to the right.

        :note: This is the place where cooperative behaviour is implemented. Vehicles acting uncooperative won't behave according to rules. I.e. 'free will' (TM) starts here.

        :param traci: traci control reference
        :return: self
        '''

        if self.disposition == VehicleDisposition.COOPERATIVE:
            # show that I'm cooperative by painting myself red
            self._properties['colour'] = Colour(255, 0, 0, 255)
            if traci:
                traci.vehicle.setColor(self.sumo_id, self.colour)
                # as I'm cooperative, always keep to the right lane
                traci.vehicle.changeLane(self.sumo_id, 0, 1)
        else:
            # show that I'm uncooperative by painting myself gray
            self._properties['colour'] = Colour(127, 127, 127, 255)
            if traci:
                traci.vehicle.setColor(self.sumo_id, self.colour)
        return self

    def update(self, position: Position, lane_index: int, speed: float, time_step: float) -> BaseVehicle:
        '''
        Update current properties of vehicle providing data acquired from TraCI call.

        For the grid cell the vehicle is in, take the global position in x-direction divided by grid
        cell size and int-rounded. For the y-coordinate take the lane index.

        :note: The cell width can be set via 'gridcellwidth' in the run config.

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
        self._lane = int(lane_index)

        # update data series based on grid cell
        self._properties['dissatisfaction'] = colmto.common.model.dissatisfaction(
            time_step - self.start_time - self._position.x / self.speed_max,
            self._position.x / self.speed_max,
            self.dsat_threshold
        )

        self._grid_based_series_dict.get(Metric.TIME_STEP.value)[(Metric.TIME_STEP.value, self._grid_position.x)] = float(time_step)
        self._grid_based_series_dict.get(Metric.POSITION_Y.value)[(Metric.POSITION_Y.value, self._grid_position.x)] = self._position.y
        self._grid_based_series_dict.get(Metric.GRID_POSITION_Y.value)[(Metric.GRID_POSITION_Y.value, self._grid_position.x)] = self._grid_position.y
        self._grid_based_series_dict.get(Metric.DISSATISFACTION.value)[(Metric.DISSATISFACTION.value, self._grid_position.x)] = self.dissatisfaction
        self._grid_based_series_dict.get(Metric.TRAVEL_TIME.value)[(Metric.TRAVEL_TIME.value, self._grid_position.x)] = self._travel_time
        self._grid_based_series_dict.get(Metric.TIME_LOSS.value)[(Metric.TIME_LOSS.value, self._grid_position.x)] = time_step - self.start_time - self._position.x / self.speed_max
        self._grid_based_series_dict.get(Metric.RELATIVE_TIME_LOSS.value)[(Metric.RELATIVE_TIME_LOSS.value, self._grid_position.x)] = (time_step - self.start_time - self._position.x / self.speed_max) / (self._position.x / self.speed_max)
        self._grid_based_series_dict.get(Metric.LANE_INDEX.value)[(Metric.LANE_INDEX.value, self._grid_position.x)] = self._lane

        return self
