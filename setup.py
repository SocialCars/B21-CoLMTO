# -*- coding: utf-8 -*-
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
import sys

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["tests"]
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


version = "0.1.1"

setup(name="colmto",
      version=version,
      description="Cooperative Lane Management and Traffic flow Optimisation (CoLMTO)",
      long_description=open("readme.md").read(),
      classifiers=[  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Programming Language :: Python"
      ],
      keywords="",  # Separate with spaces
      author="Malte Aschermann",
      author_email="masc@tu-clausthal.de",
      url="https://github.com/SocialCars/colmto",
      license="LGPL",
      packages=find_packages(exclude=["examples", "tests", "sumo"]),
      include_package_data=True,
      zip_safe=False,
      tests_require=["pytest"],
      cmdclass={"test": PyTest},

      # TODO: List of packages that this one depends upon:
      install_requires=[
          "doxypy",
          "h5py",
          "lxml",
          "matplotlib",
          "nose",
          "pytest",
          "PyYAML",
          "sh",
      ],

      # TODO: List executable scripts, provided by the package (this is just an example)
      entry_points={
        "console_scripts":
        ["colmto=run"]
      }
)
