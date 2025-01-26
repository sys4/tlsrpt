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
import email.utils
from tlsrpt import tlsrpt

class MyTestCase(unittest.TestCase):
    def test_email_headers(self):
        """
        Test if setting of email headers needed for a TLSRPT report works
        """
        msg = tlsrpt.EmailReport()
        msg['From'] = "sender@s.example.com"
        msg['To'] = "recipient@r.example.com"
        message_id = email.utils.make_msgid(domain=msg["From"].groups[0].addresses[0].domain)
        msg.add_header("Message-ID", message_id)
        msg.add_header("TLS-Report-Domain", "example.com")
        msg.add_header("TLS-Report-Submitter", "Example Inc")

        self.assertEqual(msg.get_header("Message-ID"), message_id)
        self.assertEqual(msg.get_header("TLS-Report-Domain"), "example.com")
        self.assertEqual(msg.get_header("TLS-Report-Submitter"), "Example Inc")


if __name__ == '__main__':
    unittest.main()
