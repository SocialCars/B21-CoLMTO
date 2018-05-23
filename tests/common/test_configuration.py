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
colmto: Test module for common.configuration.
'''

import unittest
import tempfile
from pathlib import Path
from types import MappingProxyType

import colmto.common.configuration


class Namespace(object):
    '''Namespace similar to argparse'''
    # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        '''Initialisation.'''
        self.__dict__.update(kwargs)


class TestConfiguration(unittest.TestCase):
    '''
    Test cases for Configuration
    '''

    def test_configuration(self):
        '''
        Test Configuration class
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_args = Namespace(
                loglevel='DEBUG',
                quiet=False,
                logfile=f_tmp.name,
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
                initialsortings=['random'],
                cooperation_probability=None
            )
            self.assertEqual(colmto.common.configuration.Configuration(l_args)._args, l_args)  # pylint: disable=protected-access

            colmto.common.configuration.Configuration(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=False,
                    gui=True,
                    onlyoneotlsegment=False,
                    cse_enabled=False,
                    runs=None,
                    scenarios=['all'],
                    initialsortings=['random'],
                    cooperation_probability=None
                )
            )
            colmto.common.configuration.Configuration(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=False,
                    gui=True,
                    onlyoneotlsegment=False,
                    cse_enabled=False,
                    runs=None,
                    scenarios='foo',
                    initialsortings=['random'],
                    cooperation_probability=None
                )
            )

    def test_configuration_baseexceptions(self):
        '''
        Test for BaseExceptions
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            with self.assertRaises(BaseException):
                colmto.common.configuration.Configuration(
                    Namespace(
                        loglevel='DEBUG',
                        quiet=False,
                        logfile=f_tmp.name,
                        runconfigfile=None,
                        scenarioconfigfile=Path(f_tmp.name),
                        vtypesconfigfile=Path(f_tmp.name),
                        freshconfigs=True,
                        headless=True,
                        gui=False,
                        onlyoneotlsegment=True,
                        cse_enabled=True,
                        runs=1,
                        scenarios=None,
                        initialsortings=['random'],
                        cooperation_probability=None
                    )
                )
            with self.assertRaises(BaseException):
                colmto.common.configuration.Configuration(
                    Namespace(
                        loglevel='DEBUG',
                        quiet=False,
                        logfile=f_tmp.name,
                        runconfigfile=Path(f_tmp.name),
                        scenarioconfigfile=None,
                        vtypesconfigfile=Path(f_tmp.name),
                        freshconfigs=True,
                        headless=True,
                        gui=False,
                        onlyoneotlsegment=True,
                        cse_enabled=True,
                        runs=1,
                        scenarios=None,
                        initialsortings=['random'],
                        cooperation_probability=None
                    )
                )

    def test_configuration_properties(self):
        '''
        Test Configuration properties
        '''

        with tempfile.NamedTemporaryFile() as f_tmp:
            l_config = colmto.common.configuration.Configuration(
                Namespace(
                    loglevel='DEBUG',
                    quiet=False,
                    logfile=f_tmp.name,
                    runconfigfile=Path(f_tmp.name),
                    scenarioconfigfile=Path(f_tmp.name),
                    vtypesconfigfile=Path(f_tmp.name),
                    freshconfigs=True,
                    headless=True,
                    gui=False,
                    onlyoneotlsegment=False,
                    cse_enabled=False,
                    runs=1000,
                    scenarios=['NI-B210'],
                    scenario_dir=Path(f_tmp.name),
                    output_dir=Path(f_tmp.name),
                    run_prefix='foo',
                    initialsortings=['random'],
                    cooperation_probability=None
                )
            )
            self.assertIsInstance(l_config.run_config, MappingProxyType)
            l_runconfig = dict(l_config.run_config)
            del l_runconfig['colmto_version']
            self.assertListEqual(l_runconfig.get('initialsortings'), ['random'])
            l_runconfig['initialsortings'] = ['best', 'random', 'worst']
            self.assertDictEqual(l_runconfig, colmto.common.configuration._DEFAULT_CONFIG_RUN)  # pylint: disable=protected-access
            self.assertIsInstance(l_config.scenario_config, MappingProxyType)
            self.assertDictEqual(dict(l_config.scenario_config), colmto.common.configuration._DEFAULT_CONFIG_SCENARIO) # pylint: disable=protected-access
            self.assertEqual(l_config.scenario_dir, Path(f_tmp.name))
            self.assertIsInstance(l_config.vtypes_config, MappingProxyType)
            self.assertDictEqual(dict(l_config.vtypes_config), colmto.common.configuration._DEFAULT_CONFIG_VTYPES) # pylint: disable=protected-access
            self.assertEqual(l_config.output_dir, Path(f_tmp.name))
            self.assertEqual(l_config.run_prefix, 'foo')
            self.assertEqual(l_config.run_config.get('cooperation_probability'), None)


if __name__ == '__main__':
    unittest.main()
