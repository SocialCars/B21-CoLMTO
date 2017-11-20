# -*- coding: utf-8 -*-
# @package colmto.sumo
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
'''This module generates static sumo configuration files for later execution.'''
# pylint: disable=no-member

import copy
import enum
from pathlib import Path
import subprocess
from types import MappingProxyType
import typing
from collections import OrderedDict

import numpy
try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree

import defusedxml.lxml

import colmto.common.configuration
import colmto.common.io
import colmto.common.log
import colmto.common.visualisation
import colmto.environment.vehicle


@enum.unique
class InitialSorting(enum.Enum):
    '''Initial sorting modes of vehicles'''
    BEST = enum.auto()
    RANDOM = enum.auto()
    WORST = enum.auto()
    _prng = numpy.random.RandomState()

    def order(self, vehicles: list):
        '''*in-place* brings list of vehicles into required order (BEST, RANDOM, WORST)'''
        if self is InitialSorting.BEST:
            vehicles.sort(key=lambda i_v: i_v.speed_max, reverse=True)
        elif self is InitialSorting.WORST:
            vehicles.sort(key=lambda i_v: i_v.speed_max)
        elif self is InitialSorting.RANDOM:
            self.prng.shuffle(vehicles)

    @property
    def prng(self):
        '''returns numpy PRNG state'''
        return self._prng.value


@enum.unique
class Distribution(enum.Enum):
    '''Enumerates distribution types for vehicle starting times'''
    LINEAR = enum.auto()
    POISSON = enum.auto()
    _prng = numpy.random.RandomState()

    def next_timestep(self, lamb, prev_start_time):
        r'''
        Calculate next time step in Exponential or linear distribution.
        Exponential distribution with
        \f$F(x) := 1 - e^{-\lambda x}\f$
        by using numpy.random.exponential(lambda).
        Linear distribution just adds 1/lamb to the previous start time.
        For every other value of distribution this function just returns the input value of
        prev_start_time.

        @param lamb: lambda
        @param prev_start_time: start time
        @param distribution: distribution, i.e. Distribution.POISSON or Distribution.LINEAR
        @retval next start time
        '''
        if self is Distribution.POISSON:
            return prev_start_time + self._prng.value.exponential(scale=lamb)
        elif self is Distribution.LINEAR:
            return prev_start_time + 1 / lamb
        return prev_start_time


