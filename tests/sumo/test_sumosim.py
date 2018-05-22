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
import os
import sys

try:
    sys.path.append(os.path.join('sumo', 'tools'))
    sys.path.append(os.path.join(os.environ.get('SUMO_HOME', os.path.join('..', '..')), 'tools'))
    import sumolib
    import colmto.sumo.sumosim
except ImportError:  # pragma: no cover
    print('Environment variable \'SUMO_HOME\' not properly declared. Skipping tests.')



class Namespace(object):
    '''Namespace similar to argparse'''
    # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        '''Initialisation.'''
        self.__dict__.update(kwargs)


class TestSumoSim(unittest.TestCase):
    '''
    Test cases for SumoSim
    '''

    @unittest.skipUnless(
        Path(f"{os.environ.get('SUMO_HOME','sumo')}/tools/sumolib").is_dir(),
        f"can't find sumolib at {os.environ.get('SUMO_HOME','sumo')}/tools/")
    def test_sumosim(self):
        '''
        Test SumoSim class
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            l_args = Namespace(
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
            )
            self.assertEqual(colmto.sumo.sumosim.SumoSim(l_args)._args, l_args)  # pylint: disable=protected-access

    @staticmethod
    @unittest.skipUnless(
        Path(f"{os.environ.get('SUMO_HOME','sumo')}/tools/sumolib").is_dir(),
        f"can't find sumolib at {os.environ.get('SUMO_HOME','sumo')}/tools/")
    def test_sumosim_runscenario_full():
        '''
        Test SumoSim.runscenarios()
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            colmto.sumo.sumosim.SumoSim(
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
                    cse_enabled=False,
                    runs=1,
                    scenarios=['NI-B210'],
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                )
            ).run_scenarios()

    @staticmethod
    @unittest.skipUnless(
        Path(f"{os.environ.get('SUMO_HOME','sumo')}/tools/sumolib").is_dir(),
        f"can't find sumolib at {os.environ.get('SUMO_HOME','sumo')}/tools/")
    def test_sumosim_runscenario_onesegment():
        '''
        Test SumoSim.runscenarios() for one otl segment
        '''
        with tempfile.NamedTemporaryFile() as f_tmp:
            colmto.sumo.sumosim.SumoSim(
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
                    cse_enabled=False,
                    runs=1,
                    scenarios=['NI-B210'],
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    initialsortings=['random']
                )
            ).run_scenarios()

    @unittest.skipUnless(
        Path(f"{os.environ.get('SUMO_HOME','sumo')}/tools/sumolib").is_dir(),
        f"can't find sumolib at {os.environ.get('SUMO_HOME','sumo')}/tools/")
    def test_sumosim_runscenarios_cse_exception(self):
        '''
        Test SumoSim.runscenarios() with CSE passing None as a scenario name
        '''
        with self.assertRaises(Exception):
            with tempfile.NamedTemporaryFile() as f_tmp, tempfile.NamedTemporaryFile() as f_tmp_hdf5:
                colmto.sumo.sumosim.SumoSim(
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
                        scenarios=['NI-B210'],
                        run_prefix='foo',
                        forcerebuildscenarios=True,
                        results_hdf5_file=Path(f_tmp_hdf5.name),
                        initialsortings=['random']
                    )
                ).run_scenario(None)

    @staticmethod
    @unittest.skipUnless(
        Path(f"{os.environ.get('SUMO_HOME','sumo')}/tools/sumolib").is_dir(),
        f"can't find sumolib at {os.environ.get('SUMO_HOME','sumo')}/tools/")
    def test_sumosim_runscenarios_cse():
        '''
        Test SumoSim.runscenarios() with CSE
        '''
        with tempfile.NamedTemporaryFile() as f_tmp, tempfile.NamedTemporaryFile() as f_tmp_hdf5:
            colmto.sumo.sumosim.SumoSim(
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
                    scenarios=['NI-B210'],
                    run_prefix='foo',
                    forcerebuildscenarios=True,
                    results_hdf5_file=Path(f_tmp_hdf5.name),
                    initialsortings=['random']
                )
            ).run_scenarios()


if __name__ == '__main__':
    unittest.main()
