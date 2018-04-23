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
colmto: Test module for colmto.common.log.
'''
import logging
import os
import tempfile
import unittest
import warnings

import colmto.common.log


class TestLogger(unittest.TestCase):
    '''
    Test cases for logger module
    '''

    def test_logger(self):
        '''Test logger'''

        f_temp_log = tempfile.NamedTemporaryFile()

        l_logs = [
            colmto.common.log.logger(
                name='foo',
                logfile=f_temp_log.name,
                quiet=False,
                loglevel=logging.INFO
            ),
            colmto.common.log.logger(
                name='foo',
                logfile=f_temp_log.name,
                quiet=False,
                loglevel=logging.INFO
            ),
            colmto.common.log.logger(
                name='foo',
                logfile=f_temp_log.name,
                quiet=False,
                loglevel=logging.INFO
            ),
            colmto.common.log.logger(
                name='foo',
                logfile=f_temp_log.name,
                quiet=False,
                loglevel=logging.DEBUG
            )
        ]

        for i_logger in l_logs:
            with self.subTest(pattern=i_logger):
                i_logger.info('foo')

        for i_level in ('NOTSET', 'INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'):
            with self.subTest(pattern=i_level):
                l_log = colmto.common.log.logger(
                    name='foo{}'.format(i_level),
                    logfile=f_temp_log.name,
                    quiet=True,
                    loglevel=i_level
                )
                self.assertTrue(
                    os.path.exists(os.path.dirname(f_temp_log.name))
                )
                self.assertTrue(
                    l_log.name,
                    'foo{}'.format(i_level)
                )
                self.assertEqual(
                    logging.getLevelName(l_log.level),
                    i_level
                )

        with self.assertRaises(ValueError):
            colmto.common.log.logger(
                name='bar',
                logfile=f_temp_log.name,
                quiet=True,
                loglevel='this should raise value error: Unknown level'
            )

        with self.assertRaises(TypeError):
            colmto.common.log.logger(
                name='bar',
                logfile=f_temp_log.name,
                quiet=True,
                loglevel=['this should fail']
            )

        with self.assertRaises(TypeError):
            colmto.common.log.logger(
                name='barz',
                logfile=f_temp_log.name,
                quiet='foo',
                loglevel='info'
            )

    def test_deprecated(self):
        '''
        Test deprecated decorator
        '''

        @colmto.common.log.deprecated
        def deprecated_function(arg):
            '''Deprecated dummy function'''
            return arg

        with warnings.catch_warnings():
            self.assertEqual(
                deprecated_function('foo'),
                'foo'
            )


if __name__ == '__main__':
    unittest.main()
