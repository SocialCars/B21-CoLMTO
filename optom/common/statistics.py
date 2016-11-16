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
"""Statistics module"""
from __future__ import division
from __future__ import print_function

import os
from collections import OrderedDict
from collections import defaultdict

import math

import optom.common.log
from optom.common.io import Writer

try:
    from lxml import etree
    from lxml.etree import XSLT
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
        from xml.etree import XSLT
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            from xml.etree import XSLT
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                from xml.etree import XSLT
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    from xml.etree import XSLT
                except ImportError:
                    print("Failed to import ElementTree from any known place")

_ILOOP_TEMPLATE = etree.XML("""
    <xsl:stylesheet version= "1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
    <detector>
    <xsl:for-each select="detector/interval/typedInterval">
    <vehicle>
    <xsl:copy-of select="@id|@type|@begin"/>
    </vehicle>
    </xsl:for-each>
    </detector>
    </xsl:template>
    </xsl:stylesheet>""")


class Statistics(object):
    """Statistics class for computing/aggregating SUMO results"""

    def __init__(self, p_args):
        self._log = optom.common.log.logger(__name__, p_args.loglevel, p_args.logfile)
        self._writer = Writer(p_args)

    def dump_traveltimes_from_iloops(self, p_run_data, p_run_config, p_scenario_config,
                                     p_scenarioname, p_initialsorting, p_current_run, p_resultsdir):
        """Reading and aggregating induction loop logs and write them to csv/json files."""

        self._log.debug("Reading and aggregating induction loop logs")

        l_vehicles = p_run_data.get("vehicles")
        l_iloopfile = p_run_data.get("iloopfile")
        l_root = etree.parse(l_iloopfile)
        l_iloop_detections = XSLT(_ILOOP_TEMPLATE)(l_root).iter("vehicle")
        l_detectors = sorted(p_scenario_config.get("detectorpositions").keys())

        # create a dictionary with vid -> detectorid -> timestep hierarchy for json output,
        # for csv the same but flat
        l_vehicle_data_json = defaultdict(dict)
        l_vehicle_data_csv = []
        for i_v in l_iloop_detections:
            l_vehicle_data_json[i_v.get("type")][i_v.get("id")] = float(i_v.get("begin"))

        # calculate traveltimes and timeloss for each adjacent detector pair
        # a vehicle passed by using the recorded timestamp
        for i_vid, i_vdata in l_vehicle_data_json.iteritems():
            l_vehicle_speed_max = l_vehicles.get(i_vid).speed_max

            l_vehicle_data_csv_row = OrderedDict()
            l_vehicle_data_csv_row["vehicle"] = "a{}".format(i_vid),
            l_vehicle_data_csv_row["vtype"] = l_vehicles.get(i_vid).vtype,
            l_vehicle_data_csv_row["speed_max"] = l_vehicle_speed_max

            i_vdata["vtype"] = l_vehicles.get(i_vid).vtype
            i_vdata["speed_max"] = l_vehicle_speed_max

            l_detector_pairs = [(l_detectors[0], l_detectors[-1]),
                                (l_detectors[1], l_detectors[-2])] + zip(l_detectors[1:-2:2],
                                                                         l_detectors[2:-1:2])

            for i_detector_x, i_detector_y in l_detector_pairs:
                l_traveltime = None
                l_opt_travel_time = None
                l_timeloss = None
                l_detector_distance = p_scenario_config.get("detectorpositions").get(
                    i_detector_y) - p_scenario_config.get("detectorpositions").get(i_detector_x)

                if i_vdata.get(i_detector_y) is not None and i_vdata.get(i_detector_x) is not None:
                    l_traveltime = i_vdata.get(i_detector_y) - i_vdata.get(i_detector_x)
                    l_opt_travel_time = l_detector_distance / l_vehicle_speed_max
                    l_timeloss = l_traveltime - l_opt_travel_time

                i_vdata["{}-{}".format(i_detector_x, i_detector_y)] = {
                    "distance": l_detector_distance,
                    "optimal_traveltime": l_opt_travel_time,
                    "travel_time": l_traveltime,
                    "time_loss": l_timeloss
                }
                l_vehicle_data_csv_row[
                    "{}-{}-distance".format(i_detector_x, i_detector_y)
                ] = l_detector_distance
                l_vehicle_data_csv_row[
                    "{}-{}-optimal_traveltime".format(i_detector_x, i_detector_y)
                ] = l_opt_travel_time
                l_vehicle_data_csv_row[
                    "{}-{}-travel_time".format(i_detector_x, i_detector_y)
                ] = l_traveltime
                l_vehicle_data_csv_row[
                    "{}-{}-time_loss".format(i_detector_x, i_detector_y)
                ] = l_timeloss

            l_vehicle_data_csv.append(l_vehicle_data_csv_row)

        self._log.debug("Writing %s results", p_scenarioname)
        l_aadtveh = "{}aadt".format(p_scenario_config.get("parameters").get("aadt")) \
            if p_run_config.get("aadt").get("enabled") \
            else "{}veh".format(p_run_config.get("nbvehicles").get("value"))
        self._writer.write_json(
            dict(l_vehicle_data_json),
            os.path.join(
                p_resultsdir,
                "{}-{}-{}-run{}-TT-TL.json.gz".format(
                    p_scenarioname, l_aadtveh, p_initialsorting,
                    str(p_current_run).zfill(
                        int(math.ceil(math.log10(p_run_config.get("runs"))))
                    )
                )
            )
        )

        l_csv_fieldnames = l_vehicle_data_csv[0].keys() if len(l_vehicle_data_csv) > 0 else []
        self._writer.write_csv(
            l_csv_fieldnames,
            l_vehicle_data_csv,
            os.path.join(
                p_resultsdir,
                "{}-{}-{}-run{}-TT-TL.csv".format(
                    p_scenarioname, l_aadtveh, p_initialsorting,
                    str(p_current_run).zfill(
                        int(math.ceil(math.log10(p_run_config.get("runs"))))
                    )
                )
            )
        )

        return l_vehicle_data_json, l_vehicle_data_csv

    @staticmethod
    def h_spread(p_data):
        """
        Calculate H-Spread of given data points
        Weisstein, Eric W. "H-Spread." From MathWorld--A Wolfram Web Resource.
        http://mathworld.wolfram.com/H-Spread.html
        Weisstein, Eric W. "Hinge." From MathWorld--A Wolfram Web Resource.
        http://mathworld.wolfram.com/Hinge.html
        :param p_data: Iterable set of data elements of (preferably) 4n+5 for n=0,1,...,N,
                       i.e. minimum length is 5
        :return: H_2 - H_1 if p_data contains at least 5 elements, otherwise raises ArithmeticError
        """
        l_data = sorted(p_data)
        l_n = len(l_data)

        if l_n < 5:
            raise ArithmeticError

        l_h1 = l_data[int((l_n + 3) / l_n - 1)]
        l_h2 = l_data[int((3 * l_n + 1) / 4 - 1)]
        return l_h2 - l_h1
