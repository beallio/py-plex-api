import unittest
import plexapi
import json


class testPlexServer(unittest.TestCase):
    server_url, server_port = 'http://192.168.1.101', 32400
    server = None
    library = None

    @classmethod
    def setUpClass(cls):
        cls.server = plexapi.Server(testPlexServer.server_url,
                                    testPlexServer.server_port)
        cls.library = cls.server.library()

    def test_bad_connection(self):
        with self.assertRaises(plexapi.PlexConnectionError):
            plexapi.Server('http://192.168.1.102',
                           testPlexServer.server_port)

    def test_good_connection(self):
        testPlexServer.server = testPlexServer.server

    def test_print_server(self):
        plex = testPlexServer.server
        self.assertIsInstance(plex.__str__(), str)

    def test_server_get_info(self):
        plex = testPlexServer.server
        json_converted = json.loads(plex.get_info())
        self.assertIsInstance(json_converted, dict)

    def test_server_servers(self):
        plex = testPlexServer.server
        json_converted = json.loads(plex.get_servers())
        self.assertIsInstance(json_converted, list)

    def test_server_channels(self):
        plex = testPlexServer.server
        json_converted = json.loads(plex.get_channels())
        self.assertIsInstance(json_converted, list)

    def test_server_prefs(self):
        plex = testPlexServer.server
        json_converted = json.loads(plex.get_preferences())
        self.assertIsInstance(json_converted, list)

    def test_print_library(self):
        library = testPlexServer.library
        self.assertIsInstance(library.__str__(), str)

    def test_recentlyadded(self):
        library = testPlexServer.library
        self.assertIsInstance(library.get_recently_added(), str)