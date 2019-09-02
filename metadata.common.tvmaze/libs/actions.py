# coding: utf-8
#
# Copyright (C) 2019, Roman Miroshnychenko aka Roman V.M. <roman1972@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Plugin route actions"""

from __future__ import absolute_import
import sys
from six import itervalues
from six.moves import urllib_parse
import xbmcgui
import xbmcplugin
from . import tvmaze, data_utils

_HANDLE = int(sys.argv[1])


def find_show(title, year=None):
    """Find a show by title"""
    shows = tvmaze.search_show(title)
    if year is not None:
        show = tvmaze.filter_by_year(shows, year)
        shows = [show] if show else ()
    for show in shows:
        show_name = u'{} ({})'.format(show['show']['name'], show['show']['premiered'][:4])
        list_item = xbmcgui.ListItem(show_name, offscreen=True)
        list_item.setArt({'thumb': show['show']['image']['medium']})
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            url=str(show['show']['id']),
            listitem=list_item,
            isFolder=True
        )


def get_details(show_id):
    show_info = tvmaze.load_show_info(show_id)
    list_item = xbmcgui.ListItem(show_info['name'], offscreen=True)
    list_item = data_utils.add_main_show_info(list_item, show_info)
    xbmcplugin.setResolvedUrl(_HANDLE, succeeded=True, listitem=list_item)


def get_episode_list(show_id):
    try:
        show_info = tvmaze.load_show_info_from_cache(show_id)
    except tvmaze.TvMazeCacheError:
        show_info = tvmaze.load_show_info(show_id)
    for episode in itervalues(show_info['episodes']):
        list_item = xbmcgui.ListItem(episode['name'], offscreen=True)
        list_item = data_utils.add_episode_info(list_item, episode, full_info=False)
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            url=str(episode['id']),
            listitem=list_item,
            isFolder=False
        )


def get_episode_details(path):
    raise NotImplementedError


def router(paramstring):
    """
    Route addon calls

    :param paramstring: url-encoded query string
    :type paramstring: str
    :raises ValueError: on unknown call action
    """
    params = dict(urllib_parse.parse_qsl(paramstring))
    if params['action'] == 'find':
        find_show(params['title'], params.get('year'))
    elif params['action'] == 'getdetails':
        get_details(params['url'])
    elif params['action'] == 'getepisodelist':
        get_episode_list(params['url'])
    elif params['action'] == 'getepisodedetails':
        get_episode_details(params['url'])
    else:
        raise RuntimeError('Invalid addon call: {}'.format(sys.argv))
    xbmcplugin.endOfDirectory(_HANDLE)
