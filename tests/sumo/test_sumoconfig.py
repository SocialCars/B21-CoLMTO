# -*- coding: utf-8 -*-
# @package tests.common
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
colmto: Test module for common.sumo.
'''

import unittest
import tempfile
from pathlib import Path

import colmto.sumo.sumocfg
from colmto.common.helper import InitialSorting


class Namespace(object):
    '''Namespace similar to argparse'''
    # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        '''Initialisation.'''
        self.__dict__.update(kwargs)


class TestSUMOConfiguration(unittest.TestCase):
    '''
    Test cases for Configuration
    '''

    def test_sumo_configuration(self):
        '''
        Test SUMOConfig class
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            for i_force in (False, True):
                with self.subTest(pattern=i_force):
                    colmto.sumo.sumocfg.SumoConfig(
                        Namespace(
                            loglevel='DEBUG',
                            quiet=False,
                            logfile=f_tmp.name,
                            output_dir=Path(f_tmp.name).parent,
                            runconfigfile=Path(f_tmp.name),
                            scenarioconfigfile=Path(f_tmp.name),
                            vtypesconfigfile=Path(f_tmp.name),
                            freshconfigs=True,
                            headless=True,
                            gui=False,
                            onlyoneotlsegment=True,
                            cse_enabled=True,
                            runs=1,
                            scenarios=None,
                            run_prefix='foo',
                            forcerebuildscenarios=i_force,
                            initialsortings=['random']
                        ),
                        netconvertbinary=None,
                        duarouterbinary=None
                    )

    def test_sumo_configuration_createvehicledistribution(self):
        '''
        Test SUMOConfig _create_vehicle_distribution
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=True,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )

            self.assertDictEqual(l_sumo_config.sumo_run_config, l_sumo_config.run_config.get('sumo'))
            l_sumo_config._create_vehicle_distribution(                     # pylint: disable=protected-access
                vtype_list=('passenger', 'truck', 'tractor', 'passenger'),
                aadt=8400,
                initialsorting=InitialSorting.RANDOM,
                scenario_name='NI-B210'
            )

            with self.assertRaises(ValueError):
                l_sumo_config._create_vehicle_distribution(                 # pylint: disable=protected-access
                    vtype_list=('passenger', 'truck', 'tractor', 'passenger'),
                    aadt=8400,
                    initialsorting='meh',
                    scenario_name='NI-B210'
                )

    def test_sumo_configuration_aadt(self):
        '''
        Test SUMOConfig aadt
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=True,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )
            self.assertEqual(l_sumo_config.aadt({'scenarioname': 'NI-B210'}), 13000.0)

    def test_sumo_configuration_settingsxml(self):
        '''
        Test SUMOConfig _generate_settings_xml
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=True,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )
            l_sumo_config._generate_settings_xml(l_sumo_config.run_config, f_tmp.name, forcerebuildscenarios=True)  # pylint: disable=protected-access
            l_sumo_config._generate_settings_xml(l_sumo_config.run_config, f_tmp.name, forcerebuildscenarios=False) # pylint: disable=protected-access

    def test_sumo_configuration_nodexml(self):
        '''
        Test SUMOConfig _generate_node_xml
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=True,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )
            l_sumo_config._generate_node_xml(l_sumo_config.scenario_config.get('NI-B210'), f_tmp.name, forcerebuildscenarios=True)  # pylint: disable=protected-access
            l_sumo_config._generate_node_xml(l_sumo_config.scenario_config.get('NI-B210'), f_tmp.name, forcerebuildscenarios=False) # pylint: disable=protected-access
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=False,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )
            l_sumo_config._generate_node_xml(l_sumo_config.scenario_config.get('NI-B210'), f_tmp.name, forcerebuildscenarios=True)  # pylint: disable=protected-access

    def test_sumo_configuration_edge_xml(self):
        '''
        Test SUMOConfig _generate_edge_xml
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_sumo_config = colmto.sumo.sumocfg.SumoConfig(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    output_dir=Path(f_tmp.name).parent,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=True,
                    cse_enabled=True,
                    runs=1,
                    scenarios=None,
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                ),
                netconvertbinary=None,
                duarouterbinary=None
            )
            l_sumo_config._generate_edge_xml('NI-B210', l_sumo_config.scenario_config.get('NI-B210'), f_tmp.name, forcerebuildscenarios=True)  # pylint: disable=protected-access
            l_sumo_config._generate_edge_xml('NI-B210', l_sumo_config.scenario_config.get('NI-B210'), f_tmp.name, forcerebuildscenarios=False) # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
