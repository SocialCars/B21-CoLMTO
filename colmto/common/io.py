# -*- coding: utf-8 -*-
# @package colmto.common
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
"""I/O module"""

import csv
import gzip
import os

import json
import numpy

try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader, SafeDumper

import yaml

import h5py

try:
    from lxml import etree
    from lxml.etree import XSLT
except ImportError:  # pragma: no cover
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
        from xml.etree import XSLT
    except ImportError:  # pragma: no cover
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            from xml.etree import XSLT
        except ImportError:  # pragma: no cover
            try:
                # normal cElementTree install
                import cElementTree as etree
                from xml.etree import XSLT
            except ImportError:  # pragma: no cover
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    from xml.etree import XSLT
                except ImportError:  # pragma: no cover
                    print("Failed to import ElementTree from any known place")

import colmto.common.log


def xslt(template):
    """
    Wrapper to apply template to XSLT and return transformation object.
    @param template XSLT template
    @retval transformation object
    """
    return XSLT(template)


class Reader(object):
    """Read xml, json and yaml files."""

    def __init__(self, args):
        """C'tor."""
        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        else:
            self._log = colmto.common.log.logger(__name__)

    def read_etree(self, fname):
        """Parses xml file with etree. Returns etree object"""

        self._log.debug("Parsing %s with etree", fname)

        return etree.parse(fname)

    def read_json(self, filename):
        """Reads json file. Returns dictionary."""

        self._log.debug("Reading %s", filename)

        with gzip.GzipFile(filename, "r") \
                if filename.endswith(".gz") \
                else open(filename, mode="r") as f_json:
            return json.loads(f_json.read())

    def read_yaml(self, filename):
        """
        Reads yaml file and returns dictionary.
        If filename ends with .gz treat file as gzipped yaml.
        """
        self._log.debug("Reading %s", filename)

        if filename.endswith(".gz"):
            return yaml.load(gzip.GzipFile(filename, "r"), Loader=SafeLoader)

        return yaml.load(open(filename), Loader=SafeLoader)


class Writer(object):
    """Class for writing data to json, yaml, csv, hdf5."""

    def __init__(self, args=None):
        if args is not None:
            self._log = colmto.common.log.logger(__name__, args.loglevel, args.quiet, args.logfile)
        else:
            self._log = colmto.common.log.logger(__name__)

    def write_json_pretty(self, obj, filename):
        """Write json in human readable form (slow!). If filename ends with .gz, compress file."""

        self._log.debug("Writing %s", filename)
        with gzip.open(filename, "wt") if filename.endswith(".gz") \
                else open(filename, mode="w") as f_json:
            json.dump(obj, f_json, sort_keys=True, indent=4, separators=(", ", " : "))

    def write_json(self, obj, filename):
        """Write json in compact form, compress file with gzip if filename ends with .gz."""

        self._log.debug("Writing %s", filename)
        with gzip.open(filename, "wt") if filename.endswith(".gz") \
                else open(filename, mode="w") as f_json:
            json.dump(obj, f_json)

    def write_yaml(self, obj, filename, default_flow_style=False):
        """Write yaml, compress file with gzip if filename ends with .gz."""

        self._log.debug("Writing %s", filename)
        with gzip.open(filename, "wt") if filename.endswith(".gz") \
                else open(filename, mode="w") as f_yaml:
            yaml.dump(data=obj, stream=f_yaml, Dumper=SafeDumper, default_flow_style=default_flow_style)

    def write_csv(self, fieldnames, rowdict, filename):
        """Write row dictionary with provided fieldnames as csv with headers."""

        self._log.debug("Writing %s", filename)
        with open(filename, "w") as f_csv:
            csv_writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(rowdict)

    def write_hdf5(self, object_dict, hdf5_file, hdf5_base_path, **kwargs):
        """Write an object to a specific path into an open file, identified by fileid

        @param hdf5_file The file name
        @param hdf5_base_path Destination path in HDF5 structure, will be created if not existent.
        @param object_dict Object(s) to be stored in a named dictionary structure
                          ([name] -> str|int|float|list|numpy)
        @param **kwargs Optional arguments passed to create_dataset
        """
        self._log.debug("Writing %s", hdf5_file)

        # verify whether arguments are sane
        if not isinstance(object_dict, dict):
            raise TypeError("objectdict is not a dictionary")

        with h5py.File(hdf5_file, mode="a") as f_hdf5:

            # create group if it doesn't exist
            l_group = f_hdf5[hdf5_base_path] \
                if hdf5_base_path in f_hdf5 else f_hdf5.create_group(hdf5_base_path)

            # add datasets for each element of objectdict,
            # if they already exist by name, overwrite them
            for i_path, i_object_value in Writer._flatten_object_dict(object_dict).items():

                # remove filters if we have a scalar object, i.e. string, int, float
                if isinstance(i_object_value.get("value"), (str, int, float)):
                    kwargs.pop("compression", None)
                    kwargs.pop("compression_opts", None)
                    kwargs.pop("fletcher32", None)
                    kwargs.pop("chunks", None)

                if i_path in l_group:
                    # remove previous object by i_path id and add the new one
                    del l_group[i_path]

                if i_object_value.get("value") is not None \
                        and i_object_value.get("attr") is not None:
                    try:
                        l_group.create_dataset(
                            name=i_path,
                            data=numpy.asarray(i_object_value.get("value"))
                            if not isinstance(i_object_value.get("value"), str)
                            else i_object_value.get("value"),
                            **kwargs
                        ).attrs.update(
                            i_object_value.get("attr")
                            if isinstance(i_object_value.get("attr"), dict) else {}
                        )
                    except TypeError as error:
                        self._log.error(
                            "error writing %s: %s (%s)",
                            i_path,
                            i_object_value.get("value"),
                            error
                        )
                        raise TypeError(error)

    @staticmethod
    def _flatten_object_dict(dictionary):
        """
        Flatten dictionary and apply a "/"-separated key (path) structure for HDF5 writing.
        @param dictionary: dictionary
        @retval: dictionary with flattened structure
        """
        def items():
            """
            Expand dictionary.

            yields (key, value) pairs of sub-dictionaries
            @retval: (key, value) pairs
            """
            for i_k, i_v in list(dictionary.items()):
                if isinstance(i_v, dict) and "value" not in list(i_v.keys()):
                    for i_sk, i_sv in list(Writer._flatten_object_dict(i_v).items()):
                        yield os.path.join(str(i_k), str(i_sk)), i_sv
                else:
                    yield i_k, i_v
        return dict(items())
