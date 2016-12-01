# -*- coding: utf-8 -*-
# @package optom
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Optimisation of Overtaking Manoeuvres project.   #
# # Copyright (c) 2016, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
"""Runtime to control SUMO."""
from __future__ import division
from __future__ import print_function

import subprocess

from optom.common import log


class Runtime(object):
    """Runtime class"""
    # pylint: disable=too-few-public-methods
    def __init__(self, p_args, p_sumo_config, p_sumo_binary):
        """C'tor."""
        self._sumo_config = p_sumo_config
        self._sumo_binary = p_sumo_binary
        self._log = log.logger(__name__, p_args.loglevel, p_args.quiet, p_args.logfile)

    def run(self, p_run_config, p_scenario_name, p_run_number):
        """
        Run provided scenario.

        :param p_run_config Run configuration
        :param p_scenario_name Name of scenario (for logging purpose)
        :param p_run_number Number of current run (for logging purpose)
        """

        self._log.info("Running scenario %s: run %d", p_scenario_name, p_run_number)
        l_sumoprocess = subprocess.check_output(
            [
                self._sumo_binary,
                "-c", p_run_config.get("configfile"),
                "--gui-settings-file", p_run_config.get("settingsfile"),
                "--time-to-teleport", "-1",
                "--no-step-log",
                "--fcd-output", p_run_config.get("fcdfile")
            ],
            stderr=subprocess.STDOUT,
            bufsize=-1
        )
        self._log.debug("%s : %s", self._sumo_binary, l_sumoprocess.replace("\n", ""))
