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
import versioneer

class PyTest(TestCommand):
    '''pytest class'''
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True  # pylint: disable=attribute-defined-outside-init

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


VERSION = versioneer.get_version()
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'
    ],
    keywords='',  # Separate with spaces
    author='Malte Aschermann',
    author_email='masc@tu-clausthal.de',
    url='https://gitlab.com/ascm/colmto',
    license='LGPL',
    packages=find_packages(exclude=['examples', 'tests', 'sumo']),
    include_package_data=True,
    zip_safe=False,
    tests_require=['pytest'],
    # cmdclass={
    #     'test': PyTest,
    #     'build_sphinx': BuildDoc
    # },
    cmdclass=versioneer.get_cmdclass(),
    command_options={
        'build_sphinx': {
            'project': ('setup.py', DESCRIPTION),
            'version': ('setup.py', VERSION),
            'release': ('setup.py', VERSION),
        }
    },
    install_requires=tuple(
        filter(
            lambda r: r.find('git+http') == -1, (r.replace('\n', '') for r in open('requirements.txt').readlines())
        )
    ),
    entry_points={
        'console_scripts': ['colmto=colmto.__main__:main']
    }
)
