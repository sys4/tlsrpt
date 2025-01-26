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
from tlsrpt import plugins

class MyTestCase(unittest.TestCase):
    def plugin_entrypoint(self, group, url, expected_typename):
        """
        Test existance of an entrypoint to be loaded as storage back-end
        :param group: name of the group
        :param url: URL describing the storage back-end
        :param expected_typename: expected typename of the loaded storage back-end
        """
        cls = plugins.get_plugin(group, url)
        self.assertEqual(cls.__name__, expected_typename)

    def test_plugin_entrypoints(self):
        """
        Test existance and loadability of the defined plugin entrypoints
        """
        self.plugin_entrypoint("tlsrpt.collectd", "sqlite:///tmp/test-collectd.sqlite", "TLSRPTCollectdSQLite")
        self.plugin_entrypoint("tlsrpt.collectd", "dummy://", "DummyCollectd")
        self.plugin_entrypoint("tlsrpt.fetcher", "sqlite:///tmp/test-collectd.sqlite", "TLSRPTFetcherSQLite")


if __name__ == '__main__':
    unittest.main()
