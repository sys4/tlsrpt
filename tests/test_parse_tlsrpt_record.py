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


class MyTestCase(unittest.TestCase):
    def test_invalid_format(self):
        with self.assertRaises(Exception) as cm:
            utility.parse_tlsrpt_record("not a tlsrpt record")
        self.assertEqual(cm.exception.__str__(), "Malformed TLSRPT record: No semicolon found")

    def test_invalid_version(self):
        with self.assertRaises(Exception) as cm:
            utility.parse_tlsrpt_record("v=TLSRPTv99;rua=mailto:reports@example.com")
        self.assertEqual(cm.exception.__str__(), "Unsupported TLSRPT version: v=TLSRPTv99")

    def test_valid1(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1;rua=mailto:reports@example.com")
        self.assertEqual(len(ruas), 1)
        self.assertEqual(ruas[0], "mailto:reports@example.com")

    def test_valid1trailing(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1;rua=mailto:reports@example.com;")
        self.assertEqual(len(ruas), 1)
        self.assertEqual(ruas[0], "mailto:reports@example.com")

    def test_valid2(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1;rua=mailto:reports@example.com,mailto:hostmaster@example.com")
        self.assertEqual(len(ruas), 2)
        self.assertEqual(ruas[0], "mailto:reports@example.com")
        self.assertEqual(ruas[1], "mailto:hostmaster@example.com")

    def test_valid3(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1;rua=mailto:reports@example.com,mailto:hostmaster@example.com,https://reportbot.example.com:12345/tlsrpt")
        self.assertEqual(len(ruas), 3)
        self.assertEqual(ruas[0], "mailto:reports@example.com")
        self.assertEqual(ruas[1], "mailto:hostmaster@example.com")
        self.assertEqual(ruas[2], "https://reportbot.example.com:12345/tlsrpt")

    def test_valid3spaces(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1; rua=mailto:reports@example.com,mailto:hostmaster@example.com,https://reportbot.example.com:12345/tlsrpt")
        self.assertEqual(len(ruas), 3)
        self.assertEqual(ruas[0], "mailto:reports@example.com")
        self.assertEqual(ruas[1], "mailto:hostmaster@example.com")
        self.assertEqual(ruas[2], "https://reportbot.example.com:12345/tlsrpt")

    def test_valid3trailing(self):
        ruas = utility.parse_tlsrpt_record("v=TLSRPTv1;rua=mailto:reports@example.com,mailto:hostmaster@example.com,https://reportbot.example.com:12345/tlsrpt;")
        self.assertEqual(len(ruas), 3)
        self.assertEqual(ruas[0], "mailto:reports@example.com")
        self.assertEqual(ruas[1], "mailto:hostmaster@example.com")
        self.assertEqual(ruas[2], "https://reportbot.example.com:12345/tlsrpt")

if __name__ == '__main__':
    unittest.main()
