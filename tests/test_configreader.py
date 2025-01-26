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
from unittest.mock import patch
import collections
from io import StringIO
import os
import sys
import tempfile

from tlsrpt import config

ConfigTest = collections.namedtuple("ConfigTest",
                                    ["nr",
                                     "ocfe",
                                     "ocfx",
                                     "ocxe",
                                     "ocxx",
                                     "oxfe",
                                     "oxfx",
                                     "oxxe",
                                     "oxxx"])

options_test = {
    "nr": {"type": int, "default": None, "help": ""},
    "ocfe": {"type": str, "default": "d", "help": ""},
    "ocfx": {"type": str, "default": "d", "help": ""},
    "ocxe": {"type": str, "default": "d", "help": ""},
    "ocxx": {"type": str, "default": "d", "help": ""},
    "oxfe": {"type": str, "default": "d", "help": ""},
    "oxfx": {"type": str, "default": "d", "help": ""},
    "oxxe": {"type": str, "default": "d", "help": ""},
    "oxxx": {"type": str, "default": "d", "help": ""},
}

(cfgfilefd, cfgfilename) = tempfile.mkstemp()


class MyTestCase(unittest.TestCase):
    def reset(self, co, fo, eo):
        self.cfgfilename = cfgfilename
        self.section = "TestSection"
        self.envprefix = "TESTPREFIX_"

        sys.argv.clear()
        sys.argv.append("dummy")
        if co is not None:
            for k in co:
                sys.argv.append("--"+k)
                sys.argv.append(co[k])

        os.environ.clear()  # remove only prefix-itmes?
        if eo is not None:
            for k in eo:
                os.environ[self.envprefix+k.upper()] = eo[k]

        try:
            os.remove(self.cfgfilename)
        except OSError:
            pass
        if fo is not None:
            sys.argv.append("--config_file")
            sys.argv.append(self.cfgfilename)
            f = open(self.cfgfilename, "w", encoding="utf8")
            print("[" + self.section + "]", file=f)
            for k in fo:
                print(k, "=", fo[k], file=f)
            f.close()

    def do_test(self, expect, co, fo, eo):
        self.reset(co, fo, eo)
        (tmp, pars, _, warnings) = config.options_from_cmd_cfg_env(options_test, "/etc/none", self.section, self.envprefix, {})
        cres = ConfigTest(**tmp)

        for k in options_test:
            if k not in expect:
                expect[k] = None
        cexp = ConfigTest(**expect)
        self.assertEqual(cexp, cres)
        try:
            os.remove(self.cfgfilename)
        except OSError:
            pass

    def test_override(self):
        self.do_test({"ocfe": "c", 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {"ocfe": "c"}, {"ocfe": "f"}, {"ocfe": "e"})

    def test_all(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'oxfe': "f", 'oxfx': "f"},
                     {'oxxe': "e"})

    def test_all_override(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'ocxe': "f", 'ocxx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocfx': "e", 'ocxe': "e", 'ocxx': "e", 'oxfe': "e", 'oxfx': "e", 'oxxe': "e"})

    def test_noenv(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "d", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'ocxe': "f", 'ocxx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {})

    def test_nocfg(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "e", 'oxfx': "e", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {},
                     {'ocfe': 'e', 'ocfx': "e", 'ocxe': "e", 'ocxx': "e", 'oxfe': "e", 'oxfx': "e", 'oxxe': "e"})

    def test_nocmd(self):
        self.do_test({'ocfe': 'f', 'ocfx': "f", 'ocxe': "f", 'ocxx': "f", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {},
                     {'ocfe': 'f', 'ocfx': "f", 'ocxe': "f", 'ocxx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocfx': "e", 'ocxe': "e", 'ocxx': "e", 'oxfe': "e", 'oxfx': "e", 'oxxe': "e"})

    def test_nocmd2(self):
        self.do_test({'ocfe': 'f', 'ocfx': "f", 'ocxe': "e", 'ocxx': "e", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocfx': "e", 'ocxe': "e", 'ocxx': "e", 'oxfe': "e", 'oxfx': "e", 'oxxe': "e"})

    def test_normal_all(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    def test_normal_nocmd(self):
        self.do_test({'ocfe': 'f', 'ocfx': "f", 'ocxe': "e", 'ocxx': "d", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    def test_normal_nocfg(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "e", 'oxfx': "d", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    def test_normal_noenv(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "d", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {})

    def test_normal_onlycmd(self):
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {},
                     {})

    def test_normal_onlycfg(self):
        self.do_test({'ocfe': 'f', 'ocfx': "f", 'ocxe': "d", 'ocxx': "d", 'oxfe': "f", 'oxfx': "f", 'oxxe': "d", 'oxxx': "d"},
                     {},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {})

    def test_normal_onlyenv(self):
        self.do_test({'ocfe': 'e', 'ocfx': "d", 'ocxe': "e", 'ocxx': "d", 'oxfe': "e", 'oxfx': "d", 'oxxe': "e", 'oxxx': "d"},
                     {},
                     {},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    def test_b0rkexpectation(self):
        with self.assertRaises(Exception) as cm:
            self.do_test({'b0rk_ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                         {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                         {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                         {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertRegex(cm.exception.__str__(), "got an unexpected keyword argument 'b0rk_ocfe'")

    @patch('sys.stderr', new_callable=StringIO)
    def test_b0rkcmd(self, mock_stderr):
        with self.assertRaises(SystemExit):
            self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                         {'b0rk_ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                         {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                         {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertRegex(mock_stderr.getvalue(), r"dummy: error: unrecognized arguments: --b0rk_ocfe c")

    def test_b0rkcfg(self):
        with self.assertRaises(SyntaxError) as cm:
            self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                         {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                         {'b0rk_ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                         {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertRegex(cm.exception.__str__(), r"Unknown key b0rk_ocfe in config file")

    def test_b0rkenv(self):  # mispelled or non-existent config options as environment variables cause no problem
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "d", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'b0rk_ocfe': 'e', 'b0rk_ocxe': "e", 'b0rk_oxfe': "e", 'b0rk_oxxe': "e"})

    def test_intarg_argparse_needs_strings(self):  # fake commandline must use strings, not ints
        with self.assertRaises(Exception) as cm:
            self.do_test({'nr': 3, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                         {'nr': 3, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},  # cmdline with int parm for nr
                         {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                         {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertEqual(cm.exception.__str__(), "'int' object is not subscriptable")

    def test_intarg_default(self):
        global options_test
        # patch default value into options
        options_test["nr"]["default"] = 4
        self.do_test({'nr': 4, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        # remove patched default value from options
        options_test["nr"]["default"] = None
        self.do_test({'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    def test_intarg_cmd_int(self):
        self.do_test({'nr': 4, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                     {'nr': "4", 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                     {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                     {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})

    @patch('sys.stderr', new_callable=StringIO)
    def test_intarg_cmd_string(self, mock_stderr):
        with self.assertRaises(SystemExit):
            self.do_test({'nr': 4, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                         {'nr': "text", 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                         {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                         {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertRegex(mock_stderr.getvalue(), r"dummy: error: argument --nr: invalid int value: 'text'")

    @patch('sys.stderr', new_callable=StringIO)
    def test_intarg_cmd_float(self, mock_stderr):
        with self.assertRaises(SystemExit):
            self.do_test(
                {'nr': 4, 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c", 'oxfe': "f", 'oxfx': "f", 'oxxe': "e", 'oxxx': "d"},
                {'nr': "3.1415", 'ocfe': 'c', 'ocfx': "c", 'ocxe': "c", 'ocxx': "c"},
                {'ocfe': 'f', 'ocfx': "f", 'oxfe': "f", 'oxfx': "f"},
                {'ocfe': 'e', 'ocxe': "e", 'oxfe': "e", 'oxxe': "e"})
        self.assertRegex(mock_stderr.getvalue(), r"dummy: error: argument --nr: invalid int value: '3.1415'")

    def test_type_int_cmd(self):
        self.do_test({'nr': 4,
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {'nr': "4"}, {}, {})

    def test_type_int_cfg(self):
        self.do_test({'nr': 4,
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {'nr': "4"}, {})

    def test_type_int_env(self):
        self.do_test({'nr': 4,
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {}, {'nr': "4"})

    def test_type_int_def(self):  # no type conversion is done for defaults
        global options_test
        orig = options_test["nr"]["default"]
        options_test["nr"]["default"] = "4"
        self.do_test({'nr': "4",  # string from defaults will remain string
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {}, {})
        options_test["nr"]["default"] = 4
        self.do_test({'nr': 4,  # int from defaults will remain int
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {}, {})
        options_test["nr"]["default"] = orig
        # default-less parameter can be expected as "None" or just left out of expectations, both will succeed
        self.do_test({'nr': None,
                      'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {}, {})
        self.do_test({'ocfe': 'd', 'ocfx': "d", 'ocxe': "d", 'ocxx': "d", 'oxfe': "d", 'oxfx': "d", 'oxxe': "d", 'oxxx': "d"},
                     {}, {}, {})


if __name__ == '__main__':
    unittest.main()
