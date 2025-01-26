#
#    Copyright (C) 2024-2025 sys4 AG
#    Author Boris Lohner bl@sys4.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#

import unittest
import tlsrpt.tlsrpt
import os


class MyTestCase(unittest.TestCase):
    def get_fields_from_config_named_tuple(self, config):
        """
        Collect command line options from named tuple
        :param config: The named tuple class containing the command line options
        :return: A sorted list of the command line options, including options added by the argparse module
        """
        fields = list(config._fields)
        # add options from argparse module
        fields.append("help")
        fields.append("config_file")
        fields.sort()
        return fields

    def get_options_from_manpage(self, manpage, has_pidfile):
        """
        Collect the command line options that are documented in a manpage
        :param manpage: the name of the man page
        :return: A sorted list of the documented command line options
        """
        documented = []
        for manpage_source in [manpage+".adoc", "manpage-common-options.adoc"]:
            mpf = os.path.join(os.path.dirname(__file__), "..", "doc", "manpages", manpage_source)
            with open(mpf) as mp:
                lines = mp.readlines()
                for line in lines:
                    if line.startswith("*--"):
                        parts = line.partition("*--")
                        parts = parts[2].partition("*")
                        option = parts[0]
                        if option == "pidfilename" and not has_pidfile:
                            continue
                        documented.append(option)
        documented.sort()
        return documented

    def check_manpage_against_options(self, manpage, config, has_pidfile):
        """
        Check if the command line options defined in a named tuple match the options documented in a manpage
        :param manpage: Name of the manpage
        :param config: Named tuple class containing the command line parameters
        """
        self.maxDiff = None
        fields = self.get_fields_from_config_named_tuple(config)
        documented = self.get_options_from_manpage(manpage, has_pidfile)
        self.assertListEqual(fields, documented)

    def test_collectd_manpage(self):
        """
        Check if manpages match actual command line options for tlsrpt-collectd
        """
        self.check_manpage_against_options("tlsrpt-collectd", tlsrpt.tlsrpt.ConfigCollectd, True)

    def test_fetcher_manpage(self):
        """
        Check if manpage matches actual command line options for tlsrpt-fetcher
        """
        self.check_manpage_against_options("tlsrpt-fetcher", tlsrpt.tlsrpt.ConfigFetcher, False)

    def test_reportd_manpage(self):
        """
        Check if manpage matches actual command line options for tlsrpt-reportd
        """
        self.check_manpage_against_options("tlsrpt-reportd", tlsrpt.tlsrpt.ConfigReportd, True)


if __name__ == '__main__':
    unittest.main()
