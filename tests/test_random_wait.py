#
#    Copyright (C) 2024 sys4 AG
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
from sys4_tlsrpt import tlsrpt   # unit under test


class MyTestCase(unittest.TestCase):
    def test_something(self):
        config = tlsrpt.ConfigReporter()
        now=tlsrpt.tlsrpt_utc_time_now()
        n = config.next_time_domainlist()
        self.assertGreater(n, now)


if __name__ == '__main__':
    unittest.main()
