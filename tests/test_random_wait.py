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
from tlsrpt import utility   # unit under test
import datetime


class MyTestCase(unittest.TestCase):
    def test_monotone_time(self):
        now = utility.tlsrpt_utc_time_now()
        today = utility.tlsrpt_utc_date_now()
        today = datetime.datetime.combine(today, datetime.datetime.min.time(), tzinfo=datetime.timezone.utc)
        self.assertGreaterEqual(now, today)

    def test_monotone_days(self):
        today = utility.tlsrpt_utc_date_now()
        yesterday = utility.tlsrpt_utc_date_yesterday()
        self.assertGreater(today, yesterday)

    def test_report_timestamp_utc_alignment(self):
        """
        Test alignment to UTC timezone of report timestamps and test for expected values
        """
        day_length_in_s = 24*3600
        days = {"2024-01-01": 1704067200,
                "2024-02-01": 1706745600,
                "2024-07-01": 1719792000,
                "2024-09-08": 1725753600,
                "2024-09-28": 1727481600,
                "2024-11-07": 1730937600,
                "2024-12-01": 1733011200,
                }
        for day, expected_ts in days.items():
            ts = utility.tlsrpt_report_start_timestamp(day)
            offset = ts % day_length_in_s
            self.assertEqual(offset, 0, msg=f"Timestamp for day {day} is off by {offset}")
            self.assertEqual(ts, expected_ts)


if __name__ == '__main__':
    unittest.main()