class SumoConfig(colmto.common.configuration.Configuration):
    '''Create SUMO configuration files'''

    def __init__(self, args, netconvertbinary, duarouterbinary):
        '''C'tor'''
        super().__init__(args)

        self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        self._writer = colmto.common.io.Writer(args)

        # initialise numpy PRNG
        self._prng = numpy.random.RandomState()

        self._binaries = {
            'netconvert': netconvertbinary,
            'duarouter': duarouterbinary
        }

        self.sumo_config_dir.mkdir(parents=True, exist_ok=True)
        self.runsdir.mkdir(parents=True, exist_ok=True)
        self.resultsdir.mkdir(parents=True, exist_ok=True)

        if self._args.forcerebuildscenarios:
            self._log.debug(
                '--force-rebuild-scenarios set '
                '-> rebuilding/overwriting scenarios if already present'
            )

        # generate color map for vehicle max speeds
        l_global_maxspeed = max(
            [
                i_scenario.get('parameters').get('speedlimit')
                for i_scenario in self.scenario_config.values()
                ]
        )
        self._speed_colormap = colmto.common.visualisation.mapped_cmap(
            'plasma',
            l_global_maxspeed
        )

    @property
    def sumo_config_dir(self) -> Path:
        '''
        Returns:
             directory of SUMO config
        '''
        return self.output_dir / 'SUMO'

    @property
    def runsdir(self) -> Path:
        '''
        Returns:
             directory of runs
        '''
        return self.output_dir / 'SUMO' / self.run_prefix / 'runs'

    @property
    def resultsdir(self) -> Path:
        '''
        Returns:
            directory for results
        '''
        return self.output_dir / 'SUMO' / self.run_prefix / 'results'

    @property
    def sumo_run_config(self):
        '''
        Returns:
             copy of sumo run config
        '''
        return copy.copy(
            self.run_config.get('sumo')
        )

    def generate_scenario(self, scenarioname):
        '''generate SUMO scenario based on scenario name'''

        self._log.debug('Generating scenario %s', scenarioname)

        l_destinationdir = self.runsdir / scenarioname
        l_destinationdir.mkdir(parents=True, exist_ok=True)

        l_scenarioconfig = self.scenario_config.get(scenarioname)

        l_scenarioruns = {
            'scenarioname': scenarioname,
            'runs': {}
        }

        l_nodefile = l_scenarioruns['nodefile'] = l_destinationdir / f'{scenarioname}.nod.xml'
        l_edgefile = l_scenarioruns['edgefile'] = l_destinationdir / f'{scenarioname}.edg.xml'
        l_netfile = l_scenarioruns['netfile'] = l_destinationdir / f'{scenarioname}.net.xml'
        l_settingsfile = l_scenarioruns['settingsfile'] = l_destinationdir \
                                                          / f'{scenarioname}.settings.xml'

        self._generate_node_xml(
            l_scenarioconfig, l_nodefile, self._args.forcerebuildscenarios
        )
        self._generate_edge_xml(
            scenarioname, l_scenarioconfig, l_edgefile, self._args.forcerebuildscenarios
        )
        self._generate_settings_xml(
            l_scenarioconfig, self.run_config, l_settingsfile, self._args.forcerebuildscenarios
        )
        self._generate_net_xml(
            l_nodefile, l_edgefile, l_netfile, self._args.forcerebuildscenarios
        )

        return l_scenarioruns

    def generate_run(
            self,
            scenario_run_config,
            initial_sorting: InitialSorting,
            run_number,
            vtype_list):
        '''generate run configurations

        @param scenario_run_config: run configuration of scenario
        @param initial_sorting: initial sorting of vehicles (InitialSorting enum)
        @param run_number: number of current run
        @retval
            run configuration dictionary
        '''
        self._log.debug(
            'Generating run %s for %s sorting', run_number, initial_sorting.name.lower()
        )
        l_scenarioname = scenario_run_config.get('scenarioname')

        l_destinationdir = self.runsdir / l_scenarioname

        (l_destinationdir / initial_sorting.name.lower()).mkdir(parents=True, exist_ok=True)

        (l_destinationdir / initial_sorting.name.lower() / str(run_number))\
            .mkdir(parents=True, exist_ok=True)

        self._log.debug(
            'Generating SUMO run configuration for scenario %s / sorting %s / run %d',
            l_scenarioname, initial_sorting.name, run_number
        )

        l_tripfile = l_destinationdir / initial_sorting.name.lower() / str(run_number) \
                     / '{l_scenarioname}.trip.xml'

        l_routefile = l_destinationdir / initial_sorting.name.lower() / str(run_number) \
                      / '{l_scenarioname}.rou.xml'

        l_configfile = l_destinationdir / initial_sorting.name.lower() / str(run_number) \
                       / '{l_scenarioname}.sumo.cfg'

        l_output_measurements_dir = self.resultsdir / l_scenarioname \
                                    / initial_sorting.name.lower() / str(run_number)

        l_output_measurements_dir.mkdir(parents=True, exist_ok=True)

        l_runcfgfiles = [l_tripfile, l_routefile, l_configfile]

        if [fname for fname in l_runcfgfiles if not fname.exists()]:
            self._log.debug(
                'Incomplete/non-existing SUMO run configuration for %s, %s, %d -> (re)building',
                l_scenarioname, initial_sorting.name, run_number
            )
            self._args.forcerebuildscenarios = True

        self._generate_config_xml(
            {
                'configfile': l_configfile,
                'netfile': scenario_run_config.get('netfile'),
                'routefile': l_routefile,
                'settingsfile': scenario_run_config.get('settingsfile')
            },
            self.run_config.get('simtimeinterval'), self._args.forcerebuildscenarios
        )

        l_vehicles = self._generate_trip_xml(
            scenario_run_config, initial_sorting, vtype_list, l_tripfile,
            self._args.forcerebuildscenarios
        )

        self._generate_route_xml(
            scenario_run_config.get('netfile'), l_tripfile, l_routefile,
            self._args.forcerebuildscenarios
        )

        return {
            'scenarioname': l_scenarioname,
            'sumoport': self.run_config.get('sumo').get('port'),
            'runnumber': run_number,
            'vehicles': l_vehicles,
            'settingsfile': scenario_run_config.get('settingsfile'),
            'tripfile': l_tripfile,
            'routefile': l_routefile,
            'configfile': l_configfile,
            'fcdfile': l_output_measurements_dir / '{l_scenarioname}.fcd-output.xml',
            'scenario_config': self.scenario_config.get(l_scenarioname)
        }

    def _generate_node_xml(self, scenarioconfig, nodefile: Path, forcerebuildscenarios=False):
        '''
        Generate SUMO's node configuration file.

        @param scenarioconfig: Scenario configuration
        @param nodefile: Destination to write node file
        @param forcerebuildscenarios: rebuild scenarios,
                                        even if they already exist for current run
        '''

        if Path(nodefile).exists() and not forcerebuildscenarios:
            return

        self._log.debug('Generating node xml')

        # parameters
        l_length = scenarioconfig.get('parameters').get('length')
        l_nbswitches = scenarioconfig.get('parameters').get('switches')
        l_segmentlength = l_length / (l_nbswitches + 1)

        if self._args.onlyoneotlsegment:
            l_length = 2 * l_segmentlength  # two times segment length

        l_nodes = etree.Element('nodes')
        etree.SubElement(
            l_nodes, 'node', attrib={'id': 'enter', 'x': str(-l_segmentlength), 'y': '0'}
        )
        etree.SubElement(
            l_nodes, 'node', attrib={'id': '21start', 'x': '0', 'y': '0'}
        )
        etree.SubElement(
            l_nodes, 'node', attrib={'id': '21end', 'x': str(l_length), 'y': '0'}
        )

        # dummy node for easier from-to routing
        etree.SubElement(
            l_nodes,
            'node',
            attrib={
                'id': 'exit',
                'x': str(
                    l_length + 0.1
                    if l_nbswitches % 2 == 1 or self._args.onlyoneotlsegment
                    else l_length + l_segmentlength
                ),
                'y': '0'
            }
        )

        with open(nodefile, 'w') as f_nodesxml:
            f_nodesxml.write(
                defusedxml.lxml.tostring(l_nodes, pretty_print=True, encoding='unicode')
            )

    def _generate_edge_xml(
            self, scenario_name: str, scenario_config, edgefile: Path, forcerebuildscenarios=False):
        '''
        Generate SUMO's edge configuration file.

        @param scenario_name: Name of scenario (required to id detector positions)
        @param scenario_config: Scenario configuration
        @param edgefile: Destination to write edge file
        @param forcerebuildscenarios: Rebuild scenarios,
                                        even if they already exist for current run
        '''

        if Path(edgefile).exists() and not forcerebuildscenarios:
            return

        self._log.debug('Generating edge xml for %s', scenario_name)

        # parameters
        l_length = scenario_config.get('parameters').get('length')
        l_nbswitches = scenario_config.get('parameters').get('switches')
        l_maxspeed = scenario_config.get('parameters').get('speedlimit')

        # assume even distributed otl segment lengths
        l_segmentlength = l_length / (l_nbswitches + 1)

        # create edges xml
        l_edges = etree.Element('edges')

        # Entering edge with one lane, leading to 2+1 Roadway
        etree.SubElement(
            l_edges,
            'edge',
            attrib={
                'id': 'enter_21start',
                'from': 'enter',
                'to': '21start',
                'numLanes': '1',
                'speed': str(l_maxspeed)
            }
        )

        # 2+1 Roadway
        l_21edge = etree.SubElement(
            l_edges,
            'edge',
            attrib={
                'id': '21segment',
                'from': '21start',
                'to': '21end',
                'numLanes': '2',
                'spreadType': 'center',
                'speed': str(l_maxspeed)
            }
        )

        # deny access to lane 1 (OTL) to vehicle with vClass 'custom2'
        # <lane index='1' disallow='custom2'/>
        etree.SubElement(
            l_21edge,
            'lane',
            attrib={
                'index': '1',
                'disallow': 'custom1'
            }
        )

        if self.scenario_config.get(
                scenario_name
        ).get('parameters').get('detectorpositions') is None:
            self.scenario_config.get(
                scenario_name
            ).get('parameters')['detectorpositions'] = [0, l_segmentlength]

        self._generate_switches(l_21edge, scenario_config)

        # Exit lane
        etree.SubElement(
            l_edges,
            'edge',
            attrib={
                'id': '21end_exit',
                'from': '21end',
                'to': 'exit',
                'numLanes': '1',
                'spreadType': 'right',
                'speed': str(l_maxspeed)
            }
        )

        with open(edgefile, 'w') as f_edgexml:
            f_edgexml.write(
                defusedxml.lxml.tostring(l_edges, pretty_print=True, encoding='unicode')
            )

    def _generate_switches(self, edge, scenario_config):
        '''
        Generate switches if not pre-defined in scenario config.

        @param edge: edge
        @param scenario_config: scenario config dictionary
        '''
        self._log.debug('generating switches')

        l_length = scenario_config.get('parameters').get('length')
        l_nbswitches = scenario_config.get('parameters').get('switches')
        l_segmentlength = l_length / (l_nbswitches + 1)
        l_parameters = scenario_config.get('parameters')

        if isinstance(l_parameters.get('switchpositions'), (list, tuple)):
            # add splits and joins
            l_add_otl_lane = True
            for i_segmentpos in l_parameters.get('switchpositions'):
                etree.SubElement(
                    edge,
                    'split',
                    attrib={
                        'pos': str(i_segmentpos),
                        'lanes': '0 1' if l_add_otl_lane else '0',
                        'speed': str(scenario_config.get('parameters').get('speedlimit'))
                    }
                )

                l_add_otl_lane ^= True
        else:
            self._log.info('Rebuilding switches')
            scenario_config.get('parameters')['switchpositions'] = []
            # compute and add splits and joins
            l_add_otl_lane = True
            for i_segmentpos in range(0, int(l_length), int(l_segmentlength)) \
                    if not self._args.onlyoneotlsegment \
                    else range(0, int(2 * l_segmentlength - 1), int(l_segmentlength)):
                etree.SubElement(
                    edge,
                    'split',
                    attrib={
                        'pos': str(i_segmentpos),
                        'lanes': '0 1' if l_add_otl_lane else '0',
                        'speed': str(scenario_config.get('parameters').get('speedlimit'))
                    }
                )

                scenario_config.get(
                    'parameters'
                ).get(
                    'switchpositions'
                ).append(i_segmentpos)

                l_add_otl_lane ^= True

    @staticmethod
    def _generate_config_xml(config_files: dict, simtimeinterval, forcerebuildscenarios=False):
        '''
        Generate SUMO's main configuration file.

        @param config_files: Dictionary of config file locations,
                             i.e. netfile, routefile, settingsfile
        @param simtimeinterval: Time interval of simulation
        @param forcerebuildscenarios: Rebuild scenarios,
                                        even if they already exist for current run
        '''
        if not isinstance(simtimeinterval, list):
            raise TypeError

        if not len(simtimeinterval) == 2:
            raise ValueError

        if config_files.get('configfile').exists() and not forcerebuildscenarios:
            return

        l_configuration = etree.Element('configuration')
        l_input = etree.SubElement(l_configuration, 'input')
        etree.SubElement(
            l_input,
            'net-file',
            attrib={'value': str(config_files.get('netfile'))}
        )
        etree.SubElement(
            l_input,
            'route-files',
            attrib={'value': str(config_files.get('routefile'))}
        )
        etree.SubElement(
            l_input,
            'gui-settings-file',
            attrib={'value': str(config_files.get('settingsfile'))}
        )
        l_time = etree.SubElement(l_configuration, 'time')
        etree.SubElement(
            l_time,
            'begin',
            attrib={'value': str(simtimeinterval[0])}
        )

        with open(config_files.get('configfile'), 'w') as f_configxml:
            f_configxml.write(
                defusedxml.lxml.tostring(
                    l_configuration,
                    pretty_print=True,
                    encoding='unicode'
                )
            )

    @staticmethod
    def _generate_settings_xml(scenarioconfig: dict, runcfg: MappingProxyType,
                               settingsfile: Path, forcerebuildscenarios=False):
        '''
        Generate SUMO's settings configuration file.

        @param scenarioconfig: Scenario configuration
        @param runcfg: Run configuration
        @param settingsfile: Destination to write settings file
        @param forcerebuildscenarios: Rebuild scenarios,
                                        even if they already exist for current run
        '''
        if Path(settingsfile).exists() and not forcerebuildscenarios:
            return

        l_viewsettings = etree.Element('viewsettings')
        etree.SubElement(
            l_viewsettings, 'viewport',
            attrib={'x': str(scenarioconfig.get('parameters').get('length') / 2),
                    'y': '0',
                    'zoom': '100'}
        )
        etree.SubElement(
            l_viewsettings, 'delay', attrib={'value': str(runcfg.get('sumo').get('gui-delay'))}
        )

        with open(settingsfile, 'w') as f_configxml:
            f_configxml.write(
                defusedxml.lxml.tostring(
                    l_viewsettings,
                    pretty_print=True,
                    encoding='unicode'
                )
            )

    def _create_vehicle_distribution(self,
                                     vtype_list: typing.Iterable,
                                     aadt: float,
                                     initialsorting: InitialSorting,
                                     scenario_name
                                    ) -> typing.Dict[int, colmto.environment.vehicle.SUMOVehicle]:
        '''
        Create a distribution of vehicles based on

        @param vtype_list: list of vehicle types
        @param aadt: annual average daily traffic (vehicles/day/lane)
        @param initialsorting: initial sorting of vehicles (by max speed), i.e. InitialSorting enum
        @param scenario_name: name of scenario
        @retval OrderedDict of ID -> colmto.environment.vehicle.Vehicle
        '''

        if not isinstance(initialsorting, InitialSorting):
            raise ValueError

        self._log.debug(
            'Create vehicle distribution with %s', self._run_config.get('vtypedistribution')
        )

        l_vehps = aadt / (24 * 60 * 60) \
            if not self._run_config.get('vehiclespersecond').get('enabled') \
            else self._run_config.get('vehiclespersecond').get('value')

        l_vehicle_list = [
            colmto.environment.vehicle.SUMOVehicle(
                vehicle_type=vtype,
                vtype_sumo_cfg=self.vtypes_config.get(vtype),
                speed_deviation=self._run_config.get(
                    'vtypedistribution'
                ).get(vtype).get('speedDev'),
                sigma=self._run_config.get(
                    'vtypedistribution'
                ).get(vtype).get('sigma'),
                speed_max=min(
                    self._prng.choice(
                        self._run_config.get('vtypedistribution').get(vtype).get('desiredSpeeds')
                    ),
                    self.scenario_config.get(scenario_name).get('parameters').get('speedlimit')
                )
            ) for vtype in vtype_list
        ]

        # sort speeds according to initial sorting flag
        initialsorting.order(l_vehicle_list)

        # assign a new id according to sort order and starting time to each vehicle
        l_vehicles = OrderedDict()
        for i, i_vehicle in enumerate(l_vehicle_list):
            # update colors
            i_vehicle.color = numpy.array(self._speed_colormap(i_vehicle.speed_max))*255
            # update start time
            i_vehicle.start_time = Distribution[
                self.run_config.get('starttimedistribution').upper()
            ].next_timestep(
                l_vehps,
                l_vehicle_list[i - 1].start_time if i > 0 else 0
            )
            l_vehicles[f'vehicle{i}'] = i_vehicle
        return l_vehicles

    def aadt(self, scenario_runs):
        '''
        returns currently configured AADT (annual average daily traffic (vehicles/day/lane))

        :param scenario_runs: scenario runs
        :return: aadt
        '''
        return self.scenario_config.get(
            scenario_runs.get('scenarioname')
        ).get(
            'parameters'
        ).get(
            'aadt'
        ) if not self.run_config.get('aadt').get('enabled') \
            else self.run_config.get('aadt').get('value')

    def _generate_trip_xml(self,  # pylint: disable=too-many-arguments
                           scenario_runs: dict,
                           initialsorting: InitialSorting,
                           vtype_list: list,
                           tripfile: Path, forcerebuildscenarios=False
                          ) -> typing.Dict[int, colmto.environment.vehicle.SUMOVehicle]:
        '''
        Generate SUMO's trip file.

        @param scenario_runs:
        @param initialsorting:
        @param tripfile:
        @param forcerebuildscenarios:
        @retval vehicles
        '''

        if Path(tripfile).exists() and not forcerebuildscenarios:
            return OrderedDict({})
        self._log.debug('Generating trip xml for %s', scenario_runs.get('scenarioname'))

        self._log.debug(
            'Scenario\'s AADT %d of %d vehicles/average annual day',
            self.aadt(scenario_runs), len(vtype_list)
        )

        l_vehicles = self._create_vehicle_distribution(
            vtype_list,
            self.aadt(scenario_runs),
            initialsorting,
            scenario_runs.get('scenarioname')
        )

        # xml
        l_trips = etree.Element('trips')

        # create a sumo vehicle_type for each vehicle
        for i_vid, i_vehicle in l_vehicles.items():

            # filter for relevant attributes and transform to string
            l_vattr = {k: str(v) for k, v in i_vehicle.properties.items()}
            l_vattr.update({
                'id': str(i_vid),
                'color': f'{i_vehicle.color[0]/255.},'
                         f'{i_vehicle.color[1]/255.},'
                         f'{i_vehicle.color[2]/255.},'
                         f'{i_vehicle.color[3]/255.}'
            })

            # override parameters speedDev, desiredSpeed, and length if defined in run config
            l_runcfgspeeddev = self.run_config \
                .get('vtypedistribution') \
                .get(l_vattr.get('vType')) \
                .get('speedDev')
            if l_runcfgspeeddev is not None:
                l_vattr['speedDev'] = str(l_runcfgspeeddev)

            l_runcfgsigma = self.run_config \
                .get('vtypedistribution') \
                .get(l_vattr.get('vType')) \
                .get('sigma')
            if l_runcfgsigma is not None:
                l_vattr['sigma'] = str(l_runcfgsigma)

            l_runcfglength = self.run_config \
                .get('vtypedistribution') \
                .get(l_vattr.get('vType')) \
                .get('length')
            if l_runcfglength is not None:
                l_vattr['length'] = str(l_runcfglength)

            l_vattr['speedlimit'] = str(i_vehicle.speed_max)
            l_vattr['maxSpeed'] = str(i_vehicle.speed_max)

            # fix tractor vType to trailer
            if l_vattr['vType'] == 'tractor':
                l_vattr['vType'] = 'trailer'

            l_vattr['type'] = l_vattr.get('vType')

            etree.SubElement(l_trips, 'vType', attrib=l_vattr)

        # add trip for each vehicle
        for i_vid, i_vehicle in l_vehicles.items():
            etree.SubElement(l_trips, 'trip', attrib={
                'id': i_vid,
                'depart': str(i_vehicle.start_time),
                'from': 'enter_21start',
                'to': '21end_exit',
                'type': i_vid,
                'departSpeed': 'max',
            })

        with open(tripfile, 'w') as f_tripxml:
            f_tripxml.write(
                defusedxml.lxml.tostring(
                    l_trips, pretty_print=True, encoding='unicode'
                )
            )

        return l_vehicles

    # create net xml using netconvert
    def _generate_net_xml(
            self, nodefile: Path, edgefile: Path, netfile: Path, forcerebuildscenarios=False):
        '''
        Generate SUMO's net xml.

        @param nodefile:
        @param edgefile:
        @param netfile:
        @param forcerebuildscenarios:
        '''

        if Path(netfile).exists() and not forcerebuildscenarios:
            return

        l_netconvertprocess = subprocess.check_output(
            [
                self._binaries.get('netconvert'),
                f'--node-files={nodefile}',
                f'--edge-files={edgefile}',
                f'--output-file={netfile}'
            ],
            stderr=subprocess.STDOUT,
            bufsize=-1,
            close_fds=True
        )
        self._log.debug(
            '%s: %s',
            self._binaries.get('netconvert'),
            l_netconvertprocess.decode('utf8').replace('\n', '')
        )

    def _generate_route_xml(
            self, netfile: Path, tripfile: Path, routefile: Path, forcerebuildscenarios=False):
        '''
        Generate SUMO's route xml.

        @param netfile:
        @param tripfile:
        @param routefile:
        @param forcerebuildscenarios:
        '''

        if Path(routefile).exists() and not forcerebuildscenarios:
            return

        l_duarouterprocess = subprocess.check_output(
            [
                self._binaries.get('duarouter'),
                '-n', netfile,
                '-t', tripfile,
                '-o', routefile
            ],
            stderr=subprocess.STDOUT,
            bufsize=-1,
            close_fds=True
        )
        self._log.debug(
            '%s: %s',
            self._binaries.get('duarouter'),
            l_duarouterprocess.decode('utf8').replace('\n', '')
        )
