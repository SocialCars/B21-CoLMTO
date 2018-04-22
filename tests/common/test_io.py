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
colmto: Test module for common.io.
'''

import json
import tempfile
import logging
import gzip

import h5py

import yaml
try:
    from yaml import CSafeDumper as SafeDumper
except ImportError:  # pragma: no cover
    from yaml import SafeDumper

import unittest

import colmto.common.io


class Namespace(object):
    '''Namespace similar to argparse'''
    # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        '''Initialisation.'''
        self.__dict__.update(kwargs)

class TestIO(unittest.TestCase):
    '''
    Test cases for IO module
    '''

    def test_reader_read_yaml(self):
        '''Test read_yaml method from Reader class.'''

        l_yaml_gold = {
            'vehicle56': {
                'timesteps': {
                    '981.00': {
                        'lane': '21segment.4080_1',
                        'angle': '90.00',
                        'lanepos': '778.36',
                        'y': '1.65',
                        'x': '6218.36',
                        'speed': '8.25'
                    },
                    '1322.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '778.48',
                        'y': '-1.65',
                        'x': '8939.98',
                        'speed': '7.28'
                    },
                    '767.00': {
                        'lane': '21segment.2720_1',
                        'angle': '90.00',
                        'lanepos': '428.48',
                        'y': '1.65',
                        'x': '4508.48',
                        'speed': '8.00'
                    },
                    '1365.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '1123.24',
                        'y': '-1.65',
                        'x': '9284.74',
                        'speed': '7.64'
                    },
                    '476.00': {
                        'lane': 'enter_21start_0',
                        'angle': '90.00',
                        'lanepos': '409.40',
                        'y': '-1.65',
                        'x': '409.40',
                        'speed': '7.56'
                    },
                    '1210.00': {
                        'lane': '21segment.5440_1',
                        'angle': '90.00',
                        'lanepos': '1273.80',
                        'y': '1.65',
                        'x': '8073.80',
                        'speed': '11.97'
                    }
                }
            }
        }

        f_temp_test = tempfile.NamedTemporaryFile()
        f_temp_test.write(yaml.dump(l_yaml_gold, Dumper=SafeDumper).encode('utf8'))
        f_temp_test.seek(0)

        self.assertEqual(
            colmto.common.io.Reader(None).read_yaml(f_temp_test.name),
            l_yaml_gold
        )

        f_temp_test.close()

        # gzip
        f_temp_test = tempfile.NamedTemporaryFile(suffix='.gz')
        f_gz = gzip.GzipFile(f_temp_test.name, 'a')
        f_gz.write(yaml.dump(l_yaml_gold, Dumper=SafeDumper).encode('utf8'))
        f_gz.close()
        f_temp_test.seek(0)

        self.assertEqual(
            colmto.common.io.Reader(None).read_yaml(f_temp_test.name),
            l_yaml_gold
        )
        f_temp_test.close()


    def test_write_yaml(self):
        '''Test write_yaml method from Writer class.'''
        l_yaml_gold = {
            'vehicle56': {
                'timesteps': {
                    '981.00': {
                        'lane': '21segment.4080_1',
                        'angle': '90.00',
                        'lanepos': '778.36',
                        'y': '1.65',
                        'x': '6218.36',
                        'speed': '8.25'
                    },
                    '1322.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '778.48',
                        'y': '-1.65',
                        'x': '8939.98',
                        'speed': '7.28'
                    },
                    '767.00': {
                        'lane': '21segment.2720_1',
                        'angle': '90.00',
                        'lanepos': '428.48',
                        'y': '1.65',
                        'x': '4508.48',
                        'speed': '8.00'
                    },
                    '1365.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '1123.24',
                        'y': '-1.65',
                        'x': '9284.74',
                        'speed': '7.64'
                    },
                    '476.00': {
                        'lane': 'enter_21start_0',
                        'angle': '90.00',
                        'lanepos': '409.40',
                        'y': '-1.65',
                        'x': '409.40',
                        'speed': '7.56'
                    },
                    '1210.00': {
                        'lane': '21segment.5440_1',
                        'angle': '90.00',
                        'lanepos': '1273.80',
                        'y': '1.65',
                        'x': '8073.80',
                        'speed': '11.97'
                    }
                }
            }
        }

        f_temp_test = tempfile.NamedTemporaryFile()

        args = Namespace(
            loglevel='debug', quiet=False, logfile='foo.log'
        )
        colmto.common.io.Writer(args).write_yaml(l_yaml_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            yaml.safe_load(f_temp_test),
            l_yaml_gold
        )

        f_temp_test.close()

        # gzip
        f_temp_test = tempfile.NamedTemporaryFile(suffix='.gz')
        colmto.common.io.Writer(None).write_yaml(l_yaml_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            yaml.safe_load(gzip.GzipFile(f_temp_test.name, 'r')),
            l_yaml_gold
        )
        f_temp_test.close()


    def test_write_json(self):
        '''Test write_json method from Writer class.'''
        l_json_gold = {
            'vehicle56': {
                'timesteps': {
                    '981.00': {
                        'lane': '21segment.4080_1',
                        'angle': '90.00',
                        'lanepos': '778.36',
                        'y': '1.65',
                        'x': '6218.36',
                        'speed': '8.25'
                    },
                    '1322.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '778.48',
                        'y': '-1.65',
                        'x': '8939.98',
                        'speed': '7.28'
                    },
                    '767.00': {
                        'lane': '21segment.2720_1',
                        'angle': '90.00',
                        'lanepos': '428.48',
                        'y': '1.65',
                        'x': '4508.48',
                        'speed': '8.00'
                    },
                    '1365.00': {
                        'lane': '21end_exit_0',
                        'angle': '90.00',
                        'lanepos': '1123.24',
                        'y': '-1.65',
                        'x': '9284.74',
                        'speed': '7.64'
                    },
                    '476.00': {
                        'lane': 'enter_21start_0',
                        'angle': '90.00',
                        'lanepos': '409.40',
                        'y': '-1.65',
                        'x': '409.40',
                        'speed': '7.56'
                    },
                    '1210.00': {
                        'lane': '21segment.5440_1',
                        'angle': '90.00',
                        'lanepos': '1273.80',
                        'y': '1.65',
                        'x': '8073.80',
                        'speed': '11.97'
                    }
                }
            }
        }

        args = Namespace(
            loglevel=logging.DEBUG, quiet=False, logfile='foo.log'
        )
        f_temp_test = tempfile.NamedTemporaryFile()
        colmto.common.io.Writer(args).write_json(l_json_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            json.load(f_temp_test),
            l_json_gold
        )

        f_temp_test.close()

        # gzip
        f_temp_test = tempfile.NamedTemporaryFile(suffix='.gz')
        colmto.common.io.Writer(None).write_json(l_json_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            json.load(gzip.GzipFile(f_temp_test.name, 'r')),
            l_json_gold
        )
        f_temp_test.close()

        # test write.json_pretty
        f_temp_test = tempfile.NamedTemporaryFile()
        colmto.common.io.Writer(None).write_json_pretty(l_json_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            json.load(f_temp_test),
            l_json_gold
        )

        f_temp_test.close()

        # gzip
        f_temp_test = tempfile.NamedTemporaryFile(suffix='.gz')
        colmto.common.io.Writer(None).write_json_pretty(l_json_gold, f_temp_test.name)
        f_temp_test.seek(0)

        self.assertEqual(
            json.load(gzip.GzipFile(f_temp_test.name, 'r')),
            l_json_gold
        )
        f_temp_test.close()


    def test_flatten_object_dict(self):
        '''test flatten_object_dict'''
        l_test_dict = {
            'foo': {
                'baz': {
                    'value': 23,
                    'attr': 'baz'
                }
            },
            'bar': {
                'bar': {
                    'value': 42,
                    'attr': 'bar'
                }
            },
            'baz': {
                'foo': {
                    'value': 21,
                    'attr': 'foo'
                }
            }
        }
        l_gold_dict = {
            'foo/baz': {
                'value': 23,
                'attr': 'baz'
            },
            'bar/bar': {
                'value': 42,
                'attr': 'bar'
            },
            'baz/foo': {
                'value': 21,
                'attr': 'foo'
            }
        }

        self.assertEqual(
            # pylint: disable=protected-access
            colmto.common.io.Writer(None)._flatten_object_dict(l_test_dict),
            # pylint: enable=protected-access
            l_gold_dict
        )


    def test_write_csv(self):
        '''test write_csv'''
        f_temp_test = tempfile.NamedTemporaryFile()
        colmto.common.io.Writer(None).write_csv(
            ['foo', 'bar'],
            [{'foo': 1, 'bar': 1}, {'foo': 2, 'bar': 2}],
            f_temp_test.name
        )
        f_temp_test.seek(0)

        with f_temp_test as csv_file:
            self.assertEqual(
                ''.encode('utf8').join(csv_file.readlines()).decode('utf8'),
                'foo,bar\r\n1,1\r\n2,2\r\n'
            )

        f_temp_test.close()


    def test_write_hdf5(self):
        '''test write_hdf5'''
        l_obj_dict = {
            'foo/baz': {
                'value': 23,
                'attr': 'baz'
            },
            'bar/bar': {
                'value': 42,
                'attr': 'bar'
            },
            'baz/foo': {
                'value': 21,
                'attr': 'foo'
            },
            'none/here': {
                'value': None,
                'attr': None
            }
        }

        f_temp_test = tempfile.NamedTemporaryFile(suffix='.hdf5')

        colmto.common.io.Writer(None).write_hdf5(
            object_dict=l_obj_dict,
            hdf5_file=f_temp_test.name,
            hdf5_base_path='root'
        )
        f_temp_test.seek(0)
        l_hdf = h5py.File(f_temp_test.name, 'r')
        l_test_dict = {}
        l_hdf['root'].visititems(
            lambda key, value: l_test_dict.update({key: value.value})
            if isinstance(value, h5py.Dataset) else None
        )
        l_hdf.close()
        self.assertEqual(
            l_test_dict,
            {'bar/bar': 42, 'baz/foo': 21, 'foo/baz': 23}
        )

        colmto.common.io.Writer(None).write_hdf5(
            object_dict={
                'foo/baz': {
                    'value': 11,
                    'attr': {'info': 'meh'}
                }
            },
            hdf5_file=f_temp_test.name,
            hdf5_base_path='root'
        )

        l_hdf = h5py.File(f_temp_test.name, 'r')
        l_test_dict = {}
        self.assertEqual(
            l_hdf['root/foo/baz'].value,
            11
        )
        self.assertEqual(
            l_hdf['root/foo/baz'].attrs.get('info'),
            'meh'
        )
        l_hdf.close()

        # test for exceptions
        with self.assertRaises(TypeError):
            colmto.common.io.Writer(None).write_hdf5(
                object_dict='foo',
                hdf5_file=f_temp_test.name,
                hdf5_base_path='root'
            )

        with self.assertRaises(IOError):
            colmto.common.io.Writer(None).write_hdf5(
                object_dict=l_obj_dict,
                hdf5_file='{}/'.format(f_temp_test.name),
                hdf5_base_path='root'
            )

        with self.assertRaises(TypeError):
            colmto.common.io.Writer(None).write_hdf5(
                object_dict={
                    'foo/baz': {
                        'value': lambda x: x,
                        'attr': {'info': 'meh'}
                    }
                },
                hdf5_file=f_temp_test.name,
                hdf5_base_path='root'
            )


if __name__=='__main__':
    unittest.main()
