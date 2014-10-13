import urllib2
import urlparse
import json

from xml.etree.ElementTree import XML, Element, tostring
from xmltodict import parse as xmlparse

import exceptions as plexexc


def convert_xml_to_json(values):
    #assert isinstance(values, str)
    values = xmlparse(values)
    output = json.dumps(values, sort_keys=True, skipkeys=True)
    return output


def convert_parse_dump_json(xml):
    return json.dumps(xmlparse(tostring(xml)))


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
        self.info = self.query(Server.SERVERINFO)

    def __repr__(self):
        return str(convert_xml_to_json(self.info))

    def __str__(self):
        return str(convert_xml_to_json(self.info))

    @property
    def address_and_port(self):
        """
        Creates full HTTP address for plex server
        >>> 'http://192.168.1.10:32400'

        :return: str
        """
        scheme = 'http'
        address = self._address
        if not address.startswith(scheme):
            address = ''.join([scheme, '://', address])
        return ''.join([address, ':', str(self._port)])

    @property
    def json(self):
        """
        Returns data in JSON-parsed string
        :return: str
        """
        return json.dumps(xmlparse(self.info))

    @property
    def xml(self):
        """
        Returns data in an XML element
        :return: Element
        """
        return XML(self.info)

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
        return Channels(server=self, query=Server.CHANNELS_ALL)

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
            raise plexexc.PlexConnectionError(err)
        else:
            resp.close()
        return output

    def _test_connection(self):
        """
        Test if connection to Plex is active or not, returns error if unable to
        access _server
        >>> True
        >>> PlexConnectionError
        :return: bool, PlexConnectionError
        """
        # // TODO Need to complete code for authorization if necessary
        resp = self.query(Server.SERVERINFO)
        return resp is not None


class Base(object):
    def __init__(self, server, query):
        assert isinstance(server, Server)
        assert isinstance(query, str)
        self._server = server
        self._query = query

    def __repr__(self):
        return self.query()

    def __str__(self):
        return str(convert_xml_to_json(self.query()))

    @property
    def json(self):
        return convert_xml_to_json(self.query())

    @property
    def xml(self):
        return XML(self.query())

    def query(self):
        return self._server.query(self._query)

    @property
    def items(self):
        return False


class Preferences(Base):
    def __init__(self, server, query):
        super(Preferences, self).__init__(server, query)


class Servers(Base):
    def __init__(self, server, query):
        super(Servers, self).__init__(server, query)


class Channels(Base):
    def __init__(self, server, query):
        super(Channels, self).__init__(server, query)

    @property
    def items(self):
        return [Channel(channel) for channel in self.xml]


class Sections(Base):
    def __init__(self, server, query):
        super(Sections, self).__init__(server, query)

    @property
    def items(self):
        return [Section(self._server, section) for section in self.xml]


class NowPlaying(Base):
    def __init__(self, server, query):
        super(NowPlaying, self).__init__(server, query)


class RecentlyAdded(Base):
    EPISODES = 'Directory'
    MOVIES = 'Video'

    def __init__(self, server, query):
        super(RecentlyAdded, self).__init__(server, query)

    def __repr__(self):
        return str(self.items)

    def __str__(self):
        return str(self.__dict__)

    @property
    def episodes(self):
        return RecentlyAddedVideos(class_obj=self, query=RecentlyAdded.EPISODES)

    @property
    def movies(self):
        return RecentlyAddedVideos(class_obj=self, query=RecentlyAdded.MOVIES)

    @property
    def items(self):
        output = []
        for video in self.xml:
            if RecentlyAdded.EPISODES == video.tag:
                output += [Episode(self._server, video)]
            elif RecentlyAdded.MOVIES == video.tag:
                output += [Movie(self._server, video)]
            else:
                raise plexexc.PlexLibraryUndefinedType
        return output


class RecentlyAddedVideos(object):
    def __init__(self, class_obj, query):
        self._class_obj = class_obj
        self._server = class_obj._server
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
        xml = XML(self._class_obj.query())
        return xml.findall(self._query)

    @property
    def items(self):
        if self._query == RecentlyAdded.MOVIES:
            return [Movie(xml=movie, server=self._server) for movie in
                    self._get_videos_xml()]
        if self._query == RecentlyAdded.EPISODES:
            return [Episode(xml=episode, server=self._server) for episode in
                    self._get_videos_xml()]


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
        return Sections(self._server, self._server.LIBRARYSECTIONS)


