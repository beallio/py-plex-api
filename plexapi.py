import logging
import urllib2
import urlparse
from collections import OrderedDict, namedtuple
from operator import itemgetter
from time import localtime, strftime
import datetime
from xml.etree.ElementTree import XML, Element

import xmltodict
import json


LOGGER = logging.getLogger(__name__)


def convert_xml_to_json(server_ouput):
    xml = XML(server_ouput)
    return xmltodict.parse(server_ouput)


def split_output(result):
    if ',' in result:
        result = tuple(result.split(','))
        try:
            result = tuple([int(itm) for itm in result])
        except TypeError:
            pass
    return result


class Server(object):
    """

    https://code.google.com/p/plex-api/wiki/PlexWebAPIOverview
    contains information required Plex HTTP APIs

    serverinfo: Transcode bitrateinfo, myPlexauthentication info
    nowplaying: This will retrieve the "Now Playing" Information of the PMS.
    librarysections: Contains all of the sections on the PMS. This acts as
                    a directory and you are able to "walk" through it.
    prefs: Gets the _server preferences
    servers: get the local List of servers
    ondeck: Show ondeck list
    channels_all: Returns all get_channels installed in Plex Server
    channels_recentlyviewed: Get listing of recently viewed get_channels
    recentlyadded: Gets listing of recently added media, in descending
                    order by date added
    metadata: Returns metadata from media, e.g. /library/metadata/<val>
                when <val> is an integer tied to a specific episode or movie
    """
    METADATA = '/library/metadata/'
    SERVERINFO = '/'
    NOWPLAYING = '/status/sessions'
    LIBRARYSECTIONS = '/library/sections'
    PREFS = '/:/prefs'
    SERVERS = '/servers'
    ONDECK = '/library/onDeck'
    CHANNELS_ALL = '/channels/all'
    RECENTLYADDED = '/library/recentlyAdded'

    def __init__(self, address, port):
        assert isinstance(address, str)
        assert isinstance(port, int)
        self._address = address.rstrip('/')
        self._port = port
        self._test_server_connection()

    def __repr__(self):
        return self.get_info()

    def __str__(self):
        print 'Plex library: {}'.format(self.address_and_port)
        return str(self.get_info())

    @property
    def address_and_port(self):
        scheme = 'http'
        address = self._address
        if not address.startswith(scheme):
            address = ''.join([scheme, '://', address])
        return ''.join([address, ':', str(self._port)])

    def get_info(self):
        xml = self.query(Server.SERVERINFO)
        output = json.dumps({key: xml.attrib[key] for key in xml.attrib})
        return output

    def get_servers(self):
        xml = self.query(Server.SERVERS)
        output = json.dumps([element.attrib for element in xml])
        return output

    def get_preferences(self):
        xml = self.query(Server.PREFS)
        output = json.dumps([element.attrib for element in xml])
        return output

    def get_channels(self):
        xml = self.query(Server.CHANNELS_ALL)
        output = json.dumps([element.attrib for element in xml])
        return output

    def library(self):
        return Library(server=self)

    def query(self, api_call, library_id=None):
        """
        Call plex api, and return XML data

        For /status/sessions:
        >>> '<MediaContainer size="0"></MediaContainer>'

        :param api_call:
        :return: str
        :raises: PlexConnectionError
        """
        if library_id is None:
            # no extra api call for this
            library_id = ''
        try:
            full_api_call = ''.join([api_call, library_id])
            resp = urllib2.urlopen(
                urlparse.urljoin(self.address_and_port, full_api_call))
            output = resp.read()
        except urllib2.URLError as err:
            raise PlexConnectionError(err)
        else:
            resp.close()
        return XML(output)

    def _test_server_connection(self):
        """
        Test if connection to Plex is active or not, returns error if unable to
        access _server
        >>> True
        >>> PlexConnectionError
        :return: bool, PlexConnectionError
        """
        # // TODO Need to complete code for authorization if necessary
        resp = self.query('serverinfo')
        return resp is not None


class Library(object):
    ALL = 0
    TVSHOWS = 10
    MOVIES = 20

    def __init__(self, server):
        assert isinstance(server, Server)
        self._server = server
        self._section_key_mapping = self._map_section_keys()

    def __repr__(self):
        return self

    def __str__(self):
        return str(self.get_sections())

    def get_now_playing(self):
        xml = self._server.query(self._server.NOWPLAYING)
        return xml

    def get_recently_added(self, query_type=ALL):
        assert isinstance(query_type, int)
        xml = self._server.query(self._server.RECENTLYADDED)
        output = []
        if query_type == Library.TVSHOWS:
            output += self._get_tvshow_data(xml)
        elif query_type == Library.MOVIES:
            output += self._get_movie_data(xml)
        else:
            output += self._get_tvshow_data(xml) + self._get_movie_data(xml)
        return json.dumps(output)

    def get_sections(self):
        xml = self._server.query(self._server.LIBRARYSECTIONS)
        output = [element.attrib for element in xml]
        return json.dumps(output)

    def _map_section_keys(self):
        xml = self._server.query(self._server.LIBRARYSECTIONS)
        return {int(element.attrib['key']): element.attrib['type'] for
                element in xml}

    def _get_movie_data(self, xml):
        assert isinstance(xml, Element)
        videos = xml.findall('Video')
        output = []
        for element in videos:
            # Movie
            pass
        return output

    def _get_tvshow_data(self, xml):
        assert isinstance(xml, Element)
        videos = xml.findall('Directory')
        output = []
        for element in videos:
            output.append(TVShow(self, element)._data)
        return output


