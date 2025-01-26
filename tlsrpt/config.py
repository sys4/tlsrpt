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

import argparse
import configparser
import os


def _options_from_cmd(options, pospar):
    """
    Helper function for options_from_cmd_cfg_env().
    """
    parser = argparse.ArgumentParser(allow_abbrev=False)
    for k in options:
        parser.add_argument("--" + k, type=options[k]["type"], help=options[k]["help"])
    for k in pospar:
        parser.add_argument(k, type=pospar[k]["type"], help=pospar[k]["help"], nargs=pospar[k]["nargs"])
    tmp = parser.parse_args()
    o = vars(tmp)  # extract dict from Namespace object
    opts = {}  # configuration options
    for k in options:
        opts[k] = o[k]
    pars = {}  # positional
    for k in pospar:
        pars[k] = o[k]
    return opts, pars


def options_from(order: str, options: dict, default_config_file: str, config_section: str, envprefix: str,
                 pospar: dict):
    """
    Get options dict from command line, configuration file, environment variables and default in an arbitrary order.
    :param order: string defining the order of the four sources, e.g. "cefd" where the characters mean:
     "c": commandline, "e": environment, "f": configfile, "d": defaults
    :param options: dict of option definitions
    :param default_config_file: name of the default config file to read when no --config_file option is given
    :param config_section: name of the section to read from a config file
    :param envprefix: prefix for environment variable names
    :param pospar: options only valid for command line, these are positional parameters
    :return: tuple of dict of all options and their values from command line, config file, environment or the defaults,
             the positional parameters from the command line and the sources where the options originated
    """
    # ocmd: options from command line
    # Add a parameter to specify a config file on the command line
    config_file_options = {"config_file": {"type": str, "default": None, "help": "Configuration file"}}
    (ocmd, params) = _options_from_cmd({**options, **config_file_options}, pospar)
    # remove the added parameter from the results
    user_config_file = ocmd.pop("config_file", None)

    # accumulate warnings to be returned
    warnings = []

    # ocfg: options from config file
    config_file = default_config_file
    if user_config_file is not None:
        if not os.path.isfile(user_config_file):
            raise FileNotFoundError("Config file not found: " + user_config_file)
        config_file = user_config_file

    ocfg = {}
    if os.path.isfile(config_file):
        cp = configparser.ConfigParser()
        cp.read(config_file)
        if config_section not in cp.sections():  # raise clearer exception instead of just running into KeyError
            raise SyntaxError("Section " + config_section + " not found in config file " + config_file)
        ocfgitems = cp.items(config_section)
    else:
        ocfgitems = {}

    # check for invalid options from config file
    for (k, v) in ocfgitems:
        if v is None or v == "":
            raise SyntaxError("Key " + k + " without value in config file " + config_file)
        elif k not in options:
            raise SyntaxError("Unknown key " + k + " in config file " + config_file)
        else:
            ocfg[k] = options[k]["type"](v)

    # oenv: options from environment
    oenv = {}
    for k in options:
        ek = envprefix + k.upper()  # environment-key: option "--key" becomes "PREFIX_KEY" as environment variable
        if ek in os.environ:
            oenv[k] = options[k]["type"](os.environ[ek])
    # check for invalid options from environment, but report them only as warnings
    for e in os.environ:
        if e.startswith(envprefix):
            ek = e.replace(envprefix,"",1).lower()
            if ek not in options:
                warnings.append(f"'{ek}' is no valid config option to be configured by environment variable {e}")

    # odef: options from defaults
    # While cmd and cfg and env need to be type converted from strings, the default values don´t need type conversion.
    # Therefore default ints need to be specified as ints, not as strings
    odef = dict(map(lambda kv: (kv[0], options[kv[0]]["default"]), options.items()))

    # combine results
    result = {}
    sources = {}
    ordermap = {"c": ocmd, "f": ocfg, "e": oenv, "d": odef}
    for k in options:
        tmp = None
        for sourcekey in order:
            src = ordermap[sourcekey]
            if tmp is None and k in src:
                tmp = src[k]
                sources[k] = sourcekey
        result[k] = tmp
    return result, params, sources, warnings


def options_from_cmd_cfg_env(options: dict, default_config_file: str, config_section: str, envprefix: str,
                             pospar: dict):
    """
    Get options dict from command line, configuration file, environment variables and defaults in that order.
    :param options: dict of option definitions
    :param default_config_file: name of the default config file to read when no --config_file option is given
    :param config_section: name of the section to read from a config file
    :param envprefix: prefix for environment variable names
    :param pospar: options only valid for command line, these are positional parameters
    :return: tuple of dict of all options and their values from command line, config file, environment or the defaults,
             the positional parameters from the command line and the sources where the options originated
    """
    return options_from("cfed", options, default_config_file, config_section, envprefix, pospar)


def options_from_cmd_env_cfg(options: dict, default_config_file: str, config_section: str, envprefix: str,
                             pospar: dict):
    """
    Get options dict from command line, environment variables, configuration file and defaults in that order.
    :param options: dict of option definitions
    :param default_config_file: name of the default config file to read when no --config_file option is given
    :param config_section: name of the section to read from a config file
    :param envprefix: prefix for environment variable names
    :param pospar: options only valid for command line, these are positional parameters
    :return: tuple of dict of all options and their values from command line, config file, environment or the defaults,
             the positional parameters from the command line and the sources where the options originated
    """
    return options_from("cefd", options, default_config_file, config_section, envprefix, pospar)
