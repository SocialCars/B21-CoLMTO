# -*- coding: utf-8 -*-
# @package colmto
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
# pylint: disable=too-few-public-methods
'''Colmto main module.'''
import argparse
import datetime

from pathlib import Path

import colmto.common.configuration
import colmto.common.log
import colmto.sumo.sumosim


class Colmto(object):
    '''Colmto main class'''

    def __init__(self):
        '''Initialisation.'''

        # get config dir  ~/.colmto and create if not exist
        l_config_dir = Path('~/.colmto').expanduser()
        l_config_dir.mkdir(exist_ok=True)

        l_parser = argparse.ArgumentParser(
            prog='colmto',
            description='Process parameters for CoLMTO.'
        )

        l_parser.add_argument(
            '--runconfigfile', dest='runconfigfile', type=Path,
            default=l_config_dir / 'runconfig.yaml'
        )
        l_parser.add_argument(
            '--scenarioconfigfile', dest='scenarioconfigfile', type=Path,
            default=l_config_dir / 'scenarioconfig.yaml'
        )
        l_parser.add_argument(
            '--vtypesconfigfile', dest='vtypesconfigfile', type=Path,
            default=l_config_dir / 'vtypesconfig.yaml'
        )
        l_parser.add_argument(
            '--fresh-configs',
            dest='freshconfigs',
            action='store_true',
            default=False,
            help=f'generate fresh config files (overwrite existing ones in {l_config_dir})'
        )
        l_parser.add_argument(
            '--output-dir', dest='output_dir', type=Path,
            default=l_config_dir
        )
        l_parser.add_argument(
            '--output-scenario-dir', dest='scenario_dir', type=Path,
            default=l_config_dir, help='target directory scenario files will be written to'
        )
        l_parser.add_argument(
            '--output-results-dir', dest='results_dir', type=Path,
            default=l_config_dir, help='target directory results will be written to'
        )
        l_parser.add_argument(
            '--output-hdf5-file', dest='results_hdf5_file', type=Path,
            default=None, help='target HDF5 file results will be written to'
        )

        l_parser.add_argument(
            '--scenarios', dest='scenarios', type=str, nargs='*',
            default=None
        )

        l_parser.add_argument(
            '--initialsortings', dest='initialsortings', type=str, nargs='*',
            default=None
        )

        l_parser.add_argument(
            '--cooperation-probability', dest='cooperation_probability', type=float,
            default=None
        )

        l_parser.add_argument(
            '--runs', dest='runs', type=int,
            default=None
        )
        l_parser.add_argument(
            '--run_prefix', dest='run_prefix', type=str,
            default=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        )
        l_parser.add_argument(
            '--logfile', dest='logfile', type=Path,
            default=l_config_dir / 'colmto.log'
        )
        l_parser.add_argument(
            '--loglevel', dest='loglevel', type=str,
            default='INFO'
        )
        l_parser.add_argument(
            '-q', '--quiet', dest='quiet', action='store_true',
            default=False, help='suppress log info output to stdout'
        )
        l_parser.add_argument(
            '--debug',
            dest='loglevel',
            action='store_const',
            const='DEBUG',
            help='Equivalent to \'--loglevel DEBUG\''
        )

        l_mutex_group_run_choice = l_parser.add_mutually_exclusive_group(required=False)
        l_mutex_group_run_choice.add_argument(
            '--sumo', dest='runsumo', action='store_true',
            default=False, help='run SUMO simulation'
        )

        l_sumo_group = l_parser.add_argument_group('SUMO')

        l_sumo_group.add_argument(
            '--cse', dest='cse_enabled', action='store_true',
            default=None, help='run SUMO simulation with central optimisation entity (CSE)'
        )

        l_mutex_sumo_group = l_sumo_group.add_mutually_exclusive_group(required=False)
        l_mutex_sumo_group.add_argument(
            '--headless', dest='headless', action='store_true',
            default=None, help='run without SUMO GUI'
        )
        l_mutex_sumo_group.add_argument(
            '--gui', dest='gui', action='store_true',
            default=None, help='run with SUMO GUI'
        )
        l_sumo_group.add_argument(
            '--force-rebuild-scenarios', dest='forcerebuildscenarios', action='store_true',
            default=False,
            help='Rebuild and overwrite existing SUMO scenarios in configuration directory '
                 f'({l_config_dir})'
        )
        l_sumo_group.add_argument(
            '--only-one-otl-segment', dest='onlyoneotlsegment', action='store_true',
            default=False, help='Generate SUMO scenarios with only on OTL segment'
        )
        self._args = l_parser.parse_args()

        # get logger
        self._log = colmto.common.log.logger(
            __name__,
            self._args.loglevel,
            self._args.quiet,
            self._args.logfile
        )

    def run(self):
        '''Run CoLMTO'''
        self._log.info('---- Starting CoLMTO ----')
        l_configuration = colmto.common.configuration.Configuration(self._args)
        self._log.debug('Initial loading of configuration done')

        if l_configuration.run_config.get('sumo').get('enabled') or self._args.runsumo:
            self._log.info('---- Starting SUMO Baseline Simulation ----')
            colmto.sumo.sumosim.SumoSim(self._args).run_scenarios()


def main():
    '''main entry point'''
    Colmto().run()


if __name__ == '__main__':
    main()
