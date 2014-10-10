import logging
import urllib2
import urlparse
from collections import OrderedDict, namedtuple
from operator import itemgetter
import datetime
from xml.etree.ElementTree import XML, Element, tostringlist, tostring

from xmltodict import parse as xmlparse
import json


LOGGER = logging.getLogger(__name__)
JSON_OUTPUT = True


def split_output(result):
    if ',' in result:
        result = tuple(result.split(','))
        try:
            result = tuple([int(itm) for itm in result])
        except TypeError:
            pass
    return result


def determine_output(values):
    if JSON_OUTPUT:
        assert isinstance(values, OrderedDict)
        output = convert_xml_to_json(values)
    else:
        output = XML(values)
    return output


def convert_xml_to_json(values):
    #assert isinstance(values, str)
    values = xmlparse(values)
    output = json.dumps(values, sort_keys=True, skipkeys=True)
    return output


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
        return str(convert_xml_to_json(self._info))

    def __str__(self):
        return str(convert_xml_to_json(self._info))

    @property
    def address_and_port(self):
        scheme = 'http'
        address = self._address
        if not address.startswith(scheme):
            address = ''.join([scheme, '://', address])
        return ''.join([address, ':', str(self._port)])

    @property
    def json(self):
        return convert_xml_to_json(self._info)

    @property
    def xml(self):
        return XML(self._info)

    @property
    def library(self):
        return Library(server=self, query=Server.LIBRARYSECTIONS)

    @property
    def preferences(self):
        return Preferences(server=self, query=Server.PREFS)

    @property
    def servers(self):
        return Servers(server=self, query=Server.SERVERS)

    @property
    def channels(self):
        return Servers(server=self, query=Server.CHANNELS_ALL)

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
        return output

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

    @property
    def _info(self):
        return self.query(Server.SERVERINFO)


class Base(object):
    def __init__(self, server, query):
        assert isinstance(server, Server)
        assert isinstance(query, str)
        self._server = server
        self._query = query

    def __repr__(self):
        return self._info

    def __str__(self):
        return str(convert_xml_to_json(self._info))

    @property
    def json(self):
        return convert_xml_to_json(self._info)

    @property
    def xml(self):
        return XML(self._info)

    @property
    def _info(self):
        return self._server.query(self._query)


class Preferences(Base):
    def __init__(self, server, query):
        super(Preferences, self).__init__(server, query)


class Servers(Base):
    def __init__(self, server, query):
        super(Servers, self).__init__(server, query)


class Channels(Base):
    def __init__(self, server, query):
        super(Channels, self).__init__(server, query)


class Sections(Base):
    def __init__(self, server, query):
        super(Sections, self).__init__(server, query)


class NowPlaying(Base):
    def __init__(self, server, query):
        super(NowPlaying, self).__init__(server, query)


class RecentlyAdded(Base):
    EPISODES = 'Directory'
    MOVIES = 'Video'

    def __init__(self, server, query):
        super(RecentlyAdded, self).__init__(server, query)

    @property
    def episodes(self):
        return RecentlyAddedVideos(class_obj=self, query=RecentlyAdded.EPISODES)

    @property
    def movies(self):
        return RecentlyAddedVideos(class_obj=self, query=RecentlyAdded.MOVIES)


class RecentlyAddedVideos(object):
    def __init__(self, class_obj, query):
        self._class_obj = class_obj
        self._query = query

    @property
    def json(self):
        videos_xml = self._get_videos_xml()
        videos = [xmlparse(tostring(video)) for video in videos_xml]
        return json.dumps(videos)

    @property
    def xml(self):
        return self._get_videos_xml()

    def _get_videos_xml(self):
        xml = XML(self._class_obj._info)
        return xml.findall(self._query)


class Library(Base):
    def __init__(self, server, query):
        super(Library, self).__init__(server, query)

    def __str__(self):
        return str(self.sections.json)

    @property
    def nowplaying(self):
        return NowPlaying(self._server, self._server.NOWPLAYING)

    @property
    def recentlyadded(self):
        return RecentlyAdded(self._server, self._server.RECENTLYADDED)

    @property
    def sections(self):
        return RecentlyAdded(self._server, self._server.LIBRARYSECTIONS)


class Video(object):
    DATE_FORMAT = '%m/%d/%Y'

    def __init__(self, library, video_data):
        assert isinstance(library, Library)
        assert isinstance(video_data, Element)
        self._library = library
        self._server = self._library._server
        self._video_data = video_data

    def __repr__(self):
        return str(self.get_data())

    def __str__(self):
        return str(self.get_data())

    def get_data(self):
        return self._extract_data()

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
        return

    def _process_metadata(self, metadata):
        # To be overridden by subclass
        return