class Section(object):
    """
    Section object.  Contains data regarding a library Section Type in a
    dictionary

     '@agent': 'com.plexapp.agents.imdb',
     '@allowSync': '0',
     '@art': '/:/resources/movie-fanart.jpg',
     '@composite': '/library/sections/1/composite/1413178721',
     '@createdAt': '1403479581',
     '@filters': '1',
     '@key': '1',
     '@language': 'en',
     '@refreshing': '0',
     '@scanner': 'Plex Movie Scanner',
     '@thumb': '/:/resources/movie.png',
     '@title': 'Movies',
     '@type': 'movie',
     '@updatedAt': '1413178721',
     '@uuid': 'ccc3be41-8fe3-46fb-8999-2609788f733e',
     'Location': {'@id': '1',
                   '@path': '/Entertainment/Movies'}

    """
    def __init__(self, server, xml):
        assert isinstance(server, Server)
        self.xml = xml
        self.__dict__ = dict(self.__dict__.items() + xml.attrib.items())

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)


class Season(object):
    def __init__(self, library, xml):
        assert isinstance(library, Library)
        self.xml = xml
        self.__dict__ = dict(self.__dict__.items() + xml.attrib.items())

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)


class Video(object):
    def __init__(self, server, xml):
        assert isinstance(server, Server)
        assert isinstance(xml, Element)
        self._server = server
        self.xml = xml
        self.__dict__ = dict(self.__dict__.items() + xml.attrib.items())

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)

    @property
    def media(self):
        """

        """
        return Media(self.xml)

    def _get_metadata(self):
        # to be overwritten by subclass
        pass

    def _query_season_metadata(self, metadata_key):
        assert isinstance(metadata_key, str)
        shows_key = metadata_key.split('/')
        shows_key = '/'.join(shows_key[-2:])
        try:
            metadata = self._server.query(self._server.METADATA, shows_key)
        except KeyError as err:
            raise plexexc.PlexMissingVideoKey(err)
        except urllib2.URLError as err:
            raise plexexc.PlexConnectionError(err)
        else:
            return metadata


class Episode(Video):
    def __init__(self, server, xml):
        super(Episode, self).__init__(server, xml)
        self._season_metadata = self._get_season_metadata()
        self.xml = self._get_metadata()
        self.__dict__ = dict(self.__dict__.items() + self.xml.attrib.items())

    def _get_metadata(self):
        try:
            # use index to find show in season container
            # shows are in array base 1, so offset by -1 to find correct show
            show_index = int(self.leafCount) - 1
        except KeyError as err:
            raise plexexc.PlexMissingVideoKey(err)
        else:
            return self._season_metadata[show_index]

    def _get_season_metadata(self):
        try:
            season_key = self.key
        except KeyError as err:
            raise plexexc.PlexMissingSeasonKey(err)
        else:
            return XML(self. _query_season_metadata(season_key))


class Movie(Video):
    def __init__(self, server, xml):
        super(Movie, self).__init__(server, xml)


class Media(object):
    """
    Media object.  Returns data regarding the media type for a Video in
    a dictionary
    """
    def __init__(self, xml):
        assert isinstance(xml, Element)
        self.xml = xml.findall('Media')

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    @property
    def json(self):
        files = [xmlparse(tostring(media_file)) for media_file in self.xml]
        return json.dumps(files)

    @property
    def items(self):
        return [File(media_file) for media_file in self.xml]


class File(object):
    """
    File-like object.  Returns data regarding the media type for a Video
    file object

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
    def __init__(self, xml):
        assert isinstance(xml, Element)
        self.xml = xml
        self.__dict__ = dict(self.__dict__.items() + self.xml.attrib.items())
        self.part = Part(self.xml)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)


class Part(object):
    """
    'container': 'mkv',
    'duration': '1399107', (microseconds)
    'file': '/path/filename.mkv',
    'id': '2177',
    'key': '/library/parts/2177/file.mkv',
    'size': u'758966231' (in bytes)
    """
    def __init__(self, xml):
        assert isinstance(xml, Element)
        self.xml = xml.find('Part')
        self.__dict__ = dict(self.__dict__.items() + self.xml.attrib.items())

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        pass

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)


class Channel(object):
    def __init__(self, xml):
        self.xml = xml
        self.__dict__ = dict(self.__dict__.items() + xml.attrib.items())

    @property
    def json(self):
        return convert_parse_dump_json(self.xml)