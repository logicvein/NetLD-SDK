#!/usr/bin/env python
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2016  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

"""
This script converts a mkdocs.yml table of contents into a reStructuredText table of contents.
"""

import sys
import yaml

class BadSectionError(Exception):
    """Raised when a section doesn't contain either a filename or a list of
    headings/files for a subsection"""
    pass


def print_toc_section(items, caption):
    """ data is a list of single-item dictionaries, each of which represent a
        page title and a file. Sections are represented by having the dictionary value
        be another list, rather than a filename.

        Here's some example input:

   [{'Home': 'index.md'},
    {'Clearwater Architecture': 'Clearwater_Architecture.md'},
    {'Clearwater Tour': 'Clearwater_Tour.md'},
    {'Support': 'Support.md'},
    {'Installation': [{'Installation Instructions': 'Installation_Instructions.md'},
                      {'All-in-one Images': 'All_in_one_Images.md'},
                      {'Configuring Zoiper': 'Configuring_Zoiper.md'}]},
    {'Upgrading and Modifying': [{'Upgrading Clearwater': 'Upgrading_Clearwater.md'},
                                 {'Migrating to etcd': 'Migrating_To_etcd.md'}]}]

    """

    # Output the rST section heading
    # .. _{}:
    #    :caption: {}
    #    :titlesonly:
    print """
.. toctree::
   :titlesonly:
"""

    for item in items:
        for title, filename in item.iteritems():
            if isinstance(filename, basestring):
            # Special-case the index page, to avoid infinite recursion -
            # Sphinx looks in each of the files you list for a table of
            # contents, so it can list the subheadings, so listing this file
            # causes infinite recursion.
            # http://stackoverflow.com/questions/16123951/how-do-i-include-the-homepage-in-the-sphinx-toc.

                if filename == "index.md":
                    filename = "self"
                print >> sys.stderr, "toc {}: {}".format(title, filename)
                print "   {} <{}>".format(title, filename.replace(".md", ".rst"))
            elif isinstance(filename, list):
            # This is a subsection heading rather than a particular file, so
            # recurse into it
                print >> sys.stderr, "nested toc section {}: {}".format(title, filename)
                print_toc_section(filename, title)
            else:
                raise BadSectionError("Section contains badly-typed information ({}, not str or list)".format(type(filename)))

    # Separate sections with a blank line
    print ""

with open('mkdocs.yml', 'r') as f:
    data = yaml.load(f)
    print_toc_section(data['pages'], "Overview")

