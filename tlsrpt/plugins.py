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

from importlib.metadata import entry_points
import urllib.parse
import sys

class NoImplementationException(Exception):
    pass

def get_plugin(group, url):
    """
    Load a plugin via defined entrypoints
    :param group: name of the group to load a plugin for
    :param url: URL describing the plugin, the scheme gives the name for the plugin to load
    :return: found class implementing the plugin
    :raises NoImplementationException: if no matching plugin can be found
    """
    parsed_url = urllib.parse.urlparse(url)
    all_eps = entry_points()
    if sys.version_info[:2] >= (3, 10):
        eps = all_eps.select(group=group)
    else:
        try:
            eps = all_eps[group]
        except KeyError:
            raise NoImplementationException(f"No entry points found for {group}")
    for ep in eps:
        if ep.name == parsed_url.scheme:
            return ep.load()
    raise NoImplementationException(f"No {parsed_url.scheme} implementation found for {group} in search for {url}")
