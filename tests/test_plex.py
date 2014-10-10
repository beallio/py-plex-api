import unittest
import plexapi
import json
from xml.etree.ElementTree import Element


class testPlexServer(unittest.TestCase):
    server_url, server_port = 'http://192.168.1.101', 32400
    server = None
    library = None

    @classmethod
    def setUpClass(cls):
        cls.server = plexapi.Server(testPlexServer.server_url,
                                    testPlexServer.server_port)
        cls.library = cls.server.library

    def test_bad_connection(self):
        with self.assertRaises(plexapi.PlexConnectionError):
            plexapi.Server('http://192.168.1.102',
                           testPlexServer.server_port)

    def test_good_connection(self):
        testPlexServer.server = testPlexServer.server

    def test_print_server(self):
        plex = testPlexServer.server
        self.assertIsInstance(plex.__str__(), str)

    def test_server_info(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.json), dict)
        self.assertIsInstance(plex.xml, Element)

    def test_server_servers(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.servers.json), dict)
        self.assertIsInstance(plex.servers.xml, Element)

    def test_server_channels(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.channels.json), dict)
        self.assertIsInstance(plex.channels.xml, Element)

    def test_server_prefs(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.preferences.json), dict)
        self.assertIsInstance(plex.preferences.xml, Element)

    def test_print_library(self):
        library = testPlexServer.library
        self.assertIsInstance(library.__str__(), str)

    def test_recentlyadded_all(self):
        library = testPlexServer.library
        self.assertIsInstance(library.get_recently_added(), str)

    def test_recentlyadded_tvshows(self):
        library = testPlexServer.library
        self.assertIsInstance(library.get_recently_added(library.TVSHOWS), str)

    def test_recentlyadded_movies(self):
        library = testPlexServer.library
        self.assertIsInstance(library.get_recently_added(library.MOVIES), str)
