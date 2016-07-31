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
from __future__ import division
from __future__ import print_function

try:
    from lxml import etree
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                except ImportError:
                    print("Failed to import ElementTree from any known place")
try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeLoader, SafeDumper
import itertools
import os
import random
import subprocess

import optom.configuration.configuration
import optom.common.io
import optom.common.colormaps
import optom.common.log
import optom.environment.vehicle

s_iloop_template = etree.XML("""
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


class SumoConfig(optom.configuration.configuration.Configuration):

    def __init__(self, p_args, p_netconvertbinary, p_duarouterbinary):
        super(SumoConfig, self).__init__(p_args)

        self._log = optom.common.log.logger(__name__, p_args.loglevel, p_args.quiet, p_args.logfile)
        self._writer = optom.common.io.Writer(p_args)
        self._netconvertbinary = p_netconvertbinary
        self._duarouterbinary = p_duarouterbinary
        self._forcerebuildscenarios = p_args.forcerebuildscenarios
        self._sumoconfigdir = os.path.join(self.outputdir, "SUMO")
        self._runsdir = os.path.join(self.outputdir, "SUMO", self._runprefix, "runs")
        self._resultsdir = os.path.join(self.outputdir, "SUMO", self._runprefix, "results")

        if not os.path.exists(self._sumoconfigdir):
            os.makedirs(self._sumoconfigdir)

        if not os.path.exists(self._runsdir):
            os.makedirs(self._runsdir)

        if not os.path.exists(self._resultsdir):
            os.makedirs(self._resultsdir)

        if self._forcerebuildscenarios:
            self._log.debug("--force-rebuild-scenarios set -> rebuilding/overwriting scenarios if already present")
        self._onlyoneotlsegment = p_args.onlyoneotlsegment

        # dump configuration
        self._writer.write_yaml(
            {
                "optomversion": self._optomversion,
                "runconfig": self.runconfig,
                "scenarioconfig": self.scenarioconfig,
                "vtypesconfig": self.vtypesconfig
            },
            os.path.join(p_args.outputdir, "SUMO", self._runprefix, "configuration.yaml")
        )

        # generate color map for vehicle max speeds
        l_global_maxspeed = max(
            map(
                lambda i_scenario: i_scenario.get("parameters").get("maxSpeed"),
                self.scenarioconfig.itervalues()
            )
        )
        self._speed_colormap = optom.common.colormaps.get_mapped_cmap(
            "plasma",
            l_global_maxspeed
        )

    @property
    def sumoconfigdir(self):
        return self._sumoconfigdir

    @property
    def runsdir(self):
        return self._runsdir

    @property
    def resultsdir(self):
        return self._resultsdir

    def get(self, p_key):
        return self.runconfig.get("sumo").get(p_key)

    def generate_scenario(self, p_scenarioname):
        l_destinationdir = os.path.join(self._runsdir, p_scenarioname)
        if not os.path.exists(os.path.join(l_destinationdir)):
            os.mkdir(l_destinationdir)

        l_scenarioconfig = self.scenarioconfig.get(p_scenarioname)
        l_runcfg = self.runconfig

        l_scenarioruns = {
            "scenarioname": p_scenarioname,
            "runs": {}
        }

        l_nodefile = l_scenarioruns["nodefile"] = os.path.join(l_destinationdir, "{}.nod.xml".format(p_scenarioname))
        l_edgefile = l_scenarioruns["edgefile"] = os.path.join(l_destinationdir, "{}.edg.xml".format(p_scenarioname))
        l_netfile = l_scenarioruns["netfile"] = os.path.join(l_destinationdir, "{}.net.xml".format(p_scenarioname))
        l_settingsfile = l_scenarioruns["settingsfile"] = os.path.join(
            l_destinationdir, "{}.settings.xml".format(p_scenarioname)
        )

        self._generate_node_xml(l_scenarioconfig, l_nodefile, self._forcerebuildscenarios)
        l_scenarioruns["detectorpositions"] = self._generate_edge_xml(l_scenarioconfig, l_edgefile,
                                                                      self._forcerebuildscenarios)
        self._generate_settings_xml(l_scenarioconfig, l_runcfg, l_settingsfile, self._forcerebuildscenarios)
        self._generate_net_xml(l_nodefile, l_edgefile, l_netfile, self._forcerebuildscenarios)

        return l_scenarioruns

    def generate_run(self, p_scenarioruns, p_initialsorting, p_run):
        l_scenarioname = p_scenarioruns.get("scenarioname")
        l_scenarioconfig = self.scenarioconfig.get(l_scenarioname)
        l_detector_positions = p_scenarioruns.get("detectorpositions")
        l_destinationdir = os.path.join(self._runsdir, p_scenarioruns.get("scenarioname"))
        if not os.path.exists(os.path.join(l_destinationdir)):
            os.mkdir(l_destinationdir)

        l_runcfg = self.runconfig

        if not os.path.exists(os.path.join(l_destinationdir, str(p_initialsorting))):
            os.mkdir(os.path.join(os.path.join(l_destinationdir, str(p_initialsorting))))

        if not os.path.exists(os.path.join(l_destinationdir, str(p_initialsorting), str(p_run))):
            os.mkdir(os.path.join(os.path.join(l_destinationdir, str(p_initialsorting), str(p_run))))

        self._log.debug(
            "Generating SUMO run configuration for scenario %s / sorting %s / run %d",
            l_scenarioname, p_initialsorting, p_run
        )

        l_netfile = p_scenarioruns.get("netfile")
        l_settingsfile = p_scenarioruns.get("settingsfile")

        l_additionalfile = os.path.join(
            l_destinationdir, str(p_initialsorting), str(p_run), "{}.add.xml".format(l_scenarioname)
        )
        l_tripfile = os.path.join(
            l_destinationdir, str(p_initialsorting), str(p_run), "{}.trip.xml".format(l_scenarioname)
        )
        l_routefile = os.path.join(
            l_destinationdir, str(p_initialsorting), str(p_run), "{}.rou.xml".format(l_scenarioname)
        )
        l_configfile = os.path.join(
            l_destinationdir, str(p_initialsorting), str(p_run), "{}.sumo.cfg".format(l_scenarioname)
        )
        # l_tripinfofile = os.path.join(l_destinationdir, str(p_initialsorting), str(p_run),
        # "{}.tripinfo-output.xml".format(l_scenarioname))
        l_iloopfile = os.path.join(
            self._runsdir, l_scenarioname, str(p_initialsorting), str(p_run), "{}.inductionLoops.xml".format(
                l_scenarioname
            )
        )

        # l_fcdfile = os.path.join(l_destinationdir, str(p_initialsorting), str(p_run),
        # "{}.fcd-output.xml".format(l_scenarioname))
        l_runcfgfiles = [l_tripfile, l_additionalfile, l_routefile, l_configfile]

        if len(filter(lambda fname: not os.path.isfile(fname), l_runcfgfiles)) > 0:
            self._log.debug(
                "Incomplete/non-existing SUMO run configuration for %s, %s, %d -> (re)building",
                l_scenarioname, p_initialsorting, p_run
            )
            self._forcerebuildscenarios = True

        self._generate_additional_xml(
            l_scenarioconfig, l_detector_positions, l_iloopfile, l_additionalfile,
            self._forcerebuildscenarios
        )
        self._generate_config_xml(
            l_configfile, l_netfile, l_routefile, l_additionalfile, l_settingsfile, l_runcfg.get("simtimeinterval"),
            self._forcerebuildscenarios
        )
        self._generate_trip_xml(
            l_scenarioconfig, l_runcfg, p_initialsorting, l_tripfile,
            self._forcerebuildscenarios
        )
        self._generate_route_xml(
            l_netfile, l_tripfile, l_routefile,
            self._forcerebuildscenarios
        )

        return {
            "settingsfile": l_settingsfile,
            "additionalfile": l_additionalfile,
            "tripfile": l_tripfile,
            "routefile": l_routefile,
            # "tripinfofile": l_tripinfofile,
            "configfile": l_configfile,
            # "fcdfile": l_fcdfile,
            "iloopfile": l_iloopfile
        }

    def _generate_node_xml(self, p_scenarioconfig, p_nodefile, p_forcerebuildscenarios=False):
        if os.path.isfile(p_nodefile) and not p_forcerebuildscenarios:
            return

        # parameters
        l_length = p_scenarioconfig.get("parameters").get("length")
        l_nbswitches = p_scenarioconfig.get("parameters").get("switches")
        l_segmentlength = l_length / (l_nbswitches + 1)

        if self._onlyoneotlsegment:
            l_length = 2 * l_segmentlength  # two times segment length

        l_nodes = etree.Element("nodes")
        etree.SubElement(l_nodes, "node", attrib={"id": "enter", "x": str(-l_segmentlength), "y": "0"})
        etree.SubElement(l_nodes, "node", attrib={"id": "21start", "x": "0", "y": "0"})
        etree.SubElement(l_nodes, "node", attrib={"id": "21end", "x": str(l_length), "y": "0"})

        # dummy node for easier from-to routing
        etree.SubElement(
            l_nodes,
            "node",
            attrib={
                "id": "exit",
                "x": str(
                    l_length + 0.1 if l_nbswitches % 2 == 1 or self._onlyoneotlsegment else l_length + l_segmentlength),
                "y": "0"
            }
        )

        with open(p_nodefile, "w") as f_pnodesxml:
            f_pnodesxml.write(etree.tostring(l_nodes, pretty_print=True))

    def _generate_edge_xml(self, p_scenarioconfig, p_edgefile, p_forcerebuildscenarios=False):
        if os.path.isfile(p_edgefile) and not p_forcerebuildscenarios:
            return

        # parameters
        l_length = p_scenarioconfig.get("parameters").get("length")
        l_nbswitches = p_scenarioconfig.get("parameters").get("switches")
        l_maxspeed = p_scenarioconfig.get("parameters").get("maxSpeed")

        # assume even distributed otl segment lengths
        l_segmentlength = l_length / (l_nbswitches + 1)

        # create edges xml
        l_edges = etree.Element("edges")

        # find slowest vehicle speed to be used as parameter for entering lane
        l_lowestspeed = min(
            map(lambda vtype: vtype.get("desiredSpeed"), self.runconfig.get("vtypedistribution").itervalues())
        )

        # Entering edge with one lane, leading to 2+1 Roadway
        etree.SubElement(
            l_edges,
            "edge",
            attrib={
                "id": "enter_21start",
                "from": "enter",
                "to": "21start",
                "numLanes": "1",
                "speed": str(l_lowestspeed)
            }
        )

        # 2+1 Roadway
        l_21edge = etree.SubElement(
            l_edges,
            "edge",
            attrib={
                "id": "21segment",
                "from": "21start",
                "to": "21end",
                "numLanes": "2",
                "spreadType": "center",
                "speed": str(l_maxspeed)
            }
        )

        # add splits and joins
        l_detector_positions = {
            "iloop": {
                "enter_21start": l_segmentlength-5,
                "21end_exit": l_segmentlength-5,
                "switches": []
            },
            "otl": []
        }

        l_addotllane = True
        for i_segmentpos in xrange(0, int(l_length), int(l_segmentlength)) \
                if not self._onlyoneotlsegment else xrange(0, int(2 * l_segmentlength - 1), int(l_segmentlength)):
            etree.SubElement(
                l_21edge,
                "split",
                attrib={
                    "pos": str(i_segmentpos),
                    "lanes": "0 1" if l_addotllane else "0",
                    "speed": str(l_maxspeed)
                }
            )

            l_detector_positions.get("iloop").get("switches").append(i_segmentpos)
            l_addotllane ^= True

        # Exit lane
        etree.SubElement(
            l_edges,
            "edge",
            attrib={
                "id": "21end_exit",
                "from": "21end",
                "to": "exit",
                "numLanes": "1",
                "spreadType": "right",
                "speed": str(l_maxspeed)
            }
        )

        with open(p_edgefile, "w") as f_pedgexml:
            f_pedgexml.write(etree.tostring(l_edges, pretty_print=True))

        return l_detector_positions

    def _generate_additional_xml(self, p_scenarioconfig, p_detector_positions, p_iloopfile, p_additionalfile,
                                 p_forcerebuildscenarios):
        if os.path.isfile(p_additionalfile) and not p_forcerebuildscenarios:
            return

        # parameters
        l_length = p_scenarioconfig.get("parameters").get("length")
        l_nbswitches = p_scenarioconfig.get("parameters").get("switches")
        # assume even distributed otl segment lengths
        l_segmentlength = l_length / (l_nbswitches + 1)

        l_additional = etree.Element("additional")
        # place induction loop right before the first split (i.e. end of starting edge)
        #     <inductionLoop id="myLoop1" lane="foo_0" pos="42" freq="900" file="out.xml"/>
        etree.SubElement(
            l_additional,
            "inductionLoop",
            attrib={
                "id": "1_pre21",
                "lane": "enter_21start_0",
                "pos": str(p_detector_positions.get("iloop").get("enter_21start")),
                "friendlyPos": "true",
                "splitByType": "true",
                "freq": "1",
                "file": p_iloopfile
            }
        )

        # induction loop at the beginning of last one-lane segment (21end_exit)
        etree.SubElement(
            l_additional,
            "inductionLoop",
            attrib={
                "id": "2_post21",
                "lane": "21end_exit_0" if l_nbswitches % 2 == 0 and not self._onlyoneotlsegment
                else "21segment.{}_0".format(p_detector_positions.get("iloop").get("switches")[-1]),
                "pos": "0",
                "friendlyPos": "true",
                "splitByType": "true",
                "freq": "1",
                "file": p_iloopfile
            }
        )

        # induction loop at the end of last one-lane segment (exit)
        etree.SubElement(
            l_additional,
            "inductionLoop",
            attrib={
                "id": "3_exit",
                "lane": "21segment.{}_0".format(
                    p_detector_positions.get("iloop").get("switches")[-1]
                ) if l_nbswitches % 2 == 1 or self._onlyoneotlsegment else "21end_exit_0",
                "pos": str(p_detector_positions.get("iloop").get("21end_exit")),
                "friendlyPos": "true",
                "splitByType": "true",
                "freq": "1",
                "file": p_iloopfile
            }
        )

        with open(p_additionalfile, "w") as f_paddxml:
            f_paddxml.write(etree.tostring(l_additional, pretty_print=True))

    # create sumo config
    def _generate_config_xml(self, p_configfile, p_netfile, p_routefile, p_additionalfile, p_settingsfile,
                             p_simtimeinterval, p_forcerebuildscenarios=False):
        if os.path.isfile(p_configfile) and not p_forcerebuildscenarios:
            return
        assert type(p_simtimeinterval) == list and len(p_simtimeinterval) == 2

        l_configuration = etree.Element("configuration")
        l_input = etree.SubElement(l_configuration, "input")
        etree.SubElement(l_input, "net-file", attrib={"value": p_netfile})
        etree.SubElement(l_input, "route-files", attrib={"value": p_routefile})
        etree.SubElement(l_input, "additional-files", attrib={"value": p_additionalfile})
        etree.SubElement(l_input, "gui-settings-file", attrib={"value": p_settingsfile})
        l_time = etree.SubElement(l_configuration, "time")
        etree.SubElement(l_time, "begin", attrib={"value": str(p_simtimeinterval[0])})

        with open(p_configfile, "w") as f_pconfigxml:
            f_pconfigxml.write(etree.tostring(l_configuration, pretty_print=True))

    def _generate_settings_xml(self, p_scenarioconfig, p_runcfg, p_settingsfile, p_forcerebuildscenarios=False):
        if os.path.isfile(p_settingsfile) and not p_forcerebuildscenarios:
            return

        l_viewsettings = etree.Element("viewsettings")
        etree.SubElement(l_viewsettings, "viewport",
                         attrib={"x": str(p_scenarioconfig.get("parameters").get("length") / 2),
                                 "y": "0",
                                 "zoom": "100"})
        etree.SubElement(l_viewsettings, "delay", attrib={"value": str(p_runcfg.get("sumo").get("gui-delay"))})

        with open(p_settingsfile, "w") as f_pconfigxml:
            f_pconfigxml.write(etree.tostring(l_viewsettings, pretty_print=True))

    def _next_timestep(self, p_lambda, p_prevstarttime, p_distribution="poisson"):
        if p_distribution == "poisson":
            return p_prevstarttime + random.expovariate(p_lambda)
        elif p_distribution == "linear":
            return p_prevstarttime + 1 / p_lambda
        else:
            return p_prevstarttime

    def _create_vehicle_distribution(self, p_runcfg, p_scenarioconfig, p_nbvehicles, p_aadt, p_initialsorting,
                                     p_vtypedistribution):
        self._log.debug("Create fixed initial vehicle distribution with %s", p_vtypedistribution)
        l_vtypedistribution = list(itertools.chain.from_iterable(
            map(
                lambda (k, v): [k] * int(round(100 * v.get("fraction"))),
                p_vtypedistribution.iteritems()
            )
        ))

        l_vehps = p_aadt / (24 * 60 * 60) \
            if not p_runcfg.get("vehiclespersecond").get("enabled") else p_runcfg.get("vehiclespersecond").get("value")

        l_vehicles = map(
            lambda vtype: optom.environment.vehicle.Vehicle(vtype=self.vtypesconfig.get(vtype),
                                                            speed_sigma=p_vtypedistribution.get(vtype).get("speedDev")
                                                            ),
            [random.choice(l_vtypedistribution) for i in xrange(p_nbvehicles)]
        )

        # update colors
        for i_vehicle in l_vehicles:
            i_vehicle.color = self._speed_colormap(i_vehicle.speedmax)

        # sort speeds according to initialsorting flag
        assert p_initialsorting in ["best", "random", "worst"]

        if p_initialsorting == "best":
            l_vehicles.sort(key=lambda v: v.speedmax, reverse=True)
        elif p_initialsorting == "worst":
            l_vehicles.sort(key=lambda v: v.speedmax)

        # assign start time and id to each vehicle
        for i, i_vehicle in enumerate(l_vehicles):
            i_vehicle.provision("vehicle{}".format(i),
                                self._next_timestep(l_vehps,
                                                    l_vehicles[i - 1].timestart if i > 0 else 0,
                                                    p_runcfg.get("starttimedistribution")))

        return l_vehicles

    def _generate_trip_xml(self, p_scenarioconfig, p_runcfg, p_initialsorting, p_tripfile,
                           p_forcerebuildscenarios=False):
        if os.path.isfile(p_tripfile) and not p_forcerebuildscenarios:
            return

        # generate simple traffic demand by considering AADT, Vmax, roadtype etc
        l_aadt = p_scenarioconfig.get("parameters").get("aadt") \
            if not p_runcfg.get("aadt").get("enabled") else p_runcfg.get("aadt").get("value")

        l_timebegin, l_timeend = p_runcfg.get("simtimeinterval")

        # number of vehicles = AADT / [seconds of day] * [scenario time in seconds]
        l_numberofvehicles = int(round(l_aadt / (24 * 60 * 60) * (l_timeend - l_timebegin))) \
            if not p_runcfg.get("nbvehicles").get("enabled") else p_runcfg.get("nbvehicles").get("value")

        self._log.debug("Scenario's AADT of %d vehicles/average annual day => %d vehicles for %d simulation seconds",
                        l_aadt, l_numberofvehicles, (l_timeend - l_timebegin))

        l_vehicles = self._create_vehicle_distribution(
            p_runcfg,
            p_scenarioconfig,
            l_numberofvehicles,
            l_aadt,
            p_initialsorting,
            p_runcfg.get("vtypedistribution")
        )

        # xml
        l_trips = etree.Element("trips")

        # create a sumo vtype for each vehicle
        for i_vehicle in l_vehicles:

            # filter for relevant attributes
            l_vattr = dict(map(lambda (k, v): (k, str(v)), filter(
                lambda (k, v): k in ["vClass", "length", "width", "height", "minGap", "accel", "decel", "speedFactor",
                                     "speedDev"], i_vehicle.vtype.iteritems()
            )))

            l_vattr["id"] = str(i_vehicle.id)
            l_vattr["color"] = "{},{},{},{}".format(*i_vehicle.color)
            # override parameters speedDev, desiredSpeed, and length if defined in run config
            l_runcfgspeeddev = self.runconfig.get("vtypedistribution").get(l_vattr.get("vClass")).get("speedDev")
            if l_runcfgspeeddev is not None:
                l_vattr["speedDev"] = str(l_runcfgspeeddev)

            l_runcfgdesiredspeed = self.runconfig.get("vtypedistribution").get(l_vattr.get("vClass")).get(
                "desiredSpeed")
            l_vattr["maxSpeed"] = str(l_runcfgdesiredspeed) if l_runcfgdesiredspeed is not None else str(
                i_vehicle.speedmax)

            l_runcfglength = self.runconfig.get("vtypedistribution").get(l_vattr.get("vClass")).get("length")
            if l_runcfglength is not None:
                l_vattr["length"] = str(l_runcfglength)

            # fix tractor vClass to trailer
            if l_vattr["vClass"] == "tractor":
                l_vattr["vClass"] = "trailer"
            l_vattr["type"] = l_vattr.get("vClass")

            etree.SubElement(l_trips, "vType", attrib=l_vattr)

        # add trips
        for i_vehicle in l_vehicles:
            etree.SubElement(l_trips, "trip", attrib={
                "id": i_vehicle.id,
                "depart": str(i_vehicle.timestart),
                "from": "enter_21start",
                "to": "21end_exit",
                "type": i_vehicle.id,
                "departSpeed": "max",
            })

        with open(p_tripfile, "w") as f_ptripxml:
            f_ptripxml.write(etree.tostring(l_trips, pretty_print=True))

    # create net xml using netconvert
    def _generate_net_xml(self, p_nodefile, p_edgefile, p_netfile, p_forcerebuildscenarios=False):
        if os.path.isfile(p_netfile) and not p_forcerebuildscenarios:
            return

        l_netconvertprocess = subprocess.check_output(
            [
                self._netconvertbinary,
                "--node-files={}".format(p_nodefile),
                "--edge-files={}".format(p_edgefile),
                "--output-file={}".format(p_netfile)
            ],
            stderr=subprocess.STDOUT
        )
        self._log.debug("%s: %s", self._netconvertbinary, l_netconvertprocess.replace("\n", ""))

    def _generate_route_xml(self, p_netfile, p_tripfile, p_routefile, p_forcerebuildscenarios=False):
        if os.path.isfile(p_routefile) and not p_forcerebuildscenarios:
            return

        l_duarouterprocess = subprocess.check_output(
            [
                self._duarouterbinary,
                "-n", p_netfile,
                "-t", p_tripfile,
                "-o", p_routefile
            ],
            stderr=subprocess.STDOUT
        )
        self._log.debug("%s: %s", self._duarouterbinary, l_duarouterprocess.replace("\n", ""))

    def aggregate_iloop_file(self, p_iloopfile):
        l_iloopdata = {}
        self._log.debug("Reading and aggregating induction loop logs")

        l_root = etree.parse(p_iloopfile)
        l_iloop_detections = etree.XSLT(s_iloop_template)(l_root).iter("vehicle")
        l_vehicle_data = {}
        for i_v in l_iloop_detections:
            if i_v.get("type") in l_vehicle_data:
                l_vehicle_data.get(i_v.get("type"))[i_v.get("id")] = float(i_v.get("begin"))
            else:
                l_vehicle_data[i_v.get("type")] = {
                    i_v.get("id"): float(i_v.get("begin"))
                }

        for i_vid, i_vdata in l_vehicle_data.iteritems():
            for i_pair in itertools.combinations(sorted(i_vdata.iteritems(), key=lambda i: i[1]), 2):
                i_vdata[(i_pair[0][0], i_pair[1][0])] = i_pair[1][1] - i_pair[0][1]

        return l_vehicle_data