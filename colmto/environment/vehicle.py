# -*- coding: utf-8 -*-
# @package colmto.environment
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
'''Vehicle classes for storing vehicle data/attributes/states.'''

from types import MappingProxyType
import numpy

import colmto.cse.rule


class BaseVehicle(object):
    '''Base Vehicle.'''

    def __init__(self):
        '''C'tor'''

        self._properties = {
            'position': numpy.array((0.0, 0.0)),
            'speed': 0.0,
        }

    @property
    def properties(self) -> MappingProxyType:
        '''
        @retval vehicle properties as MappingProxyType dictionary bundle
        '''
        return MappingProxyType(self._properties)

    @property
    def speed(self) -> float:
        '''
        @retval current speed at time step
        '''
        return self._properties.get('speed')

    @speed.setter
    def speed(self, speed: float):
        '''
        Set vehicle speed
        @param speed current position
        '''
        self._properties['speed'] = float(speed)

    @property
    def position(self) -> numpy.ndarray:
        '''
        @retval current position
        '''
        # TODO: return named tuple
        return numpy.array(self._properties.get('position'))

    @position.setter
    def position(self, position: numpy.ndarray):
        '''
        Set vehicle position
        @param position current position
        '''
        self._properties['position'] = numpy.array(position)


class SUMOVehicle(BaseVehicle):
    '''SUMO vehicle class.'''

    # pylint: disable=too-many-arguments
    def __init__(self,
                 vehicle_type=None,
                 vtype_sumo_cfg=None,
                 speed_deviation=0.0,
                 sigma=0.0,
                 speed_max=0.0):
        '''
        C'tor.

        @param vehicle_type
        @param vtype_sumo_cfg
        @param speed_deviation
        @param sigma
        @param speed_max
        '''

        super().__init__()

        if isinstance(vtype_sumo_cfg, dict):
            self._properties.update(vtype_sumo_cfg)

        self._properties.update(
            {
                'color': numpy.array((255, 255, 0, 255)),
                'start_time': 0.0,
                'speedDev': speed_deviation,
                'sigma': sigma,
                'maxSpeed': speed_max,
                'vType': vehicle_type,
                'vClass': colmto.cse.rule.SUMORule.to_allowed_class(),
                'grid_position': numpy.array((0, 0))
            }
        )

        self._travel_stats = {
            'start_time': 0.0,
            'travel_time': 0.0,
            'vehicle_type': vehicle_type,
            'grid': {
                'pos_x': [],
                'pos_y': [],
                'time_loss': [],
                'relative_time_loss': [],
                'speed': [],
                'dissatisfaction': []
            },
            'step': {
                'number': [],
                'pos_x': [],
                'pos_y': [],
                'time_loss': [],
                'relative_time_loss': [],
                'speed': [],
                'dissatisfaction': []
            }
        }

    @property
    def grid_position(self) -> numpy.ndarray:
        '''
        @retval current grid position
        '''
        return numpy.array(self._properties.get('grid_position'))

    @grid_position.setter
    def grid_position(self, position: numpy.ndarray):
        '''
        Updates current position
        @param position current grid position
        '''
        self._properties['grid_position'] = numpy.array(position, dtype=int)

    @property
    def vehicle_type(self) -> str:
        '''
        @retval vehicle type
        '''
        return str(self._properties.get('vType'))

    @property
    def start_time(self) -> float:
        '''
        Returns start time

        @retval start time
        '''
        return float(self._properties.get('start_time'))

    @start_time.setter
    def start_time(self, start_time: float):
        '''
        Sets start time.

        @param start_time start time
        '''
        self._properties['start_time'] = float(start_time)

    @property
    def color(self) -> numpy.ndarray:
        '''
        Returns:
            color
        '''
        return numpy.array(self._properties.get('color'))

    @color.setter
    def color(self, color: numpy.ndarray):
        '''
        Update color
        @param color Color (rgba-tuple, e.g. (255, 255, 0, 255))
        '''
        self._properties['color'] = numpy.array(color)

    @property
    def vehicle_class(self) -> str:
        '''
        @retval SUMO vehicle class
        '''
        return str(self._properties.get('vClass'))

    @property
    def speed_max(self) -> float:
        '''
        @retval self._properties.get('maxSpeed')
        '''
        return float(self._properties.get('maxSpeed'))

    @property
    def travel_time(self) -> float:
        '''
        Returns current travel time

        @retval travel time
        '''
        return float(self._travel_stats.get('travel_time'))

    @property
    def travel_stats(self) -> MappingProxyType:
        '''
        @brief Returns MappingProxyType travel stats dictionary

        @retval self._travel_stats
        '''
        return MappingProxyType(self._travel_stats)

    @property
    def dsat_threshold(self) -> float:
        '''
        returns dissatisfaction threshold
        @retval self.properties.get('dsat_threshold')
        '''
        return float(self._properties.get('dsat_threshold'))

    @dsat_threshold.setter
    def dsat_threshold(self, threshold: float):
        ''' sets dissatisfaction threshold '''
        self._properties['dsat_threshold'] = float(threshold)

    @staticmethod
    def _dissatisfaction(
            time_loss: float,
            optimal_travel_time: float,
            time_loss_threshold=0.2) -> float:
        r'''Calculate driver's dissatisfaction.
        Calculate driver's dissatisfaction.
        \f{eqnarray*}{
            TT &:=& \text{travel time}, \\
            TT^{*} &:=& \text{optimal travel time}, \\
            TL &:=& \text{time loss}, \\
            TLT &:=& \text{time loss threshold}, \\
            \text{dissatisfaction} &:=& dsat(TL, TT^{*}, TLT) \\
            &=&\frac{1}{1+e^{(-TL + TLT \cdot TT^{*}) \cdot 0{.}5}}.\\
            &&\text{note: using a smoothening factor of 0.5 to make the transition not that sharp}
        \f}
        @param time_loss time loss
        @param time_loss_threshold cut-off point of acceptable time loss
            relative to optimal travel time in [0,1]
        @param optimal_travel_time optimal travel time
        @retval dissatisfaction ([0,1] normalised)
        '''

        # pylint: disable=no-member
        return numpy.divide(
            1.,
            1 + numpy.exp((-time_loss + time_loss_threshold * optimal_travel_time)) * .5
        )
        # pylint: enable=no-member

    def record_travel_stats(self, time_step: float) -> BaseVehicle:
        r'''Record travel statistics to vehicle.
        Write travel stats, i.e. travel time, time loss, position,
        and dissatisfaction of vehicle for a given time step into self._travel_stats

        @param time_step current time step
        @retval self
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
                self._dissatisfaction(
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
                    self._dissatisfaction(
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
            self._dissatisfaction(
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
        @param class_name vehicle class
        @retval self
        '''
        self._properties['vClass'] = str(class_name)
        return self

    def update(self, position: tuple, lane_index: int, speed: float) -> BaseVehicle:
        '''
        Update current properties of vehicle providing data acquired from TraCI call.

        For the grid cell the vehicle is in, take the global position in x-direction divided by grid
        cell size and int-rounded. For the y-coordinate take the lane index.
        NOTE: We assume a fixed grid cell size of 4 meters. This has to be set via cfg in future.

        @param position: tuple TraCI provided position
        @param lane_index: int TraCI provided lane index
        @param speed: float TraCI provided speed
        @retval self Vehicle reference
        '''

        # set current position
        self._properties['position'] = numpy.array(position)
        # set current grid position
        self._properties['grid_position'] = numpy.array(
            (
                int(round(position[0]/4.)-1),
                int(lane_index)
            )
        )
        # set speed
        self._properties['speed'] = float(speed)

        return self
