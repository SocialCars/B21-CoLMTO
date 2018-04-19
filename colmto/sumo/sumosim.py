# -*- coding: utf-8 -*-
# @package colmto.sumo
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
'''Main module to run/initialise SUMO scenarios.'''
# pylint: disable=no-member

import os
import sys
import numpy

try:
    sys.path.append(os.path.join('sumo', 'tools'))
    sys.path.append(os.path.join(os.environ.get('SUMO_HOME', os.path.join('..', '..')), 'tools'))
    import sumolib
except ImportError:  # pragma: no cover
    raise ImportError('please declare environment variable \'SUMO_HOME\' as the root')

import colmto.common.io
import colmto.common.statistics
import colmto.common.log
import colmto.cse.cse
from colmto.sumo.sumocfg import SumoConfig
from colmto.sumo.sumocfg import InitialSorting
import colmto.sumo.runtime


class SumoSim(object):  # pylint: disable=too-many-instance-attributes
    '''Class for initialising/running SUMO scenarios.'''

    def __init__(self, args):
        '''Initialisation.'''

        self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        self._args = args

        # initialise numpy PRNG
        self._prng = numpy.random.RandomState()

        self._sumocfg = SumoConfig(
            args,
            sumolib.checkBinary('netconvert'),
            sumolib.checkBinary('duarouter')
        )
        self._writer = colmto.common.io.Writer(args)
        self._statistics = colmto.common.statistics.Statistics(args)
        self._allscenarioruns = {}  # map scenarios -> runid -> files
        self._runtime = colmto.sumo.runtime.Runtime(
            args,
            self._sumocfg,
            sumolib.checkBinary('sumo')
            if self._sumocfg.sumo_run_config.get('headless')
            else sumolib.checkBinary('sumo-gui')
        )

    def run_scenario(self, scenario_name):
        '''
        Run given scenario.

        :param scenario_name: Scenario name to look up in cfgs.
        '''

        if self._sumocfg.scenario_config.get(scenario_name) is None:
            self._log.error(r'/!\ scenario %s not found in configuration', scenario_name)
            raise Exception

        l_scenario = self._sumocfg.generate_scenario(scenario_name)
        l_vtype_list = self._sumocfg.run_config.get('vtype_list')

        if scenario_name not in l_vtype_list:
            self._log.debug('Generating new vtype_list')

            l_vtypes, l_vtypefractions = zip(
                *(
                    (k, v.get('fraction', 0))
                    for k, v in self._sumocfg.run_config.get('vtypedistribution').items()
                )
            )

            l_numberofvehicles = int(
                round(
                    self._sumocfg.aadt(l_scenario) / (24 * 60 * 60) * -numpy.subtract(
                        *self._sumocfg.run_config.get('simtimeinterval')
                    )
                )
            ) if not self._sumocfg.run_config.get('nbvehicles').get('enabled') \
                else self._sumocfg.run_config.get('nbvehicles').get('value')

            l_vtype_list[scenario_name] = self._prng.choice(
                l_vtypes,
                size=l_numberofvehicles,
                p=l_vtypefractions
            )

        else:
            self._log.debug('Using pre-configured vtype_list')

        for i_initial_sorting in self._sumocfg.run_config.get('initialsortings'):

            for i_run in range(self._sumocfg.run_config.get('runs')):

                if self._sumocfg.run_config.get('cse-enabled'):
                    # cse mode: apply cse rules to vehicles and run with TraCI

                    self._writer.write_hdf5(
                        self._statistics.global_stats(
                            self._statistics.merge_vehicle_series(
                                i_run,
                                self._runtime.run_traci(
                                    self._sumocfg.generate_run(
                                        l_scenario,
                                        InitialSorting[i_initial_sorting.upper()],
                                        i_run,
                                        l_vtype_list.get(scenario_name)
                                    ),
                                    colmto.cse.cse.SumoCSE(
                                        self._args
                                    ).add_rules_from_cfg(
                                        self._sumocfg.run_config.get('rules')
                                    )
                                )
                            )
                        ),
                        hdf5_file=self._args.results_hdf5_file
                        if self._args.results_hdf5_file
                        else self._sumocfg.resultsdir / f'{self._sumocfg.run_prefix}.hdf5',
                        hdf5_base_path=os.path.join(
                            scenario_name,
                            str(self._sumocfg.aadt(self._sumocfg.generate_scenario(scenario_name))),
                            i_initial_sorting,
                            str(i_run)
                        ),
                        compression='gzip',
                        compression_opts=9,
                        fletcher32=True
                    )
                else:
                    self._runtime.run_standalone(
                        self._sumocfg.generate_run(
                            l_scenario,
                            InitialSorting[i_initial_sorting.upper()],
                            i_run,
                            l_vtype_list.get(scenario_name)
                        )
                    )

                l_aadt = self._sumocfg.scenario_config.get(scenario_name).get(
                    'parameters'
                ).get('aadt') if not self._sumocfg.run_config.get('aadt').get('enabled') \
                    else self._sumocfg.run_config.get('aadt').get('value')
                self._log.info(
                    'Scenario %s, AADT %d (%d vph), sorting %s: Finished run %d/%d',
                    scenario_name,
                    l_aadt,
                    int(l_aadt / 24),
                    i_initial_sorting,
                    i_run + 1,
                    self._sumocfg.run_config.get('runs')
                )

    def run_scenarios(self):
        '''
        Run all scenarios defined by cfgs/commandline.
        '''

        for i_scenarioname in self._sumocfg.run_config.get('scenarios'):
            self.run_scenario(i_scenarioname)

        # convert vtype_lists from numpy arrays to plain lists
        for i_scenarioname in self._sumocfg.run_config.get('vtype_list').keys():
            if isinstance(
                    self._sumocfg.run_config.get('vtype_list').get(i_scenarioname),
                    numpy.ndarray
            ):
                self._sumocfg.run_config.get('vtype_list')[i_scenarioname] \
                    = self._sumocfg.run_config.get('vtype_list').get(i_scenarioname).tolist()


        # dump configuration to run dir
        self._writer.write_yaml(
            {
                'run_config': dict(self._sumocfg.run_config),
                'scenario_config': dict(self._sumocfg.scenario_config),
                'vtypes_config': dict(self._sumocfg.vtypes_config)
            },
            self._sumocfg.sumo_config_dir / self._sumocfg.run_prefix / 'configuration.yaml'
        )
