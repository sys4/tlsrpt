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
import tlsrpt.randpool


class MyTestCase(unittest.TestCase):
    def check_all_same(self, ar, value=None):
        """
        Checks if all values in dict ar are the same.
        :param ar: dict to be checked
        :param value: an optional value that all values in dict ar should be equal to
        :return: true if all values in dict ar are the same
        """
        if value is None:  # no goal value given,  use first value as goal
            value = ar[0]
        for k, v in ar.items():
            if v != value:
                return False
        return True

    def run_complete_pools(self, size):
        """
        Run tests with a pool of size size
        :param size: the size of the random pool to test
        """
        iterations = 5
        randpool = tlsrpt.randpool.RandPool(size)
        # initialize counters
        count = {}
        for i in range(0, size):
            count[i] = 0
        self.assertTrue(self.check_all_same(count, 0))
        # run iterations
        expected = 0
        for n in range(0, iterations):
            expected += 1
            for i in range(0, size):
                count[randpool.get()] += 1
                if i < size - 1:
                    self.assertFalse(self.check_all_same(count))
            self.assertTrue(self.check_all_same(count, expected))

    def test_normal_pool(self):
        self.run_complete_pools(10)

    def test_minimal_pool(self):
        self.run_complete_pools(1)

    def test_huge_pool(self):
        self.run_complete_pools(10000)


if __name__ == '__main__':
    unittest.main()
