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
import base64
import sys
from six import PY3, itervalues
from six.moves import urllib_parse
import xbmcgui
import xbmcplugin
from . import tvmaze, data_utils
from .utils import logger

_HANDLE = int(sys.argv[1])


def find_show(title, year=None):
    """Find a show by title"""
    logger.debug('Searching for TV show {} - {}'.format(title, year))
    search_results = tvmaze.search_show(title)
    if year is not None:
        search_result = tvmaze.filter_by_year(search_results, year)
        search_results = [search_result] if search_result else ()
    for search_result in search_results:
        show_name = search_result['show']['name']
        if search_result['show']['premiered']:
            show_name += u' ({})'.format(search_result['show']['premiered'][:4])
        list_item = xbmcgui.ListItem(show_name, offscreen=True)
        image = search_result['show']['image']
        if image:
            thumb = image['medium']
            list_item.addAvailableArtwork(thumb, 'thumb')
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            url=str(search_result['show']['id']),
            listitem=list_item,
            isFolder=True
        )


def get_details(show_id):
    logger.debug('Getting details for show id {}'.format(show_id))
    show_info = tvmaze.load_show_info(show_id)
    list_item = xbmcgui.ListItem(show_info['name'], offscreen=True)
    list_item = data_utils.add_main_show_info(list_item, show_info)
    xbmcplugin.setResolvedUrl(_HANDLE, True, list_item)


def get_episode_list(show_id):
    logger.debug('Getting episode list for show id {}'.format(show_id))
    try:
        show_info = tvmaze.load_show_info_from_cache(show_id)
    except tvmaze.TvMazeCacheError:
        show_info = tvmaze.load_show_info(show_id)
    for episode in itervalues(show_info['episodes']):
        list_item = xbmcgui.ListItem(episode['name'], offscreen=True)
        list_item = data_utils.add_episode_info(list_item, episode, full_info=False)
        encoded_ids = urllib_parse.urlencode(
            {'show_id': str(show_id), 'episode_id': str(episode['id'])}
        )
        if PY3:
            encoded_ids = encoded_ids.encode('ascii')
        url = base64.b64encode(encoded_ids).decode('ascii')
        xbmcplugin.addDirectoryItem(
            _HANDLE,
            url=url,
            listitem=list_item,
            isFolder=True
        )


def get_episode_details(encoded_ids):
    encoded_ids = base64.b64decode(encoded_ids).decode('ascii')
    decoded_ids = dict(urllib_parse.parse_qsl(encoded_ids))
    logger.debug('Getting episode details for {}'.format(decoded_ids))
    episode_info = tvmaze.load_episode_info(
        int(decoded_ids['show_id']), int(decoded_ids['episode_id'])
    )
    list_item = xbmcgui.ListItem(episode_info['name'], offscreen=True)
    list_item = data_utils.add_episode_info(list_item, episode_info, full_info=True)
    xbmcplugin.setResolvedUrl(_HANDLE, True, list_item)


def get_show_from_nfo_url(nfo_url):
    logger.debug('Parsing NFO URL {}'.format(nfo_url))
    parse_result = data_utils.parse_nfo_url(nfo_url)
    if parse_result:
        if parse_result.provider == 'tvmaze':
            show_info = tvmaze.load_show_info(parse_result.show_id)
        else:
            show_info = tvmaze.load_show_info_by_external_id(
                parse_result.provider,
                parse_result.show_id
            )
        if show_info:
            list_item = xbmcgui.ListItem(show_info['name'], offscreen=True)
            xbmcplugin.addDirectoryItem(
                _HANDLE,
                url=str(show_info['id']),
                listitem=list_item,
                isFolder=True
            )


def get_artwork(show_id):
    logger.debug('Getting artwork for show ID {}'.format(show_id))
    if show_id.startswith('tt'):
        provider = 'imdb'
    else:
        provider = 'thetvdb'
    show_info = tvmaze.load_show_info_by_external_id(provider, show_id)
    list_item = xbmcgui.ListItem(show_info['name'])
    list_item.setArt(data_utils.get_show_artwork(show_info))
    xbmcplugin.setResolvedUrl(_HANDLE, True, list_item)


def router(paramstring):
    """
    Route addon calls

    :param paramstring: url-encoded query string
    :type paramstring: str
    :raises RuntimeError: on unknown call action
    """
    params = dict(urllib_parse.parse_qsl(paramstring))
    logger.debug('Called addon with params: {}'.format(sys.argv))
    if params['action'] == 'find':
        find_show(params['title'], params.get('year'))
    elif params['action'] == 'getdetails':
        get_details(params['url'])
    elif params['action'] == 'getepisodelist':
        get_episode_list(params['url'])
    elif params['action'] == 'getepisodedetails':
        get_episode_details(params['url'])
    elif params['action'].lower() == 'nfourl':
        get_show_from_nfo_url(params['nfo'])
    elif params['action'] == 'getartwork':
        get_artwork(params['id'])
    else:
        raise RuntimeError('Invalid addon call: {}'.format(sys.argv))
    xbmcplugin.endOfDirectory(_HANDLE)