class Section(object):
    def __init__(self, library):
        assert isinstance(library, Library)
        pass


class Season(object):
    def __init__(self, library):
        assert isinstance(library, Library)
        pass
    pass


class Episode(Video):
    def __init__(self, library, video_data):
        super(Episode, self).__init__(library, video_data)

    def _extract_data(self):
        output = {}
        elem_data = self._video_data.attrib
        output.update(type=elem_data.get('librarySectionTitle', 'Unknown'),
                      series_summary=elem_data.get('parentSummary', ''),
                      series_title=elem_data.get('parentTitle', ''),
                      series_coverart=elem_data.get('parentThumb', ''),
                      season_coverart=elem_data.get('thumb', ''),
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
        return determine_output(output)

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

        def check_dates(value, date_format=None):
            """
            Check if Originally Available Date and Added at date exist.
            Convert to date time objects, and format datetime object

            :param value: key value for lookup in element
            :type value: str
            :param date_format: datetime format string
            :type date_format: str
            :return output: datetime.datetime
            :return output_conv: str
            """
            try:
                if date_format:
                    # parse string with supplied date formatting string
                    output = datetime.datetime.strptime(attribs[value],
                                                        date_format)
                else:
                    # no formatting string supplied, assume time since epoch
                    output = datetime.datetime.fromtimestamp(
                        int(attribs[value]))
                output_conv = convert_date(output)
            except KeyError:
                # Date data not available
                output, output_conv = ['Not available'] * 2
            return output, output_conv

        assert isinstance(metadata, Element)
        output = {}
        attribs = metadata.attrib
        orig_avail, orig_avail_conv = check_dates('originallyAvailableAt',
                                                  '%Y-%m-%d')
        added_at, added_at_conv = check_dates('addedAt')
        output.update(show_coverart=attribs.get('thumb', ''),
                      duration_seconds=float(
                          attribs.get('duration', 0)) / 1000.0,
                      originallyAvailableAt=orig_avail_conv,
                      rating=float(attribs.get('rating', 0)),
                      summary=attribs.get('summary', ''),
                      title=attribs.get('title', ''),
                      addedAt=added_at_conv,
                      basetype=attribs.get('type', 0))
        if not JSON_OUTPUT:
            output.update(addedAt_dt=added_at,
                          originallyAvailableAt_dt=orig_avail)
        for element in metadata:
            if element.tag == 'Media':
                # capture Media data in Media object
                value = Media(element).get_data()
            else:
                value = element.attrib
                value = value['tag']
                # Extract Writers, directors, etc
            if element.tag in output:
                output[element.tag] += [value]
            else:
                output[element.tag] = [value]
        return output


class Movie(Video):
    def __init__(self, library, video_data):
        super(Movie, self).__init__(library, video_data)
        self.json = self._extract_data()

    def _extract_data(self):
        output = {}
        elem_data = self._video_data.attrib
        return json.dumps(output)


class Media(object):
    """
    Media object.  Returns data regarding the media type for a Video in
    a dictionary

        'aspectRatio': '1.78', (width / height)
        'audioChannels': 6,
        'audioCodec': 'ac3',
        'bitrate': 4340,
        'container': 'mkv',
        'duration': 1399107, (in microseconds)
        'file': '/TV/Show Title/Season XX/Filename.ext', (directory location)
        'height': 720, (in pixels)
        'id': 2177,
        'key': '/library/parts/2177/file.ext',
        'size': 758966231, (in bytes)
        'videoCodec': 'h264',
        'videoFrameRate': '24p',
        'videoResolution': 720,
        'width': 1280 (in pixels)
    """
    def __init__(self, data):
        assert isinstance(data, Element)
        self.element = data

    def __repr__(self):
        return str(self.element)

    def __str__(self):
        return str(self.get_data())

    def get_data(self):
        """
        Returns parsed data regarding media type
        :return: dict
        """
        return determine_output(self._parse_data())

    def _parse_data(self):
        """
        Parses data for media type from container element
        :return: dict
        """
        def save_values(data):
            """
            Loops through element attribute dictionary and saves data to output
            dict
            :param data: element attribute dictionary
            :type data: Element
            :return: None
            """
            for key in data.attrib:
                try:
                    # attempt to save key as int
                    output[key] = int(data.attrib[key])
                except (ValueError, KeyError):
                    # not an integer, save as original value
                    output[key] = data.attrib[key]
        output = {}
        save_values(self.element)
        for element in self.element:
            # loop through child element to capture data
            save_values(element)
        return output


class PlexConnectionError(Exception):
    """
    Unable to connect to Plex server
    """
    pass


class PlexAPIKeyNotFound(Exception):
    pass


class PlexLibraryUndefinedType(Exception):
    pass


class PlexMissingVideoKey(Exception):
    pass