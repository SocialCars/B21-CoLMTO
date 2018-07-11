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

import colmto.cse.rule
import colmto.common.model
from colmto.common.helper import Position
from colmto.common.helper import VehicleType
from colmto.common.helper import VehicleDisposition
from colmto.common.helper import StatisticSeries
from colmto.common.helper import GridPosition
from colmto.common.helper import Colour
from colmto.common.helper import Metric
from types import MappingProxyType
import typing
if typing.TYPE_CHECKING:
    import traci

from collections import OrderedDict
import pandas


class BaseVehicle(object):
    '''Base Vehicle.'''

    def __init__(self):
        '''Initialisation'''
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
    def speed(self) -> float:
        '''
        :return: current speed at time step
        '''
        return self._properties.get('speed')

    @property
    def position(self) -> Position:
        '''
        :return: current position
        '''
        return self._properties.get('position')


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
                 vehicle_type: str = None,
                 vtype_sumo_cfg: dict = None,
                 speed_deviation: float = 0.0,
                 sigma: float = 0.0,
                 speed_max: float = 0.0,
                 cooperation_probability: typing.Union[None, float]=None):
        '''
        Initialisation.

        :type environment: dict
        :param environment: environment
        :type vehicle_type: str
        :param vehicle_type: SUMO vehicle type
        :type vtype_sumo_cfg: dict
        :param vtype_sumo_cfg: (optional) SUMO config
        :type speed_deviation: float
        :param speed_deviation: speed deviation (Krauss driver model)
        :type sigma: float
        :param sigma: sigma (Krauss driver model)
        :type speed_max: float
        :param speed_max: maximum desired or capable speed of vehicle
        :type cooperation_probability: float
        :param cooperation_probability: disposition for cooperative driving with :math:`p\in [0,1]\cup \{None\}`. :math:`p=1` or `None` means always cooperative (default), :math:`p=0` always uncooperative

        '''

        super().__init__()

        if isinstance(vtype_sumo_cfg, dict):
            self._properties.update(vtype_sumo_cfg)

        self._properties.update(
            {
                'colour': Colour(red=255, green=255, blue=0, alpha=255),
                'normal_colour': Colour(red=255, green=255, blue=0, alpha=255),
                'start_time': 0.0,
                'start_position': Position(x=0.0, y=0.0),
                'speedDev': speed_deviation,
                'sigma': sigma,
                'maxSpeed': speed_max,
                'vType': vehicle_type,
                'vClass': colmto.cse.rule.SUMORule.allowed_class_name(),
                'grid_position': Position(x=0, y=0),
                'time_step': 0.0,
                'travel_time': 0.0,
                'dissatisfaction': 0.0,
                'cooperation_disposition': VehicleDisposition.COOPERATIVE if not cooperation_probability else VehicleDisposition.choose(cooperation_probability)
            }
        )

        self._environment = environment

        # prepare grid-based series using OrderedDicts to maintain the order of keys
        self._grid_based_series_dict = {
            i_metric.value : OrderedDict()
            for i_metric in StatisticSeries.GRID.metrics()
        }

    @property
    def lane(self) -> int:
        '''
        :return: current lane index
        '''
        return int(self._properties.get('lane_index'))

    @property
    def grid_position(self) -> GridPosition:
        '''
        :return: current GridPosition
        '''
        return GridPosition(*self._properties.get('grid_position'))

    @property
    def sumo_id(self) -> str:
        '''
        Get assigned SUMO vehicle id

        :return: vehicle id as string
        '''
        return self._properties.get('sumo_id')

    @sumo_id.setter
    def sumo_id(self, sumo_id: str):
        '''
        Set SUMO vehicle id

        :param sumo_id: vehicle id
        :type sumo_id: str
        '''
        self._properties['sumo_id'] = str(sumo_id)

    @property
    def vehicle_type(self) -> VehicleType:
        '''
        Get vehicle type

        :return: VehicleType
        '''
        return VehicleType[str(self._properties.get('vType')).upper()] \
            if self._properties.get('vType') else VehicleType.UNDEFINED

    @property
    def cooperation_disposition(self) -> VehicleDisposition:
        '''
        Vehicle cooperation dispostion, i.e. cooperative or uncooperative

        :return: VehicleDisposition
        '''
        return self._properties.get('cooperation_disposition')

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
    def start_position(self) -> Position:
        '''
        Include the initial position in calculations, as SUMO tends to put vehicles at positions > 0 in their 0th time step.

        :return: start position
        '''
        return Position(*self._properties.get('start_position'))

    @start_position.setter
    def start_position(self, start_position: Position):
        '''
        Include the initial position in calculations, as SUMO tends to put vehicles at positions > 0 in their 0th time step.

        :param start_position_x: start position on x axis
        '''
        self._properties['start_position'] = Position(*start_position)

    @property
    def travel_time(self) -> float:
        '''
        :return: current travel time
        '''
        return float(self._properties.get('travel_time'))

    @property
    def time_step(self) -> float:
        '''
        Current time step

        :return: time step as float
        '''
        return float(self._properties.get('time_step'))

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

    def deny_otl_access(self, _traci: 'traci' = None) -> BaseVehicle:
        '''
        Signal the vehicle that overtaking lane (OTL) access has been denied.
        It is now the vehicle's responsibility to act cooperatively, i.e.
        1. set own class to deny, 2. change colour to red and 3. do a lane change to the right.

        :note: This is the place where cooperative behaviour is implemented. Vehicles acting uncooperative won't behave according to rules. I.e. 'free will' (TM) starts here.

        :param _traci: traci control reference
        :return: self
        '''

        if self.cooperation_disposition == VehicleDisposition.COOPERATIVE:
            # show that I'm cooperative by painting myself red
            self._properties['colour'] = Colour(255, 0, 0, 255)
            if _traci:
                _traci.vehicle.setColor(self.sumo_id, self.colour)
                # as I'm cooperative, always keep to the right lane
                _traci.vehicle.changeLane(self.sumo_id, 0, 1)
        else:
            # show that I'm uncooperative by painting myself gray
            self._properties['colour'] = Colour(127, 127, 127, 255)
            if _traci:
                _traci.vehicle.setColor(self.sumo_id, self.colour)
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
        l_position = Position(*position)
        assert l_position.x >= 0 and l_position.y >= 0
        self._properties['position'] = l_position
        self._properties['grid_position'] = l_position.gridified(width=self._environment.get('gridcellwidth'))
        assert float(speed) >= 0
        self._properties['speed']  = float(speed)
        assert float(time_step) >= 0
        self._properties['time_step'] = float(time_step)
        assert float(time_step) >= self.start_time
        self._properties['travel_time'] = float(time_step) - self.start_time
        assert int(lane_index) in (0, 1)
        self._properties['lane_index'] = int(lane_index)

        # vehicle/generic optimal travel time: round positions of division as SUMO reports positions with reduced
        # accuracy (2 significant figures) to avoid negative travel time losses.
        l_generic_optimal_travel_time = round(self.position.x / self.speed_max, 2)

        # Vehicle optimal travel time: include, i.e. substract the start_position as SUMO puts
        # vehicles at lane positions greater than 0 in their first active time step if they started
        # between the previous and current global (runtime) time step.
        l_vehicle_optimal_travel_time = round((self.position.x - self.start_position.x) / self.speed_max, 2)
        l_vehicle_time_loss = self.travel_time - l_vehicle_optimal_travel_time
        assert l_vehicle_time_loss >= 0

        self._properties['dissatisfaction'] = colmto.common.model.dissatisfaction(
            time_loss=l_vehicle_time_loss,
            optimal_travel_time=l_generic_optimal_travel_time,
            time_loss_threshold=self.dsat_threshold
        )
        assert 0 <= self.dissatisfaction <= 1

        # update data series based on grid cell
        self._grid_based_series_dict.get(Metric.TIME_STEP.value)[
            (Metric.TIME_STEP.value, self.grid_position.x)
        ] = float(time_step)
        self._grid_based_series_dict.get(Metric.POSITION_Y.value)[
            (Metric.POSITION_Y.value, self.grid_position.x)
        ] = self.position.y
        self._grid_based_series_dict.get(Metric.GRID_POSITION_Y.value)[
            (Metric.GRID_POSITION_Y.value, self.grid_position.x)
        ] = self.grid_position.y
        self._grid_based_series_dict.get(Metric.DISSATISFACTION.value)[
            (Metric.DISSATISFACTION.value, self.grid_position.x)
        ] = self.dissatisfaction
        self._grid_based_series_dict.get(Metric.TRAVEL_TIME.value)[
            (Metric.TRAVEL_TIME.value, self.grid_position.x)
        ] = self.travel_time
        self._grid_based_series_dict.get(Metric.TIME_LOSS.value)[
            (Metric.TIME_LOSS.value, self.grid_position.x)
        ] = l_vehicle_time_loss
        self._grid_based_series_dict.get(Metric.RELATIVE_TIME_LOSS.value)[
            (Metric.RELATIVE_TIME_LOSS.value, self.grid_position.x)
        ] = l_vehicle_time_loss / l_generic_optimal_travel_time if l_generic_optimal_travel_time > 0 else 0
        self._grid_based_series_dict.get(Metric.LANE_INDEX.value)[
            (Metric.LANE_INDEX.value, self.grid_position.x)
        ] = self.lane

        return self