class Video(object):
    DATE_FORMAT = '%m/%d/%Y'

    def __init__(self, library, video_data):
        assert isinstance(library, Library)
        assert isinstance(video_data, Element)
        self._library = library
        self._server = self._library._server
        self._element = video_data
        self._data = None

    def __repr__(self):
        pass

    def __str__(self):
        return str(self._data)

    def get_info(self):
        return self._data

    def _query_show_metadata(self, metadata_key, index):
        assert isinstance(metadata_key, str)
        assert isinstance(index, int)
        shows_key = metadata_key.split('/')
        shows_key = '/'.join(shows_key[-2:])
        try:
            metadata = self._server.query(self._server.METADATA, shows_key)
            # use index to find show in season container
            # shows are in array base 1, so offset by -1 to find correct show
            metadata = metadata[index - 1]
        except KeyError as err:
            raise PlexMissingVideoKey(err)
        except urllib2.URLError as err:
            raise PlexConnectionError(err)
        else:
            return metadata

    def _extract_data(self):
        # To be overridden by subclass
        pass

    def _process_metadata(self, metadata):
        # To be overridden by subclass
        pass


class TVShow(Video):
    def __init__(self, library, video_data):
        super(TVShow, self).__init__(library, video_data)
        self._data = self._extract_data()

    @property
    def get_json(self):
        return json.dumps(self._data)

    @property
    def get_data(self):
        return self._data

    def _extract_data(self):
        output = {}
        elem_data = self._element.attrib
        output.update(type=elem_data.get('librarySectionTitle', 'Unknown'),
                      series_summary=elem_data.get('parentSummary', ''),
                      series_title=elem_data.get('parentTitle', ''),
                      series_coverart=elem_data.get('parentThumb', ''),
                      season_coverart=elem_data.get('art', ''),
                      season=elem_data.get('title', ''))
        try:
            show_index = int(elem_data['leafCount'])
            shows_in_season = elem_data['key']
        except KeyError as err:
            raise PlexMissingVideoKey(err)
        else:
            video_metadata = self._query_show_metadata(shows_in_season,
                                                       show_index)
            output.update(self._process_metadata(video_metadata))
        return json.dumps(output)

    def _process_metadata(self, metadata):
        """

        Notes: Plex returns duration is in microseconds; addedAt in time since
         epoch; and originallyAvailableAt in format YYYY-MM-DD

        Convert duration to seconds, addedAt and originallyAvailableAt to
         datetime objects

        :param metadata:
        :return:
        """

        def convert_date(dt_obj):
            assert isinstance(dt_obj, datetime.datetime)
            return dt_obj.strftime(self.DATE_FORMAT)

        assert isinstance(metadata, Element)
        output = {}
        attribs = metadata.attrib
        try:
            orig_avail_conv = datetime.datetime.strptime(
                attribs['originallyAvailableAt'], '%Y-%m-%d')
            orig_avail_conv = convert_date(orig_avail_conv)
        except KeyError:
            # Originally Available At data not available
            orig_avail_conv = 'Not available'
        try:
            added_at_conv = datetime.datetime.fromtimestamp(int(
                attribs['addedAt']))
            added_at_conv = convert_date(added_at_conv)
        except KeyError:
            added_at_conv = 'Not available'
        output.update(show_coverart=attribs.get('thumb', ''),
                      duration_seconds=float(
                          attribs.get('duration', 0)) / 1000.0,
                      originallyAvailableAt=orig_avail_conv,
                      rating=float(attribs.get('rating', 0)),
                      summary=attribs.get('summary', ''),
                      title=attribs.get('title', ''),
                      addedAt=added_at_conv,
                      basetype=attribs.get('type', 0))
        for element in metadata:
            if element.tag in output:
                output[element.tag] += [element.attrib]
            else:
                output[element.tag] = [element.attrib]
        return output


class Movie(Video):
    def __init__(self, library, video_data):
        super(Movie, self).__init__(library, video_data)
        self.json = self._extract_data()

    def _extract_data(self):
        output = {}
        elem_data = self._element.attrib
        return json.dumps(output)


class PlexConnectionError(Exception):
    pass


class PlexAPIKeyNotFound(Exception):
    pass


class PlexLibraryUndefinedType(Exception):
    pass


class PlexMissingVideoKey(Exception):
    pass