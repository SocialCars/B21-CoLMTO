# -*- coding: utf-8 -*-
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
'''setup.py'''
import sys
from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand
from sphinx.setup_command import BuildDoc


class PyTest(TestCommand):
    '''pytest class'''
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True  # pylint: disable=attribute-defined-outside-init

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


VERSION = '0.1.2'
NAME = 'colmto'
DESCRIPTION = 'Cooperative Lane Management and Traffic flow Optimisation'

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open('readme.md').read(),
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'
    ],
    keywords='',  # Separate with spaces
    author='Malte Aschermann',
    author_email='masc@tu-clausthal.de',
    url='https://github.com/SocialCars/colmto',
    license='LGPL',
    packages=find_packages(exclude=['examples', 'tests', 'sumo']),
    include_package_data=True,
    zip_safe=False,
    tests_require=['pytest'],
    cmdclass={
        'test': PyTest,
        'build_sphinx': BuildDoc
    },
    command_options={
        'build_sphinx': {
            'project': ('setup.py', DESCRIPTION),
            'version': ('setup.py', VERSION),
            'release': ('setup.py', VERSION),
        }
    },
    install_requires=[
        'defusedxml==0.5.0',
        'codacy-coverage==1.3.11',
        'codecov==2.0.15',
        'pytest==3.5.1',
        'pytest-cov==2.5.1',
        'h5py==2.7.1',
        'lxml==4.2.1',
        'matplotlib==2.2.2',
        'numexpr==2.6.4',
        'numpy==1.14.2',
        'bottleneck==1.2.1',
        'pandas==0.22.0',
        'PyYAML==3.12',
        'pygments-style-solarized==0.1.1',
        'sh==1.12.14',
        'Sphinx==1.7.4'
    ],

    entry_points={
        'console_scripts': ['colmto=colmto.__main__:main']
    }
)
